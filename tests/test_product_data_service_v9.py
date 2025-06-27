import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(monkeypatch):
    # Import necessary classes within the function scope if explicit imports are disallowed outside,
    # or assume they are available in the test file's global scope.
    # For this response, we assume ProductDataService and MagicMock are available.
    from app.services.product_data_service import ProductDataService
    from unittest.mock import MagicMock

    # Prepare a mock instance for LocalProductService
    mock_local_service_instance = MagicMock()
    
    # Define the data that the mock's get_products_by_category method will return.
    # This list has more items than the test limit to ensure the slicing logic in ProductDataService is applied.
    mock_products_from_local_service = [
        {"id": "p1", "name": "Laptop", "category": "Electronics", "price": 1200},
        {"id": "p2", "name": "Mouse", "category": "Electronics", "price": 25},
        {"id": "p3", "name": "Keyboard", "category": "Electronics", "price": 75},
        {"id": "p4", "name": "Monitor", "category": "Electronics", "price": 300},
    ]
    mock_local_service_instance.get_products_by_category.return_value = mock_products_from_local_service

    # Patch the LocalProductService class within the module where ProductDataService is defined.
    # This ensures that when ProductDataService() is instantiated, it uses our mock instance.
    monkeypatch.setattr('app.services.product_data_service.LocalProductService', 
                        MagicMock(return_value=mock_local_service_instance))

    # Instantiate the ProductDataService (which will now use our mocked LocalProductService)
    service = ProductDataService()

    # Define test parameters
    test_category = "Electronics"
    test_limit = 2

    # Call the target function
    result = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that LocalProductService's get_products_by_category was called exactly once with the correct arguments.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(test_category)

    # 2. Verify that the result matches the expected products after ProductDataService applies the limit.
    expected_result = mock_products_from_local_service[:test_limit]
    assert result == expected_result
    
    # 3. Verify the type and length of the result
    assert isinstance(result, list)
    assert len(result) == test_limit
    assert all(isinstance(p, dict) for p in result)
