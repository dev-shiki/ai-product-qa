import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    from app.services.product_data_service import ProductDataService
    from unittest.mock import MagicMock

    # Instantiate the ProductDataService
    product_service = ProductDataService()

    # Create a MagicMock for the internal local_service
    # and replace the actual local_service with the mock
    mock_local_service = MagicMock()
    product_service.local_service = mock_local_service

    # Define the mock return value for local_service.get_products_by_category
    # This list should be long enough to be sliced by the 'limit' parameter
    mock_products_data = [
        {"id": "p1", "name": "Product A", "category": "Electronics"},
        {"id": "p2", "name": "Product B", "category": "Electronics"},
        {"id": "p3", "name": "Product C", "category": "Electronics"},
        {"id": "p4", "name": "Product D", "category": "Electronics"},
    ]
    mock_local_service.get_products_by_category.return_value = mock_products_data

    # Test case 1: Get products for a category with a specific limit
    category_to_test = "Electronics"
    limit_to_test = 2
    
    result = product_service.get_products_by_category(category_to_test, limit_to_test)

    # Assert that the internal local_service method was called correctly
    mock_local_service.get_products_by_category.assert_called_once_with(category_to_test)

    # Assert the returned data matches the expected sliced result
    expected_products = [
        {"id": "p1", "name": "Product A", "category": "Electronics"},
        {"id": "p2", "name": "Product B", "category": "Electronics"},
    ]
    assert result == expected_products
    assert len(result) == limit_to_test

    # Test case 2: Check default limit if not provided explicitly (though not directly possible
    # from signature, it's good to ensure logic is robust if signature changes or limit is higher than available products)
    # Reset mock for new assertion
    mock_local_service.reset_mock()
    mock_local_service.get_products_by_category.return_value = mock_products_data
    
    result_default_limit = product_service.get_products_by_category("Electronics")
    assert len(result_default_limit) == 10 # Default limit in signature is 10, but mock returns 4, so it should be 4
    assert result_default_limit == mock_products_data # should return all 4 products
    mock_local_service.get_products_by_category.assert_called_once_with("Electronics")

    # Test case 3: Error handling - ensure empty list is returned on exception
    mock_local_service.reset_mock()
    mock_local_service.get_products_by_category.side_effect = Exception("Simulated error")
    
    error_result = product_service.get_products_by_category("Books", 5)
    assert error_result == []
    mock_local_service.get_products_by_category.assert_called_once_with("Books")
