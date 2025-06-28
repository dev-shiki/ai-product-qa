import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock the LocalProductService instance that ProductDataService will use.
    mock_local_service_instance = mocker.Mock()

    # Configure the mock's get_products_by_category method to return a list
    # longer than the typical limit to test the slicing logic.
    mock_local_service_instance.get_products_by_category.return_value = [
        {"id": "p1", "name": "Laptop A", "category": "Electronics"},
        {"id": "p2", "name": "Laptop B", "category": "Electronics"},
        {"id": "p3", "name": "Smartphone X", "category": "Electronics"},
        {"id": "p4", "name": "Tablet Y", "category": "Electronics"},
        {"id": "p5", "name": "Headphones Z", "category": "Electronics"},
    ]

    # Patch the LocalProductService class itself so that when ProductDataService
    # is initialized, it uses our mock instance.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Import ProductDataService after patching to ensure it uses the mocked dependency.
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # Define test parameters
    test_category = "Electronics"
    test_limit = 3

    # Act: Call the function under test
    products = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that the mock local service's method was called correctly
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # 2. Verify the number of products returned matches the limit
    assert len(products) == test_limit

    # 3. Verify the content of the returned products (first few items)
    assert products[0]["id"] == "p1"
    assert products[1]["id"] == "p2"
    assert products[2]["id"] == "p3"

    # 4. Ensure products beyond the limit are not included
    assert all(p["id"] not in ["p4", "p5"] for p in products)

    # Test with a category that might return fewer products than the limit
    mock_local_service_instance.get_products_by_category.return_value = [
        {"id": "f1", "name": "Chair A", "category": "Furniture"},
        {"id": "f2", "name": "Table B", "category": "Furniture"},
    ]
    test_category_2 = "Furniture"
    test_limit_2 = 5
    products_2 = service.get_products_by_category(test_category_2, test_limit_2)

    assert len(products_2) == 2 # Should return all available, not capped at 5
    mock_local_service_instance.get_products_by_category.assert_called_with(test_category_2)

    # Test with a category that returns no products
    mock_local_service_instance.get_products_by_category.return_value = []
    test_category_3 = "NonExistent"
    test_limit_3 = 10
    products_3 = service.get_products_by_category(test_category_3, test_limit_3)
    assert len(products_3) == 0
    mock_local_service_instance.get_products_by_category.assert_called_with(test_category_3)
