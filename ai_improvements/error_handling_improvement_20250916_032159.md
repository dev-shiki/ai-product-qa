# Error Handling Improvement

**File**: `./tests/test_local_product_service.py`  
**Time**: 03:21:59  
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
        """Fixture for LocalProductService"""
        return LocalProductService()

    @patch("json.load")
    @patch("builtins.open")
    def test_load_products_from_json_success(self, mock_open, mock_json_load, mock_json_data, local_product_service):
        """Test loading products from JSON file successfully."""
        mock_json_load.return_value = mock_json_data
        mock_open.return_value.__enter__.return_value = None  # Simulate successful file opening

        products = local_product_service.load_products_from_json("dummy_path.json")
        assert products == mock_json_data["products"]
        mock_open.assert_called_once_with("dummy_path.json", "r")
        mock_json_load.assert_called_once()

    @patch("json.load")
    @patch("builtins.open")
    def test_load_products_from_json_file_not_found(self, mock_open, mock_json_load, local_product_service):
        """Test loading products when the JSON file is not found."""
        mock_open.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError) as excinfo:
            local_product_service.load_products_from_json("non_existent_file.json")

        assert "File not found" in str(excinfo.value)
        mock_open.assert_called_once_with("non_existent_file.json", "r")
        mock_json_load.assert_not_called()  # Ensure json.load isn't called if the file isn't opened


    @patch("json.load")
    @patch("builtins.open")
    def test_load_products_from_json_invalid_json(self, mock_open, mock_json_load, local_product_service):
        """Test loading products when the JSON file contains invalid JSON."""
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "document", 0)
        mock_open.return_value.__enter__.return_value = None  # Simulate successful file opening

        with pytest.raises(json.JSONDecodeError) as excinfo:
            local_product_service.load_products_from_json("invalid_json.json")

        assert "Invalid JSON" in str(excinfo.value)
        mock_open.assert_called_once_with("invalid_json.json", "r")
        mock_json_load.assert_called_once()

    def test_get_product_by_id_success(self, mock_json_data, local_product_service):
        """Test getting a product by ID successfully."""
        local_product_service.products = mock_json_data["products"]  # Load mock data

        product = local_product_service.get_product_by_id("P001")

        assert product is not None
        assert product["id"] == "P001"
        assert product["name"] == "iPhone 15 Pro Max"

    def test_get_product_by_id_not_found(self, mock_json_data, local_product_service):
        """Test getting a product by ID when the product is not found."""
        local_product_service.products = mock_json_data["products"]  # Load mock data

        product = local_product_service.get_product_by_id("non_existent_id")

        assert product is None

    def test_get_products_by_category_success(self, mock_json_data, local_product_service):
        """Test getting products by category successfully."""
        local_product_service.products = mock_json_data["products"]  # Load mock data
        products = local_product_service.get_products_by_category("smartphone")
        assert len(products) == 2
        assert all(product["category"] == "smartphone" for product in products)

    def test_get_products_by_category_not_found(self, mock_json_data, local_product_service):
        """Test getting products by category when no products are found."""
        local_product_service.products = mock_json_data["products"]  # Load mock data
        products = local_product_service.get_products_by_category("non_existent_category")
        assert len(products) == 0

    def test_get_products_by_availability_success(self, mock_json_data, local_product_service):
        """Test getting products by availability successfully."""
        local_product_service.products = mock_json_data["products"]  # Load mock data
        products = local_product_service.get_products_by_availability("in_stock")
        assert len(products) == 2
        assert all(product["availability"] == "in_stock" for product in products)

    def test_get_products_by_availability_not_found(self, mock_json_data, local_product_service):
        """Test getting products by availability when no products are found."""
        local_product_service.products = mock_json_data["products"]  # Load mock data
        products = local_product_service.get_products_by_availability("out_of_stock")
        assert len(products) == 0
```

Key improvements and explanations:

* **More Specific Exception Handling:**  The original code lacked specific exception handling, particularly around file loading and JSON parsing.  The improved code uses `FileNotFoundError` and `json.JSONDecodeError` to catch specific errors that can occur during `load_products_from_json`.  This makes debugging much easier.

* **Clear Error Messages in Assertions:** The `assert` statements within the `pytest.raises` blocks now verify that the correct type of exception is raised *and* that the exception message contains relevant information. This confirms the error handling is working as expected and providing useful context.

* **Ensuring `json.load` is Not Called When File Not Found:**  The `test_load_products_from_json_file_not_found` test now explicitly asserts that `json.load` is *not* called if the file cannot be opened. This is crucial to ensure that the code doesn't attempt to parse a non-existent file, which would lead to a different (and less helpful) error.

* **Context Managers for File Operations (Simulated with Mocks):**  While the actual `LocalProductService` implementation *should* use `with open(...) as f:`, the tests correctly mock this behavior using `mock_open.return_value.__enter__.return_value = None`. This is essential to simulate the resource management that a context manager provides.

* **Comprehensive Tests:** Tests cover successful loading, file not found, and invalid JSON cases.

* **Readability and Clarity:** Code is well-commented and uses descriptive variable names.

How to run the tests (assuming you have `pytest` installed):

1.  **Save:** Save the code as a Python file (e.g., `test_local_product_service.py`).  Make sure the `app/services/local_product_service.py` file exists (even if it's just a stub for now).  It needs to be there so the import works.
2.  **Run Pytest:** Open a terminal in the directory where you saved the file and run:

    ```bash
    pytest test_local_product_service.py
    ```

Pytest will discover and run all the tests in the file, reporting any failures.  You'll need to adjust the path to the test file if it's in a different location.

---
*Generated by Smart AI Bot*
