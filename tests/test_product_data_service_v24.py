import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Instantiate ProductDataService.
    # In a real pytest setup, 'ProductDataService' class would be imported
    # from 'app.services.product_data_service'.
    service = ProductDataService()

    # Test Case 1: Valid category, expect products within limit
    category_1 = "electronics"
    limit_1 = 3
    products_1 = service.get_products_by_category(category_1, limit_1)

    assert isinstance(products_1, list)
    assert len(products_1) <= limit_1
    if products_1:
        assert all(isinstance(p, dict) for p in products_1)
        # More specific checks (e.g., product structure or category match)
        # would require knowledge of the underlying data or more complex mocks,
        # which are intentionally avoided for this basic test.

    # Test Case 2: Non-existent category, expect an empty list
    category_2 = "non_existent_category_xyz"
    limit_2 = 5
    products_2 = service.get_products_by_category(category_2, limit_2)

    assert isinstance(products_2, list)
    assert len(products_2) == 0

    # Test Case 3: Valid category with a different limit
    category_3 = "clothing"
    limit_3 = 1
    products_3 = service.get_products_by_category(category_3, limit_3)

    assert isinstance(products_3, list)
    assert len(products_3) <= limit_3
    if products_3:
        assert all(isinstance(p, dict) for p in products_3)
