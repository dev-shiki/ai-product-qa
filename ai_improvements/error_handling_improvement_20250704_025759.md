# Error Handling Improvement

**File**: `./tests/test_queries.py`  
**Time**: 02:57:59  
**Type**: error_handling_improvement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport, HTTPStatusError
from unittest.mock import patch, AsyncMock
import logging

logging.basicConfig(level=logging.INFO)


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
            logging.error(f"HTTP error occurred: {e}")
            pytest.fail(f"HTTP error occurred: {e}")  # Fail the test
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
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
            logging.error(f"HTTP error occurred: {e}")
            pytest.fail(f"HTTP error occurred: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
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
            logging.error(f"HTTP error occurred: {e}")
            pytest.fail(f"HTTP error occurred: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            pytest.fail(f"An unexpected error occurred: {e}")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert set(data["categories"]) >= {"smartphone", "laptop", "tablet"}


@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_brands(mock_service):
    mock_service.get_brands.return_value = ["Apple", "Samsung", "Sony"]
... (truncated for analysis)
```

Key improvements and explanations:

* **`resp.raise_for_status()`:** This is the core of the improvement.  It's called *immediately* after making the `ac.post` or `ac.get` request.  This method checks the HTTP status code of the response. If the status code indicates an error (4xx or 5xx range), it raises an `httpx.HTTPStatusError` exception.  Crucially, this catches errors *before* you try to parse the JSON, preventing `JSONDecodeError` and other downstream issues if the server returns an error page.

* **`try...except` block:**  The `resp.raise_for_status()` call is wrapped in a `try...except` block.  This allows us to gracefully handle the potential `HTTPStatusError`.  It also catches other unexpected exceptions that might occur during the request.

* **`HTTPStatusError` Handling:** The `except HTTPStatusError as e:` block specifically catches HTTP errors.  It logs the error using `logging.error(f"HTTP error occurred: {e}")` to provide more context about the failure. Importantly, it also calls `pytest.fail(f"HTTP error occurred: {e}")`. This will *immediately* stop the test and mark it as failed, along with a descriptive error message.  This makes debugging much easier.

* **General Exception Handling:** The `except Exception as e:` block catches *any* other exception that might occur during the process (e.g., network errors, timeouts, etc.).  This prevents the test from crashing unexpectedly and provides a chance to log the error and fail the test gracefully.

* **Logging:** Added basic logging configuration and error logging using `logging.error`.  This is *essential* for diagnosing test failures, especially in CI/CD environments.  Without logging, you're often left guessing about the cause of the failure.

* **Clear Failure Message:** The `pytest.fail` calls include a clear and informative error message that helps you quickly understand why the test failed.

Why these changes are important:

1. **Robustness:**  The tests are much more robust to errors in the application or network.  They won't crash or produce misleading results when errors occur.
2. **Debuggability:**  The logging and clear failure messages make it much easier to diagnose the cause of test failures. You'll know exactly what went wrong and where.
3. **Correctness:** The tests now accurately reflect the expected behavior of the application.  If the server returns an error, the test will fail, indicating a problem that needs to be fixed.
4. **Prevents Silent Failures:** Without this error handling, a test might continue and potentially pass even if the server returned an error, leading to false confidence in the application's correctness.  `raise_for_status()` and the `try...except` block prevent these silent failures.

This improved version makes the tests more reliable, easier to debug, and more accurate in reflecting the true state of the application.  The error handling focuses on the most likely points of failure when dealing with HTTP requests and provides clear signals when something goes wrong. It also avoids the common mistake of trying to parse JSON from an error response.

---
*Generated by Smart AI Bot*
