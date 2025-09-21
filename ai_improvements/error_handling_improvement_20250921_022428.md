# Error Handling Improvement

**File**: `./app/services/local_product_service.py`  
**Time**: 02:24:28  
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
                                "discount": product.get('discount', 0.0),
                                "image_url": product.get('image_url', '')
                            }
                            transformed_products.append(transformed_product)
                            
                        logger.info(f"Successfully loaded products from {json_file_path} using encoding {encoding}")  # Log success
                        return transformed_products
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode JSON with encoding {encoding}: {e}")  # Log decoding failures with specific reason
                except Exception as e:
                    logger.error(f"Error reading or processing file with encoding {encoding}: {e}", exc_info=True)  # Log general errors with traceback

            logger.error(f"Failed to load products from {json_file_path} using any of the attempted encodings.  Falling back to default products.")
            return self._get_fallback_products()  # Fallback if all encodings fail
        
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading products: {e}") # Catch all exceptions including file not found
            return self._get_fallback_products()

    def _get_fallback_products(self) -> List[Dict]:
        """Return daftar produk fallback jika gagal memuat dari file JSON."""
        logger.warning("Returning fallback products.")
        return [
            {"id": "fb_1", "name": "Fallback Product 1", "category": "Fallback", "brand": "Generic", "price": 10.0, "discount": 0.0, "image_url": ""},
            {"id": "fb_2", "name": "Fallback Product 2", "category": "Fallback", "brand": "Generic", "price": 20.0, "discount": 5.0, "image_url": ""}
        ]

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Mendapatkan produk berdasarkan ID."""
        for product in self.products:
            if product['id'] == product_id:
                return product
        return None

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Mendapatkan daftar produk berdasarkan kategori."""
        return [product for product in self.products if product['category'] == category]

    def get_random_products(self, count: int) -> List[Dict]:
        """Mendapatkan daftar produk acak."""
        return random.sample(self.products, min(count, len(self.products)))
```

Key improvements in error handling:

* **Specific Exception Handling:** The code now catches `json.JSONDecodeError` specifically to handle JSON decoding issues and logs a warning with the specific error message.  This provides more informative logging compared to a generic `except Exception` block.
* **Encoding-Specific Error Logging:** When a `JSONDecodeError` occurs during a specific encoding attempt, the log message includes the encoding that failed. This helps diagnose encoding problems.
* **General Error Logging with Traceback:** The code now includes `exc_info=True` in the general `except Exception` block within the encoding loop. This includes the full traceback in the log, which is invaluable for debugging unexpected errors during file reading or processing.
* **Clear Fallback Logging:**  The `_get_fallback_products` function now logs a warning message to indicate that fallback products are being used. This makes it clear when the primary data source has failed.
* **Comprehensive Exception Handling:** Added a general `try...except` block outside the encoding loop to catch any unexpected exceptions that may occur when loading or processing product data. This ensures that the program does not crash and gracefully falls back to using the default products. `logger.exception` is used here to capture and log the full exception information (including traceback).
* **Success Logging:** Added a logger.info message to log when the product is loaded successfully.
* **Improved Error Message:**  The error message now specifies whether there was a failure to load products using any of the encodings, and directs the developer towards the fallback products being returned.
* **File Not Found Handling:**  The code now explicitly checks if the `products.json` file exists before attempting to open it.  If the file is not found, it logs an error message and returns the fallback products.
* **Return Fallback on All Exceptions:** The core change is ensuring the fallback method is always returned if *any* exception is encountered during the loading process. This makes the service truly reliable.

These changes make the `_load_local_products` method significantly more robust and easier to debug. The logs will provide much more detailed information about any failures, helping to quickly identify and resolve problems with the data file or its encoding.

---
*Generated by Smart AI Bot*
