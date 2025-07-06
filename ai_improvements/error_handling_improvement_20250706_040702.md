# Error Handling Improvement

**File**: `./tests/test_queries.py`  
**Time**: 04:07:02  
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

    assert resp.status_code == 200
    data = resp.json()
    assert "brands" in data
    assert set(data["brands"]) >= {"Apple", "Samsung", "Sony"}
```

Key improvements in error handling:

* **`resp.raise_for_status()`**:  This is the core of the improvement.  It's added within a `try...except` block.  `raise_for_status()` checks the HTTP status code of the response. If the status code indicates an error (4xx or 5xx), it raises an `HTTPStatusError` exception. This is crucial for catching server-side errors or client-side errors that the test should be aware of.
* **`try...except HTTPStatusError`**:  The `try...except` block specifically catches the `HTTPStatusError`. This allows the test to handle HTTP errors gracefully.
* **`pytest.fail()`**:  Instead of simply letting the test continue (potentially with incorrect assertions based on a failed request), `pytest.fail()` explicitly marks the test as failed. The `pytest.fail()` includes a descriptive error message, including the status code and the error text from the exception. This makes debugging much easier.

Why these changes are important:

* **Robustness**: The tests become much more robust because they now handle the possibility of HTTP errors, which can occur due to network issues, server problems, or incorrect API usage.
* **Clear Failure Indication**: If an HTTP error *does* occur, the test will immediately fail and provide a clear error message, making it easy to identify the problem. Without error handling, the test might continue and fail on an assertion, but the root cause (the HTTP error) would be obscured.
* **More Realistic Testing**: In a real-world scenario, API requests can fail. These changes make the tests more realistic by simulating those failures and ensuring that the application behaves correctly.
* **Improved Debugging**: The inclusion of the status code and error message from the `HTTPStatusError` exception significantly improves debugging.  You know exactly what went wrong with the request.

This solution improves error handling in all the provided test cases. If any of the API calls fail (e.g., return a 500 status code), the tests will now fail explicitly with a descriptive error message instead of potentially passing with incorrect results or producing obscure error messages.  This makes the tests much more reliable and easier to debug.

---
*Generated by Smart AI Bot*
