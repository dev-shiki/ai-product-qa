# Refactoring Suggestions

**File**: `./app/services/product_data_service.py`  
**Time**: 15:57:22  
**Type**: refactoring_suggestions

## Improvement

```python
import logging
from typing import List, Dict, Optional
from app.services.local_product_service import LocalProductService
import asyncio

logger = logging.getLogger(__name__)

class ProductDataService:
    """
    Service untuk mengambil data produk dari sumber lokal yang reliable
    """
    
    def __init__(self):
        # Use LocalProductService as primary data source
        self.local_service = LocalProductService()
        logger.info("ProductDataService initialized with LocalProductService")
    
    async def search_products(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search products using local data"""
        try:
            logger.info(f"Searching products with keyword: {keyword}")
            # Use awaitable wrapper for sync method
            products = await self._run_in_executor(self.local_service.search_products, keyword, limit)
            logger.info(f"Found {len(products)} products for keyword: {keyword}")
            return products
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    async def get_products(self, limit: int = 20, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
        """Get products with optional filtering"""
        try:
            if search:
                return await self.search_products(search, limit)
            elif category:
                return await self.get_products_by_category(category, limit)  # Ensure this is also an async call or refactor
            else:
                return await self.get_all_products(limit)  # Ensure this is also an async call or refactor
        except Exception as e:
            logger.error(f"Error getting products: {str(e)}")
            # Assuming this returns synchronous data, wrap it to avoid blocking event loop
            return await self._run_in_executor(self.local_service.get_products, limit)
    
    async def get_categories(self) -> List[str]:
        """Get available categories"""
        try:
            return await self._run_in_executor(self.local_service.get_categories)
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []

    async def _run_in_executor(self, func, *args):
        """Helper function to run synchronous functions in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def get_products_by_category(self, category: str, limit: int) -> List[Dict]:
        """Get products by category using local data"""
        try:
            products = await self._run_in_executor(self.local_service.get_products_by_category, category, limit)
            logger.info(f"Found {len(products)} products for category: {category}")
            return products
        except Exception as e:
            logger.error(f"Error getting products by category: {str(e)}")
            return []

    async def get_all_products(self, limit: int) -> List[Dict]:
        """Get all products using local data"""
        try:
            products = await self._run_in_executor(self.local_service.get_products, limit)
            logger.info(f"Found {len(products)} products")
            return products
        except Exception as e:
            logger.error(f"Error getting all products: {str(e)}")
            return []
```

**Refactoring Improvement:**

*   **Encapsulation of `asyncio.run_in_executor`:** The repeated use of `asyncio.get_event_loop().run_in_executor` is now encapsulated within a private method `_run_in_executor`.  This centralizes the logic for running synchronous functions in a separate thread, making the code cleaner and easier to maintain.  It also promotes DRY (Don't Repeat Yourself) principle.

**Explanation:**

1.  **`_run_in_executor` Helper Method:** A new private method `_run_in_executor(self, func, *args)` is introduced.  It takes a synchronous function `func` and its arguments `*args` as input. It retrieves the event loop and uses `loop.run_in_executor` to execute the synchronous function in a separate thread pool, preventing the main event loop from blocking.  The result of the function is awaited and returned.

2.  **Replaced Inline Executor Calls:**  The original code had `asyncio.get_event_loop().run_in_executor` directly within `search_products`, `get_products`, and `get_categories`.  These calls are now replaced with calls to `await self._run_in_executor(...)`.

3.  **Modified return types to await the executor calls:** Because the `_run_in_executor` function is awaiting the execution in a separate thread, the methods calling it (`search_products`, `get_products`, `get_categories`, `get_products_by_category`, and `get_all_products`) must now also be `await`ed.

4. **Added `get_products_by_category` and `get_all_products` methods:** These are helper methods to fetch data and ensure that all calls to `local_service` methods are done using `_run_in_executor`.

**Why this is an Improvement:**

*   **Readability:** The code is cleaner and easier to read. The core logic of the service methods is more apparent because the threading details are hidden in the helper method.
*   **Maintainability:** If you need to change how synchronous functions are executed (e.g., use a different thread pool), you only need to modify the `_run_in_executor` method, rather than updating every call site.
*   **Testability:**  Easier to mock and test the execution of synchronous functions in an asynchronous context, as you only need to mock the `_run_in_executor` method.
*   **Reduced Duplication:**  Eliminates redundant `asyncio.get_event_loop()` calls.

**Important Note:**  This refactoring assumes that `LocalProductService`'s methods (`search_products`, `get_products`, `get_categories`, `get_products_by_category`) are synchronous.  If they are already asynchronous, this change is unnecessary and would introduce overhead.  If `get_products_by_category` and `get_all_products` were intended to be synchronous, then this code will make them synchronous. If they were meant to be asynchronous, you should define them as such and call them appropriately using `await`. I have implemented methods for each of the functions used.

---
*Generated by Smart AI Bot*
