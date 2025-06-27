import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Define a simple dummy class to act as LocalProductService for this test
    # This fulfills the "no complex mocks" and "no extra imports" constraints
    class MockLocalProductService:
        def get_products_by_category(self, category: str, limit: int = 10) -> List[Dict]:
            if category == "electronics":
                # Provide enough data to test the limit slicing
                return [
                    {"id": "e1", "name": "Laptop", "category": "electronics"},
                    {"id": "e2", "name": "Smartphone", "category": "electronics"},
                    {"id": "e3", "name": "Headphones", "category": "electronics"},
                    {"id": "e4", "name": "Tablet", "category": "electronics"},
                    {"id": "e5", "name": "Smartwatch", "category": "electronics"},
                    {"id": "e6", "name": "Camera", "category": "electronics"},
                    {"id": "e7", "name": "TV", "category": "electronics"},
                    {"id": "e8", "name": "Monitor", "category": "electronics"},
                    {"id": "e9", "name": "Keyboard", "category": "electronics"},
                    {"id": "e10", "name": "Mouse", "category": "electronics"},
                    {"id": "e11", "name": "Printer", "category": "electronics"},
                    {"id": "e12", "name": "Webcam", "category": "electronics"},
                ]
            elif category == "books":
                return [
                    {"id": "b1", "name": "Book A", "category": "books"},
                    {"id": "b2", "name": "Book B", "category": "books"},
                ]
            return []

    # Instantiate ProductDataService
    service = ProductDataService()
    
    # Replace its local_service with the mock implementation for testing isolation
    service.local_service = MockLocalProductService()

    # Test case 1: Get products from a known category with default limit (10)
    category_name = "electronics"
    products = service.get_products_by_category(category_name)
    
    assert len(products) == 10
    assert all(p['category'] == category_name for p in products)
    assert products[0]['id'] == "e1"
    assert products[-1]['id'] == "e10" # Verifikasi bahwa slicing limit bekerja

    # Test case 2: Get products with a custom limit
    custom_limit = 5
    products_custom = service.get_products_by_category(category_name, custom_limit)
    assert len(products_custom) == custom_limit
    assert products_custom[0]['id'] == "e1"
    assert products_custom[-1]['id'] == "e5"

    # Test case 3: Get products from a category with fewer items than the limit
    products_books = service.get_products_by_category("books")
    assert len(products_books) == 2
    assert all(p['category'] == "books" for p in products_books)

    # Test case 4: Get products from a non-existent category
    products_empty = service.get_products_by_category("non_existent_category")
    assert products_empty == []
