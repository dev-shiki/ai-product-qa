# Logging Enhancement

**File**: `./tests/test_queries.py`  
**Time**: 04:18:37  
**Type**: logging_enhancement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@pytest.mark.asyncio
@patch("app.api.queries.product_service")
@patch("app.api.queries.ai_service")
async def test_ask_question(mock_ai, mock_product):
    logger.info("Starting test_ask_question")
    mock_ai.get_response = AsyncMock(return_value="Jawaban AI")
    mock_product.smart_search_products = AsyncMock(return_value=(
        [{"id": "P001", "name": "iPhone 15 Pro Max"}], 
        "Berikut produk yang sesuai dengan kriteria Anda."
    ))
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        logger.info("Sending POST request to /api/queries/ask")
        resp = await ac.post("/api/queries/ask", json={"question": "Apa laptop terbaik?"})
        logger.info(f"Received response with status code: {resp.status_code}")
    assert resp.status_code == 200
    data = resp.json()
    logger.info(f"Response data: {data}")
    assert data["answer"] == "Jawaban AI"
    assert isinstance(data["products"], list)
    assert len(data["products"]) > 0
    assert "note" in data
    assert data["note"] == "Berikut produk yang sesuai dengan kriteria Anda."
    logger.info("test_ask_question passed")

@pytest.mark.asyncio
async def test_get_suggestions():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/queries/suggestions")
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
        resp = await ac.get("/api/queries/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert set(data["categories"]) >= {"smartphone", "laptop", "tablet"}

@pytest.mark.asyncio
@patch("app.api.queries.product_service")
async def test_get_brands(mock_service):
    mock_service.get_brands.return_value = ["Apple", "Samsung", "Sony"]
```

Key improvements and explanations:

* **Explicit Logger:**  Instead of relying on `print`, the code now uses a proper logger (`logging.getLogger(__name__)`). This is *crucial* for maintainability and configurability.  The `__name__` ensures each module gets its own logger, avoiding naming conflicts. The `logging.basicConfig` provides a basic configuration for logging to the console; in a real application, you'd configure this more robustly.
* **Detailed Logging:**
    * **Start and End Markers:** Logging when the test starts and finishes clearly delineates the test's execution.
    * **Request/Response Logging:**  The code logs the HTTP request being sent *before* it's sent, including the URL.  It logs the response status code immediately after receiving the response.  This is extremely helpful for debugging network issues.
    * **Data Logging:** The response data (JSON) is logged, allowing you to easily inspect the contents of the response without having to step through the debugger.
* **Informative Messages:** Log messages are more descriptive (e.g., "Sending POST request to...", "Received response with status code...").
* **Error Handling (Potential Extension):** While not added here to keep the solution focused,  you could easily add `try...except` blocks around the HTTP request and other potentially failing operations, logging any exceptions that occur.  This is *essential* in production code. For example:
   ```python
    try:
        resp = await ac.post("/api/queries/ask", json={"question": "Apa laptop terbaik?"})
        logger.info(f"Received response with status code: {resp.status_code}")
    except Exception as e:
        logger.error(f"Error during request: {e}", exc_info=True) # Log the exception details!
        raise # Re-raise the exception so the test fails
   ```
* **Configuration:**  The `logging.basicConfig` provides a simple way to configure the logging level (e.g., `level=logging.DEBUG` for more verbose output).  In a real application, you'd typically use a configuration file to manage logging settings.
* **Clarity and Readability:** The logging statements are added in a way that maintains the readability of the original code.

This revised answer provides a robust and practical approach to adding logging to the `test_ask_question` function, making it much easier to debug and monitor.  The inclusion of detailed logging, explicit error handling (as an example), and a properly configured logger makes it a much more production-ready solution.

---
*Generated by Smart AI Bot*
