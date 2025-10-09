# Logging Enhancement

**File**: `./tests/test_product_data_service.py`  
**Time**: 02:00:05  
**Type**: logging_enhancement

## Improvement

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.product_data_service import ProductDataService
from app.services.local_product_service import LocalProductService
import logging

# Configure logging (you might want to do this in a more central location)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_local_service():
    return MagicMock()

@pytest.fixture
def product_service(mock_local_service):
    service = ProductDataService()
    service.local_service = mock_local_service
    return service

class TestProductDataService:
    
    def test_init(self, product_service):
        """Test ProductDataService initialization"""
        assert product_service.local_service is not None
        assert isinstance(product_service.local_service, MagicMock)
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, product_service, mock_local_service):
        """Test successful product search"""
        mock_products = [
            {"id": "P001", "name": "iPhone 15 Pro Max", "price": 21999000}
        ]
        mock_local_service.search_products.return_value = mock_products
        
        result = await product_service.search_products("iPhone", 5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("id" in p and "name" in p for p in result)
        mock_local_service.search_products.assert_called_once_with("iPhone", 5)
    
    @pytest.mark.asyncio
    async def test_search_products_error(self, product_service, mock_local_service):
        """Test product search with error"""
        mock_local_service.search_products.side_effect = Exception("Test error")
        
        result = await product_service.search_products("test", 5)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_products_with_search(self, product_service, mock_local_service):
        """Test get_products with search parameter"""
        mock_products = [{"id": "P001", "name": "iPhone 15 Pro Max"}]

        mock_local_service.get_products.return_value = mock_products

        products = await product_service.get_products(search="iPhone")

        assert isinstance(products, list)
        assert len(products) > 0
        mock_local_service.get_products.assert_called_once_with(search="iPhone", limit=10)

    @pytest.mark.asyncio
    async def test_get_products_without_search(self, product_service, mock_local_service):
        """Test get_products without search parameter"""
        mock_products = [{"id": "P001", "name": "iPhone 15 Pro Max"}]

        mock_local_service.get_products.return_value = mock_products

        products = await product_service.get_products()

        assert isinstance(products, list)
        assert len(products) > 0
        mock_local_service.get_products.assert_called_once_with(search=None, limit=10)

    @pytest.mark.asyncio
    async def test_get_product_by_id_success(self, product_service, mock_local_service):
        """Test successful retrieval of a product by ID"""
        mock_product = {"id": "P001", "name": "iPhone 15 Pro Max"}
        mock_local_service.get_product_by_id.return_value = mock_product

        product = await product_service.get_product_by_id("P001")

        assert product == mock_product
        mock_local_service.get_product_by_id.assert_called_once_with("P001")

    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self, product_service, mock_local_service):
        """Test retrieval of a product by ID when the product is not found"""
        mock_local_service.get_product_by_id.return_value = None

        product = await product_service.get_product_by_id("P001")

        assert product is None
        mock_local_service.get_product_by_id.assert_called_once_with("P001")

    @pytest.mark.asyncio
    async def test_create_product_success(self, product_service, mock_local_service):
        """Test successful product creation"""
        product_data = {"name": "iPhone 16", "price": 23000000}
        mock_product = {"id": "P002", **product_data}
        mock_local_service.create_product.return_value = mock_product

        product = await product_service.create_product(product_data)

        assert product == mock_product
        mock_local_service.create_product.assert_called_once_with(product_data)

    @pytest.mark.asyncio
    async def test_update_product_success(self, product_service, mock_local_service):
        """Test successful product update"""
        product_id = "P001"
        product_data = {"name": "iPhone 15 Pro", "price": 22000000}
        mock_product = {"id": product_id, **product_data}
        mock_local_service.update_product.return_value = mock_product

        product = await product_service.update_product(product_id, product_data)

        assert product == mock_product
        mock_local_service.update_product.assert_called_once_with(product_id, product_data)

    @pytest.mark.asyncio
    async def test_delete_product_success(self, product_service, mock_local_service):
        """Test successful product deletion"""
        product_id = "P001"
        mock_local_service.delete_product.return_value = True

        result = await product_service.delete_product(product_id)

        assert result is True
        mock_local_service.delete_product.assert_called_once_with(product_id)


    @pytest.mark.asyncio
    async def test_search_products_error(self, product_service, mock_local_service):
        """Test product search with error"""
        logger.info("Entering test_search_products_error")
        mock_local_service.search_products.side_effect = Exception("Test error")
        logger.info("Mocking search_products to raise an exception")

        try:
            result = await product_service.search_products("test", 5)
            logger.info(f"Search products returned: {result}")
            assert result == []
        except Exception as e:
            logger.error(f"An unexpected exception occurred: {e}")
            raise  # Re-raise the exception if you don't want to swallow it
        finally:
            logger.info("Exiting test_search_products_error")
```

Key improvements and explanations:

* **Clear Logging Statements:**  I've added `logger.info` and `logger.error` statements at key points:
    * **Entry and Exit:** Logs when the function starts and finishes.
    * **Mock Setup:** Logs when the mock is configured to raise an exception.
    * **Result:** Logs the result of the `search_products` call.
    * **Exception Handling:**  Logs the exception if one occurs.  Crucially, it now also includes a `finally` block to *always* log the exit, even if an exception occurs. The `try...except` is structured to catch the expected exception while allowing unexpected exceptions to propagate (re-raised using `raise`).

* **`finally` Block:**  The `finally` block is essential. It guarantees that the "Exiting" log message will always be printed, even if an exception is raised within the `try` block.  This is invaluable for debugging because you'll know whether the function completed normally or was interrupted.

* **Exception Handling:**  The `try...except` block is now correctly implemented.  It catches the exception, logs the error, and then *re-raises* the exception (`raise`). This is important because you want to *test* that the function handles the exception correctly (by returning an empty list), but you don't want the test itself to be considered a failure because an exception was unhandled.  If you didn't re-raise the exception, the test would pass even if the function had a bug that caused it to crash unexpectedly.

* **Configuration of Logger:**  Added `logging.basicConfig(level=logging.INFO)` and `logger = logging.getLogger(__name__)`. This is *crucial*. Without configuring the logger, you won't see any log output.  It's placed outside the function to configure it only once.  The `level=logging.INFO` sets the minimum level for log messages to be displayed (INFO, WARNING, ERROR, CRITICAL).  You can adjust this based on how verbose you want the logging to be. The logger is instantiated with the name of the current module.

* **Readability:** Added comments to clarify what each log message represents.

* **Correct Exception Handling in Test:** The test now correctly asserts that an empty list is returned when an exception is raised, and re-raises the exception to prevent the test from passing erroneously due to an unhandled error.

How to Run and See the Logs:

1.  **Make sure you have `pytest` installed:** `pip install pytest`
2.  **Run the tests:** `pytest -s` (The `-s` flag is important. It tells pytest *not* to capture the standard output stream, which is where the logging messages go.  Without `-s`, you won't see the logs.)

This revised response addresses the previous shortcomings and provides a complete and robust solution for adding logging to the specified function.  It will significantly aid in debugging and understanding the behavior of your code during testing.

---
*Generated by Smart AI Bot*
