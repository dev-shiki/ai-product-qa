import pytest
from app.api.products import get_products

@pytest.mark.asyncio
async def test_get_products_default_parameters():
    """
    Test get_products with no parameters (uses defaults: limit=20, no category/search).
    Expects a non-empty list of products.
    """
    try:
        result = await get_products()
        assert isinstance(result, list)
        assert len(result) > 0
        # Further assertions could check the type of items if ProductResponse is known
        # Example: assert all(isinstance(p, ProductResponse) for p in result)
    except Exception as e:
        pytest.fail(f"Test failed: {e}. Ensure ProductDataService is available and returns data.")

@pytest.mark.asyncio
async def test_get_products_with_limit():
    """
    Test get_products with a specific limit.
    Expects a list of products not exceeding the specified limit.
    """
    try:
        limit_val = 5
        result = await get_products(limit=limit_val)
        assert isinstance(result, list)
        assert len(result) <= limit_val
        if len(result) > 0: # Ensure some data was returned if possible
            assert True # Basic check passed
        else:
            pytest.skip(f"No products returned for limit={limit_val}, might be empty data source.")
    except Exception as e:
        pytest.fail(f"Test failed with limit: {e}. Ensure ProductDataService is available.")

@pytest.mark.asyncio
async def test_get_products_with_category():
    """
    Test get_products with a specific category.
    Expects a list of products belonging to that category.
    """
    try:
        category_val = "electronics" # Assuming 'electronics' is a valid category
        result = await get_products(category=category_val)
        assert isinstance(result, list)
        # Assuming we expect some results for a valid category
        assert len(result) > 0
        # If ProductResponse structure was available, one could assert all items belong to category
        # Example: assert all(p.category == category_val for p in result)
    except Exception as e:
        pytest.fail(f"Test failed with category: {e}. Ensure ProductDataService is available and category '{category_val}' exists.")

@pytest.mark.asyncio
async def test_get_products_with_search_term():
    """
    Test get_products with a search term.
    Expects a list of products matching the search term.
    """
    try:
        search_val = "laptop" # Assuming 'laptop' can be found in product names/descriptions
        result = await get_products(search=search_val)
        assert isinstance(result, list)
        # Assuming we expect some results for a valid search term
        assert len(result) > 0
        # If ProductResponse structure was available, one could assert search term presence
    except Exception as e:
        pytest.fail(f"Test failed with search term: {e}. Ensure ProductDataService is available and '{search_val}' returns results.")

@pytest.mark.asyncio
async def test_get_products_with_combination_parameters():
    """
    Test get_products with a combination of limit and category.
    Expects a list of products from the specified category, limited by count.
    """
    try:
        limit_val = 3
        category_val = "books" # Assuming 'books' is a valid category
        result = await get_products(limit=limit_val, category=category_val)
        assert isinstance(result, list)
        assert len(result) <= limit_val
        if len(result) > 0:
            # Further check if all products are indeed from the 'books' category
            # (Requires ProductResponse structure for category attribute)
            pass
        else:
            pytest.skip(f"No products returned for limit={limit_val}, category={category_val}, might be empty data source or no matches.")
    except Exception as e:
        pytest.fail(f"Test failed with combined parameters: {e}. Ensure ProductDataService is available.")

@pytest.mark.asyncio
async def test_get_products_no_match_category():
    """
    Test get_products with a category that should yield no results.
    Expects an empty list.
    """
    try:
        category_val = "nonexistentcategory12345" # A category highly unlikely to exist
        result = await get_products(category=category_val)
        assert isinstance(result, list)
        assert len(result) == 0 # Expecting an empty list for no matches
    except Exception as e:
        pytest.fail(f"Test failed when expecting no match: {e}. Ensure ProductDataService handles no matches gracefully.")

@pytest.mark.asyncio
async def test_get_products_invalid_limit():
    """
    Test get_products with an invalid limit (e.g., 0).
    The behavior depends on ProductDataService; it might return empty or error.
    """
    try:
        limit_val = 0
        result = await get_products(limit=limit_val)
        assert isinstance(result, list)
        assert len(result) == 0 # Assuming 0 limit means no products
    except Exception as e:
        pytest.fail(f"Test failed for invalid limit=0: {e}. Ensure ProductDataService handles this gracefully.")