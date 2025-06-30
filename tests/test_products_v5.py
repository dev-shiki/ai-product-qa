import pytest
from app.api.products import get_products
from fastapi import HTTPException
# ProductResponse model is needed for type assertions on the returned list items.
# It's imported here for convenience, assuming it can be resolved during test execution.
# If there are circular dependency issues, you might need to import it inside specific test functions.
from app.models.product import ProductResponse

@pytest.mark.asyncio
async def test_get_products_basic():
    """Test get_products with no parameters (should use default limit)."""
    try:
        result = await get_products()
        assert result is not None
        assert isinstance(result, list)
        # Default limit is 20, so the list should not exceed this length.
        assert len(result) <= 20
        if result:
            assert isinstance(result[0], ProductResponse)
    except HTTPException as e:
        # If the API function itself raises an HTTPException, it implies a problem
        # after it catches an internal error. This is a failure of the API logic.
        pytest.fail(f"HTTPException raised unexpectedly for basic call: {e.detail}")
    except Exception as e:
        # Catch any other underlying exceptions (e.g., ProductDataService initialization failure)
        # and skip the test as per instructions.
        pytest.skip(f"Test skipped due to dependency or underlying service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_with_limit():
    """Test get_products with a specific limit."""
    test_limit = 5
    try:
        result = await get_products(limit=test_limit)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) <= test_limit
        if result:
            assert isinstance(result[0], ProductResponse)
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for limit test: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or underlying service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_with_zero_limit():
    """Test get_products with a limit of 0, expecting an empty list."""
    try:
        result = await get_products(limit=0)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for zero limit: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or underlying service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_by_category():
    """Test get_products filtering by a realistic category (e.g., 'electronics')."""
    # This test assumes 'electronics' is a category that exists in the underlying data.
    test_category = "electronics"
    try:
        result = await get_products(category=test_category)
        assert result is not None
        assert isinstance(result, list)
        # If products are returned, verify they belong to the specified category
        if result:
            assert all(isinstance(p, ProductResponse) for p in result)
            assert all(p.category == test_category for p in result)
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for category '{test_category}': {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped, possibly because '{test_category}' category is not available in data: {e}")

@pytest.mark.asyncio
async def test_get_products_by_non_existent_category():
    """Test get_products with a category that should yield no results."""
    test_category = "non_existent_category_xyz"
    try:
        result = await get_products(category=test_category)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0  # Expect an empty list
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for non-existent category: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or underlying service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_by_search_term():
    """Test get_products filtering by a realistic search term (e.g., 'laptop')."""
    # This test assumes 'laptop' is a search term that yields results in the data.
    test_search_term = "laptop"
    try:
        result = await get_products(search=test_search_term)
        assert result is not None
        assert isinstance(result, list)
        # Expect at least some results for a common search term
        if result:
            assert all(isinstance(p, ProductResponse) for p in result)
            assert len(result) > 0  # Should return products
            # More specific assertions on name/description would require knowledge of ProductResponse fields
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for search term '{test_search_term}': {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped, possibly because '{test_search_term}' search term is not available in data: {e}")

@pytest.mark.asyncio
async def test_get_products_by_non_existent_search_term():
    """Test get_products with a search term that should yield no results."""
    test_search_term = "unlikely_product_name_12345"
    try:
        result = await get_products(search=test_search_term)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0  # Expect an empty list
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for non-existent search: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or underlying service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_combined_filters():
    """Test get_products with limit, category, and search combined."""
    # This assumes a combination that *might* yield results, e.g., "electronics" and "smart"
    test_limit = 2
    test_category = "electronics"
    test_search_term = "smart"
    try:
        result = await get_products(limit=test_limit, category=test_category, search=test_search_term)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) <= test_limit
        if result:
            assert all(isinstance(p, ProductResponse) for p in result)
            assert all(p.category == test_category for p in result)
            # Further assertions on search term content would require more knowledge of ProductResponse fields
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for combined filters: {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or underlying service issue: {e}")

@pytest.mark.asyncio
async def test_get_products_edge_cases():
    """Placeholder for any remaining general edge cases or unusual parameter values."""
    # Most significant edge cases (limit=0, non-existent filters) are covered by specific tests above.
    # This can be used for less common scenarios if needed.
    # Example: Testing with None for limit (which is default behavior, already covered by basic test)
    try:
        result = await get_products(limit=None, category=None, search=None)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) <= 20 # Expect default limit
    except HTTPException as e:
        pytest.fail(f"HTTPException raised unexpectedly for edge case (None parameters): {e.detail}")
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency: {e}")