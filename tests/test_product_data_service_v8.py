import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic():
    # Instantiate ProductDataService. This will internally instantiate LocalProductService.
    # The test assumes LocalProductService might return actual data or an empty list.
    service = ProductDataService()

    # Test Case 1: Get products for a common category with a specific limit
    # Expecting a list of dictionaries, not exceeding the limit.
    category_name_1 = "electronics"
    limit_1 = 3
    products_1 = service.get_products_by_category(category_name_1, limit_1)

    assert isinstance(products_1, list)
    assert len(products_1) <= limit_1
    if products_1: # Only check item type if the list is not empty
        assert isinstance(products_1[0], dict)

    # Test Case 2: Get products for a non-existent category
    # Expecting an empty list.
    category_name_2 = "non_existent_category_xyz"
    limit_2 = 5
    products_2 = service.get_products_by_category(category_name_2, limit_2)

    assert isinstance(products_2, list)
    assert len(products_2) == 0

    # Test Case 3: Get products using the default limit (which is 10)
    # Expecting a list of dictionaries, not exceeding the default limit.
    category_name_3 = "books"
    products_3 = service.get_products_by_category(category_name_3) # No limit provided, uses default 10

    assert isinstance(products_3, list)
    assert len(products_3) <= 10
    if products_3:
        assert isinstance(products_3[0], dict)

    # Test Case 4: Get products with a limit of 0
    # Expecting an empty list.
    products_zero_limit = service.get_products_by_category(category_name_1, 0)
    assert isinstance(products_zero_limit, list)
    assert len(products_zero_limit) == 0
