import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Instantiate the ProductDataService
    service = ProductDataService()

    # Test with a known category and a limit
    category = "Electronics"
    limit = 2
    products = service.get_products_by_category(category, limit)

    # Assertions for basic functionality
    assert isinstance(products, list)
    assert len(products) <= limit
    if products:
        assert all(isinstance(product, dict) for product in products)

    # Test with a category that might not exist or has no products
    empty_category_products = service.get_products_by_category("NonExistentCategory", 5)
    assert isinstance(empty_category_products, list)
    assert len(empty_category_products) == 0

    # Test with a larger limit to ensure it still respects the limit or returns all available
    large_limit = 100
    all_electronics = service.get_products_by_category(category, large_limit)
    assert isinstance(all_electronics, list)
    assert len(all_electronics) <= large_limit
