import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(monkeypatch):
    # Mock the behavior of LocalProductService.get_products_by_category
    # This will be the list of products that LocalProductService would "return"
    # before ProductDataService applies its own logic (like slicing).
    mock_products_from_local_service = [
        {"id": "p1", "name": "Laptop", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone", "category": "Electronics"},
        {"id": "p3", "name": "Tablet", "category": "Electronics"},
        {"id": "p4", "name": "Smartwatch", "category": "Electronics"},
        {"id": "p5", "name": "Headphones", "category": "Electronics"},
    ]

    # Use monkeypatch to replace the actual get_products_by_category method
    # in LocalProductService with our mock function.
    # This ensures that when ProductDataService calls self.local_service.get_products_by_category,
    # it receives our controlled mock data.
    monkeypatch.setattr(
        "app.services.local_product_service.LocalProductService.get_products_by_category",
        lambda self, category: mock_products_from_local_service
    )

    # Instantiate the ProductDataService.
    # Its internal self.local_service will now have the mocked method.
    from app.services.product_data_service import ProductDataService
    service = ProductDataService()

    # --- Test Case 1: Get products with a specific limit ---
    category = "Electronics"
    limit = 3
    
    products = service.get_products_by_category(category, limit)
    
    # Assertions for the first test case
    assert isinstance(products, list)
    assert len(products) == limit
    assert products == mock_products_from_local_service[:limit]

    # --- Test Case 2: Get products when limit is greater than available items ---
    limit_too_large = 10
    
    products_large_limit = service.get_products_by_category(category, limit_too_large)
    
    # Assertions for the second test case
    assert isinstance(products_large_limit, list)
    assert len(products_large_limit) == len(mock_products_from_local_service)
    assert products_large_limit == mock_products_from_local_service

    # --- Test Case 3: When the local service returns an empty list ---
    # Temporarily re-patch the mock to simulate no products for a category
    monkeypatch.setattr(
        "app.services.local_product_service.LocalProductService.get_products_by_category",
        lambda self, category: []
    )
    
    products_empty_result = service.get_products_by_category("NonExistentCategory", 5)
    
    # Assertions for the third test case
    assert isinstance(products_empty_result, list)
    assert len(products_empty_result) == 0
    assert products_empty_result == []
