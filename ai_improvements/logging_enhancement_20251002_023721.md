# Logging Enhancement

**File**: `./app/services/local_product_service.py`  
**Time**: 02:37:21  
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
            logger.debug(f"JSON file path: {json_file_path}") # added logging

            if not json_file_path.exists():
                logger.error(f"Products JSON file not found at: {json_file_path}")
                return self._get_fallback_products()
            
            # Try different encodings
            encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    logger.debug(f"Attempting to read file with encoding: {encoding}") # added logging
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
                            
                        logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file with encoding: {encoding}") # added logging
                        return transformed_products
                except UnicodeDecodeError as e:
                    logger.debug(f"Failed to decode with encoding {encoding}: {e}") # added logging
                    continue  # Try the next encoding
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON with encoding {encoding}: {e}")
                    return self._get_fallback_products()
                except Exception as e:
                    logger.exception(f"An unexpected error occurred while loading products: {e}")
                    return self._get_fallback_products()
            
            logger.error("Failed to load products with all tried encodings. Using fallback products.") # added logging
            return self._get_fallback_products()  # If all encodings fail
        except Exception as e:
            logger.exception(f"An unexpected error occurred during product loading: {e}")  # Added logging
            return self._get_fallback_products()

```

Key improvements and explanations:

* **Explicitly Log Entry and Exit:**  The most important addition is logging at the *beginning* of the function (`logger.info("Loading local products from JSON file...")`) and before returning. This provides clear evidence of when the function was called and whether it completed successfully or not.
* **Debug Logging for Key Variables:** Added `logger.debug(f"JSON file path: {json_file_path}")` to verify the file path being used.  Debug logging is essential for troubleshooting.
* **Encoding Loop Logging:** Added `logger.debug(f"Attempting to read file with encoding: {encoding}")` and `logger.debug(f"Failed to decode with encoding {encoding}: {e}")` within the encoding loop to track which encodings are being tried and why they might be failing.  This is crucial for debugging encoding issues.
* **Success Logging:** Added `logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file with encoding: {encoding}")` when products are successfully loaded.  This confirms success and shows the number of loaded products.
* **Error Handling Logging:**  Includes `logger.error` for file not found and JSON decode errors, *and* logs the specific exception (`e`) using f-strings.  This makes debugging much easier.  Critically, I also log a message if the fallback is used, providing clear evidence the fallback was activated.
* **Exception Logging:** Uses `logger.exception` in the `except` blocks.  This is *critical* because `logger.exception` logs the *full* stack trace, providing a detailed view of where the error originated, which is essential for debugging complex issues.
* **Fallback Logging:** Added a log message before returning the fallback products in all failure scenarios, making it explicit when the fallback mechanism is being used.
* **Clarity and Consistency:**  Used consistent f-string formatting for log messages and kept the log messages concise but informative.
* **Use of Appropriate Log Levels:**  Employed `logger.info`, `logger.debug`, `logger.error`, and `logger.exception` appropriately to distinguish between informational messages, debugging messages, errors, and exceptions.

This revised response addresses all the previous issues and provides a much more robust and informative logging implementation.  The changes will significantly aid in debugging and understanding the behavior of the `_load_local_products` function.  Remember to configure the logging level appropriately (e.g., `logging.basicConfig(level=logging.DEBUG)`) to see the debug messages.

---
*Generated by Smart AI Bot*
