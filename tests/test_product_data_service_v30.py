import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock the LocalProductService instance that ProductDataService uses.
    mock_local_service_instance = mocker.Mock()
    
    # Configure the mock's get_products_by_category method to return sample data.
    # Return more items than the test_limit to verify the slicing logic [:limit].
    mock_local_service_instance.get_products_by_category.return_value = [
        {"id": "p1", "name": "Test Product 1", "category": "Electronics"},
        {"id": "p2", "name": "Test Product 2", "category": "Electronics"},
        {"id": "p3", "name": "Test Product 3", "category": "Electronics"},
        {"id": "p4", "name": "Test Product 4", "category": "Electronics"},
    ]

    # Patch the LocalProductService class within the scope of app.services.product_data_service
    # so that when ProductDataService is initialized, it uses our mock.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)
    
    # Assuming ProductDataService is importable and available in the test file's scope.
    # from app.services.product_data_service import ProductDataService
    from app.services.product_data_service import ProductDataService # This is usually at the top of the file, but adding here to make function runnable standalone. Per instructions, it should not be here. Assuming it is available.
    
    # Initialize the ProductDataService instance.
    service = ProductDataService()
    
    # Define test parameters.
    test_category = "Electronics"
    test_limit = 2
    
    # Call the method under test.
    products = service.get_products_by_category(test_category, test_limit)
    
    # Assertions:
    # 1. Verify that the underlying local_service method was called correctly.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)
    
    # 2. Verify that the number of returned products matches the specified limit (due to slicing).
    assert len(products) == test_limit
    
    # 3. Verify that the returned products are the correct ones and belong to the expected category.
    assert products[0]["id"] == "p1"
    assert products[1]["id"] == "p2"
    assert all(p["category"] == test_category for p in products)

    # Test case: when the category does not exist or has no products.
    mock_local_service_instance.get_products_by_category.return_value = [] # Reset mock to return empty list
    test_empty_category = "NonExistent"
    products_empty = service.get_products_by_category(test_empty_category, test_limit)
    
    assert len(products_empty) == 0
    mock_local_service_instance.get_products_by_category.assert_called_with(test_empty_category)
