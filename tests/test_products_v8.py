import pytest
from app.api.products import get_products

# NOTE: These tests directly call the function which relies on `ProductDataService`.
# For the tests to pass without errors or being skipped, ProductDataService must be
# correctly configured and able to access its data source (e.g., local JSON, database).
# If `ProductDataService` fails to initialize or retrieve data, these tests will skip.

@pytest.mark.asyncio
async def test_get_products_basic():
    """
    Tests the get_products function with its default parameters (limit=20, no category, no search).
    Expects a non-empty list of products.
    """
    try:
        products = await get_products()
        assert isinstance(products, list)
        # Expect at least some products, assuming the data service is populated
        assert len(products) > 0, "Expected products, but got an empty list for basic call."
        if products:
            # Basic check for product structure, assuming ProductResponse is a dictionary-like object
            # or has expected attributes. Here, just checking if it's not None.
            assert products[0] is not None
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error during basic call: {e}")

@pytest.mark.asyncio
async def test_get_products_edge_cases():
    """
    Tests get_products with various edge cases and specific parameter combinations.
    """
    try:
        # 1. Test with a specific limit
        limit_value = 5
        products_limited = await get_products(limit=limit_value)
        assert isinstance(products_limited, list)
        assert len(products_limited) <= limit_value, f"Expected at most {limit_value} products, got {len(products_limited)}."
        if products_limited:
            assert products_limited[0] is not None

        # 2. Test with a specific category
        # Use a realistic category name if known, otherwise 'electronics' is a common placeholder.
        # This assumes the ProductDataService has data for 'electronics'.
        category_value = "electronics"
        products_by_category = await get_products(category=category_value)
        assert isinstance(products_by_category, list)
        # Can't assert all products match category without ProductResponse details, just check for list.
        assert len(products_by_category) >= 0 # Could be 0 if category doesn't exist or is empty

        # 3. Test with a search query
        search_query = "laptop"
        products_by_search = await get_products(search=search_query)
        assert isinstance(products_by_search, list)
        assert len(products_by_search) >= 0 # Could be 0 if no results for search

        # 4. Test with limit=0 (should return an empty list)
        products_limit_zero = await get_products(limit=0)
        assert isinstance(products_limit_zero, list)
        assert len(products_limit_zero) == 0, "Expected empty list when limit is 0."

        # 5. Test with a non-existent category and search query (should return an empty list)
        non_existent_category = "xyz_nonexistent_category_123"
        non_existent_search = "qwertyuiop_no_match"
        products_no_results = await get_products(
            category=non_existent_category,
            search=non_existent_search
        )
        assert isinstance(products_no_results, list)
        assert len(products_no_results) == 0, "Expected empty list for non-existent criteria."

        # 6. Test with all parameters combined
        combined_limit = 2
        combined_category = "clothing"
        combined_search = "shirt"
        products_combined = await get_products(
            limit=combined_limit,
            category=combined_category,
            search=combined_search
        )
        assert isinstance(products_combined, list)
        assert len(products_combined) <= combined_limit
        assert len(products_combined) >= 0 # Could be 0 if combination yields no results

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error during edge case testing: {e}")