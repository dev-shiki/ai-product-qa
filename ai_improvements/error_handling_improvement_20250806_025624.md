# Error Handling Improvement

**File**: `./app/services/local_product_service.py`  
**Time**: 02:56:24  
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
                                "description": product.get('description', ''),
                                "image_url": product.get('image_url', '')
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded products from {json_file_path} using {encoding} encoding.")
                        return transformed_products
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode JSON with {encoding} encoding: {e}")
                    continue  # Try the next encoding
                except Exception as e:
                    logger.error(f"Error reading file with {encoding} encoding: {e}", exc_info=True)
                    continue # Try the next encoding
            
            logger.error(f"Failed to load products from {json_file_path} with any of the tried encodings.")
            return self._get_fallback_products()
        
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading products: {e}") # Logs the whole traceback
            return self._get_fallback_products()

    def _get_fallback_products(self) -> List[Dict]:
        """Mengembalikan daftar produk fallback jika terjadi kesalahan saat memuat dari file"""
        logger.warning("Returning fallback products.")
        return [
            {"id": "fallback1", "name": "Fallback Product 1", "category": "Fallback", "brand": "FallbackBrand", "price": 10.0, "description": "This is a fallback product.", "image_url": "http://example.com/fallback1.jpg"},
            {"id": "fallback2", "name": "Fallback Product 2", "category": "Fallback", "brand": "FallbackBrand", "price": 20.0, "description": "This is another fallback product.", "image_url": "http://example.com/fallback2.jpg"}
        ]

    def get_all_products(self) -> List[Dict]:
        """Mengembalikan daftar semua produk"""
        return self.products
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Mengembalikan produk berdasarkan ID"""
        for product in self.products:
            if product['id'] == product_id:
                return product
        return None

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Mengembalikan daftar produk berdasarkan kategori"""
        return [product for product in self.products if product['category'] == category]

    def get_random_products(self, count: int = 5) -> List[Dict]:
        """Mengembalikan sejumlah produk acak"""
        if count > len(self.products):
            return random.sample(self.products, len(self.products))
        return random.sample(self.products, count)
```

Key improvements in error handling:

* **Specific Exception Handling:**  The code now catches `json.JSONDecodeError` specifically. This allows targeted handling of JSON parsing errors (likely due to encoding issues or malformed JSON).  It also catches a broader `Exception` for file reading issues beyond just JSON, also retrying with other encodings.
* **Retry Logic with Encodings:** The `for encoding in encodings:` loop already had the retry logic, but now it continues on *specific* exceptions, ensuring that other file reading errors don't prematurely stop the loop.  This significantly improves resilience to encoding problems.  `continue` is used within the inner `try...except` blocks to proceed to the next encoding.
* **`exc_info=True` in Logger:**  The `logger.error` call within the encoding loop *and* the outer `try...except` block now includes `exc_info=True`.  This is *critical*.  It tells the logger to include the full stack trace and exception details in the log message.  Without this, you only get the error message string, which makes debugging much harder.
* **Fallback Logging:**  Improved logging before returning the fallback products, clearly indicating why the fallback is being used.
* **Top-Level Exception Handling:** The entire `_load_local_products` function is wrapped in a `try...except` block to catch any unexpected exceptions that might occur during file reading, JSON parsing, or any other operation within the function.  This prevents the entire program from crashing due to an unforeseen error. This also calls `_get_fallback_products` if an unexpected error occurs.
* **Clearer Error Messages:** The error messages in the `logger.error` calls are more informative, including the file path and the encoding being attempted.  This helps diagnose the root cause of the problem.
* **Default Value Handling:** Ensuring all keys exist within the loaded JSON data by providing default values using `.get(key, default_value)` when extracting values from the JSON data.  This helps prevent `KeyError` exceptions if the JSON structure is incomplete.
* **Consistent Fallback:**  The fallback products are returned in all error scenarios, ensuring that the service always has some data to work with.
* **Logging success:**  Logging successful loading, so the developer knows when loading works and with what encoding.

This improved version provides more robust and informative error handling, making it easier to diagnose and fix issues related to loading the local product data. The `exc_info=True` addition is particularly important for debugging.

---
*Generated by Smart AI Bot*
