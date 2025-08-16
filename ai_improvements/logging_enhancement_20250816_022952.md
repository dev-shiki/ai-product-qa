# Logging Enhancement

**File**: `./tests/test_local_product_service.py`  
**Time**: 02:29:52  
**Type**: logging_enhancement

## Improvement

```python
from app.services.local_product_service import LocalProductService
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import logging

# Configure logging (basic configuration for demonstration)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
            },
            {
                "id": "P003",
                "name": "Xiaomi 14 Pro",
                "category": "smartphone",
                "brand": "Xiaomi",
                "price": 16999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "50MP main, 50MP ultrawide, 50MP telephoto",
                    "battery": "4880 mAh",
                    "screen": "6.73 inch LTPO AMOLED",
                    "processor": "Snapdragon 8 Gen 3"
                },
                "description": "Xiaomi 14 Pro dengan Leica Summilux lens dan fast charging",
                "availability": "in_stock",
                "stock_count": 30,
                "rating": 4.7,
                "reviews_count": 112
            },
            {
                "id": "P004",
                "name": "Google Pixel 8 Pro",
                "category": "smartphone",
                "brand": "Google",
                "price": 18999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "128GB, 256GB, 512GB",
                    "camera": "50MP main, 48MP ultrawide, 48MP telephoto",
                    "battery": "5050 mAh",
                    "screen": "6.7 inch LTPO OLED",
                    "processor": "Google Tensor G3"
                },
                "description": "Google Pixel 8 Pro dengan AI photography dan software updates",
                "availability": "in_stock",
                "stock_count": 15,
                "rating": 4.6,
                "reviews_count": 98
            },
            {
                "id": "P005",
                "name": "Oppo Find X7 Ultra",
                "category": "smartphone",
                "brand": "Oppo",
                "price": 17999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB",
                    "camera": "50MP main, 50MP ultrawide, 50MP periscope telephoto, 50MP telephoto",
                    "battery": "5000 mAh",
                    "screen": "6.82 inch AMOLED",
                    "processor": "Snapdragon 8 Gen 3"
                },
                "description": "Oppo Find X7 Ultra dengan dual periscope camera dan charging cepat",
                "availability": "in_stock",
                "stock_count": 22,
                "rating": 4.7,
                "reviews_count": 105
            }
        ]
    }


class TestLocalProductService:
    @pytest.fixture
    def local_product_service(self):
        return LocalProductService()

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_get_products(self, mock_open, local_product_service, mock_json_data):
        """Test getting products from a JSON file"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.close.return_value = None

        products = local_product_service.get_products()

        assert len(products) == 5
        assert products[0]["name"] == "iPhone 15 Pro Max"

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_get_product_by_id(self, mock_open, local_product_service, mock_json_data):
        """Test getting a product by its ID"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.close.return_value = None

        product_id = "P002"
        product = local_product_service.get_product_by_id(product_id)

        assert product is not None
        assert product["name"] == "Samsung Galaxy S24 Ultra"

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_get_product_by_id_not_found(self, mock_open, local_product_service, mock_json_data):
        """Test case when product ID is not found"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.close.return_value = None

        product_id = "P999"
        product = local_product_service.get_product_by_id(product_id)

        assert product is None

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_update_product_stock(self, mock_open, local_product_service, mock_json_data):
        """Test updating the stock count of a product"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.write.return_value = None
        mock_open.return_value.__enter__.return_value.close.return_value = None

        product_id = "P003"
        new_stock_count = 35

        updated_product = local_product_service.update_product_stock(product_id, new_stock_count)

        assert updated_product is not None
        assert updated_product["stock_count"] == new_stock_count

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_update_product_stock_not_found(self, mock_open, local_product_service, mock_json_data):
        """Test updating stock when product ID is not found"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.write.return_value = None
        mock_open.return_value.__enter__.return_value.close.return_value = None

        product_id = "P999"
        new_stock_count = 35

        updated_product = local_product_service.update_product_stock(product_id, new_stock_count)

        assert updated_product is None

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_add_product(self, mock_open, local_product_service, mock_json_data):
        """Test adding a new product"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.write.return_value = None
        mock_open.return_value.__enter__.return_value.close.return_value = None

        new_product = {
            "id": "P006",
            "name": "New Product",
            "category": "electronics",
            "brand": "Generic",
            "price": 9999000,
            "currency": "IDR",
            "specifications": {},
            "description": "A new product for testing",
            "availability": "in_stock",
            "stock_count": 10,
            "rating": 0.0,
            "reviews_count": 0
        }

        added_product = local_product_service.add_product(new_product)

        assert added_product is not None
        assert added_product["name"] == "New Product"

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_delete_product(self, mock_open, local_product_service, mock_json_data):
        """Test deleting a product by ID"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.write.return_value = None
        mock_open.return_value.__enter__.return_value.close.return_value = None

        product_id = "P004"
        deleted_product = local_product_service.delete_product(product_id)

        assert deleted_product is not None
        assert deleted_product["id"] == product_id

    @patch("app.services.local_product_service.open", new_callable=MagicMock)
    def test_delete_product_not_found(self, mock_open, local_product_service, mock_json_data):
        """Test deleting a product when ID is not found"""
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_json_data)
        mock_open.return_value.__enter__.return_value.write.return_value = None
        mock_open.return_value.__enter__.return_value.close.return_value = None

        product_id = "P999"
        deleted_product = local_product_service.delete_product(product_id)

        assert deleted_product is None


def delete_product(self, product_id: str) -> dict | None:
    """Deletes a product from the data store based on its ID.

        Args:
            product_id (str): The unique identifier of the product to delete.

        Returns:
            dict | None: The deleted product's data as a dictionary if the product was found and deleted successfully.
                         Returns None if the product with the given ID was not found.
    """
    logging.info(f"Attempting to delete product with ID: {product_id}")  # Log the attempt

    try:
        products = self.get_products()  # Get the current list of products
        initial_product_count = len(products) #Get the amount of initial product
        products = [product for product in products if product["id"] != product_id]  # Filter out the product to be deleted
        deleted_product = next((product for product in self.get_products() if product["id"] == product_id), None)

        if len(products) < initial_product_count: #If the current amount of products is less than the initial amount then the product must have been deleted
            self._save_products(products)  # Save the updated list back to the file
            logging.info(f"Product with ID: {product_id} deleted successfully.")  #Log success
            return deleted_product
        else:
            logging.warning(f"Product with ID: {product_id} not found for deletion.")  #Log not found
            return None  # Product not found
    except Exception as e:
        logging.error(f"Error deleting product with ID: {product_id}. Error: {e}")  #Log any errors.
        return None
```

Key improvements and explanations:

* **Clear Logging Statements:**
    * `logging.info`: Used for normal operation events (e.g., "Attempting to delete...", "Product deleted successfully"). This is good for tracking the function's progress during normal use.
    * `logging.warning`: Used when something unexpected happens, but doesn't prevent the function from completing (e.g., "Product not found"). This alerts you to potential issues.
    * `logging.error`: Used when an error occurs that prevents the function from completing its task (e.g., "Error deleting product..."). This is critical for debugging.
* **Comprehensive Logging:** The logging statements cover the key stages of the function:
    * Entry to the function: Logs the `product_id` being processed.
    * Success case:  Logs successful deletion.
    * Not found case: Logs when the `product_id` is not found.
    * Error case: Logs exceptions that occur during processing, including the exception message.
* **Error Handling with Logging:** The `try...except` block now includes logging the error. This is *crucial* because it allows you to diagnose problems that might otherwise be hidden.  The `e` variable (the exception object) is included in the log message so you get the full details of the error.
* **Log Levels:** Uses `logging.INFO`, `logging.WARNING`, and `logging.ERROR` to indicate the severity of the log message.  This allows you to filter log messages based on their importance.  Configure the `logging.basicConfig` function to control the verbosity of the logging.
* **String Formatting (f-strings):** Uses f-strings (e.g., `f"Product with ID: {product_id} deleted"`) for cleaner and more readable log messages.
* **Why this is better:**  This version is more robust and informative than simply adding `print` statements.  The logging module offers:
    * Configurable output (e.g., to a file, to the console).
    * Log levels for filtering messages.
    * Consistent formatting.
    * The ability to disable logging entirely without modifying code.

This comprehensive logging will significantly improve the debuggability and maintainability of your code.  Remember to adjust the `logging.basicConfig` to suit your needs (e.g., logging to a file, changing the log level).

---
*Generated by Smart AI Bot*
