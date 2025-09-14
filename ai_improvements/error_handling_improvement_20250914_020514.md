# Error Handling Improvement

**File**: `./app/api/products.py`  
**Time**: 02:05:14  
**Type**: error_handling_improvement

## Improvement

```python
from fastapi import APIRouter, HTTPException
from app.services.product_data_service import ProductDataService
from app.models.product import ProductResponse
from typing import List, Optional

router = APIRouter()
product_service = ProductDataService()

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    limit: Optional[int] = 20,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Get products from local data source"""
    try:
        products = await product_service.get_products(
            limit=limit,
            category=category,
            search=search
        )
        return products
    except ValueError as ve:
        #  Handle specific validation errors from the service layer.  For example,
        #  if limit is negative. This is preferable to catching all exceptions.
        raise HTTPException(status_code=400, detail=str(ve))
    except ProductDataService.DataUnavailableError as de:
        # Handle cases where the data source is temporarily unavailable.
        raise HTTPException(status_code=503, detail=str(de))
    except Exception as e:
        # Log the error for debugging.  Include context, such as the parameters passed.
        print(f"Error getting products with limit={limit}, category={category}, search={search}: {e}") #Crucial logging!
        raise HTTPException(status_code=500, detail="Internal Server Error: Unable to retrieve products.")

@router.get("/categories")
async def get_categories():
    """Get available product categories"""
    try:
        categories = await product_service.get_categories()
        return {"categories": categories}
    except Exception as e:
        print(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Unable to retrieve categories.")

@router.get("/search")
async def search_products(query: str, limit: Optional[int] = 10):
    """Search products by query"""
    try:
        products = await product_service.search_products(query, limit)
        return {"products": products, "query": query, "source": "local"}
    except Exception as e:
        print(f"Error searching products with query={query}, limit={limit}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Product search failed.")

@router.get("/top-rated")
async def get_top_rated_products(limit: Optional[int] = 10):
    """Get top rated products"""
    try:
        products = await product_service.get_top_rated_products(limit)
        return {"products": products, "source": "local"}
    except Exception as e:
        print(f"Error getting top rated products with limit={limit}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Unable to retrieve top-rated products.")
```

Key improvements and explanations:

* **Specific Exception Handling:**  Instead of catching *all* `Exception` types with a blanket `except Exception as e:`, the code now attempts to catch more specific exceptions.  This is **crucial**.  The example adds `ValueError` (which could arise from invalid input to the service layer) and a hypothetical `ProductDataService.DataUnavailableError` (to handle cases where the data source is down).  You should tailor these specific exceptions to the *actual* exceptions that `ProductDataService` might raise.

* **Clearer Error Messages:**  The `detail` in the `HTTPException` now provides a more user-friendly message like "Internal Server Error: Unable to retrieve products."  Avoid exposing internal error details directly to the client, as this could reveal sensitive information or confuse them.  Use generic messages and log the actual exception internally.

* **Logging:**  The most important addition is logging.  `print(f"Error getting products with limit={limit}, category={category}, search={search}: {e}")` logs the exception `e` along with the relevant parameters *before* raising the `HTTPException`.  This is essential for debugging and diagnosing issues in production.  Without logging, you'll be flying blind.  In a real application, you would use a proper logging library (like `logging` in Python) instead of `print`.  Logging libraries allow you to control the level of detail, where logs are stored, and how they are formatted.

* **Appropriate HTTP Status Codes:**  The `HTTPException` now uses more appropriate status codes.  A `ValueError` translates to a 400 (Bad Request), indicating client-side error. A data unavailability error translates to a 503 (Service Unavailable).  A generic error still results in a 500 (Internal Server Error), but hopefully you'll rarely hit that because you're handling more specific exceptions.

* **Handles Potential Issues in `ProductDataService`:** Assumes `ProductDataService` might throw exceptions like `DataUnavailableError` when its data source is unreachable or `ValueError` when an argument is invalid, such as a negative `limit`. This makes the solution more robust.

How to use the logging library (example):

```python
import logging

# Configure logging (e.g., to a file) - do this once at the start of your application.
logging.basicConfig(filename='product_api.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    limit: Optional[int] = 20,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Get products from local data source"""
    try:
        products = await product_service.get_products(
            limit=limit,
            category=category,
            search=search
        )
        return products
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except ProductDataService.DataUnavailableError as de:
        raise HTTPException(status_code=503, detail=str(de))
    except Exception as e:
        logging.exception(f"Error getting products with limit={limit}, category={category}, search={search}") # Use logging.exception
        raise HTTPException(status_code=500, detail="Internal Server Error: Unable to retrieve products.")


```

Key improvements to the logging example:

* `import logging`: Imports the necessary library.
* `logging.basicConfig(...)`:  This configures the logging system.  Crucially, it sets `level=logging.ERROR`.  This means that only errors and critical errors will be logged.  You can adjust this based on how verbose you want your logging to be.  The `format` argument specifies how the log messages will appear.  It also tells the program to write the logs to a file called `product_api.log`
* `logging.exception(...)`:  Inside the `except` block, `logging.exception()` is used.  This is *much* better than `print` because it automatically includes the full traceback information in the log, making it far easier to diagnose the root cause of the error.

This revised solution provides significantly better error handling, logging, and user feedback, making your API much more robust and easier to maintain. Remember to define the custom exception `ProductDataService.DataUnavailableError` appropriately.

---
*Generated by Smart AI Bot*
