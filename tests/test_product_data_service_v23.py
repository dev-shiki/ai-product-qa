import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock the instance of LocalProductService that ProductDataService will use
    mock_local_service_instance = mocker.MagicMock()

    # Configure the mock's get_products_by_category method to return sample data
    mock_local_service_instance.get_products_by_category.return_value = [
        {"id": "p1", "name": "Laptop Pro", "category": "Electronics"},
        {"id": "p2", "name": "Smartwatch X", "category": "Electronics"},
        {"id": "p3", "name": "Gaming Mouse", "category": "Electronics"},
        {"id": "p4", "name": "USB Hub", "category": "Electronics"},
        {"id": "p5", "name": "Monitor Ultra", "category": "Electronics"},
    ]

    # Patch the LocalProductService class itself.
    # This ensures that when ProductDataService initializes, it uses our mock.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Instantiate ProductDataService (assuming ProductDataService is in scope for the test file)
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # --- Test Case 1: Get products for a specific category with a limit ---
    category_name = "Electronics"
    limit_value = 3
    products = service.get_products_by_category(category_name, limit_value)

    # Assertions for Test Case 1
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_name)
    assert isinstance(products, list)
    assert len(products) == limit_value
    assert all(p.get("category") == category_name for p in products)
    assert products[0]["id"] == "p1"
    assert products[2]["id"] == "p3"

    # Reset mock call history for the next scenario
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 2: Limit is greater than available mocked products ---
    # The method should return all available products from the mock, capped by their actual count.
    limit_value_large = 10
    products_large = service.get_products_by_category(category_name, limit_value_large)

    # Assertions for Test Case 2
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_name)
    assert isinstance(products_large, list)
    assert len(products_large) == 5  # Should be capped by the 5 items returned by the mock
    assert all(p.get("category") == category_name for p in products_large)

    # Reset mock
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 3: Category with no products ---
    # Configure mock to return an empty list for a non-existent category
    mock_local_service_instance.get_products_by_category.return_value = []
    category_no_products = "NonExistentCategory"
    products_empty = service.get_products_by_category(category_no_products)

    # Assertions for Test Case 3
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_no_products)
    assert isinstance(products_empty, list)
    assert len(products_empty) == 0

    # Reset mock
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 4: Exception handling ---
    # Simulate an error from the underlying service
    mock_local_service_instance.get_products_by_category.side_effect = Exception("Simulated service error")
    category_error = "Books"
    products_error = service.get_products_by_category(category_error)

    # Assertions for Test Case 4
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_error)
    assert isinstance(products_error, list)
    assert len(products_error) == 0 # ProductDataService should catch the exception and return an empty list
