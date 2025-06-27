import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock the LocalProductService class that ProductDataService initializes.
    # This ensures that when ProductDataService is created, it uses our mock.
    mock_local_service_instance = mocker.MagicMock()
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Prepare dummy data for the mock's get_products_by_category method
    dummy_products = [
        {"id": "p1", "name": "Laptop A", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone B", "category": "Electronics"},
        {"id": "p3", "name": "Tablet C", "category": "Electronics"},
        {"id": "p4", "name": "Headphones D", "category": "Electronics"},
        {"id": "p5", "name": "Monitor E", "category": "Electronics"},
    ]
    mock_local_service_instance.get_products_by_category.return_value = dummy_products

    # Initialize the ProductDataService (it will now use our mocked LocalProductService)
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # --- Test Case 1: Get products with a specific category and limit ---
    test_category = "Electronics"
    test_limit = 3
    result = service.get_products_by_category(test_category, test_limit)

    # Assert that the underlying local_service method was called correctly
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # Assert the returned data matches the expected slice
    expected_result = dummy_products[:test_limit]
    assert result == expected_result
    assert len(result) == test_limit

    # --- Test Case 2: Get products when limit is greater than available items ---
    mock_local_service_instance.get_products_by_category.reset_mock() # Reset mock call count
    test_limit_large = 10 # Larger than the number of dummy products
    result_large_limit = service.get_products_by_category(test_category, test_limit_large)

    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)
    # It should return all available products since the limit exceeds them
    assert result_large_limit == dummy_products
    assert len(result_large_limit) == len(dummy_products)

    # --- Test Case 3: Error handling (should return an empty list on exception) ---
    mock_local_service_instance.get_products_by_category.reset_mock()
    mock_local_service_instance.get_products_by_category.side_effect = Exception("Simulated service error")
    result_error = service.get_products_by_category("NonExistentCategory", 5)

    mock_local_service_instance.get_products_by_category.assert_called_once_with("NonExistentCategory")
    assert result_error == []
