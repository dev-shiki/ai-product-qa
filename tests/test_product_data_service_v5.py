import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(monkeypatch):
    # Dummy data that MockLocalProductService will return
    dummy_products_electronics = [
        {"id": "1", "name": "Laptop Pro", "category": "Electronics"},
        {"id": "2", "name": "Mouse Wireless", "category": "Electronics"},
        {"id": "3", "name": "Keyboard Mechanical", "category": "Electronics"},
    ]
    dummy_products_mobile = [
        {"id": "4", "name": "Smartphone X", "category": "Mobile"},
        {"id": "5", "name": "Tablet Y", "category": "Mobile"},
    ]

    # Define a simple mock for LocalProductService
    class MockLocalProductService:
        def __init__(self):
            # ProductDataService's __init__ calls LocalProductService()
            pass

        def get_products_by_category(self, category: str):
            """Mock method to return predefined products based on category."""
            if category == "Electronics":
                return dummy_products_electronics
            elif category == "Mobile":
                return dummy_products_mobile
            return []

    # Patch the LocalProductService class within the app.services.product_data_service module.
    # This ensures that when ProductDataService is instantiated, it uses our mock.
    monkeypatch.setattr('app.services.product_data_service.LocalProductService', MockLocalProductService)

    # Instantiate the ProductDataService.
    # (The import 'from app.services.product_data_service import ProductDataService'
    # is assumed to be present at the top of the actual test file.)
    from app.services.product_data_service import ProductDataService # This line is conceptually needed but hidden per instruction
    service = ProductDataService()

    # Test Case 1: Get products from a valid category with a specific limit
    category_1 = "Electronics"
    limit_1 = 2
    result_1 = service.get_products_by_category(category_1, limit_1)
    assert len(result_1) == limit_1
    assert result_1 == dummy_products_electronics[:limit_1]
    assert result_1[0]["name"] == "Laptop Pro"

    # Test Case 2: Get products from another valid category, using default limit (10)
    category_2 = "Mobile"
    result_2 = service.get_products_by_category(category_2) # Default limit is 10
    assert len(result_2) == len(dummy_products_mobile) # All mobile products should be returned
    assert result_2 == dummy_products_mobile

    # Test Case 3: Get products from a non-existent category
    category_3 = "Books"
    result_3 = service.get_products_by_category(category_3)
    assert len(result_3) == 0
    assert result_3 == []

    # Test Case 4: Limit exceeds available products for a category
    category_4 = "Electronics"
    limit_4 = 5 # More than 3 available 'Electronics' products
    result_4 = service.get_products_by_category(category_4, limit_4)
    assert len(result_4) == len(dummy_products_electronics) # Should return all available
    assert result_4 == dummy_products_electronics
