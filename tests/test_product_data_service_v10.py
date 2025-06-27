import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Import the service class within the test function if running it in isolation,
    # or ensure it's imported at the module level in a real test file.
    # For this specific output format, we assume ProductDataService is accessible.
    from app.services.product_data_service import ProductDataService

    # Mock the LocalProductService class so that when ProductDataService is initialized,
    # its self.local_service attribute becomes a mock object.
    mock_local_service_class = mocker.patch('app.services.product_data_service.LocalProductService')
    
    # Instantiate the service. self.local_service will now be our mock.
    service = ProductDataService()
    
    # Define dummy data that the mocked local_service method should return.
    mock_products_from_source = [
        {"id": "p1", "name": "Laptop", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone", "category": "Electronics"},
        {"id": "p3", "name": "Headphones", "category": "Electronics"},
        {"id": "p4", "name": "Smartwatch", "category": "Electronics"},
        {"id": "p5", "name": "Tablet", "category": "Electronics"},
    ]
    
    # Configure the mock method's return value.
    # When service.local_service.get_products_by_category is called, it will return mock_products_from_source.
    service.local_service.get_products_by_category.return_value = mock_products_from_source

    # Define the test parameters
    test_category = "Electronics"
    test_limit = 3
    
    # Call the method under test
    result = service.get_products_by_category(test_category, limit=test_limit)
    
    # Assertions
    # 1. Verify that the underlying local_service method was called correctly
    service.local_service.get_products_by_category.assert_called_once_with(test_category)
    
    # 2. Verify the number of products returned matches the limit
    assert len(result) == test_limit
    
    # 3. Verify the content of the returned products (should be the first 'limit' items)
    expected_products = mock_products_from_source[:test_limit]
    assert result == expected_products

    # Test with a different limit where source has fewer items than limit
    test_category_small = "Books"
    test_limit_large = 10
    mock_products_small_source = [
        {"id": "b1", "name": "The Great Novel", "category": "Books"},
        {"id": "b2", "name": "Cookbook", "category": "Books"},
    ]
    service.local_service.get_products_by_category.return_value = mock_products_small_source
    
    result_small = service.get_products_by_category(test_category_small, limit=test_limit_large)

    # 4. Verify that the underlying local_service method was called correctly again
    service.local_service.get_products_by_category.assert_called_with(test_category_small) # called with new category
    assert len(result_small) == len(mock_products_small_source) # Should return all available, capped by source
    assert result_small == mock_products_small_source

    # Test case for no products found for a category
    test_category_empty = "NonExistentCategory"
    service.local_service.get_products_by_category.return_value = []
    
    result_empty = service.get_products_by_category(test_category_empty)
    
    assert len(result_empty) == 0
    assert result_empty == []
