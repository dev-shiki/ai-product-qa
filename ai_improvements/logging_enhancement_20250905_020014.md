# Logging Enhancement

**File**: `./app/services/local_product_service.py`  
**Time**: 02:00:14  
**Type**: logging_enhancement

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
        logger.info("Loading local products from JSON file...")  # Added logging
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
                    logger.debug(f"Attempting to read file with encoding: {encoding}") # Added logging
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
                                "image_url": product.get('image_url', ''),
                                "additional_images": product.get('additional_images', []),
                            }
                            transformed_products.append(transformed_product)
                        logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file using encoding: {encoding}") # Added logging
                        return transformed_products
                except UnicodeDecodeError as e:
                    logger.warning(f"UnicodeDecodeError with encoding {encoding}: {e}") # Added logging
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"JSONDecodeError: {e}.  Returning fallback products.") # Added logging
                    return self._get_fallback_products()
            
            logger.error("Failed to load products with all encodings. Returning fallback products.") # Added logging
            return self._get_fallback_products()
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading products: {e}") # Added logging
            return self._get_fallback_products()
    
    def _get_fallback_products(self) -> List[Dict]:
        """Return hardcoded fallback products"""
        # Fallback data jika file JSON tidak dapat dimuat
        logger.warning("Using fallback products as the primary data source failed to load.")
        fallback_products = [
            {
                "id": "1",
                "name": "Laptop Acer Aspire",
                "category": "Electronics",
                "brand": "Acer",
                "price": 7000000.0,
                "description": "Laptop untuk kebutuhan sehari-hari.",
                "image_url": "https://example.com/acer_aspire.jpg",
                "additional_images": []
            },
            {
                "id": "2",
                "name": "Kemeja Pria Katun",
                "category": "Fashion",
                "brand": "Generic",
                "price": 150000.0,
                "description": "Kemeja kasual untuk pria.",
                "image_url": "https://example.com/kemeja_pria.jpg",
                "additional_images": []
            }
        ]
        return fallback_products

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Mendapatkan produk berdasarkan ID."""
        for product in self.products:
            if product['id'] == product_id:
                return product
        return None

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Mendapatkan daftar produk berdasarkan kategori."""
        return [product for product in self.products if product['category'] == category]

    def search_products(self, query: str) -> List[Dict]:
        """Mencari produk berdasarkan query."""
        query = query.lower()
        return [
            product for product in self.products
            if query in product['name'].lower() or query in product['description'].lower()
        ]

    def get_random_products(self, num_products: int = 5) -> List[Dict]:
        """Mendapatkan daftar produk secara acak."""
        if num_products > len(self.products):
            return self.products
        return random.sample(self.products, num_products)
```

Key improvements and explanations:

* **`logger.info("Loading local products from JSON file...")`**: Added at the very beginning of the function to indicate the start of the loading process.
* **`logger.debug(f"Attempting to read file with encoding: {encoding}")`**:  Uses `logger.debug` as it is only useful information if debugging a file encoding issue.  Shows which encoding is being tried.
* **`logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file using encoding: {encoding}")`**: Added after successfully loading and transforming products, including the encoding used.  This confirms success and which encoding worked.
* **`logger.warning(f"UnicodeDecodeError with encoding {encoding}: {e}")`**:  Reports Unicode decode errors, which are the main reason why multiple encodings are tried.  Uses `logger.warning` because it's an expected (but undesirable) error.
* **`logger.error(f"JSONDecodeError: {e}.  Returning fallback products.")`**:  Crucially catches JSON decoding errors. This is important because a file might be read without Unicode errors but still contain invalid JSON. The error message `e` provides details about why the JSON parsing failed, which can be helpful for debugging the JSON file.
* **`logger.error("Failed to load products with all encodings. Returning fallback products.")`**:  Reports that all encodings failed.
* **`logger.exception(f"An unexpected error occurred while loading products: {e}")`**:  This is the most important addition. The `logger.exception()` method is used inside the `except Exception as e:` block.  This logs the *entire* exception, including the traceback, which is essential for debugging unexpected errors (e.g., file permission issues, unexpected data types).  Using `logger.exception` is much better than `logger.error(str(e))` because it includes the stack trace.
* **`logger.warning("Using fallback products as the primary data source failed to load.")`**:  Added to the `_get_fallback_products` to indicate when fallback data is being used.
* **Clearer Messages**: More descriptive log messages that explain *what* is happening.  The messages now explicitly state when the code is attempting to read the file, when it succeeds, and when it falls back to the default products.  This makes the logs much easier to understand.
* **Correct Logging Level**: Used `logger.info` for normal operation, `logger.warning` for recoverable errors (like encoding issues), and `logger.error` and `logger.exception` for unrecoverable errors.  `logger.debug` is used for information that is only valuable during debugging.
* **Included the Exception Message**: The log messages include the exception message itself (e.g., the specific `UnicodeDecodeError` or `JSONDecodeError`). This helps pinpoint the exact cause of the failure.
* **No redundant logging**: Avoids logging the same information multiple times.
* **Error Handling**: Properly handles potential `UnicodeDecodeError` and `JSONDecodeError` exceptions when reading and parsing the JSON file.

This revised solution provides much more informative and helpful logging, making it easier to debug any issues that may arise when loading the local product data.  It is also efficient, only logging when necessary.

---
*Generated by Smart AI Bot*
