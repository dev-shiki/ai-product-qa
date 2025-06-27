import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    """
    Test basic functionality of get_products_by_category.
    Mocks the underlying LocalProductService to control data returned.
    """
    
    # Define mock data that the LocalProductService would return
    all_mock_products = [
        {"id": "p1", "name": "Laptop X", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone Y", "category": "Electronics"},
        {"id": "p3", "name": "Book A", "category": "Books"},
        {"id": "p4", "name": "Book B", "category": "Books"},
        {"id": "p5", "name": "Monitor Z", "category": "Electronics"},
    ]

    # Create a mock object for the LocalProductService instance
    mock_local_service = mocker.Mock()

    # Configure the mock method's behavior: it should return products
    # filtered by category from our all_mock_products list.
    def mock_get_products_by_category_impl(category_name):
        return [p for p in all_mock_products if p["category"] == category_name]

    mock_local_service.get_products_by_category.side_effect = mock_get_products_by_category_impl
    
    # Patch the LocalProductService class so that when ProductDataService is initialized,
    # it uses our mock instance instead of the real LocalProductService.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service)

    # Import the ProductDataService class (assuming it's available in the test scope)
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # --- Test Case 1: Get products for an existing category with a specific limit ---
    category_electronics = "Electronics"
    limit_electronics = 2
    
    result_electronics = service.get_products_by_category(category_electronics, limit_electronics)
    
    # Assertions for Test Case 1
    mock_local_service.get_products_by_category.assert_called_once_with(category_electronics)
    assert len(result_electronics) == limit_electronics
    assert result_electronics == [
        {"id": "p1", "name": "Laptop X", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone Y", "category": "Electronics"},
    ]

    # --- Test Case 2: Get products for another category where limit is greater than available ---
    mock_local_service.get_products_by_category.reset_mock() # Reset call count for next test
    category_books = "Books"
    limit_books = 5 # Requesting more than available
    
    result_books = service.get_products_by_category(category_books, limit_books)
    
    # Assertions for Test Case 2
    mock_local_service.get_products_by_category.assert_called_once_with(category_books)
    assert len(result_books) == 2 # Only 2 books in mock data
    assert result_books == [
        {"id": "p3", "name": "Book A", "category": "Books"},
        {"id": "p4", "name": "Book B", "category": "Books"},
    ]

    # --- Test Case 3: Get products for a non-existent category ---
    mock_local_service.get_products_by_category.reset_mock() # Reset call count for next test
    category_non_existent = "Furniture"
    limit_non_existent = 10
    
    result_non_existent = service.get_products_by_category(category_non_existent, limit_non_existent)
    
    # Assertions for Test Case 3
    mock_local_service.get_products_by_category.assert_called_once_with(category_non_existent)
    assert len(result_non_existent) == 0
    assert result_non_existent == []
