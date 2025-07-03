# Logging Enhancement

**File**: `./tests/test_products.py`  
**Time**: 02:25:28  
**Type**: logging_enhancement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import logging

# Configure logging (you might want to configure this globally in your test suite)
logging.basicConfig(level=logging.DEBUG)  # Set the desired logging level

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products(mock_service):
    logger = logging.getLogger(__name__)  # Get a logger instance

    logger.debug("Starting test_get_products")  # Log the start of the test

    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple",
        "price": 21999000,
        "currency": "IDR",
        "description": "iPhone 15 Pro Max dengan titanium design, kamera 48MP, dan performa terbaik",
        "specifications": {
            "rating": 4.8,
            "sold": 100,
            "stock": 25,
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "Apple Store"
        },
        "images": ["https://example.com/P001.jpg"],
        "url": "https://shopee.co.id/P001"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        logger.debug("Sending GET request to /api/products/")  # Log the request
        resp = await ac.get("/api/products/")
        logger.debug(f"Received response with status code: {resp.status_code}")  # Log the response status

    assert resp.status_code == 200
    data = resp.json()
    logger.debug(f"Response data: {data}")  # Log the response data

    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)

    logger.debug("test_get_products completed successfully")  # Log the end of the test


@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products_with_category(mock_service):
    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        "name": "iPhone 15 Pro Max",
        "category": "smartphone",
        "brand": "Apple",
        "price": 21999000,
        "currency": "IDR",
        "description": "iPhone 15 Pro Max dengan titanium design, kamera 48MP, dan performa terbaik",
        "specifications": {
            "rating": 4.8,
            "sold": 100,
            "stock": 25,
... (truncated for analysis)
```

Key improvements and explanations:

* **Import `logging`:**  The code now imports the `logging` module, which is essential for using the logging functionality.
* **Configure Logging:**  `logging.basicConfig(level=logging.DEBUG)` sets up basic logging.  **Crucially, you should configure the logging level to suit your needs.**  `DEBUG` is very verbose.  Consider `INFO` or `WARNING` for less output.  This also configures a basic handler that prints to the console.  For more robust logging, you should use a `logging.FileHandler` or a more complex configuration.  The configuration should typically be done *once* at the beginning of your test run, not inside each test function.  I recommend doing it in `conftest.py` if you have one, or at the top of your test module.
* **Get a Logger Instance:** `logger = logging.getLogger(__name__)` creates a logger instance.  Using `__name__` is a good practice because it makes it easy to identify where the log messages are coming from.
* **Log Messages:**  I've added several log messages using `logger.debug()`.  `debug()` is used for detailed information that is primarily useful for debugging.  Other logging levels (e.g., `info()`, `warning()`, `error()`) can be used for different types of messages.  Critically, messages are logged at the beginning and end of the test, before and after the API call, and for the response status code and data.
* **f-strings:** Using f-strings (e.g., `f"Response data: {data}"`) makes it easy to include variable values in log messages.
* **Error Handling (Important Consideration):**  This example doesn't explicitly include error handling in the `try...except` sense.  However, if the API call (`ac.get("/api/products/")`) were to raise an exception, the logging statement *before* the call would execute, but the ones *after* wouldn't.  To make logging more robust, consider wrapping the API call and assertions in a `try...except` block to log any exceptions that occur.

Here's an example of how to incorporate better error handling and logging:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import logging

logging.basicConfig(level=logging.INFO)


@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products(mock_service):
    logger = logging.getLogger(__name__)

    logger.info("Starting test_get_products")

    mock_service.get_products = AsyncMock(return_value=[{
        "id": "P001",
        # ... (rest of your data)
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            logger.debug("Sending GET request to /api/products/")
            resp = await ac.get("/api/products/")
            logger.debug(f"Received response with status code: {resp.status_code}")
            resp.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            data = resp.json()
            logger.debug(f"Response data: {data}")

            assert resp.status_code == 200
            assert isinstance(data, list)
            assert len(data) > 0
            assert all("id" in p and "name" in p for p in data)

            logger.info("test_get_products completed successfully")

        except Exception as e:
            logger.exception(f"An error occurred during test_get_products: {e}")  # Log the exception with traceback
            raise  # Re-raise the exception to fail the test
```

Key changes in the error handling example:

* **`try...except` Block:** Encloses the potentially failing code.
* **`logger.exception()`:**  Logs the exception *and* a traceback.  This is extremely valuable for debugging.  It's very important to use `logger.exception` instead of just `logger.error` when you're logging exceptions, so you get the full traceback.
* **`resp.raise_for_status()`:**  This line checks the HTTP status code of the response. If the status code indicates an error (4xx or 5xx), it raises an `HTTPError` exception, which will be caught by the `except` block.  This is good practice for handling API errors.
* **`raise` (Re-raising the exception):** After logging the exception, the `raise` statement re-raises the exception. This is important because it ensures that the test still fails if an error occurs.  If you don't re-raise, the test will pass even if the API call failed, which is not what you want.  The test runner will then report a failure along with the exception and traceback.

This more robust example provides much better insight into potential problems during test execution.  Remember to adjust the logging level and output destination (e.g., file) based on your specific needs.  It is also good practice to remove the logging statements once you are done debugging, or change the level to `INFO` or `WARNING` so that you don't have too much output.

---
*Generated by Smart AI Bot*
