# Error Handling Improvement

**File**: `./app/services/local_product_service.py`  
**Time**: 01:58:27  
**Type**: error_handling_improvement

## Improvement

```python
import logging
import json
import random
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LocalProductService:
    """
    Service untuk data produk lokal yang reliable dan tidak bergantung pada API eksternal
    """
    
    def __init__(self):
        self.products = self._load_local_products()
        logger.info(f"Loaded {len(self.products)} local products from JSON file")
    
    def _load_local_products(self) -> List[Dict]:
        """Load produk dari file JSON lokal"""
        try:
            # Get the path to the data/products.json file
            current_dir = Path(__file__).parent.parent.parent
            json_file_path = current_dir / "data" / "products.json"
            
            if not json_file_path.exists():
                logger.error(f"Products JSON file not found at: {json_file_path}")
                return self._get_fallback_products()
            
            # Try different encodings
            encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(json_file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        # Remove BOM if present
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        
                        data = json.loads(content)
                        products = data.get('products', [])
                        
                        # Transform products to match expected format
                        transformed_products = []
                        for product in products:
                            transformed_product = {
                                "id": product.get('id', ''),
                                "name": product.get('name', ''),
                                "category": product.get('category', ''),
                                "brand": product.get('brand', ''),
                                "price": product.get('price', 0.0),
                                "stock": product.get('stock', 0)
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded products using encoding: {encoding}")
                        return transformed_products
                
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode JSON with encoding {encoding}: {e}")
                except Exception as e:
                    logger.exception(f"Error reading or processing file with encoding {encoding}: {e}")

            logger.error("Failed to load products using any encoding.  Falling back to default products.")
            return self._get_fallback_products()

        except Exception as e:
            logger.exception(f"Unexpected error loading local products: {e}")
            return self._get_fallback_products()

    def _get_fallback_products(self) -> List[Dict]:
        """Return daftar produk fallback jika file JSON tidak dapat dimuat."""
        logger.warning("Returning fallback products due to loading failure.")
        return [
            {"id": "fb-1", "name": "Fallback Product 1", "category": "Fallback", "brand": "Fallback", "price": 10.0, "stock": 100},
            {"id": "fb-2", "name": "Fallback Product 2", "category": "Fallback", "brand": "Fallback", "price": 20.0, "stock": 50},
        ]

    def get_all_products(self) -> List[Dict]:
        """Return semua produk."""
        return self.products
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Return produk berdasarkan ID."""
        for product in self.products:
            if product["id"] == product_id:
                return product
        return None

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Return produk berdasarkan kategori."""
        return [product for product in self.products if product["category"] == category]

    def get_random_products(self, num_products: int) -> List[Dict]:
        """Return sejumlah produk acak."""
        if num_products > len(self.products):
            logger.warning(f"Requested {num_products} random products, but only {len(self.products)} available. Returning all products.")
            return self.products
        return random.sample(self.products, num_products)
```

Key improvements and explanations:

* **More Specific Exception Handling:** The code now specifically catches `json.JSONDecodeError` which is crucial when working with JSON data. This allows for targeted error messages and handling when JSON parsing fails due to encoding or formatting issues.  A broader `Exception` is still caught within the encoding loop to catch file read errors or other unexpected issues.  An outermost `Exception` catch ensures that any unhandled error doesn't crash the application and also triggers the fallback mechanism.

* **Detailed Logging:**  Instead of a generic error message, the logging now includes the specific encoding that failed during JSON decoding. This is immensely helpful for debugging encoding-related problems.  Logging is also added for successful loading, specifying the encoding that worked.  The final `logger.error` clarifies that all encodings failed.  `logger.exception` is used instead of `logger.error` in the outer try-except block to log the full traceback.

* **Fallback Mechanism with Warning:** The `_get_fallback_products` function is now called when *any* error occurs during the loading process, *including* failure to decode with *any* of the tested encodings.  A warning is logged to indicate that fallback products are being used, making it clear to the user that the main data source failed.

* **Clearer Error Messages:** The error messages are more descriptive, indicating the type of error encountered (e.g., "Failed to decode JSON").

* **Handles all encoding errors:**  Iterates through a list of possible encodings. If one fails, it tries the next. Only if all fail does it give up.

* **Handles File Not Found Error:** Explicitly checks for the file existence and returns the fallback products.

* **Improved Data Handling within `_load_local_products`:** If your original product data has some missing fields, your loading routine will now complete.

* **`logger.exception` for comprehensive error logging:** Using `logger.exception` provides a full traceback, making debugging much easier. This is especially useful in production environments.

This improved version provides significantly better error handling, making the `LocalProductService` more robust and easier to debug in case of data loading issues. The combination of specific exception handling, informative logging, and a reliable fallback mechanism ensures that the service can continue to function even when unexpected problems occur.

---
*Generated by Smart AI Bot*
