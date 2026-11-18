"""
try_queries.py - a quick way to SEE what the recommender returns, without starting the web app.
Handy for checking quality and for tuning the numbers at the top of recommender.py.

    python try_queries.py                       # a built-in set of examples
    python try_queries.py "Diwali" "Halloween"  # your own queries
"""
import sys
from pathlib import Path

from catalog import load_products
from recommender import Recommender, load_occasions, normalize

DATA = Path(__file__).parent / "data"
EXAMPLES = ["Diwali", "Valentine's Day", "bday", "diwai", "festival of colours", "Halloween", "chocolate", "xqzvw"]

recommender = Recommender(load_products(DATA / "products.json", DATA / "categories.json"),
                          load_occasions(DATA / "occasions.json"))

for query in sys.argv[1:] or EXAMPLES:
    answer = recommender.recommend(query, limit=5)
    understood = answer["resolved_occasion"]
    print(f'\n"{query}" -> understood as: {understood["name"] + " (" + understood["match_type"] + ")" if understood else "free text"}'
          f'   ({answer["total"]} matches)')
    for r in answer["results"]:
        b = r["score_breakdown"]
        print(f'   {r["relevance"]:.2f}  similarity={b["semantic"]:.2f} keyword={b["keyword"]:.2f} '
              f'penalty={b["penalty"]:.2f}  {r["title"][:36]:36} [{r["vendor_category_desc"]}]')
