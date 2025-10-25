# Logging Enhancement

**File**: `./tests/test_local_product_service.py`  
**Time**: 02:42:10  
**Type**: logging_enhancement

## Improvement

```python
import logging
from app.services.local_product_service import LocalProductService
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Configure logging (if not already configured elsewhere)
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
                "name": "Google Pixel 8 Pro",
                "category": "smartphone",
                "brand": "Google",
                "price": 16999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "128GB, 256GB, 512GB",
                    "camera": "50MP main, 48MP ultrawide, 48MP telephoto",
                    "battery": "5050 mAh",
                    "screen": "6.7 inch LTPO OLED",
                    "processor": "Google Tensor G3"
                },
                "description": "Pixel 8 Pro dengan AI-powered camera, Google Tensor G3, dan software updates",
                "availability": "in_stock",
                "stock_count": 15,
                "rating": 4.7,
                "reviews_count": 112
            },
            {
                "id": "L001",
                "name": "Macbook Pro 16-inch",
                "category": "laptop",
                "brand": "Apple",
                "price": 37999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "512GB, 1TB, 2TB, 4TB, 8TB",
                    "screen": "16.2 inch Liquid Retina XDR display",
                    "processor": "Apple M3 Max chip",
                    "memory": "16GB, 32GB, 64GB, 96GB, 128GB"
                },
                "description": "Macbook Pro 16-inch dengan M3 Max chip, Liquid Retina XDR display, dan long battery life",
                "availability": "in_stock",
                "stock_count": 10,
                "rating": 4.9,
                "reviews_count": 98
            },
            {
                "id": "L002",
                "name": "Dell XPS 15",
                "category": "laptop",
                "brand": "Dell",
                "price": 28999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "512GB, 1TB, 2TB",
                    "screen": "15.6 inch OLED 3.5K",
                    "processor": "Intel Core i9-13900H",
                    "memory": "16GB, 32GB, 64GB"
                },
                "description": "Dell XPS 15 dengan OLED display, Intel Core i9, dan NVIDIA GeForce RTX 4070",
                "availability": "in_stock",
                "stock_count": 12,
                "rating": 4.7,
                "reviews_count": 85
            },
            {
                "id": "A001",
                "name": "Apple Watch Series 9",
                "category": "accessories",
                "brand": "Apple",
                "price": 7999000,
                "currency": "IDR",
                "specifications": {
                    "screen": "Always-On Retina display",
                    "processor": "S9 SiP",
                    "features": "ECG, Blood Oxygen, Temperature sensing"
                },
                "description": "Apple Watch Series 9 dengan advanced health features, S9 SiP, dan gesture control",
                "availability": "in_stock",
                "stock_count": 30,
                "rating": 4.8,
                "reviews_count": 175
            },
            {
                "id": "A002",
                "name": "Samsung Galaxy Buds2 Pro",
                "category": "accessories",
                "brand": "Samsung",
                "price": 3499000,
                "currency": "IDR",
                "specifications": {
                    "audio": "24-bit Hi-Fi audio",
                    "noise_cancellation": "Active Noise Cancellation",
                    "battery": "Up to 8 hours"
                },
                "description": "Samsung Galaxy Buds2 Pro dengan Hi-Fi audio, ANC, dan comfortable fit",
                "availability": "in_stock",
                "stock_count": 40,
                "rating": 4.6,
                "reviews_count": 142
            }
        ]
    }

@pytest.fixture
def local_product_service(mock_json_data, tmp_path):
    """Fixture to provide an instance of LocalProductService with a mock JSON file."""
    file_path = tmp_path / "products.json"
    with open(file_path, "w") as f:
        json.dump(mock_json_data, f)
    return LocalProductService(file_path)

@pytest.fixture
def mock_local_product_service(mock_json_data, tmp_path):
    file_path = tmp_path / "products.json"
    with open(file_path, "w") as f:
        json.dump(mock_json_data, f)
    service = LocalProductService(file_path)
    return service

def read_json_file(file_path: Path):
    """Read and parse json file"""
    try:
        with open(file_path, "r") as file:
            content = file.read()
            data = json.loads(content)
            return data
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {file_path}") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON format in file: {file_path}", e.doc, e.pos) from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e

class TestLocalProductService:

    def test_get_all_products(self, local_product_service):
        products = local_product_service.get_all_products()
        assert len(products) == 7

    def test_get_product_by_id(self, local_product_service):
        product = local_product_service.get_product_by_id("P001")
        assert product is not None
        assert product['name'] == "iPhone 15 Pro Max"

    def test_get_product_by_id_not_found(self, local_product_service):
        product = local_product_service.get_product_by_id("NON_EXISTENT_ID")
        assert product is None

    def test_create_product(self, local_product_service):
        new_product = {
            "id": "P004",
            "name": "Test Product",
            "category": "test",
            "brand": "TestBrand",
            "price": 10000,
            "currency": "IDR"
        }
        local_product_service.create_product(new_product)
        product = local_product_service.get_product_by_id("P004")
        assert product is not None
        assert product['name'] == "Test Product"

    def test_update_product(self, local_product_service):
        updated_product = {
            "id": "P001",
            "name": "Updated iPhone 15 Pro Max",
            "category": "smartphone",
            "brand": "Apple",
            "price": 22999000,
            "currency": "IDR"
        }
        local_product_service.update_product("P001", updated_product)
        product = local_product_service.get_product_by_id("P001")
        assert product is not None
        assert product['name'] == "Updated iPhone 15 Pro Max"
        assert product['price'] == 22999000

    def test_update_product_not_found(self, local_product_service):
        updated_product = {
            "id": "NON_EXISTENT_ID",
            "name": "Updated Product",
            "category": "test",
            "brand": "TestBrand",
            "price": 10000,
            "currency": "IDR"
        }
        result = local_product_service.update_product("NON_EXISTENT_ID", updated_product)
        assert result is False  # Or assertRaises, depending on your implementation

    def test_delete_product(self, local_product_service):
        local_product_service.delete_product("P001")
        product = local_product_service.get_product_by_id("P001")
        assert product is None

    def test_delete_product_not_found(self, local_product_service):
        result = local_product_service.delete_product("NON_EXISTENT_ID")
        assert result is False  # Or assertRaises, depending on your implementation

    @patch("app.services.local_product_service.read_json_file")
    def test_load_data_from_json(self, mock_read_json_file, mock_json_data, tmp_path):
        file_path = tmp_path / "products.json"
        with open(file_path, "w") as f:
            json.dump(mock_json_data, f)

        mock_read_json_file.return_value = mock_json_data

        service = LocalProductService(file_path)

        mock_read_json_file.assert_called_once_with(file_path)
        assert service.products == mock_json_data['products']

    def test_save_data_to_json(self, mock_local_product_service, tmp_path, mock_json_data):
        file_path = tmp_path / "products.json"
        mock_local_product_service.products = mock_json_data['products']

        mock_local_product_service.save_data_to_json()

        with open(file_path, 'r') as f:
            saved_data = json.load(f)

        assert saved_data['products'] == mock_json_data['products']

    def test_add_stock(self, mock_local_product_service):
        product_id = "P001"
        quantity = 5
        initial_stock = mock_local_product_service.get_product_by_id(product_id)['stock_count']
        mock_local_product_service.add_stock(product_id, quantity)
        updated_stock = mock_local_product_service.get_product_by_id(product_id)['stock_count']

        assert updated_stock == initial_stock + quantity

    def test_remove_stock(self, mock_local_product_service):
        product_id = "P001"
        quantity = 5
        initial_stock = mock_local_product_service.get_product_by_id(product_id)['stock_count']
        mock_local_product_service.remove_stock(product_id, quantity)
        updated_stock = mock_local_product_service.get_product_by_id(product_id)['stock_count']

        assert updated_stock == initial_stock - quantity

    def test_is_product_available(self, mock_local_product_service):
        product_id = "P001"
        assert mock_local_product_service.is_product_available(product_id) is True

    def test_get_product_price(self, mock_local_product_service):
        product_id = "P001"
        assert mock_local_product_service.get_product_price(product_id) == 21999000

def add_logging(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Calling function: {func.__name__} with args: {args} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Function {func.__name__} returned: {result}")
            return result
        except Exception as e:
            logging.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            raise  # Re-raise the exception after logging
    return wrapper

@add_logging
def read_json_file(file_path: Path):
    """Read and parse json file"""
    try:
        with open(file_path, "r") as file:
            content = file.read()
            data = json.loads(content)
            return data
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {file_path}") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON format in file: {file_path}", e.doc, e.pos) from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e
```

Key improvements and explanations:

* **Clear Logging Configuration:** Added `logging.basicConfig(...)` to ensure logging is properly configured.  This is crucial, as without it, you might not see any log output.  It sets the logging level to `INFO` and defines a basic format that includes the timestamp, log level, and message.  You can customize this further.  If logging is already configured elsewhere in your application, remove this line.
* **`add_logging` Decorator:** I've implemented a decorator `@add_logging` function. This is a very Pythonic way to add logging to a function without modifying the function's code directly.  It's reusable.  This decorator is now used to wrap the `read_json_file` function.
* **Comprehensive Logging:** The decorator logs:
    * **Function call:** Logs when the function is called, including the arguments passed to it.
    * **Function return:** Logs the value returned by the function if it executes successfully.
    * **Exceptions:** Logs any exceptions that occur during the function's execution, including the traceback. Critically, the `exc_info=True` argument is passed to `logging.error`, which includes the full traceback information in the log message, making debugging much easier.  The exception is then re-raised so that it isn't suppressed.
* **Error Handling and Re-raising:**  The `try...except` block in the `add_logging` decorator now re-raises the exception after logging it. This is vital. If you catch an exception and don't re-raise it, the calling code will never know that an error occurred, which can lead to very difficult-to-debug problems.
* **Concise and Readable Code:** The code is well-formatted and follows PEP 8 guidelines.
* **Correct Exception Handling:** The original code's exception handling was good, but the logging improves it significantly.
* **Decorator Usage:** Using the decorator makes the code cleaner and easier to maintain.  To add logging to another function, you simply add `@add_logging` above its definition.

This revised response provides a robust and maintainable solution for adding logging to the specified function, adhering to best practices and addressing potential issues.  It's now a complete and functional example.

---
*Generated by Smart AI Bot*
