# Error Handling Improvement

**File**: `./tests/test_products.py`  
**Time**: 03:26:31  
**Type**: error_handling_improvement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport, HTTPStatusError
from unittest.mock import patch, AsyncMock
import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products(mock_service):
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
        try:
            resp = await ac.get("/api/products/")
            resp.raise_for_status()  # Raise HTTPStatusError for bad responses (4xx or 5xx)
        except HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            pytest.fail(f"Request failed: {e}") # Fail the test if there is an HTTP error.
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)

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
        try:
            resp = await ac.get("/api/products/?category=smartphone")
            resp.raise_for_status()
        except HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            pytest.fail(f"Request failed: {e}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)
```

Key improvements:

* **`resp.raise_for_status()`:**  This is the core improvement. It checks the HTTP status code of the response. If the status code indicates an error (4xx or 5xx), it raises an `HTTPStatusError` exception.  This is the standard way to handle HTTP errors in `httpx`.
* **`try...except` block:**  The `ac.get()` call is now wrapped in a `try...except` block to catch potential exceptions.  This allows us to handle errors gracefully.
* **Specific `HTTPStatusError` handling:** The code specifically catches `HTTPStatusError`, allowing you to handle HTTP-related errors separately from other potential exceptions.
* **General `Exception` handling:** A general `Exception` catch-all is included to handle any unexpected errors during the request. This prevents the test from crashing and provides more informative error messages.
* **Logging:**  Includes `logger.error` and `logger.exception` to log the error. This is crucial for debugging. `logger.exception` automatically includes the traceback.
* **`pytest.fail()`:** Instead of just letting the exception bubble up (which might lead to less clear pytest output), the `pytest.fail()` function is used to explicitly mark the test as failed and provide a descriptive message.  This makes it immediately clear why the test failed.
* **Clear Error Messages:** The error messages passed to `pytest.fail()` are more informative, including the original exception.

This revised version significantly improves the error handling, making the tests more robust and easier to debug.  It addresses the shortcomings of the original code by properly checking for and handling HTTP errors and other potential exceptions during the request process.  It also provides useful logging for debugging purposes.  This pattern of wrapping `httpx` calls in `try...except` blocks and using `raise_for_status()` is best practice.

---
*Generated by Smart AI Bot*
