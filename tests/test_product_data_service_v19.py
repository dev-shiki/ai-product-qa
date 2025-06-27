import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(monkeypatch):
    # Mock data that LocalProductService.get_products_by_category would return
    # Ensure this mock data is longer than the 'limit' used in tests
    mock_all_products_for_category = [
        {"id": "101", "name": "Smartphone X", "category": "Electronics"},
        {"id": "102", "name": "Laptop Pro", "category": "Electronics"},
        {"id": "103", "name": "Smartwatch V", "category": "Electronics"},
        {"id": "201", "name": "Fiction Book A", "category": "Books"},
    ]

    # Create a MagicMock for the LocalProductService instance
    mock_local_service_instance = MagicMock()

    # Define the side_effect for the mocked get_products_by_category method
    def mock_get_products_by_category_effect(category_arg):
        if category_arg == "Electronics":
            return [p for p in mock_all_products_for_category if p["category"] == "Electronics"]
        return []

    mock_local_service_instance.get_products_by_category.side_effect = mock_get_products_by_category_effect

    # Patch the LocalProductService class so that when ProductDataService initializes,
    # it uses our mock instance instead of the real one.
    # The patch target is the module where LocalProductService is imported by ProductDataService.
    monkeypatch.setattr('app.services.product_data_service.LocalProductService', MagicMock(return_value=mock_local_service_instance))

    # Instantiate the ProductDataService (which will now use our mocked LocalProductService)
    service = ProductDataService()

    # Test Case 1: Get products for an existing category with a specific limit
    test_category = "Electronics"
    test_limit = 2
    
    result_products = service.get_products_by_category(test_category, test_limit)
    
    # Assert the expected output
    expected_products = [
        {"id": "101", "name": "Smartphone X", "category": "Electronics"},
        {"id": "102", "name": "Laptop Pro", "category": "Electronics"},
    ]
    assert result_products == expected_products
    # Assert that the underlying mock method was called once with the correct arguments
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # Test Case 2: Get products for a non-existing category
    mock_local_service_instance.get_products_by_category.reset_mock() # Reset call count for the new test
    test_category_non_existent = "Fashion"
    
    result_empty = service.get_products_by_category(test_category_non_existent, test_limit)
    
    assert result_empty == []
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category_non_existent)

    # Test Case 3: Error handling in local_service
    mock_local_service_instance.get_products_by_category.reset_mock()
    mock_local_service_instance.get_products_by_category.side_effect = Exception("Mocked service error")

    result_error = service.get_products_by_category(test_category, test_limit)
    
    assert result_error == []
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)
