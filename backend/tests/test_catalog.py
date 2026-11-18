from catalog import is_sellable, load_products, to_product
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
GOOD = {"name": "Good", "description": "A really nice gift for everyone", "status": "ACTIVE",
        "isApproved": True, "stock": 5}


def test_only_sellable_products_are_kept():
    assert is_sellable(GOOD)
    assert not is_sellable({**GOOD, "status": "DRAFT"})
    assert not is_sellable({**GOOD, "isApproved": False})
    assert not is_sellable({**GOOD, "deletedAt": "2026-01-01"})
    assert not is_sellable({**GOOD, "stock": 0})


def test_placeholder_descriptions_are_skipped():
    assert not is_sellable({**GOOD, "description": "this group is created by Deepesh for clothes"})
    assert not is_sellable({**GOOD, "description": "deepesh created"})
    assert not is_sellable({**GOOD, "description": "gcdyuvdcbdjhbc"})
    assert is_sellable({**GOOD, "description": "Created to be worn together, a lovely pair."})  # normal use of the word


def test_both_field_naming_styles_work():
    from_pdf = to_product({"productId": 7, "vendorId": "v1", "vendor_category_desc": "Cakes", "title": "Cake",
                           "description": "Yum", "files": ["a.jpg"]}, {})
    from_json = to_product({"id": "x", "shopId": "s1", "categoryId": "c1", "name": "Teddy", "description": "Soft",
                            "mainImage": "t.png", "price": "1000", "discountPercentage": "10"}, {"c1": "Soft Toys"})
    assert (from_pdf["product_id"], from_pdf["vendor_id"], from_pdf["title"], from_pdf["image"]) == ("7", "v1", "Cake", "a.jpg")
    assert from_json["vendor_category_desc"] == "Soft Toys" and from_json["final_price"] == 900.0


def test_real_catalog_loads():
    products = load_products(DATA / "products.json", DATA / "categories.json")
    assert 90 <= len(products) <= 104                               # 110 raw rows minus the unsellable ones
    assert all(p["title"] and p["vendor_category_desc"] and p["image"] for p in products)
