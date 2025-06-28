import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Assuming ProductDataService class and unittest.mock.MagicMock are available in the test environment scope.

    # Prepare mock data for LocalProductService's response
    mock_all_products = [
        {"id": "p1", "name": "Laptop Pro", "category": "electronics"},
        {"id": "p2", "name": "Smartphone X", "category": "electronics"},
        {"id": "p3", "name": "Smart TV", "category": "electronics"},
        {"id": "p4", "name": "Wireless Headphones", "category": "electronics"},
        {"id": "p5", "name": "Gaming Console", "category": "electronics"},
        {"id": "p6", "name": "Digital Camera", "category": "electronics"},
        {"id": "p7", "name": "Smart Speaker", "category": "electronics"},
        {"id": "p8", "name": "E-Reader", "category": "electronics"},
        {"id": "p9", "name": "Fitness Tracker", "category": "electronics"},
        {"id": "p10", "name": "Portable Charger", "category": "electronics"},
        {"id": "p11", "name": "Bluetooth Keyboard", "category": "electronics"}, # Extra product
    ]

    # Instantiate ProductDataService
    service = ProductDataService()

    # Create a mock for local_service and its get_products_by_category method
    service.local_service = MagicMock()

    # --- Test Case 1: Get products with default limit (10) ---
    service.local_service.get_products_by_category.return_value = mock_all_products
    
    category_name = "electronics"
    result = service.get_products_by_category(category_name)

    # Assertions for default limit
    service.local_service.get_products_by_category.assert_called_once_with(category_name)
    assert len(result) == 10
    assert result == mock_all_products[:10]

    # --- Test Case 2: Get products with a specific limit (e.g., 5) ---
    service.local_service.get_products_by_category.reset_mock() # Reset mock for a fresh call check
    service.local_service.get_products_by_category.return_value = mock_all_products
    
    custom_limit = 5
    result_limited = service.get_products_by_category(category_name, limit=custom_limit)

    # Assertions for specific limit
    service.local_service.get_products_by_category.assert_called_once_with(category_name)
    assert len(result_limited) == custom_limit
    assert result_limited == mock_all_products[:custom_limit]

    # --- Test Case 3: Category not found (LocalProductService returns empty list) ---
    service.local_service.get_products_by_category.reset_mock()
    service.local_service.get_products_by_category.return_value = []
    
    non_existent_category = "non_existent_category"
    result_empty = service.get_products_by_category(non_existent_category)
    
    # Assertions for empty result
    service.local_service.get_products_by_category.assert_called_once_with(non_existent_category)
    assert len(result_empty) == 0
    assert result_empty == []

    # --- Test Case 4: Exception handling in LocalProductService ---
    service.local_service.get_products_by_category.reset_mock()
    service.local_service.get_products_by_category.side_effect = Exception("Simulated service error")

    error_category = "error_prone_category"
    result_error = service.get_products_by_category(error_category)
    
    # Assertions for error handling
    service.local_service.get_products_by_category.assert_called_once_with(error_category)
    assert result_error == [] # Should return an empty list on error
