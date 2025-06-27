import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock the LocalProductService.get_products_by_category method
    # to control its return value without relying on actual implementation.
    # The patch target should be where LocalProductService is imported/used in ProductDataService.
    # A list longer than the test limit is provided to ensure the slicing functionality is also tested.
    mock_full_category_products = [
        {"id": "p1", "name": "Product A", "category": "Electronics"},
        {"id": "p2", "name": "Product B", "category": "Electronics"},
        {"id": "p3", "name": "Product C", "category": "Electronics"},
        {"id": "p4", "name": "Product D", "category": "Electronics"},
        {"id": "p5", "name": "Product E", "category": "Electronics"},
        {"id": "p6", "name": "Product F", "category": "Electronics"}, # This one should be sliced off if limit is 5
    ]
    mock_get_by_category = mocker.patch(
        "app.services.product_data_service.LocalProductService.get_products_by_category",
        return_value=mock_full_category_products
    )

    # Import the ProductDataService class (assuming test environment has access)
    from app.services.product_data_service import ProductDataService

    # Instantiate the ProductDataService
    service = ProductDataService()

    # Define test parameters
    test_category = "Electronics"
    test_limit = 5

    # Call the method under test
    products = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Ensure the return type is a list
    assert isinstance(products, list)

    # 2. Ensure the number of products returned matches the limit
    assert len(products) == test_limit

    # 3. Ensure the mocked method was called with the correct category
    mock_get_by_category.assert_called_once_with(test_category)

    # 4. (Optional) Ensure the products in the result actually belong to the requested category
    for product in products:
        assert "category" in product
        assert product["category"] == test_category

    # Test with a different limit
    test_limit_all = 10 # This limit is higher than mock_full_category_products count
    products_all = service.get_products_by_category(test_category, test_limit_all)
    assert isinstance(products_all, list)
    # Since the mock returns only 6 items, the result should be max 6, not 10.
    assert len(products_all) == len(mock_full_category_products) # Should be 6

    # Test case for empty category (mocked to return empty list)
    mock_get_by_category.return_value = []
    products_empty = service.get_products_by_category("NonExistentCategory", 5)
    assert isinstance(products_empty, list)
    assert not products_empty # Check if list is empty
    mock_get_by_category.assert_called_with("NonExistentCategory") # Check last call
