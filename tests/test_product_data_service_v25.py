import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock data that LocalProductService.get_products_by_category would return
    # Create enough products to test limits
    mock_all_electronics_products = [
        {"id": f"e{i}", "name": f"Product {i}", "category": "Electronics"} for i in range(1, 15)
    ]

    # Patch the LocalProductService class definition where it's imported in ProductDataService
    # This ensures that when ProductDataService is initialized, it uses our mock.
    mock_local_service_class = mocker.patch('app.services.product_data_service.LocalProductService')
    
    # Get the mock instance that ProductDataService will use (via its __init__)
    mock_local_service_instance = mock_local_service_class.return_value
    
    # Assume ProductDataService is imported in the test file where this function resides
    # For instance: from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # --- Test Case 1: Get products for a valid category with default limit (10) ---
    mock_local_service_instance.get_products_by_category.return_value = mock_all_electronics_products
    
    test_category_1 = "Electronics"
    products_1 = service.get_products_by_category(test_category_1)

    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category_1)
    assert len(products_1) == 10
    assert all(p["category"] == test_category_1 for p in products_1)
    assert products_1 == mock_all_electronics_products[:10]
    
    mock_local_service_instance.get_products_by_category.reset_mock() # Reset call count for next scenario

    # --- Test Case 2: Get products for a valid category with a custom limit (e.g., 5) ---
    products_2 = service.get_products_by_category(test_category_1, limit=5)

    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category_1)
    assert len(products_2) == 5
    assert all(p["category"] == test_category_1 for p in products_2)
    assert products_2 == mock_all_electronics_products[:5]
    
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 3: Get products for a category with fewer items than the requested limit ---
    mock_local_service_instance.get_products_by_category.return_value = mock_all_electronics_products[:3] # Only 3 products available
    
    products_3 = service.get_products_by_category(test_category_1, limit=10) # Request 10 products

    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category_1)
    assert len(products_3) == 3 # Should return all available products (3)
    assert products_3 == mock_all_electronics_products[:3]
    
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 4: Get products for a non-existent category (LocalProductService returns empty list) ---
    mock_local_service_instance.get_products_by_category.return_value = []
    
    test_category_non_existent = "NonExistentCategory"
    products_4 = service.get_products_by_category(test_category_non_existent)

    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category_non_existent)
    assert len(products_4) == 0
    assert products_4 == []
    
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 5: Exception handling (LocalProductService call raises an exception) ---
    mock_local_service_instance.get_products_by_category.side_effect = Exception("Simulated database error")
    
    test_category_error = "ErrorCategory"
    products_5 = service.get_products_by_category(test_category_error)

    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category_error)
    assert products_5 == [] # Should return an empty list on error
    
    # Clean up side_effect to avoid affecting other tests if mocker persists mocks
    mock_local_service_instance.get_products_by_category.side_effect = None
