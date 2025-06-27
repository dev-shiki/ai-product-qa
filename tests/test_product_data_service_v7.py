import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock data that LocalProductService.get_products_by_category would return
    mock_all_products_in_category = [
        {"id": "p1", "name": "Laptop A", "category": "electronics"},
        {"id": "p2", "name": "Smartphone B", "category": "electronics"},
        {"id": "p3", "name": "Headphones C", "category": "electronics"},
    ]

    # Create a mock for the LocalProductService instance
    mock_local_service = mocker.MagicMock()
    mock_local_service.get_products_by_category.return_value = mock_all_products_in_category

    # Patch the LocalProductService class so that when ProductDataService initializes,
    # it uses our mock instance instead of the real one.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service)

    # Instantiate the service under test
    service = ProductDataService()

    category = "electronics"
    limit = 2

    # Call the method being tested
    result = service.get_products_by_category(category, limit)

    # Assertions
    # 1. Verify that local_service.get_products_by_category was called with the correct arguments
    mock_local_service.get_products_by_category.assert_called_once_with(category)

    # 2. Verify the type of the result
    assert isinstance(result, list)

    # 3. Verify the length of the result, which should be limited by the 'limit' parameter
    assert len(result) == limit

    # 4. Verify the content of the result matches the expected sliced data
    expected_products = [
        {"id": "p1", "name": "Laptop A", "category": "electronics"},
        {"id": "p2", "name": "Smartphone B", "category": "electronics"},
    ]
    assert result == expected_products
