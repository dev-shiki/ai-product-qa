# Error Handling Improvement

**File**: `./tests/test_queries.py`  
**Time**: 04:05:27  
**Type**: error_handling_improvement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport, HTTPStatusError
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
@patch("app.api.queries.ai_service")
async def test_ask_question(mock_ai, mock_product):
    mock_ai.get_response = AsyncMock(return_value="Jawaban AI")
    mock_product.smart_search_products = AsyncMock(return_value=(
        [{"id": "P001", "name": "iPhone 15 Pro Max"}], 
        "Berikut produk yang sesuai dengan kriteria Anda."
    ))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            resp = await ac.post("/api/queries/ask", json={"question": "Apa laptop terbaik?"})
            resp.raise_for_status()  # Raise HTTPStatusError for bad responses (4xx or 5xx)
        except HTTPStatusError as e:
            pytest.fail(f"Request failed: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Jawaban AI"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0
    assert "note" in data
    assert data["note"] == "Berikut produk yang sesuai dengan kriteria Anda."

@pytest.mark.asyncio
async def test_get_suggestions():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            resp = await ac.get("/api/queries/suggestions")
            resp.raise_for_status()
        except HTTPStatusError as e:
            pytest.fail(f"Request failed: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_categories(mock_service):
    mock_service.get_categories = AsyncMock(return_value=["smartphone", "laptop", "tablet"])
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            resp = await ac.get("/api/queries/categories")
            resp.raise_for_status()
        except HTTPStatusError as e:
            pytest.fail(f"Request failed: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert set(data["categories"]) >= {"smartphone", "laptop", "tablet"}

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_brands(mock_service):
    mock_service.get_brands.return_value = ["Apple", "Samsung", "Sony"]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            resp = await ac.get("/api/queries/brands")
            resp.raise_for_status()
        except HTTPStatusError as e:
            pytest.fail(f"Request failed: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert "brands" in data
    assert set(data["brands"]) >= {"Apple", "Samsung", "Sony"}
```

Key improvements:

* **`resp.raise_for_status()`:**  This is the core of the error handling.  It's called *after* making the request.  This method checks the HTTP status code of the response. If the status code indicates an error (4xx or 5xx), it raises an `HTTPStatusError` exception. This is the idiomatic way to handle HTTP errors with `httpx`.

* **`try...except` blocks:**  Each test now includes a `try...except` block around the `ac.get()` or `ac.post()` and the `resp.raise_for_status()` call. This allows us to catch potential exceptions during the request and response processing.

* **Specific Exception Handling:** Catches `HTTPStatusError` and a generic `Exception`.  This allows differentiation between known HTTP errors and more unexpected issues, providing more informative failure messages.

* **`pytest.fail()`:** When an exception is caught, `pytest.fail()` is called. This immediately fails the test and provides a descriptive error message, including the exception that occurred. This is *much* better than simply letting the exception bubble up, which might not be clear about where the failure originated.

* **Clearer Error Messages:** The error messages in the `pytest.fail()` calls are now much more informative. They include the specific exception that was raised, making it easier to diagnose the problem.

This improved version provides robust error handling for HTTP requests, making the tests more reliable and easier to debug.  It addresses the most common types of errors that can occur during HTTP communication.  The tests will now explicitly fail with meaningful error messages when something goes wrong with the requests themselves.  This makes the test suite much more valuable for identifying and fixing issues in the application.

---
*Generated by Smart AI Bot*
