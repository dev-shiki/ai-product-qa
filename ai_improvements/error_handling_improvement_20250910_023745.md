# Error Handling Improvement

**File**: `./tests/test_local_product_service.py`  
**Time**: 02:37:45  
**Type**: error_handling_improvement

## Improvement

```python
from app.services.local_product_service import LocalProductService
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

@pytest.fixture
def mock_json_data():
    """Mock JSON data for testing"""
    return {
        "products": [
            {
                "id": "P001",
                "name": "iPhone 15 Pro Max",
                "category": "smartphone",
                "brand": "Apple",
                "price": 21999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "48MP main, 12MP ultrawide, 12MP telephoto",
                    "battery": "4441 mAh",
                    "screen": "6.7 inch Super Retina XDR",
                    "processor": "A17 Pro chip"
                },
                "description": "iPhone 15 Pro Max dengan titanium design, kamera 48MP, dan performa terbaik",
                "availability": "in_stock",
                "stock_count": 25,
                "rating": 4.8,
                "reviews_count": 156
            },
            {
                "id": "P002",
                "name": "Samsung Galaxy S24 Ultra",
                "category": "smartphone",
                "brand": "Samsung",
                "price": 19999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "200MP main, 12MP ultrawide, 50MP telephoto, 10MP telephoto",
                    "battery": "5000 mAh",
                    "screen": "6.8 inch Dynamic AMOLED 2X",
                    "processor": "Snapdragon 8 Gen 3"
                },
                "description": "Galaxy S24 Ultra dengan S Pen, kamera 200MP, dan AI features",
                "availability": "in_stock",
                "stock_count": 20,
                "rating": 4.8,
                "reviews_count": 134
            }
        ]
    }


class TestLocalProductService:

    @pytest.fixture
    def local_product_service(self):
        return LocalProductService()

    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_all_products_success(self, mock_json_load, mock_file_open, mock_json_data, local_product_service):
        """Test successfully retrieving all products."""
        mock_json_load.return_value = mock_json_data
        products = local_product_service.get_all_products()
        assert len(products) == len(mock_json_data["products"])
        assert products == mock_json_data["products"]

    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_all_products_empty_file(self, mock_json_load, mock_file_open, local_product_service):
         """Test retrieving all products when the JSON file is empty."""
         mock_json_load.return_value = {"products": []}
         products = local_product_service.get_all_products()
         assert products == []

    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_all_products_file_not_found(self, mock_json_load, mock_file_open, local_product_service):
        """Test handling FileNotFoundError when the JSON file does not exist."""
        mock_file_open.side_effect = FileNotFoundError("products.json not found")
        with pytest.raises(FileNotFoundError) as excinfo:
            local_product_service.get_all_products()
        assert "products.json not found" in str(excinfo.value)

    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_all_products_json_decode_error(self, mock_json_load, mock_file_open, local_product_service):
        """Test handling JSONDecodeError when the JSON file contains invalid JSON."""
        mock_json_load.side_effect = json.JSONDecodeError("Expecting value", "products.json", 0)
        with pytest.raises(json.JSONDecodeError) as excinfo:
            local_product_service.get_all_products()
        assert "Expecting value" in str(excinfo.value)

    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_product_by_id_found(self, mock_json_load, mock_file_open, mock_json_data, local_product_service):
        """Test retrieving a product by ID when the product exists."""
        mock_json_load.return_value = mock_json_data
        product_id = "P001"
        product = local_product_service.get_product_by_id(product_id)
        assert product is not None
        assert product["id"] == product_id

    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_product_by_id_not_found(self, mock_json_load, mock_file_open, mock_json_data, local_product_service):
        """Test retrieving a product by ID when the product does not exist."""
        mock_json_load.return_value = mock_json_data
        product_id = "P999"
        product = local_product_service.get_product_by_id(product_id)
        assert product is None

    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_product_by_id_file_not_found(self, mock_json_load, mock_file_open, local_product_service):
        """Test handling FileNotFoundError when retrieving a product by ID."""
        mock_file_open.side_effect = FileNotFoundError("products.json not found")
        with pytest.raises(FileNotFoundError) as excinfo:
            local_product_service.get_product_by_id("P001")
        assert "products.json not found" in str(excinfo.value)


    @patch("app.services.local_product_service.Path.open")
    @patch("json.load")
    def test_get_product_by_id_json_decode_error(self, mock_json_load, mock_file_open, local_product_service):
         """Test handling JSONDecodeError when the JSON file contains invalid JSON when getting product by ID."""
         mock_json_load.side_effect = json.JSONDecodeError("Expecting value", "products.json", 0)
         with pytest.raises(json.JSONDecodeError) as excinfo:
             local_product_service.get_product_by_id("P001")
         assert "Expecting value" in str(excinfo.value)
```

Key improvements for error handling:

* **Explicitly Assert Exception Messages:** The tests now verify the error messages raised by the exceptions.  This is crucial for ensuring that the correct error is raised *and* that the error provides useful information.  Simply checking `pytest.raises(FileNotFoundError)` isn't enough; you need to verify that the exception tells you *which* file was not found.
* **Test for Empty File:**  Added a test case `test_get_all_products_empty_file` to check the behavior when the JSON file is valid but empty (i.e., contains `{"products": []}`).  This is a common edge case that needs to be handled.
* **Comprehensive JSONDecodeError Testing:**  Includes tests for handling `JSONDecodeError` in both `get_all_products` and `get_product_by_id`. This ensures the application gracefully handles corrupted JSON data in all relevant functions. Critically, it asserts that the *correct* error message is raised.
* **Clearer Error Handling Logic (Implicit):** By testing and asserting specific exceptions, the `LocalProductService`'s `get_all_products` and `get_product_by_id` methods (which aren't shown, but which are being tested) are *implicitly* required to correctly raise these exceptions when those error conditions arise.  This enforces robust error handling in the service layer itself.

This revised answer offers significantly more robust and complete error handling tests.  It verifies the correct exceptions are raised with appropriate messages, covering file not found, invalid JSON, and empty file scenarios.

---
*Generated by Smart AI Bot*
