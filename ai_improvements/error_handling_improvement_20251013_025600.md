# Error Handling Improvement

**File**: `./tests/test_products.py`  
**Time**: 02:56:00  
**Type**: error_handling_improvement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport, HTTPStatusError
from unittest.mock import patch, AsyncMock

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
            pytest.fail(f"HTTP request failed: {e}")  # Fail the test with a descriptive message
        except Exception as e:
            pytest.fail(f"Unexpected error during request: {e}")  # Catch any other potential errors

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
            pytest.fail(f"HTTP request failed: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error during request: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)

@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products_empty(mock_service):
    mock_service.get_products = AsyncMock(return_value=[])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
         try:
            resp = await ac.get("/api/products/")
            resp.raise_for_status()
         except HTTPStatusError as e:
            pytest.fail(f"HTTP request failed: {e}")
         except Exception as e:
            pytest.fail(f"Unexpected error during request: {e}")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0
```

Key improvements in the error handling:

* **`resp.raise_for_status()`:** This crucial line checks the HTTP status code of the response. If the status code indicates an error (4xx or 5xx), it raises an `HTTPStatusError`.  This is the standard way to handle HTTP errors in `httpx`.
* **`try...except` block:**  The `ac.get()` call is now wrapped in a `try...except` block to catch potential exceptions.
* **Specific Exception Handling:** The code now specifically handles `HTTPStatusError` which allows it to fail the test with a more informative message when the API returns an error code. It also catches `Exception` which would allow any other error (like connection errors, timeouts, etc.) to be caught.
* **`pytest.fail()`:** Instead of letting the exception bubble up, `pytest.fail()` is called. This immediately marks the test as failed and provides a descriptive error message to the test report, making debugging much easier.  The error message includes the original exception, providing more context.
* **Clearer Error Messages:** The error messages are more informative, indicating that the HTTP request itself failed and including the details of the error.

This improved version is more robust because it handles potential HTTP errors and other exceptions during the API call, providing better feedback when a test fails.  It also follows best practices for handling HTTP errors with `httpx`.  The specific exception handling avoids masking unexpected errors.

---
*Generated by Smart AI Bot*
