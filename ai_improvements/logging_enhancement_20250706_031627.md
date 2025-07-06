# Logging Enhancement

**File**: `./tests/test_products.py`  
**Time**: 03:16:27  
**Type**: logging_enhancement

## Improvement

```python
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import logging

# Configure logging (you might want to adjust the level and format)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


@pytest.mark.asyncio
@patch("app.api.products.product_service")
async def test_get_products(mock_service):
    logging.debug("Starting test_get_products")
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
        logging.debug("Sending GET request to /api/products/")
        resp = await ac.get("/api/products/")
        logging.debug(f"Received response with status code: {resp.status_code}")

    assert resp.status_code == 200
    data = resp.json()
    logging.debug(f"Response data: {data}")
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("id" in p and "name" in p for p in data)
    logging.debug("test_get_products completed successfully")
```

Key improvements and explanations:

* **Import `logging`:**  The `logging` module needs to be imported to use logging functionality.
* **Basic Configuration:**  `logging.basicConfig(...)` is added.  This is *crucial*. Without it, you won't see any log output. I've set it to `logging.DEBUG` so you see everything, but you can change this to `logging.INFO`, `logging.WARNING`, `logging.ERROR`, etc., to control the verbosity.  The `format` argument specifies how the log messages will be formatted.  Adjust this to your liking.  You might want to include the filename and line number where the log occurred.
* **`logging.debug()` statements:**  I've strategically added `logging.debug()` calls to log:
    * The start and end of the test function.
    * The request being sent and the URL.
    * The response status code.
    * The data received in the response.
* **f-strings for logging:** I've used f-strings to include the status code and data in the log messages, making them more informative.
* **Placement of logs:**  The logs are placed before and after key operations (like sending the request and receiving the response) to provide a clear timeline of what's happening.

How to Run and See Logs:

1. **Save:** Save the code as a Python file (e.g., `test_products.py`). Make sure your `app.main` and `app.api.products.product_service` modules are set up in a way that the test can import them.
2. **Run pytest:** From your terminal, in the same directory as the file, run: `pytest -s test_products.py`  (The `-s` flag is very important; it tells pytest *not* to capture the standard output, which is where the logging goes. Without `-s`, you won't see the log messages.)
3. **Examine Output:**  You will see the logging messages printed to your console along with the pytest results.

Example Output (with `-s`):

```
============================= test session starts ==============================
platform darwin -- Python 3.11.5, pytest-7.4.3, pluggy-1.3.0
rootdir: /Users/yourusername/projects/yourproject
collected 2 items

test_products.py::test_get_products 
2023-10-27 10:30:00,123 - DEBUG - Starting test_get_products
2023-10-27 10:30:00,124 - DEBUG - Sending GET request to /api/products/
2023-10-27 10:30:00,125 - DEBUG - Received response with status code: 200
2023-10-27 10:30:00,126 - DEBUG - Response data: [{'id': 'P001', 'name': 'iPhone 15 Pro Max', 'category': 'smartphone', 'brand': 'Apple', 'price': 21999000, 'currency': 'IDR', 'description': 'iPhone 15 Pro Max dengan titanium design, kamera 48MP, dan performa terbaik', 'specifications': {'rating': 4.8, 'sold': 100, 'stock': 25, 'condition': 'Baru', 'shop_location': 'Indonesia', 'shop_name': 'Apple Store'}, 'images': ['https://example.com/P001.jpg'], 'url': 'https://shopee.co.id/P001'}]
2023-10-27 10:30:00,127 - DEBUG - test_get_products completed successfully
.
test_products.py::test_get_products_with_category PASSED

============================== 2 passed in 0.10s ==============================
```

Remember to adapt the logging level, format, and content to best suit your debugging needs.  You can also configure logging to write to a file instead of the console.

---
*Generated by Smart AI Bot*
