# Logging Enhancement

**File**: `./app/services/local_product_service.py`  
**Time**: 03:51:20  
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
            logger.debug(f"JSON file path: {json_file_path}")  # Added logging
            
            if not json_file_path.exists():
                logger.error(f"Products JSON file not found at: {json_file_path}")
                return self._get_fallback_products()
            
            # Try different encodings
            encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            logger.debug(f"Trying encodings: {encodings}") #Added logging
            
            for encoding in encodings:
                try:
                    logger.debug(f"Trying encoding: {encoding}")  # Added logging
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
                                "description": product.get('description', ''),
                                "price": product.get('price', 0.0),
                                "image_url": product.get('image_url', '')
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded {len(transformed_products)} products using encoding: {encoding}")  # Added logging
                        return transformed_products
                except UnicodeDecodeError as e:
                    logger.warning(f"Failed to decode with {encoding}: {e}")  # Added logging
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON with {encoding}: {e}") #Added logging
            
            logger.error("Failed to load products with all encodings.")  # Added logging
            return self._get_fallback_products()
        except Exception as e:
            logger.exception("An unexpected error occurred while loading products.")  # Added logging
            return self._get_fallback_products()
```

Key improvements and explanations:

* **Entry and Exit Logging:** Added `logger.info("Loading local products from JSON file...")` at the beginning to signal the function's start and `logger.info(f"Successfully loaded {len(transformed_products)} products using encoding: {encoding}")` when successful loading occurs.  This is crucial for tracing execution flow.
* **Detailed Encoding Debugging:** Added `logger.debug(f"Trying encoding: {encoding}")` inside the encoding loop to see which encoding is being attempted at each step.  This helps diagnose encoding issues.
* **JSON Parsing Error Logging:** Added `logger.error(f"Failed to parse JSON with {encoding}: {e}")` inside the encoding loop to handle JSON parsing errors if the file is not valid JSON.  This is extremely important because a common cause of failure is an invalid JSON file.
* **Exception Handling:** Added a general `except Exception as e:` block at the outermost level with `logger.exception("An unexpected error occurred while loading products.")`.  This catches any unexpected errors during the whole process and logs a *full traceback*, which is vital for debugging.  `logger.exception` is the correct way to log the error message *and* the traceback.
* **Fallback Logging:** Maintained the logging of fallback product usage.
* **Clearer Error Messages:** Improved error messages to be more informative, including the path to the JSON file and the specific encoding that failed.
* **Debug Level Logging:**  Used `logger.debug` for information that is helpful for debugging but not necessary for normal operation.  This keeps the logs cleaner in production.
* **Encoding List Logging:** Logged the list of encodings being tried at the beginning of the loop for debugging purposes.
* **File Path Logging:** Included logging of the `json_file_path` to verify that the correct file is being accessed.

This comprehensively covers potential error scenarios, provides detailed debugging information, and ensures that you can effectively troubleshoot any issues encountered while loading product data.  The combination of `info`, `debug`, `warning`, `error`, and `exception` logging levels gives you the right amount of detail depending on the log level configured.  This is now a production-ready function with robust logging.  Remember to configure your logging levels (e.g., to `logging.INFO` or `logging.DEBUG`) appropriately for your environment.

---
*Generated by Smart AI Bot*
