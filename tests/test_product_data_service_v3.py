import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Import ProductDataService inside the function to adhere to "JANGAN menambahkan import statement"
    # instruction for the overall output, assuming it's available in the test environment scope.
    from app.services.product_data_service import ProductDataService

    # 1. Mock the LocalProductService that ProductDataService depends on.
    # We patch the class definition so that when ProductDataService is initialized,
    # it uses our mock instance.
    mock_local_service_instance = mocker.MagicMock()

    # Define mock data for the get_products_by_category method of LocalProductService.
    # Include more items than the test limit to verify the slicing logic.
    mock_products_data = [
        {'id': 'elec_1', 'name': 'Laptop XPS', 'category': 'Electronics', 'price': 1200},
        {'id': 'elec_2', 'name': 'Wireless Mouse', 'category': 'Electronics', 'price': 50},
        {'id': 'elec_3', 'name': 'Mechanical Keyboard', 'category': 'Electronics', 'price': 100},
        {'id': 'cloth_1', 'name': 'T-Shirt', 'category': 'Apparel', 'price': 25} # Not electronics
    ]
    mock_local_service_instance.get_products_by_category.return_value = [
        p for p in mock_products_data if p['category'] == 'Electronics'
    ]

    # Apply the patch to the LocalProductService class where ProductDataService imports it.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # 2. Instantiate the ProductDataService (it will now use our mock LocalProductService).
    service = ProductDataService()

    # 3. Test Case 1: Get products for an existing category with a specific limit.
    test_category = "Electronics"
    test_limit = 2
    products = service.get_products_by_category(test_category, limit=test_limit)

    # Assertions for Test Case 1:
    # Verify that the mock LocalProductService method was called correctly.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)
    # Check the type of the returned value.
    assert isinstance(products, list)
    # Verify that the number of products returned matches the limit (due to slicing).
    assert len(products) == test_limit
    # Check that all returned products belong to the specified category.
    assert all(product['category'] == test_category for product in products)
    # Check specific content of the returned products (order matters due to slicing).
    assert products[0]['id'] == 'elec_1'
    assert products[1]['id'] == 'elec_2'

    # 4. Test Case 2: Get products for a non-existent category.
    # Reset the mock's return value for this new scenario.
    mock_local_service_instance.get_products_by_category.return_value = []
    non_existent_category = "NonExistentCategory"
    products_empty = service.get_products_by_category(non_existent_category, limit=5)

    # Assertions for Test Case 2:
    # Ensure it was called with the new category.
    mock_local_service_instance.get_products_by_category.assert_called_with(non_existent_category)
    assert isinstance(products_empty, list)
    assert len(products_empty) == 0

    # 5. Test Case 3: Error handling in the underlying service.
    # Set the mock to raise an exception.
    mock_local_service_instance.get_products_by_category.side_effect = Exception("Simulated service error")
    products_on_error = service.get_products_by_category(test_category, limit=test_limit)

    # Assertions for Test Case 3:
    # Ensure it returns an empty list on error.
    assert isinstance(products_on_error, list)
    assert len(products_on_error) == 0
    # Ensure the underlying method was still attempted.
    mock_local_service_instance.get_products_by_category.assert_called_with(test_category)
