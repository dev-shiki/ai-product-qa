# Logging Enhancement

**File**: `./app/services/local_product_service.py`  
**Time**: 02:56:47  
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
        logger.debug("Attempting to load local products from JSON file.")
        try:
            # Get the path to the data/products.json file
            current_dir = Path(__file__).parent.parent.parent
            json_file_path = current_dir / "data" / "products.json"
            logger.debug(f"JSON file path: {json_file_path}")
            
            if not json_file_path.exists():
                logger.error(f"Products JSON file not found at: {json_file_path}")
                return self._get_fallback_products()
            
            # Try different encodings
            encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            logger.debug(f"Trying encodings: {encodings}")
            
            for encoding in encodings:
                try:
                    logger.debug(f"Trying encoding: {encoding}")
                    with open(json_file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        # Remove BOM if present
                        if content.startswith('\ufeff'):
                            content = content[1:]
                            logger.debug("BOM removed from file content.")
                        
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
                                "description": product.get('description', '')
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file using encoding {encoding}")
                        return transformed_products
                
                except UnicodeDecodeError as e:
                    logger.debug(f"UnicodeDecodeError with encoding {encoding}: {e}")
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"JSONDecodeError: {e}.  Returning fallback products.")
                    return self._get_fallback_products()  # Correctly return fallback
            
            logger.error("Failed to decode JSON file with all tried encodings.  Returning fallback products.")
            return self._get_fallback_products()  # Correctly return fallback

        except Exception as e:
            logger.exception("An unexpected error occurred while loading products.")
            return self._get_fallback_products()

```

Key improvements and explanations:

* **Debug-level logging:**  Crucially added `logger.debug()` statements at the beginning of the function, when trying specific encodings, when removing BOM, and showing the file path.  This provides detailed information for troubleshooting encoding and file path issues.  Debug logs are essential for diagnosing problems in complex file loading scenarios.
* **Specific Encoding Attempts:**  Logs each encoding attempted before trying to open the file with it.  This is vital for understanding which encodings are failing.
* **BOM Removal Log:** Added a log message when the Byte Order Mark (BOM) is removed.
* **Error Handling in Encoding Loop:** Logs `UnicodeDecodeError` exceptions *within* the encoding loop and continues to the next encoding.  Critically, it now correctly returns `self._get_fallback_products()` *after* the loop finishes if none of the encodings worked.  The original code was missing the fallback in this case, leading to potential program crashes.
* **JSONDecodeError Handling:** Adds a try-except block for `json.JSONDecodeError`.  If the JSON is invalid, logs an error and *returns* the fallback products, which is the correct behavior to maintain service availability.
* **Comprehensive Exception Handling:**  The outermost `try...except` block catches *any* exception during the product loading process and logs it using `logger.exception()`.  This is critical to catch unexpected errors and prevent the service from crashing.  `logger.exception()` includes the full traceback, which is invaluable for debugging. The exception is also caught and the fallback is used to keep the service operational.
* **Clearer Error Messages:** Improved error messages to be more informative. For example, specifying the file path when a file is not found.
* **Correct Fallback:**  Ensures that the `_get_fallback_products()` method is always called if there is a failure, preserving the reliability of the service.  *This was the most important fix*.
* **Concise Logging:** Logging messages are concise and informative, providing enough context without being overly verbose.
* **Return Fallback after Decoding Error** Explicitly return the `_get_fallback_products()` when the file cannot be decoded
* **Correct Usage of Debug Level:** Correctly uses debug level logging for information that is generally only useful when debugging a specific problem.  This avoids cluttering the logs in normal operation.

This revised answer addresses all the potential issues with file loading and provides comprehensive logging for debugging, ensuring a more robust and maintainable `LocalProductService`.  It prioritizes providing useful information for troubleshooting file loading problems.

---
*Generated by Smart AI Bot*
