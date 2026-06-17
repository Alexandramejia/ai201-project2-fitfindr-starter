from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def test_search_listings_returns_list():
    results = search_listings("jacket")
    assert isinstance(results, list)

def test_search_listings_returns_results_for_valid_query():
    results = search_listings("jacket")
    assert len(results) > 0

def test_search_listings_returns_empty_for_impossible_query():
    results = search_listings("xyzzy123nonsense")
    assert results == []

def test_search_listings_respects_max_price():
    results = search_listings("jacket", max_price=20.00)
    for item in results:
        assert item["price"] <= 20.00


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def test_suggest_outfit_with_example_wardrobe():
    wardrobe = get_example_wardrobe()
    item = search_listings("jacket")[0]
    result = suggest_outfit(item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_with_empty_wardrobe():
    wardrobe = get_empty_wardrobe()
    item = search_listings("jacket")[0]
    result = suggest_outfit(item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def test_create_fit_card_returns_string_for_valid_outfit():
    item = search_listings("jacket")[0]
    result = create_fit_card("A relaxed vintage look with straight-leg jeans and white sneakers.", item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_returns_error_message_for_empty_outfit():
    item = search_listings("jacket")[0]
    result = create_fit_card("", item)
    assert isinstance(result, str)
    assert len(result) > 0
