# Error Handling Improvement

**File**: `./tests/test_queries.py`  
**Time**: 03:26:35  
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
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred during the request: {e}")

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
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred during the request: {e}")

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
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred during the request: {e}")

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

* **`resp.raise_for_status()`:** This is the core of the improvement.  It's called *after* making the request, and it checks if the HTTP status code indicates an error (4xx or 5xx). If it does, it raises an `HTTPStatusError` exception.  This is far better than just checking `resp.status_code == 200` because it proactively catches error responses and provides information about the specific error.
* **`try...except` block:**  A `try...except` block is added around the `ac.get()` and `ac.post()` calls *and* the `resp.raise_for_status()` call.  This allows us to catch `HTTPStatusError` specifically and other potential exceptions that might occur during the request (e.g., network errors, timeouts, etc.). Critically, it's *outside* of the assertions, so a failed request doesn't cause misleading assertion errors.
* **`pytest.fail()`:** Instead of letting the test continue with incorrect data, `pytest.fail()` is called inside the `except` block.  This immediately marks the test as failed and provides a clear error message, including the status code and the exception message.  This makes debugging much easier.  Using `pytest.fail` rather than `assert False` provides more descriptive error output and integrates better with pytest's reporting.
* **Catch-all `Exception`:** The `except Exception as e:` is included to catch any other unexpected errors that might occur during the request. This ensures that the test fails gracefully even if an unforeseen problem arises.
* **Error Message:** The `pytest.fail()` message includes the status code and the exception details, making it easy to diagnose the cause of the failure.

This improved version provides robust error handling, ensuring that tests fail cleanly and provide informative error messages when something goes wrong during the HTTP requests.  It adheres to best practices for testing asynchronous code with `httpx` and pytest.  It's also very important to call `raise_for_status` *before* attempting to access the `resp.json()` or other response properties.

---
*Generated by Smart AI Bot*
