def titles(answer, n=None):
    return [r["title"] for r in answer["results"][:n]]


def test_diwali_products_come_first(recommender):
    answer = recommender.recommend("Diwali")
    assert answer["resolved_occasion"]["name"] == "Diwali"
    assert all("Diwali" in t for t in titles(answer, 2))


def test_holi_search_does_not_show_diwali_hampers(recommender):
    answer = recommender.recommend("Holi")
    assert all("Holi" in t for t in titles(answer, 2))
    assert not any("Diwali" in t for t in titles(answer, 5))


def test_other_occasion_penalty(recommender):
    """A hamper whose title says 'Holi' should be marked down when someone searches for Diwali."""
    answer = recommender.recommend("Diwali", limit=60)
    holi = next(r for r in answer["results"] if r["title"].startswith("Holi"))
    assert holi["score_breakdown"]["penalty"] > 0


def test_generic_multi_occasion_blurbs_do_not_win(recommender):
    """These descriptions list birthdays AND weddings AND anniversaries... they must not top 'Birthday'."""
    top = titles(recommender.recommend("bday"), 6)
    for generic in ("Housewarming Gifts", "Baby Shower & Newborn Gifts", "Engagement Gift"):
        assert generic not in top


def test_understanding_the_occasion(recommender):
    assert recommender.recommend("bday")["resolved_occasion"]["name"] == "Birthday"                 # alias
    assert recommender.recommend("diwai")["resolved_occasion"]["match_type"] == "typo"             # typo
    assert recommender.recommend("wedding anniversary")["resolved_occasion"]["name"] == "Anniversary"  # longest wins
    assert recommender.recommend("Diwali party gifts")["resolved_occasion"]["name"] == "Diwali"    # name inside text


def test_nonsense_gives_empty_result(recommender):
    answer = recommender.recommend("xqzvw")
    assert answer["total"] == 0 and answer["results"] == [] and answer["resolved_occasion"] is None
    assert recommender.recommend("   ")["results"] == []


def test_unknown_occasion_falls_back_to_keywords(recommender):
    answer = recommender.recommend("chocolate")
    assert answer["resolved_occasion"] is None
    assert any("chocolate" in t.lower() for t in titles(answer, 3))


def test_result_format(recommender):
    answer = recommender.recommend("Wedding", limit=10)
    assert 0 < answer["returned"] <= 10
    ids = [r["product_id"] for r in answer["results"]]
    assert len(ids) == len(set(ids))                                   # no duplicates
    assert answer["results"][0]["relevance"] == 1.0
    for r in answer["results"]:
        assert r["title"] and r["vendor_category_desc"] and r["image"].startswith("http") and len(r["snippet"]) <= 165
        assert not any(key.startswith("_") for key in r)               # private fields are not leaked


def test_unsellable_products_never_appear(recommender):
    ids = {r["product_id"] for q in ("Diwali", "Birthday", "chocolate") for r in recommender.recommend(q, 60)["results"]}
    assert "cmmertyb80001v8m8kl9qc977" not in ids                      # a chocolate that is still under review
