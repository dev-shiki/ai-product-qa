import pytest
from app.services.product_data_service import get_products_by_category

def test_get_products_by_category_basic(mocker):
    # Mock the LocalProductService instance that ProductDataService depends on.
    mock_local_service_instance = mocker.MagicMock()

    # Prepare mock data for products in a specific category.
    # This list has more items than the default limit (10) to test the slicing logic.
    mock_products_data = [
        {"id": "p1", "name": "Smart TV", "category": "Electronics"},
        {"id": "p2", "name": "Laptop", "category": "Electronics"},
        {"id": "p3", "name": "Smartphone", "category": "Electronics"},
        {"id": "p4", "name": "Headphones", "category": "Electronics"},
        {"id": "p5", "name": "Smartwatch", "category": "Electronics"},
        {"id": "p6", "name": "Tablet", "category": "Electronics"},
        {"id": "p7", "name": "Gaming Console", "category": "Electronics"},
        {"id": "p8", "name": "VR Headset", "category": "Electronics"},
        {"id": "p9", "name": "Drone", "category": "Electronics"},
        {"id": "p10", "name": "Digital Camera", "category": "Electronics"},
        {"id": "p11", "name": "Portable Speaker", "category": "Electronics"},
        {"id": "p12", "name": "E-Reader", "category": "Electronics"},
    ]

    # Configure the mock's get_products_by_category method to return our predefined data.
    mock_local_service_instance.get_products_by_category.return_value = mock_products_data

    # Patch the LocalProductService class itself. This ensures that when ProductDataService
    # is instantiated, its 'self.local_service' attribute points to our mock instance.
    # We assume 'ProductDataService' is available in the test's scope as per instructions.
    mocker.patch('app.services.product_data_service.LocalProductService', return_value=mock_local_service_instance)

    # Instantiate ProductDataService. It will now use our mocked LocalProductService.
    service = ProductDataService() # ProductDataService is assumed to be imported or available.

    # --- Test Case 1: Get products by category with the default limit (10) ---
    # The mock_products_data has 12 items. With default limit 10, it should return the first 10.
    category_name = "Electronics"
    
    returned_products_default = service.get_products_by_category(category_name)

    # Assert that the underlying LocalProductService method was called with the correct category.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_name)
    # Assert that the returned list contains the correct number of products (default limit applied).
    assert len(returned_products_default) == 10
    # Assert that the content of the returned list is correct based on the mock data and slicing.
    assert returned_products_default == mock_products_data[:10]

    # Reset the mock's call history for the next test scenario.
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 2: Get products by category with a specific limit (e.g., 5) ---
    specific_limit = 5
    
    returned_products_limited = service.get_products_by_category(category_name, limit=specific_limit)

    # Assert that the underlying LocalProductService method was called correctly (again, only once for its part).
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_name)
    # Assert that the returned list correctly applies the specific limit.
    assert len(returned_products_limited) == specific_limit
    assert returned_products_limited == mock_products_data[:specific_limit]

    # Reset the mock's call history and return value for the next test scenario.
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 3: Handle a category that returns no results from the local service ---
    mock_local_service_instance.get_products_by_category.return_value = []
    category_non_existent = "NonExistentCategory"

    returned_products_empty = service.get_products_by_category(category_non_existent)

    # Assert that the underlying LocalProductService method was called.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_non_existent)
    # Assert that an empty list is returned when the source has no products.
    assert returned_products_empty == []

    # Reset the mock for the last test case.
    mock_local_service_instance.get_products_by_category.reset_mock()

    # --- Test Case 4: Handle an exception raised by the local service ---
    # This tests the 'except' block, ensuring it gracefully returns an empty list on error.
    mock_local_service_instance.get_products_by_category.side_effect = Exception("Simulated service error during retrieval")

    returned_products_on_error = service.get_products_by_category(category_name)

    # Assert that the underlying LocalProductService method was still attempted to be called.
    mock_local_service_instance.get_products_by_category.assert_called_once_with(category_name)
    # Assert that an empty list is returned despite the error in the underlying service.
    assert returned_products_on_error == []

    # Clean up the side effect for good measure, though this is the end of the test.
    mock_local_service_instance.get_products_by_category.side_effect = None
