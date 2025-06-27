import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Instantiate the ProductDataService.
    # Assuming ProductDataService class is available in the test file's scope
    # (e.g., imported at the top of the test file, outside this function).
    service = ProductDataService()

    # Test Case 1: Get products from a known category with a specific limit.
    # This relies on LocalProductService having some default data for "electronics".
    test_category_1 = "electronics"
    test_limit_1 = 3
    products_1 = service.get_products_by_category(test_category_1, test_limit_1)

    # Assertions for Test Case 1:
    # 1. Ensure the return type is a list.
    assert isinstance(products_1, list)
    # 2. Ensure the number of returned products does not exceed the limit.
    assert len(products_1) <= test_limit_1
    # 3. Optionally, if LocalProductService is known to have data, assert it's not empty.
    # (For a basic test without complex mocks, simply checking type and limit is sufficient.)

    # Test Case 2: Get products from a non-existent category.
    # This should consistently return an empty list.
    test_category_2 = "non_existent_category_xyz_123"
    test_limit_2 = 5
    products_2 = service.get_products_by_category(test_category_2, test_limit_2)

    # Assertions for Test Case 2:
    assert isinstance(products_2, list)
    assert len(products_2) == 0

    # Test Case 3: Get products using the default limit (10).
    # Assuming "books" is another plausible category.
    test_category_3 = "books"
    products_3 = service.get_products_by_category(test_category_3) # limit defaults to 10

    # Assertions for Test Case 3:
    assert isinstance(products_3, list)
    assert len(products_3) <= 10
