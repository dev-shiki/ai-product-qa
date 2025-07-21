# Logging Enhancement

**File**: `./app/services/local_product_service.py`  
**Time**: 03:24:23  
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
                    logger.debug(f"Attempting to load products using encoding: {encoding}")  # Added logging
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
                                "image_url": product.get('image_url', ''),
                                "description": product.get('description', '')
                            }
                            transformed_products.append(transformed_product)
                            
                        logger.info(f"Successfully loaded {len(transformed_products)} products using encoding: {encoding}")  # Added logging
                        return transformed_products
                except Exception as e:
                    logger.warning(f"Failed to load products using encoding {encoding}: {e}")  # Added logging
            
            logger.error("Failed to load products using all tried encodings.  Falling back to default products.") #Added logging
            return self._get_fallback_products()
            
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading products: {e}") #Added logging
            return self._get_fallback_products()

```

Key improvements and explanations:

* **`logger.debug(f"Attempting to load products using encoding: {encoding}")`**:  This logs *before* each attempt to open the file with a different encoding.  This is crucial for debugging encoding issues. The `debug` level is used because it's a less common event, and we only need it when we're actively troubleshooting.
* **`logger.info(f"Successfully loaded {len(transformed_products)} products using encoding: {encoding}")`**:  Logs a success message when a particular encoding works.  Includes the encoding used and the number of products loaded.  This confirms the operation was successful and provides context. `info` level is appropriate as it signals that the intended operation has been carried out correctly.
* **`logger.warning(f"Failed to load products using encoding {encoding}: {e}")`**:  Logs a warning message when an encoding fails.  It's a warning because the code *tries* other encodings.  The `e` includes the exception details, which are critical for understanding *why* the encoding failed.
* **`logger.error("Failed to load products using all tried encodings.  Falling back to default products.")`**: Logged when all encoding attempts fail, just before the fallback.  Important to know if the system is consistently falling back to defaults.
* **`logger.exception(f"An unexpected error occurred while loading products: {e}")`**:  This is the most important addition.  The original code had a broad `except Exception as e:` block.  `logger.exception` *automatically* logs the full stack trace along with the error message.  This makes debugging significantly easier because you can see exactly where in the code the error occurred.  The logging level is `exception`, which indicates that an unexpected and potentially critical error has occurred.
* **Clearer Fallback Messages:**  The logging now makes it very clear when the code is falling back to the default/fallback products, along with the reasons for the fallback.
* **Encoding Handling**: The code attempts to handle various encodings, which is a common issue with JSON files.  The logging makes it much easier to see which encodings are being tried and which are failing.

This revised version provides much more detailed and useful logging, which will greatly simplify debugging and maintenance of the `_load_local_products` function.  The appropriate log levels are used to distinguish between normal operation, warnings, and errors.

---
*Generated by Smart AI Bot*
