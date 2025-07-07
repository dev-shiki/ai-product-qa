# Logging Enhancement

**File**: `./app/services/local_product_service.py`  
**Time**: 04:42:40  
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
        logger.info("Starting to load local products.")  # Added logging
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
                    logger.debug(f"Attempting to read products.json with encoding: {encoding}")  # Added logging
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
                                "description": product.get('description', '')
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file with encoding {encoding}")  # Added logging
                        return transformed_products
                except UnicodeDecodeError as e:
                    logger.warning(f"Failed to decode with encoding {encoding}: {e}")  # Added logging
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error with encoding {encoding}: {e}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading products: {e}")  # Added logging
            return self._get_fallback_products()
        
        logger.warning("Failed to load products using all encodings.  Using fallback products.")  # Added logging
        return self._get_fallback_products()
```

Key improvements and explanations:

* **`logger.info("Starting to load local products.")`:**  This is the first log entry in the function, indicating that the loading process has begun. This is crucial for tracing the execution flow.
* **`logger.debug(f"Attempting to read products.json with encoding: {encoding}")`:** Uses `logger.debug`.  Encoding is critical for understanding the success or failure of file reading.  Debug level is appropriate since this is implementation detail.
* **`logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file with encoding {encoding}")`:** Logs the successful loading of products, including the number of products loaded and the encoding that worked.  This confirms that the process was successful and provides context.
* **`logger.warning(f"Failed to decode with encoding {encoding}: {e}")`:** Logs warnings with the specific error messages when a `UnicodeDecodeError` occurs.  This helps to pinpoint encoding issues.
* **`logger.error(f"JSON decode error with encoding {encoding}: {e}")`:** Logs the error message when a JSON decoding error happens. This helps determine if the file is corrupted or not well formatted.
* **`logger.exception(f"An unexpected error occurred while loading products: {e}")`:** Critically, uses `logger.exception`.  This logs the exception *and* the traceback.  This is absolutely vital for debugging unexpected errors. This ensures that you have the full context of the error, including the call stack.
* **`logger.warning("Failed to load products using all encodings.  Using fallback products.")`:** Logs a warning when all encoding attempts fail, indicating that the fallback products will be used.  This provides context when fallback data is being used, highlighting a potential problem with the primary data source.

This revised solution provides comprehensive logging with appropriate levels (info, debug, warning, error, exception) to track the execution flow, identify potential issues, and diagnose errors effectively.  The use of `logger.exception` is the most important improvement, as it captures the full traceback for unexpected errors.  The use of debug level logging gives useful information that is not critical to see in normal operation.

---
*Generated by Smart AI Bot*
