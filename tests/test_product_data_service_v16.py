import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_success_and_limit(mocker):
    # Mock data that LocalProductService would return
    mock_full_product_list = [
        {"id": "p1", "name": "Laptop", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone", "category": "Electronics"},
        {"id": "p3", "name": "Tablet", "category": "Electronics"},
        {"id": "p4", "name": "Headphones", "category": "Electronics"},
        {"id": "p5", "name": "Smartwatch", "category": "Electronics"},
    ]

    # Create a mock for the LocalProductService instance.
    # This mock will be returned when ProductDataService tries to instantiate LocalProductService.
    mock_local_service_instance = mocker.MagicMock()
    mock_local_service_instance.get_products_by_category.return_value = mock_full_product_list

    # Patch the LocalProductService class itself so that ProductDataService's __init__
    # gets our mock instance when it calls LocalProductService().
    # The patch target needs to be the module where LocalProductService is *imported* and *used*.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Instantiate ProductDataService.
    # ProductDataService class is assumed to be available in the test's scope.
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # Define test parameters
    test_category = "Electronics"
    test_limit = 3

    # Call the method under test
    actual_products = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that the underlying local service method was called with the correct arguments.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # 2. Verify that the returned list contains the correct number of items, respecting the limit.
    assert len(actual_products) == test_limit

    # 3. Verify that the content of the returned list is as expected (the first 'limit' items).
    expected_products = mock_full_product_list[:test_limit]
    assert actual_products == expected_products
