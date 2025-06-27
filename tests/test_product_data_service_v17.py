import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Sample data that LocalProductService would return
    mock_products_from_local_service = [
        {"id": "1", "name": "Laptop XYZ", "category": "Electronics"},
        {"id": "2", "name": "Smartphone ABC", "category": "Electronics"},
        {"id": "3", "name": "Headphones 123", "category": "Electronics"},
        {"id": "4", "name": "Smartwatch DEF", "category": "Electronics"},
    ]

    # Create a mock instance for LocalProductService
    mock_local_service_instance = mocker.MagicMock()
    # Configure its get_products_by_category method to return our sample data
    mock_local_service_instance.get_products_by_category.return_value = mock_products_from_local_service

    # Patch the LocalProductService class within the ProductDataService module
    # This ensures that when ProductDataService is initialized, it uses our mock instance.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Instantiate ProductDataService. It will now use the mocked LocalProductService.
    # Assumes ProductDataService is available in the test scope (e.g., imported at the top of the test file).
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # Define test parameters
    test_category = "Electronics"
    test_limit = 2

    # Call the method under test
    result = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that the underlying local_service method was called correctly
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # 2. Verify that the result matches the expected products after applying the limit
    expected_result = mock_products_from_local_service[:test_limit]
    assert result == expected_result
    assert len(result) == test_limit
    assert all(p.get("category") == test_category for p in result)
