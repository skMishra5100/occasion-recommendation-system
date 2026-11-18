"""
catalog.py - load products.json and turn each raw record into a clean, simple dictionary.

Two small jobs:
  1. Skip products we should never recommend (drafts, unapproved, out of stock, placeholder rows).
  2. Convert each remaining record into the field names the assignment uses
     (product_id, vendor_id, vendor_category, vendor_category_desc, title, description, files).
"""
import json
from pathlib import Path


def clean(text):
    """Collapse line breaks / extra spaces into single spaces."""
    return " ".join(str(text or "").split())


def to_number(value):
    """Prices come as strings like "1000" - turn them into numbers (None if not possible)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def looks_like_placeholder(description):
    """Some rows hold admin notes or keyboard-mash instead of a real description, e.g.
    "this group is created by Deepesh for clothes" or "gcdyuvdcbdjhbc"."""
    text = description.lower().strip()
    if "created by" in text or text.endswith(" created"):
        return True
    one_long_word = " " not in text and len(text) >= 8
    vowels = sum(ch in "aeiou" for ch in text)
    return one_long_word and vowels / len(text) < 0.2   # almost no vowels = keyboard mash


def is_sellable(item):
    """True only for products worth showing to a customer."""
    if item.get("status", "ACTIVE") != "ACTIVE":     # drafts / "review required"
        return False
    if item.get("isApproved") is False:               # not approved by an admin
        return False
    if item.get("deletedAt"):                         # soft-deleted
        return False
    if item.get("stock", 1) <= 0:                     # out of stock
        return False
    if looks_like_placeholder(str(item.get("description", ""))):
        return False
    return True


def to_product(item, category_names):
    """Convert one raw record to a clean product dict.

    The assignment PDF and the supplied products.json use different field names
    (e.g. `title` vs `name`, `product_id` vs `id`), so each field tries both - this is the
    `payload.get("a") or payload.get("b")` pattern shown in the assignment.
    """
    category_id = item.get("vendor_category") or item.get("categoryId")

    # `files` = list of image URLs. Put mainImage first so it is the picture we show.
    files = [f if isinstance(f, str) else f.get("url") for f in item.get("files") or []]
    if item.get("mainImage"):
        files = [item["mainImage"]] + [f for f in files if f != item["mainImage"]]

    price = to_number(item.get("price"))
    discount = to_number(item.get("discountPercentage")) or 0

    return {
        "product_id": str(item.get("product_id") or item.get("productId") or item.get("id")),
        "vendor_id": item.get("vendor_id") or item.get("vendorId") or item.get("shopId"),
        "vendor_category": category_id,
        # products.json has no category names, so we look them up in data/categories.json
        "vendor_category_desc": item.get("vendor_category_desc") or category_names.get(category_id),
        "title": clean(item.get("title") or item.get("name")),
        "description": clean(item.get("description")),
        "short_description": clean(item.get("shortDescription")),
        "files": files,
        "image": files[0] if files else None,
        "brand": item.get("brand"),
        "price": price,
        "discount_percentage": discount,
        "final_price": round(price * (1 - discount / 100), 2) if price is not None else None,
    }


def load_products(products_path, categories_path):
    """Read the JSON files and return the list of sellable, cleaned products."""
    raw_items = json.loads(Path(products_path).read_text(encoding="utf-8"))
    category_names = json.loads(Path(categories_path).read_text(encoding="utf-8"))
    return [to_product(item, category_names) for item in raw_items if is_sellable(item)]
