import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Instantiate the service. ProductDataService needs to be imported by the test environment.
    service = ProductDataService()

    # Create a mock for the internal local_service attribute.
    # MagicMock is assumed to be available in the test environment (e.g., imported globally or via pytest-mock fixture).
    mock_local_service = MagicMock()
    service.local_service = mock_local_service

    # --- Test Case 1: Successful retrieval with limit applied ---
    # Prepare mock return value with more items than the limit to test slicing logic.
    mock_products_from_service = [
        {"id": f"id_{i}", "name": f"Product {i}", "category": "Electronics"} for i in range(15)
    ]
    mock_local_service.get_products_by_category.return_value = mock_products_from_service
    mock_local_service.get_products_by_category.reset_mock() # Reset call count for this specific test case

    category_name = "Electronics"
    limit_count = 5
    
    # Call the method under test
    products = service.get_products_by_category(category_name, limit_count)

    # Assertions for successful case
    mock_local_service.get_products_by_category.assert_called_once_with(category_name)
    assert isinstance(products, list)
    assert len(products) == limit_count
    assert products[0]["id"] == "id_0" # Check first item
    assert products[limit_count - 1]["id"] == f"id_{limit_count - 1}" # Check last item in slice
    assert all(p.get("category") == category_name for p in products) # All products should match category

    # --- Test Case 2: Category not found / empty result from local service ---
    mock_local_service.get_products_by_category.return_value = []
    mock_local_service.get_products_by_category.reset_mock() # Reset call count

    category_name_not_found = "NonExistentCategory"
    products_empty = service.get_products_by_category(category_name_not_found, 10)

    # Assertions for empty result case
    mock_local_service.get_products_by_category.assert_called_once_with(category_name_not_found)
    assert isinstance(products_empty, list)
    assert len(products_empty) == 0

    # --- Test Case 3: Exception handling from local service ---
    mock_local_service.get_products_by_category.side_effect = Exception("Simulated internal service error")
    mock_local_service.get_products_by_category.reset_mock() # Reset call count

    category_name_error = "CategoryWithIssue"
    products_error = service.get_products_by_category(category_name_error, 10)

    # Assertions for error handling case
    mock_local_service.get_products_by_category.assert_called_once_with(category_name_error)
    assert isinstance(products_error, list)
    assert len(products_error) == 0
