# Error Handling Improvement

**File**: `./app/services/local_product_service.py`  
**Time**: 02:35:30  
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
                                "stock": product.get('stock', 0),
                                "description": product.get('description', '')
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded products from {json_file_path} using encoding: {encoding}")
                        return transformed_products
                    
                except UnicodeDecodeError as e:
                    logger.debug(f"Attempted encoding {encoding} failed: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON from {json_file_path} using encoding {encoding}: {e}")
                    # It's crucial to re-raise the exception or return a fallback
                    # Otherwise, the program might proceed with incorrect data.
                    return self._get_fallback_products() # Or raise the exception
            
            # If all encodings fail
            logger.error(f"Failed to load products after trying multiple encodings for {json_file_path}")
            return self._get_fallback_products()
        
        except Exception as e:  # Catch any other unexpected errors
            logger.exception(f"An unexpected error occurred while loading products: {e}")
            return self._get_fallback_products()

    def _get_fallback_products(self) -> List[Dict]:
        """Return produk fallback jika file JSON tidak dapat dimuat"""
        # This is a placeholder - replace with your actual fallback mechanism
        logger.warning("Using fallback products!")
        return [
            {"id": "1", "name": "Fallback Product 1", "category": "Fallback", "brand": "Fallback", "price": 10.0, "stock": 5, "description": "A default product"},
            {"id": "2", "name": "Fallback Product 2", "category": "Fallback", "brand": "Fallback", "price": 20.0, "stock": 10, "description": "Another default product"},
        ]

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Mengembalikan produk berdasarkan ID"""
        for product in self.products:
            if product['id'] == product_id:
                return product
        return None

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Mengembalikan semua produk dalam kategori tertentu"""
        return [product for product in self.products if product['category'] == category]

    def search_products(self, query: str) -> List[Dict]:
        """Mencari produk berdasarkan query"""
        query = query.lower()
        return [
            product for product in self.products
            if query in product['name'].lower() or query in product['description'].lower() or query in product['category'].lower() or query in product['brand'].lower()
        ]

    def get_random_products(self, num_products: int) -> List[Dict]:
        """Mengembalikan sejumlah produk acak"""
        if num_products > len(self.products):
            logger.warning(f"Requested {num_products} random products, but only {len(self.products)} available. Returning all products.")
            return self.products
        return random.sample(self.products, num_products)

```

Key improvements in error handling:

* **More Specific Exception Handling:** Instead of catching just `Exception`, the code now catches `UnicodeDecodeError` and `json.JSONDecodeError` specifically.  This allows for different handling based on the type of error.
* **JSON Decode Error Handling:**  Critically, the code now handles `json.JSONDecodeError`.  If JSON decoding fails, it logs an error and returns the fallback products.  **Crucially, the original code was missing a return or raise after logging the JSONDecodeError. This is now fixed, preventing the code from continuing with potentially incomplete or corrupted data.**
* **Complete Error Handling:** A broad `except Exception as e` is added to the outer `try` block to catch any unforeseen issues during the entire loading process. This prevents the program from crashing due to unexpected errors and provides a way to gracefully fall back to default products.  A `logger.exception` is used to capture the full stack trace, which is essential for debugging.
* **Logging of Success:** Added a `logger.info` message when products are successfully loaded, including the encoding used. This provides positive feedback and helps confirm which encoding is working.
* **`debug` logging for encoding failures**: Uses `logger.debug` for logging `UnicodeDecodeError` errors. Encoding errors are usually not critical. Debug level is appropiate.
* **Robust Fallback:**  Ensures a fallback mechanism (returning `self._get_fallback_products()`) is consistently used when loading fails.  This prevents the service from being unusable.
* **Fallback Product Details:** Included `price`, `stock`, and `description` in the fallback products to more closely resemble the expected product structure.
* **No bare excepts**: Never use `except:` without specifying the exception. This can hide critical errors.
* **Clear Error Messages:**  The error messages include the specific file path and the encoding being attempted when failures occur, making debugging much easier.
* **Comprehensive Logging:** Logging is used extensively to track the loading process, including successes, failures, and fallback usage.  This provides valuable information for troubleshooting.
* **Data Validation & Transformation:** Explicitly retrieves values from the product dictionary using `.get(key, default_value)` to provide default values if a key is missing. This prevents `KeyError` exceptions and makes the code more resilient to variations in the product data structure.

These changes make the product loading process significantly more robust and provide better insight into potential issues. The logging and fallback mechanisms ensure that the service remains functional even when the local JSON file is unavailable or corrupted.

---
*Generated by Smart AI Bot*
