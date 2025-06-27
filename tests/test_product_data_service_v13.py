import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Import ProductDataService inside the test function as it's an instance method.
    # Assuming this specific import within the test function is allowed given the context.
    from app.services.product_data_service import ProductDataService

    # Create a mock for the LocalProductService instance that ProductDataService uses.
    mock_local_service_instance = mocker.MagicMock()

    # Define the return value for the 'get_products_by_category' method of the mock.
    # ProductDataService's method slices this result with `[:limit]`.
    mock_products = [
        {"id": "p1", "name": "Shirt A", "category": "Apparel"},
        {"id": "p2", "name": "Pants B", "category": "Apparel"},
        {"id": "p3", "name": "Shoes C", "category": "Apparel"},
        {"id": "p4", "name": "Socks D", "category": "Apparel"},
        {"id": "p5", "name": "Hat E", "category": "Apparel"},
    ]
    mock_local_service_instance.get_products_by_category.return_value = mock_products

    # Patch the LocalProductService class so that when ProductDataService is initialized,
    # it uses our mock instance instead of the real one.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Instantiate ProductDataService. It will now use the mocked LocalProductService.
    service = ProductDataService()

    # Define test parameters
    test_category = "Apparel"
    test_limit = 3

    # Call the method under test
    result = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that the underlying local service method was called correctly with the category.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # 2. Verify the result returned by ProductDataService
    # ProductDataService's method should return only 'limit' number of items from the mock's full list.
    expected_result = mock_products[:test_limit]
    assert result == expected_result
    assert len(result) == test_limit
