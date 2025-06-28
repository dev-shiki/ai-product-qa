import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    from app.services.product_data_service import ProductDataService

    # Mock the LocalProductService class where it is imported within ProductDataService
    # This allows us to control the instance created by ProductDataService's __init__
    mock_local_service_class = mocker.patch('app.services.product_data_service.LocalProductService')

    # Define the mock return value for LocalProductService's get_products_by_category method
    mocked_products_from_local = [
        {"id": "p1", "name": "Laptop Pro", "category": "Electronics"},
        {"id": "p2", "name": "Smartphone X", "category": "Electronics"},
        {"id": "p3", "name": "Wireless Headphones", "category": "Electronics"},
        {"id": "p4", "name": "Smartwatch 2.0", "category": "Electronics"},
    ]
    mock_local_service_class.return_value.get_products_by_category.return_value = mocked_products_from_local

    # Instantiate ProductDataService. It will now use our mocked LocalProductService.
    service = ProductDataService()

    test_category = "Electronics"
    test_limit = 2

    # Call the target function
    result = service.get_products_by_category(test_category, test_limit)

    # Assertions
    # 1. Verify that LocalProductService was instantiated
    mock_local_service_class.assert_called_once()

    # 2. Verify that the underlying local_service.get_products_by_category was called correctly
    mock_local_service_class.return_value.get_products_by_category.assert_called_once_with(test_category)

    # 3. Verify the returned products match the expected subset (due to limit)
    expected_result = mocked_products_from_local[:test_limit]
    assert result == expected_result
    assert len(result) == test_limit

    # Test case: LocalProductService returns fewer items than the limit
    mock_local_service_class.return_value.get_products_by_category.reset_mock() # Reset call count for next assertion
    mock_local_service_class.return_value.get_products_by_category.return_value = [{"id": "b1", "name": "Book A", "category": "Books"}]
    
    result_fewer = service.get_products_by_category("Books", 5)
    assert result_fewer == [{"id": "b1", "name": "Book A", "category": "Books"}]
    assert len(result_fewer) == 1
    mock_local_service_class.return_value.get_products_by_category.assert_called_once_with("Books")

    # Test case: LocalProductService returns an empty list
    mock_local_service_class.return_value.get_products_by_category.reset_mock()
    mock_local_service_class.return_value.get_products_by_category.return_value = []
    
    result_empty = service.get_products_by_category("NonExistent", 10)
    assert result_empty == []
    assert len(result_empty) == 0
    mock_local_service_class.return_value.get_products_by_category.assert_called_once_with("NonExistent")

    # Test case: An exception occurs in LocalProductService
    mock_local_service_class.return_value.get_products_by_category.reset_mock()
    mock_local_service_class.return_value.get_products_by_category.side_effect = Exception("Simulated service error")
    
    result_error = service.get_products_by_category("ErrorCategory", 5)
    assert result_error == [] # The function is designed to return an empty list on error
    mock_local_service_class.return_value.get_products_by_category.assert_called_once_with("ErrorCategory")
