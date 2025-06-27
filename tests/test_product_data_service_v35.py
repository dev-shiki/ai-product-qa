import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock LocalProductService class to control its behavior
    # This ensures that ProductDataService's __init__ uses a mock instance
    mocker.patch('app.services.product_data_service.LocalProductService')

    # Instantiate the service. Its `local_service` attribute will now be a mock object.
    service = ProductDataService()

    # Define the mock data that local_service.get_products_by_category should return
    # Ensure enough items to test the 'limit' slicing functionality
    mock_products_data = [
        {"id": "e1", "name": "Laptop X", "category": "Electronics"},
        {"id": "e2", "name": "Smartphone Y", "category": "Electronics"},
        {"id": "e3", "name": "Smartwatch Z", "category": "Electronics"},
        {"id": "e4", "name": "Headphones A", "category": "Electronics"},
    ]

    # Set the return value for the mocked method
    service.local_service.get_products_by_category.return_value = mock_products_data

    # Test Case 1: Get products with a specific limit
    category_name = "Electronics"
    limit_value = 2
    result = service.get_products_by_category(category_name, limit_value)

    # Assertions for Test Case 1
    assert isinstance(result, list)
    assert len(result) == limit_value
    assert result == mock_products_data[:limit_value]
    # Verify that the underlying mock method was called correctly
    service.local_service.get_products_by_category.assert_called_once_with(category_name)

    # Reset mock for a new test scenario within the same function
    service.local_service.get_products_by_category.reset_mock()

    # Test Case 2: Get products when the limit is greater than available items
    limit_large = 10
    result_large_limit = service.get_products_by_category(category_name, limit_large)

    # Assertions for Test Case 2
    assert isinstance(result_large_limit, list)
    assert len(result_large_limit) == len(mock_products_data) # Should return all available
    assert result_large_limit == mock_products_data
    service.local_service.get_products_by_category.assert_called_once_with(category_name)

    # Reset mock for error handling test
    service.local_service.get_products_by_category.reset_mock()

    # Test Case 3: Error handling - Simulate an exception from the local service
    service.local_service.get_products_by_category.side_effect = Exception("Simulated service error")
    result_error = service.get_products_by_category("InvalidCategory", 5)

    # Assertions for Test Case 3
    assert result_error == [] # Should return an empty list on error
    service.local_service.get_products_by_category.assert_called_once_with("InvalidCategory")
