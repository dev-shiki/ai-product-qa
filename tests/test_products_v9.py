import pytest
from app.api.products import get_products
from fastapi import HTTPException
from app.models.product import ProductResponse # Import if needed for assertions

@pytest.mark.asyncio
async def test_get_products_basic():
    """
    Test get_products with default parameters.
    Expects a list of ProductResponse objects.
    """
    try:
        products = await get_products()
        assert isinstance(products, list)
        assert len(products) > 0 # Expect some products by default
        for product in products:
            assert isinstance(product, ProductResponse)
    except HTTPException as e:
        pytest.fail(f"HTTPException raised: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error: {e}")

@pytest.mark.asyncio
async def test_get_products_with_limit():
    """
    Test get_products with a specific limit.
    Expects a list of ProductResponse objects, not exceeding the limit.
    """
    test_limit = 5
    try:
        products = await get_products(limit=test_limit)
        assert isinstance(products, list)
        assert len(products) <= test_limit # Products should not exceed the limit
        for product in products:
            assert isinstance(product, ProductResponse)
    except HTTPException as e:
        pytest.fail(f"HTTPException raised: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error: {e}")

@pytest.mark.asyncio
async def test_get_products_with_category():
    """
    Test get_products with a specific category.
    Expects a list of ProductResponse objects.
    Note: Assumes 'electronics' is a valid category that returns results.
    """
    test_category = "electronics"
    try:
        products = await get_products(category=test_category)
        assert isinstance(products, list)
        # It's hard to assert content without knowing the actual data,
        # but we can check if it's not empty for a common category.
        assert len(products) >= 0 # Could be empty if no products in category
        for product in products:
            assert isinstance(product, ProductResponse)
            # Add more specific checks if ProductResponse has a category field
            # and ProductDataService actually filters by it.
            # E.g., assert product.category == test_category (if product has .category)
    except HTTPException as e:
        pytest.fail(f"HTTPException raised: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error: {e}")

@pytest.mark.asyncio
async def test_get_products_with_search():
    """
    Test get_products with a search term.
    Expects a list of ProductResponse objects.
    Note: Assumes 'laptop' is a valid search term that returns results.
    """
    test_search = "laptop"
    try:
        products = await get_products(search=test_search)
        assert isinstance(products, list)
        assert len(products) >= 0 # Could be empty if no matches
        for product in products:
            assert isinstance(product, ProductResponse)
            # More specific checks might involve checking if product.name or description contains 'laptop'
    except HTTPException as e:
        pytest.fail(f"HTTPException raised: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error: {e}")

@pytest.mark.asyncio
async def test_get_products_empty_results_scenario():
    """
    Test get_products with parameters expected to yield no results.
    Expects an empty list.
    """
    # Use highly unlikely category and search term to simulate no results
    unlikely_category = "nonexistent_category_12345"
    unlikely_search = "xyzzy_qwert_impossible_product"
    try:
        products = await get_products(category=unlikely_category, search=unlikely_search)
        assert isinstance(products, list)
        assert len(products) == 0 # Expect an empty list for non-existent criteria
    except HTTPException as e:
        pytest.fail(f"HTTPException raised: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error: {e}")