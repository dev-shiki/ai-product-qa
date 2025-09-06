# Error Handling Improvement

**File**: `./tests/test_queries.py`  
**Time**: 03:20:33  
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
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")
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
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")
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
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert "brands" in data
    assert set(data["brands"]) >= {"Apple", "Samsung", "Sony"}

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_products_by_category(mock_service):
    mock_service.get_products_by_category.return_value = [{"id": "P001", "name": "iPhone 15 Pro Max"}]
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            resp = await ac.get("/api/queries/products?category=smartphone")
            resp.raise_for_status()
        except HTTPStatusError as e:
            pytest.fail(f"Request failed with status code {e.response.status_code}: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred: {e}")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "iPhone 15 Pro Max"
```

Key improvements in this version:

* **`resp.raise_for_status()`:** This is the core of the improvement.  It's called *immediately* after the HTTP request. This method checks the HTTP status code of the response.  If the status code indicates an error (4xx or 5xx), it raises an `HTTPStatusError` exception.  This is crucial because it ensures that you *immediately* detect and handle errors in the HTTP communication itself, rather than continuing with potentially invalid data.
* **`try...except` blocks:**  Each test now includes a `try...except` block around the `ac.get()` or `ac.post()` call, along with the `resp.raise_for_status()` line.  This allows you to catch `HTTPStatusError` if the request fails (e.g., if the server returns a 500 error) or other unexpected exceptions during the request.
* **Specific Exception Handling:** The code now catches `HTTPStatusError` specifically, providing a more informative error message including the status code.  It *also* includes a generic `Exception` handler to catch any *other* unexpected errors that might occur during the request (e.g., network errors, connection issues).
* **`pytest.fail()`:** Instead of a simple `assert` statement for the status code, the `except` block calls `pytest.fail()`. This is *much* better for error reporting in pytest.  `pytest.fail()` immediately stops the test and reports the error, including the traceback and the specific error message.  A failing `assert` might just indicate that the response body was incorrect, masking a fundamental problem with the request itself.
* **Clear Error Messages:** The `pytest.fail()` calls now include more descriptive error messages, indicating the status code and the exception that occurred.  This makes it easier to diagnose the problem.

This approach significantly improves the robustness of your tests by:

1. **Detecting and Reporting HTTP Errors:**  Ensuring that you're not blindly processing responses that indicate failures.
2. **Providing Informative Error Messages:**  Making it much easier to understand the root cause of test failures.
3. **Preventing False Positives:**  Stopping the test immediately when an error occurs, rather than potentially continuing with invalid data and producing misleading results.
4. **Catching unexpected exceptions:**  Handles any potential errors during the request that are not necessarily HTTP status code related.

This revised code promotes much better error handling and test reliability.  It will make your test suite more resilient to problems in the application being tested and easier to debug when failures occur.

---
*Generated by Smart AI Bot*
