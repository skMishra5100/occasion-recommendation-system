# Occasion-Based Product Recommendation System

A small web app where you type an **occasion** (e.g. *Birthday*, *Diwali*, *Valentine's Day*, *Office Party*) and get a
**ranked list of matching products** from the catalog, shown right below the input box.

## Screenshots

| 1. Occasion input | 2. Product results |
|---|---|
| ![Occasion input](docs/screenshots/01-occasion-input.png) | ![Product results](docs/screenshots/02-results.png) |

## Tech stack

|Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Meaning-based search | sentence-transformers (`all-MiniLM-L6-v2`) + FAISS vector DB|

## Project structure

```
backend/
  main.py          the web API (3 endpoints)
  catalog.py       loads products.json and cleans each product
  recommender.py   the recommendation logic (start reading here)
  try_queries.py   prints results for sample queries in the terminal
  data/
    products.json      the product catalog (given)
    occasions.json     list of occasions: aliases, what people gift, keywords (written by me)
    categories.json    category names for each categoryId (written by me, see "Assumptions")
  tests/           automated tests
frontend/src/
  App.jsx          the page: state + what to show
  api.js           the only file that calls the backend
  hooks/           useDebounce (wait while typing), useRecommendations (fetch results)
  components/      OccasionSearch, ResultsHeader, ProductGrid, ProductCard, EmptyState, ErrorState
```

## Setup instructions

You need **Python 3.10+** and **Node.js 22.12+** (`node -v` to check).
Run the backend and the frontend in **two separate terminals**.

### 1. Backend (terminal 1)

```bash
cd backend
python -m venv .venv
Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- The first start downloads the embedding model (about 90 MB) and then indexes the products. This takes a short while.
  When you see `Ready: 99 products indexed` the API is up.
- *Optional:* to avoid a huge download, install CPU-only PyTorch first:
  `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- Auto-generated API docs: http://localhost:8000/docs

### 2. Frontend (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The dev server forwards every `/api/...` request to the backend on port 8000, so
no extra configuration is needed.

### 3. Run the tests (optional)

```bash
cd backend  && pip install -r requirements-dev.txt 
```

## API usage

### `GET /api/recommendations?occasion=<text>&limit=<number>`

| Parameter | Required | Description |
|---|---|---|
| `occasion` | yes | Any text, 1-200 characters: `Diwali`, `bday`, `Halloween`, ... |
| `limit` | no | How many products to return, 1-60 (default 12) |

```bash
curl "http://localhost:8000/api/recommendations?occasion=Diwali&limit=3"
```

Example response (shortened; the numbers depend on the model):

```json
{
  "query": "Diwali",
  "resolved_occasion": { "name": "Diwali", "match_type": "keyword", "confidence": 1.0 },
  "total": 22,
  "returned": 3,
  "results": [
    {
      "product_id": "cml265ss000gcma01l3qqapo5",
      "vendor_id": "cml24w7at00e0ma01492d51nh",
      "vendor_category": "cml256swj00elma01jdp2zgfb",
      "vendor_category_desc": "Festive Gift Hampers",
      "title": "Diwali Luxury Gift Hampers",
      "description": "Our Diwali Luxury Gift Hampers are curated to celebrate the festival…",
      "snippet": "Our Diwali Luxury Gift Hampers are curated to celebrate the festival with elegance…",
      "files": ["https://…/hamper.png"],
      "image": "https://…/hamper.png",
      "price": 3499.0, "discount_percentage": 10.0, "final_price": 3149.1,
      "score": 0.97,
      "relevance": 1.0,
      "reasons": ["Title mentions \"diwali\"", "Related: festive, festival, hamper"],
      "score_breakdown": { "semantic": 0.62, "keyword": 1.0, "penalty": 0.0 }
    }
  ]
}
```

- `total` = how many products matched; `returned` = how many are in this response (limited by `limit`).

## How the recommendation works

A search goes through four steps (all in `backend/recommender.py`):

1. **Understand the occasion.** Match the text to a known occasion, trying in order:
   a known name or alias (`bday` → Birthday), then a typo (`diwai` → Diwali), then similar meaning
   (`festival of colours` → Holi). If none match, the raw text is searched as it is.
2. **Find products with a similar meaning.** Every product is converted to an *embedding* (a list of numbers that
   captures meaning) with sentence-transformers, and stored in a **FAISS** index. The occasion is converted the same
   way, and FAISS returns the closest products. To make the search better, the occasion is searched using a short
   description of what people gift for it ("festive hampers, dry fruits, candles, diyas…") instead of just the
   single word.
3. **Adjust the scores with simple rules.**
   - **Bonus** when the product's text names the occasion (biggest bonus if it is in the title).
   - **Penalty** when the title is clearly for a *different* occasion (a "Holi hamper" when you searched Diwali).
   - **Ignore generic descriptions.** Some descriptions list many occasions at once
     ("birthdays, weddings, anniversaries…"). Those do not count as a real mention.
4. **Return the best first.** Products far below the best match are dropped, so nonsense input returns nothing.

`final score = similarity + 0.35 × keyword bonus − 0.25 × penalty`


## Possible improvements

- Keep a small list of "good answers" per occasion to measure quality and tune the numbers automatically.
- Use an LLM to write the description of occasions that are not in `occasions.json`.
- Spread results so that near-identical products don't fill the page.

## Libraries and tools used

- [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://www.uvicorn.org/): backend API
- [sentence-transformers](https://www.sbert.net/) with the
  [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) model: text embeddings
- [FAISS](https://github.com/facebookresearch/faiss) (`faiss-cpu`) and [NumPy](https://numpy.org/): vector search
- [React](https://react.dev/), [Vite](https://vite.dev/), [Tailwind CSS](https://tailwindcss.com/): frontend
- [pytest](https://pytest.org/), [Vitest](https://vitest.dev/), [Testing Library](https://testing-library.com/): tests
- Fonts: Bricolage Grotesque and Figtree (Google Fonts, SIL Open Font License)

## AI assistance

I used an AI assistant (Claude by Anthropic) while building this project: for discussing the approach, generating and
simplifying code, writing tests.
