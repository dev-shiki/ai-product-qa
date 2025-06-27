import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(monkeypatch):
    mock_all_category_products = [
        {"id": "p1", "name": "Laptop", "category": "electronics"},
        {"id": "p2", "name": "Mouse", "category": "electronics"},
        {"id": "p3", "name": "Keyboard", "category": "electronics"},
        {"id": "p4", "name": "Monitor", "category": "electronics"},
    ]

    service = ProductDataService()

    def mock_local_service_get_products_by_category(category_name: str) -> list:
        if category_name == "electronics":
            return mock_all_category_products
        return []

    monkeypatch.setattr(
        service.local_service,
        'get_products_by_category',
        mock_local_service_get_products_by_category
    )

    category_to_test = "electronics"
    limit_to_test = 2
    expected_products = mock_all_category_products[:limit_to_test]

    result = service.get_products_by_category(category_to_test, limit_to_test)

    assert result == expected_products
    assert len(result) == limit_to_test

    limit_large = 10
    result_large_limit = service.get_products_by_category(category_to_test, limit_large)
    assert result_large_limit == mock_all_category_products
    assert len(result_large_limit) == len(mock_all_category_products)

    result_empty = service.get_products_by_category("non_existent_category", 5)
    assert result_empty == []
    assert len(result_empty) == 0
