import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Mock the LocalProductService class that ProductDataService instantiates in its __init__
    with unittest.mock.patch('app.services.product_data_service.LocalProductService') as MockLocalProductService:
        # Get the mock instance that ProductDataService will use
        mock_local_service_instance = MockLocalProductService.return_value
        
        # Configure the mock instance's get_products_by_category method for a successful call
        mock_local_service_instance.get_products_by_category.return_value = [
            {"id": "P001", "name": "Product A", "category": "Electronics"},
            {"id": "P002", "name": "Product B", "category": "Electronics"},
            {"id": "P003", "name": "Product C", "category": "Electronics"},
            {"id": "P004", "name": "Product D", "category": "Electronics"},
        ]

        # Instantiate ProductDataService. It will now use our mocked LocalProductService.
        service = ProductDataService()

        # Test case 1: Get products with a specific category and limit
        category = "Electronics"
        limit = 3
        products = service.get_products_by_category(category, limit)

        # Assertions for Test case 1
        mock_local_service_instance.get_products_by_category.assert_called_once_with(category)
        expected_products_case1 = [
            {"id": "P001", "name": "Product A", "category": "Electronics"},
            {"id": "P002", "name": "Product B", "category": "Electronics"},
            {"id": "P003", "name": "Product C", "category": "Electronics"},
        ]
        assert products == expected_products_case1
        assert len(products) == limit

        # Reset mock for next test case (important in a single function with multiple scenarios)
        mock_local_service_instance.get_products_by_category.reset_mock()

        # Test case 2: Local service returns fewer items than the requested limit
        mock_local_service_instance.get_products_by_category.return_value = [
            {"id": "B001", "name": "Book X", "category": "Books"},
            {"id": "B002", "name": "Book Y", "category": "Books"},
        ]
        category_short = "Books"
        limit_short = 5 # Requesting 5, but mock returns only 2
        products_short = service.get_products_by_category(category_short, limit_short)

        # Assertions for Test case 2
        mock_local_service_instance.get_products_by_category.assert_called_once_with(category_short)
        expected_products_case2 = [
            {"id": "B001", "name": "Book X", "category": "Books"},
            {"id": "B002", "name": "Book Y", "category": "Books"},
        ]
        assert products_short == expected_products_case2
        assert len(products_short) == 2 # Should match the number of items returned by mock

        # Reset mock for next test case
        mock_local_service_instance.get_products_by_category.reset_mock()

        # Test case 3: An exception occurs in the local service call
        mock_local_service_instance.get_products_by_category.side_effect = Exception("Simulated service error")
        category_error = "ErrorCategory"
        products_error = service.get_products_by_category(category_error, limit)

        # Assertions for Test case 3
        mock_local_service_instance.get_products_by_category.assert_called_once_with(category_error)
        assert products_error == [] # Service should return an empty list on error
