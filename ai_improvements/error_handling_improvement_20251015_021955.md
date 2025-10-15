# Error Handling Improvement

**File**: `./tests/test_queries.py`  
**Time**: 02:19:55  
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
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")  # Explicitly fail the test
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

Key improvements in error handling:

* **`resp.raise_for_status()`:**  This is the most important addition.  It checks if the HTTP response status code indicates an error (4xx or 5xx). If it does, it raises an `HTTPStatusError` exception. This is the standard way to handle HTTP errors.  Without this, your tests could proceed even if the API endpoint returned an error, leading to misleading results.
* **`try...except` blocks:**  Each `async with AsyncClient(...)` block is now wrapped in a `try...except` block.  This allows us to catch potential exceptions during the API call.
* **Specific Exception Handling (`HTTPStatusError`):** The code now specifically catches `HTTPStatusError`.  This allows for more targeted error handling.  If an HTTP error occurs, we can now provide a more informative error message including the status code.
* **Catch-all `Exception`:**  A broader `except Exception` clause is included to catch any other unexpected exceptions that might occur during the request (e.g., network errors, timeouts, etc.). This prevents the test from crashing due to unhandled exceptions.
* **`pytest.fail()`:** Instead of potentially continuing with assertions after an error, `pytest.fail()` is called within the `except` blocks.  This immediately marks the test as failed and provides a clear error message in the test output, making debugging easier.  The error message now includes the status code or the exception message, providing more context.

This revised code provides robust error handling, ensuring that tests fail gracefully and provide informative error messages when something goes wrong during the API calls.  This makes the tests more reliable and easier to debug.  The error messages in the `pytest.fail` calls are also more informative, which aids in root cause analysis.

---
*Generated by Smart AI Bot*
