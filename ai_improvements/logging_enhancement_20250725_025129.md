# Logging Enhancement

**File**: `./tests/test_products.py`  
**Time**: 02:51:29  
**Type**: logging_enhancement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import logging

# Configure logging (adjust level as needed)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products(mock_service):
    logger.info("Starting test_get_products")  # Log start of the test
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
        logger.info("Sending GET request to /api/products/")  # Log the API call
        resp = await ac.get("/api/products/")
        logger.info(f"Received response with status code: {resp.status_code}") # Log the response status code

    assert resp.status_code == 200
    data = resp.json()
    logger.debug(f"Response data: {data}")  # Log the response data (DEBUG level)
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)
    logger.info("test_get_products passed")  # Log the successful completion of the test


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
            "condition": "Baru",
            "shop_location": "Indonesia",
            "shop_name": "Apple Store"
        },
        "images": ["https://example.com/P001.jpg"],
        "url": "https://shopee.co.id/P001"
    }])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/?category=smartphone")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_product_by_id(mock_service):
    mock_service.get_product = AsyncMock(return_value={
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
    })
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/products/P001")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "id" in data and "name" in data

```

Key improvements and explanations:

* **Clear Logging Configuration:**  The code now includes `logging.basicConfig(level=logging.INFO)`.  This is *crucial*. Without this, you might not see any log output.  I've set the default level to `INFO`, but you can adjust it to `DEBUG` for more verbose output or `WARNING` or `ERROR` for less. The logger name is set to the module name using `logger = logging.getLogger(__name__)`. This helps identify where the logs originate.

* **Informative Log Messages:**  The log messages are now more descriptive.  They indicate the start of the test, the API call being made, the response status code, and (at the DEBUG level) the response data.  This gives you a much better picture of what's happening during the test.

* **DEBUG Level for Data:**  Logging the entire response data is done at the `DEBUG` level.  This is good practice because you usually only want to see that level of detail when you're actively debugging a problem.  You won't be overwhelmed with data during normal test runs.

* **Log Test Completion:** Added a log message when `test_get_products` successfully completes. This confirms that the test not only started, but also finished without throwing an unhandled exception.

* **Correct Placement:** The logging statements are placed strategically to give you the most useful information at key points in the function's execution.

* **No Unnecessary Code:** Only the requested function was modified.

How to run with logging:

1.  **Save:** Save the code as a Python file (e.g., `test_products.py`).
2.  **Install pytest and httpx:** `pip install pytest httpx pytest-asyncio`
3.  **Run the test:** `pytest -s test_products.py`

The `-s` flag is important. It tells pytest *not* to capture standard output (where logging goes). If you don't use `-s`, you won't see the log messages in your terminal.  If you want to see more details, change `logging.INFO` to `logging.DEBUG`.

This revised answer provides a complete and practical solution for adding effective logging to your pytest function.  Remember to adjust the logging level and message content to suit your specific debugging needs.

---
*Generated by Smart AI Bot*
