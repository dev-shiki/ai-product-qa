import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock data that the underlying LocalProductService would return (more items than the test limit)
    mock_all_category_products = [
        {"id": "prod_a", "name": "Fantasy Book", "category": "Fiction"},
        {"id": "prod_b", "name": "Sci-Fi Novel", "category": "Fiction"},
        {"id": "prod_c", "name": "Mystery Thriller", "category": "Fiction"},
        {"id": "prod_d", "name": "Historical Drama", "category": "Fiction"},
        {"id": "prod_e", "name": "Romance Anthology", "category": "Fiction"},
    ]

    # Patch the LocalProductService class itself within the product_data_service module.
    # This ensures that when ProductDataService is initialized, it uses our mock.
    mock_local_service_class = mocker.patch('app.services.product_data_service.LocalProductService')

    # Get the mock instance that ProductDataService's __init__ will create
    # and configure its 'get_products_by_category' method to return our mock data.
    mock_local_service_instance = mock_local_service_class.return_value
    mock_local_service_instance.get_products_by_category.return_value = mock_all_category_products

    # Instantiate the ProductDataService.
    # (Assuming ProductDataService is accessible in this scope, e.g., already imported by the test runner)
    from app.services.product_data_service import ProductDataService # This import is typically added by the user
    service = ProductDataService()

    # Define test parameters
    test_category = "Fiction"
    test_limit = 3

    # Call the function under test
    result_products = service.get_products_by_category(test_category, test_limit)

    # Assertions:

    # 1. Verify that the underlying local_service method was called exactly once with the correct category.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # 2. Verify the type of the result (should be a list).
    assert isinstance(result_products, list)

    # 3. Verify the number of products returned matches the specified limit.
    # The get_products_by_category function in ProductDataService applies [:limit] slicing.
    assert len(result_products) == test_limit

    # 4. Verify the content of the returned products.
    # It should be the first `test_limit` items from our mock data.
    expected_products = mock_all_category_products[:test_limit]
    assert result_products == expected_products
