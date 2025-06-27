import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Prepare mock data that LocalProductService.get_products_by_category would return
    mock_all_category_products = [
        {"id": "101", "name": "Laptop X", "category": "Electronics"},
        {"id": "102", "name": "Smartphone Y", "category": "Electronics"},
        {"id": "103", "name": "Tablet Z", "category": "Electronics"},
        {"id": "104", "name": "Smartwatch A", "category": "Electronics"},
        {"id": "105", "name": "Headphones B", "category": "Electronics"},
    ]

    # Create a mock instance for LocalProductService
    # This mock instance will be used by ProductDataService
    mock_local_service_instance = mocker.Mock()
    
    # Configure the mock instance's get_products_by_category method
    mock_local_service_instance.get_products_by_category.return_value = mock_all_category_products

    # Patch the LocalProductService class itself in the module where ProductDataService imports it
    # This ensures that when ProductDataService initializes, it uses our mock LocalProductService
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Instantiate ProductDataService
    # Assumes ProductDataService is available in the test scope (e.g., imported at the file level)
    service = ProductDataService()

    category_to_test = "Electronics"
    limit_to_test = 3

    # Call the function under test
    actual_products = service.get_products_by_category(category_to_test, limit_to_test)

    # Assertions for basic functionality:
    # 1. Ensure the result is a list
    assert isinstance(actual_products, list)
    
    # 2. Ensure the length of the list is correct (respects the limit)
    assert len(actual_products) == limit_to_test
    
    # 3. Ensure the content of the list is correct (first 'limit_to_test' items from the mock data)
    assert actual_products == mock_all_category_products[:limit_to_test]

    # 4. Verify that the underlying LocalProductService method was called as expected
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_to_test)
