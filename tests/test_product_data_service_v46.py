import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock data that LocalProductService.get_products_by_category would return
    mock_all_category_products = [
        {"id": "prod1", "name": "Laptop XPS", "category": "electronics"},
        {"id": "prod2", "name": "Monitor Ultra", "category": "electronics"},
        {"id": "prod3", "name": "Webcam Pro", "category": "electronics"},
        {"id": "prod4", "name": "Gaming Mouse", "category": "electronics"},
        {"id": "prod5", "name": "Headphones Noise Cancelling", "category": "electronics"},
    ]

    # Patch the method called internally by get_products_by_category
    mock_local_service_method = mocker.patch(
        'app.services.local_product_service.LocalProductService.get_products_by_category',
        return_value=mock_all_category_products
    )

    # Instantiate the service whose method we are testing
    # ProductDataService is assumed to be available in the test's scope.
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    test_category = "electronics"
    test_limit = 3

    # Call the method under test
    result = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that the underlying local_service method was called with the correct category
    mock_local_service_method.assert_called_once_with(test_category)

    # 2. Verify the return type and length (should respect the limit)
    assert isinstance(result, list)
    assert len(result) == test_limit

    # 3. Verify the content matches the expected sliced data
    assert result == mock_all_category_products[:test_limit]

    # Test when limit is greater than available products
    test_limit_all = 10
    result_all = service.get_products_by_category(test_category, test_limit_all)
    assert len(result_all) == len(mock_all_category_products)
    assert result_all == mock_all_category_products
