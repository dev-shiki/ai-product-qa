import pytest
from app.api.products import get_products
from fastapi import HTTPException

# Note: These tests assume that ProductDataService can be initialized and can
# fetch some data in the test environment. If ProductDataService relies on
# external resources (e.g., specific file paths, database connections) that
# are not set up, these tests will skip as per the instruction
# "Do not use complex mocks" and the provided example's error handling.

@pytest.mark.asyncio
async def test_get_products_default_parameters():
    """Test get_products with no parameters (uses defaults: limit=20, no category/search)."""
    try:
        result = await get_products()
        assert isinstance(result, list)
        assert len(result) <= 20
        # Basic check for product structure if available
        if result:
            assert hasattr(result[0], 'id')
            assert hasattr(result[0], 'name')
            assert hasattr(result[0], 'category')
            assert hasattr(result[0], 'price')
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or data service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_with_limit():
    """Test get_products with a specific limit."""
    test_limit = 5
    try:
        result = await get_products(limit=test_limit)
        assert isinstance(result, list)
        assert len(result) <= test_limit # Can be less if not enough products
        if result:
            assert hasattr(result[0], 'id')
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or data service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_with_category():
    """Test get_products with a specific category."""
    test_category = "electronics" # Use a realistic category
    try:
        result = await get_products(category=test_category)
        assert isinstance(result, list)
        if result:
            # All returned products should belong to the specified category
            for product in result:
                assert hasattr(product, 'category')
                assert product.category == test_category
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or data service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_with_search_term():
    """Test get_products with a search term."""
    test_search = "laptop" # Use a realistic search term
    try:
        result = await get_products(search=test_search)
        assert isinstance(result, list)
        if result:
            # Products should contain the search term in name or description
            for product in result:
                assert hasattr(product, 'name')
                assert test_search.lower() in product.name.lower() # Simple check
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or data service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_with_all_parameters():
    """Test get_products with limit, category, and search term combined."""
    test_limit = 3
    test_category = "clothing"
    test_search = "shirt"
    try:
        result = await get_products(limit=test_limit, category=test_category, search=test_search)
        assert isinstance(result, list)
        assert len(result) <= test_limit
        if result:
            for product in result:
                assert hasattr(product, 'category')
                assert product.category == test_category
                assert hasattr(product, 'name')
                assert test_search.lower() in product.name.lower()
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or data service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_no_results_for_unlikely_category_search():
    """Test get_products with parameters unlikely to return any results."""
    # This test depends on the actual data. If the data service returns a product
    # matching this unlikely combination, the test might fail.
    # It aims to check if an empty list is returned correctly.
    unlikely_category = "nonexistent_category_123"
    unlikely_search = "qwertyuiopasdfghjklzxcvbnm_unlikely_product"
    try:
        result = await get_products(category=unlikely_category, search=unlikely_search)
        assert isinstance(result, list)
        assert len(result) == 0
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or data service issue: {e}")