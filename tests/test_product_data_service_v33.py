import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Arrange
    # Mock the internal local_service.get_products_by_category method.
    # We mock the method on the class `LocalProductService` so that any instance
    # of `LocalProductService` created by `ProductDataService` will have this mocked method.
    mock_local_service_get_by_category = mocker.patch(
        'app.services.local_product_service.LocalProductService.get_products_by_category'
    )

    # Define the mock data that the mocked method will return
    mock_products_data = [
        {"id": "1", "name": "Laptop A", "category": "Electronics"},
        {"id": "2", "name": "Laptop B", "category": "Electronics"},
        {"id": "3", "name": "Monitor C", "category": "Electronics"},
        {"id": "4", "name": "Keyboard D", "category": "Electronics"},
        {"id": "5", "name": "Mouse E", "category": "Electronics"},
    ]
    mock_local_service_get_by_category.return_value = mock_products_data

    # Instantiate the ProductDataService.
    # (Assuming ProductDataService is imported at the module level where this test resides)
    service = ProductDataService()

    category_to_test = "Electronics"
    limit_to_test = 3

    # Act
    # Call the target function on the ProductDataService instance
    result = service.get_products_by_category(category_to_test, limit_to_test)

    # Assert
    # 1. Verify that the underlying local service method was called exactly once
    #    with the correct category.
    mock_local_service_get_by_category.assert_called_once_with(category_to_test)

    # 2. Verify that the result matches the expected sliced data from the mock.
    #    The `get_products_by_category` method applies [:limit] slicing.
    expected_products = mock_products_data[:limit_to_test]
    assert result == expected_products
    assert len(result) == limit_to_test
