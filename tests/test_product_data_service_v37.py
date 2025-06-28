import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Import the service class inside the function to avoid global imports if the request implies that
    # For a real pytest setup, ProductDataService would typically be imported at the top of the test file.
    # However, to strictly adhere to "JANGAN menambahkan import statement" in the output,
    # we simulate its availability or import it locally if absolutely necessary for the snippet.
    # In a real scenario, ProductDataService would be imported at the file level.
    from app.services.product_data_service import ProductDataService

    # Prepare mock data for LocalProductService's method
    mock_products_from_local_service = [
        {"id": "p1", "name": "Laptop", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone", "category": "Electronics"},
        {"id": "p3", "name": "Headphones", "category": "Electronics"},
        {"id": "p4", "name": "Smart Watch", "category": "Electronics"},
        {"id": "p5", "name": "Tablet", "category": "Electronics"},
    ]

    # Mock the `get_products_by_category` method of `LocalProductService`
    # The patch target path must be where `LocalProductService` is imported and used,
    # which is `app.services.product_data_service.LocalProductService`.
    mock_get_by_category = mocker.patch(
        'app.services.product_data_service.LocalProductService.get_products_by_category',
        return_value=mock_products_from_local_service
    )

    # Initialize the service under test
    service = ProductDataService()

    # Define test parameters
    test_category = "Electronics"
    test_limit = 3

    # Call the method being tested
    result = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that the underlying LocalProductService method was called correctly
    mock_get_by_category.assert_called_once_with(test_category)

    # 2. Verify the returned products match the expected slice based on the limit
    expected_products = mock_products_from_local_service[:test_limit]
    assert result == expected_products
    assert len(result) == test_limit # Ensure the limit was applied
