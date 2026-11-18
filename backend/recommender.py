"""
recommender.py - the recommendation engine. Read it top to bottom; it follows the same order as a search.

HOW A SEARCH WORKS
  1. Understand the occasion  "bday" -> Birthday  (known name -> typo -> similar meaning)
  2. Find similar products    embeddings + FAISS: which products are closest in meaning to the occasion?
  3. Adjust the scores        + bonus if the product mentions the occasion in its text
                              - penalty if the title is clearly for a DIFFERENT occasion
  4. Return the best ones     highest score first

WHY NOT JUST EMBEDDINGS?
  Many products in this catalog share the same description (e.g. the Diwali, Holi and Christmas
  hampers), so meaning alone cannot tell them apart. Looking for the occasion's name in the product
  text fixes that. Meaning (embeddings) + keywords = "hybrid" search.
"""
import difflib
import json
from pathlib import Path

import faiss
import numpy as np

# ---------------------------------------------------------------------------
# Numbers you can tweak (run `python try_queries.py` after changing them)
# ---------------------------------------------------------------------------
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"   # small, fast, good general-purpose embeddings

MIN_SIMILARITY = 0.20          # a product below this similarity is treated as unrelated
KEEP_RATIO = 0.60              # ...and so is a product scoring below 60% of the best match
KEYWORD_WEIGHT = 0.35          # how much the keyword bonus counts compared with similarity
OTHER_OCCASION_PENALTY = 0.25  # taken off products whose title is for a different occasion
TYPO_CUTOFF = 0.84             # how close a misspelling must be to a known name ("diwai" -> "diwali")
MEANING_CUTOFF = 0.55          # how close in meaning the query must be to a known occasion

STOPWORDS = {"a", "an", "and", "for", "the", "to", "of", "my", "me", "in", "on", "with", "gift", "gifts",
             "idea", "ideas", "present", "presents", "some", "something", "what", "you", "your"}


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------
def normalize(text):
    """Lowercase and strip punctuation: "Valentine's Day!" -> "valentines day"."""
    text = text.lower().replace("'", "").replace("’", "")
    return " ".join("".join(ch if ch.isalnum() else " " for ch in text).split())


def contains(text, phrase):
    """True if `phrase` appears in `text` as whole word(s). Allows a plural: "hamper" matches "hampers"."""
    padded = f" {text} "
    return any(f" {phrase}{ending} " in padded for ending in ("", "s", "es"))


def make_snippet(text, max_chars=160):
    """Shorten a description for the product card, cutting at a word boundary."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"


def load_occasions(path):
    """Read data/occasions.json and add normalized copies of the names we match against."""
    occasions = json.loads(Path(path).read_text(encoding="utf-8"))
    for occ in occasions:
        occ["key"] = normalize(occ["name"])                                   # "valentines day"
        occ["names"] = [normalize(n) for n in [occ["name"], *occ["aliases"]]]  # name + aliases
        occ["related"] = {normalize(r) for r in occ.get("related", [])}       # occasions that are close cousins
        # extra keywords, without the occasion's own name (that is already scored separately)
        occ["extra_keywords"] = [k for k in map(normalize, occ["keywords"]) if k not in occ["names"]]
    return occasions


# ---------------------------------------------------------------------------
# The recommender
# ---------------------------------------------------------------------------
class Recommender:
    def __init__(self, products, occasions, model=None):
        """`model` is only passed in by the tests (a tiny fake). Normally we load the real one."""
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(MODEL_NAME)
        self.model = model
        self.products = products
        self.occasions = occasions

        # --- Step A: turn every product into a vector and put the vectors in a FAISS index ---
        texts = [f'{p["title"]}. Category: {p["vendor_category_desc"]}. '
                 f'{p["description"] or p["short_description"]}' for p in products]
        vectors = self.embed(texts)
        self.index = faiss.IndexFlatIP(vectors.shape[1])   # inner product on unit vectors = cosine similarity
        self.index.add(vectors)

        # --- Step B: turn every occasion into vectors too ---
        # "label" vector: short text, used to recognise what the user typed
        self.label_vectors = self.embed([f'{o["name"]} ({", ".join(o["aliases"][:6])})' for o in occasions])
        # "profile" vector: long description of what people gift, used to search for products
        self.profile_vectors = self.embed([f'Gift ideas for {o["name"]}. {o["description"]}' for o in occasions])

        # --- Step C: pre-compute text we compare against, and which occasions each product names ---
        for p in products:
            p["_title"] = normalize(p["title"])
            p["_text"] = normalize(f'{p["title"]} {p["description"]} {p["short_description"]}')
            p["_title_occasions"] = self.occasions_named_in(p["_title"])
            p["_desc_occasions"] = self.occasions_named_in(normalize(p["description"]))

    # ----- helpers --------------------------------------------------------
    def embed(self, texts):
        """Text -> unit-length vectors (so a dot product equals cosine similarity)."""
        return np.asarray(self.model.encode(texts, normalize_embeddings=True), dtype="float32")

    def occasions_named_in(self, text):
        """Which occasions does this text mention by name? e.g. "holi dry fruits hampers" -> {"holi"}"""
        return {o["key"] for o in self.occasions if any(contains(text, name) for name in o["names"])}

    
    def find_occasion(self, query, query_vector):
        """Match what the user typed to a known occasion. Returns (occasion, how, confidence)."""
        # 1a. The query contains a known name/alias: "bday", "diwali gifts". Longest match wins, so
        #     "wedding anniversary" picks Anniversary rather than Wedding.
        best, best_length = None, 0
        for occ in self.occasions:
            for name in occ["names"]:
                if len(name) > best_length and contains(query, name):
                    best, best_length = occ, len(name)
        if best:
            return best, "keyword", 1.0

        # 1b. A typo of a known name: "diwai" -> "diwali"
        if len(query) >= 4:
            lookup = {name: occ for occ in self.occasions for name in occ["names"]}
            close = difflib.get_close_matches(query, list(lookup), n=1, cutoff=TYPO_CUTOFF)
            if close:
                return lookup[close[0]], "typo", 1.0

        # 1c. Similar meaning: "festival of colours" is close to Holi
        similarity = self.label_vectors @ query_vector
        best_index = int(np.argmax(similarity))
        if similarity[best_index] >= MEANING_CUTOFF:
            return self.occasions[best_index], "meaning", float(similarity[best_index])

        return None, "none", float(similarity[best_index])  

    
    @staticmethod
    def keyword_score(product, names, keywords):
        """0..1 score for how clearly the product's TEXT mentions the occasion, plus the reasons why."""
        score, reasons = 0.0, []

        title_hit = next((n for n in names if contains(product["_title"], n)), None)
        text_hit = next((n for n in names if contains(product["_text"], n)), None)
        if title_hit:                                   # strongest signal: the title names the occasion
            score += 1.0
            reasons.append(f'Title mentions "{title_hit}"')
        elif text_hit and len(product["_desc_occasions"]) < 3:
            # Mentioned only in the description. If the description lists 3+ different occasions
            # ("birthdays, weddings, anniversaries...") it is a generic blurb, so we ignore it.
            score += 0.5
            reasons.append(f'Description mentions "{text_hit}"')

        hits = [k for k in keywords if contains(product["_text"], k)]
        score += min(0.15 * len(hits), 0.45)            # each related keyword adds a little, up to a cap
        if hits:
            reasons.append("Related: " + ", ".join(hits[:3]))
        return min(score, 1.0), reasons

    # ----- The whole search -------------------------------------------------
    def recommend(self, query, limit=12):
        query = query.strip()
        q = normalize(query)
        if not q:
            return {"query": query, "resolved_occasion": None, "total": 0, "returned": 0, "results": []}

        query_vector = self.embed([query])[0]
        occasion, how, confidence = self.find_occasion(q, query_vector)

        # Decide what to search with.
        if occasion:
            i = self.occasions.index(occasion)
            # mostly the occasion's rich description, plus a little of what the user actually typed
            search_vector = 0.75 * self.profile_vectors[i] + 0.25 * query_vector
            search_vector /= np.linalg.norm(search_vector)
            names, keywords = occasion["names"], occasion["extra_keywords"]
        else:
            search_vector = query_vector
            names = [q]
            keywords = [w for w in q.split() if len(w) > 2 and w not in STOPWORDS]

        # Step 2: FAISS gives the similarity of EVERY product (the catalog is small, so we ask for all).
        similarities, product_ids = self.index.search(search_vector.reshape(1, -1), len(self.products))
        similarities, product_ids = similarities[0], product_ids[0]       # best first
        cutoff = max(MIN_SIMILARITY, KEEP_RATIO * similarities[0])

        # Step 3: score each product.
        scored = []
        for similarity, pid in zip(similarities, product_ids):
            product = self.products[pid]
            keyword, reasons = self.keyword_score(product, names, keywords)

            # Skip unrelated products - unless the text clearly mentions the occasion.
            if similarity < cutoff and keyword < 0.5:
                continue

            # Penalty: the title names a different occasion ("Holi hamper" when searching Diwali).
            penalty = 0.0
            if occasion:
                others = product["_title_occasions"]
                if others and occasion["key"] not in others and not (others & occasion["related"]):
                    penalty = OTHER_OCCASION_PENALTY

            score = float(similarity) + KEYWORD_WEIGHT * keyword - penalty
            scored.append((score, float(similarity), keyword, penalty, reasons, product))

        # Step 4: best first, cut to `limit`.
        scored.sort(key=lambda row: row[0], reverse=True)
        best_score = max(scored[0][0], 1e-9) if scored else 1.0
        results = []
        for score, similarity, keyword, penalty, reasons, product in scored[:limit]:
            result = {k: v for k, v in product.items() if not k.startswith("_")}   # drop our private fields
            result.update(
                snippet=make_snippet(product["description"] or product["short_description"]),
                score=round(score, 4),
                relevance=round(max(score, 0) / best_score, 4),      # 0..1 compared with the best result
                reasons=reasons[:3],
                score_breakdown={"semantic": round(similarity, 4), "keyword": round(keyword, 4), "penalty": penalty},
            )
            results.append(result)

        return {
            "query": query,
            "resolved_occasion": {"name": occasion["name"], "match_type": how, "confidence": round(confidence, 3)}
            if occasion else None,
            "total": len(scored),
            "returned": len(results),
            "results": results,
        }
