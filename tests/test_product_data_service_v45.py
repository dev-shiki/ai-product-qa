import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Import necessary tools locally to adhere to the "no top-level imports in output" constraint
    # while enabling proper unit testing with mocking.
    from unittest.mock import MagicMock, patch
    from app.services.product_data_service import ProductDataService

    # Arrange: Set up a mock for the LocalProductService dependency
    mock_local_service = MagicMock()
    
    # Configure the mock's get_products_by_category method.
    # The ProductDataService method takes a slice `[:limit]`, so we provide more data than the test limit
    # to ensure the slicing logic in `ProductDataService` is correctly applied.
    mock_all_category_products = [
        {"id": "prod_a", "name": "Laptop XYZ", "category": "Electronics"},
        {"id": "prod_b", "name": "Smartphone ABC", "category": "Electronics"},
        {"id": "prod_c", "name": "Smartwatch DEF", "category": "Electronics"},
        {"id": "prod_d", "name": "Tablet GHI", "category": "Electronics"},
    ]
    mock_local_service.get_products_by_category.return_value = mock_all_category_products

    # Act: Use `patch` to replace `ProductDataService.local_service` with our mock
    # during the execution of this test. Then, instantiate and call the target method.
    with patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service):
        service = ProductDataService()
        
        # Test Case 1: Happy path - get products with a specified category and limit
        category_name = "Electronics"
        desired_limit = 2
        products = service.get_products_by_category(category_name, desired_limit)
        
        # Assertions for Test Case 1:
        assert isinstance(products, list)
        assert len(products) == desired_limit  # Verify that the limit was applied
        assert all(isinstance(p, dict) for p in products)
        assert all(p.get("category") == category_name for p in products)
        
        # Verify that the underlying mock method was called exactly once with the correct arguments
        mock_local_service.get_products_by_category.assert_called_once_with(category_name)
        
        # Test Case 2: Scenario where fewer products are available than the requested limit
        mock_local_service.get_products_by_category.reset_mock() # Clear previous call history
        mock_local_service.get_products_by_category.return_value = [
            {"id": "book_1", "name": "The Great Novel", "category": "Books"}
        ]
        category_books = "Books"
        limit_high = 5 # Requesting more than available
        products_books = service.get_products_by_category(category_books, limit_high)
        
        # Assertions for Test Case 2:
        assert len(products_books) == 1  # Should return all available (1), not the higher limit
        assert products_books[0]["category"] == category_books
        mock_local_service.get_products_by_category.assert_called_once_with(category_books)

        # Test Case 3: Error handling - mock the underlying service to raise an exception
        mock_local_service.get_products_by_category.reset_mock()
        mock_local_service.get_products_by_category.side_effect = Exception("Simulated LocalProductService error")
        
        products_on_error = service.get_products_by_category("NonExistentCategory", 10)
        
        # Assertions for Test Case 3:
        assert products_on_error == []  # Should return an empty list when an error occurs
        mock_local_service.get_products_by_category.assert_called_once_with("NonExistentCategory")
