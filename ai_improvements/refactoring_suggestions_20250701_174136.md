# Refactoring Suggestions

**File**: `./app/services/local_product_service.py`  
**Time**: 17:41:36  
**Type**: refactoring_suggestions

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
        json_file_path = self._get_json_file_path()

        if not json_file_path.exists():
            logger.error(f"Products JSON file not found at: {json_file_path}")
            return self._get_fallback_products()
        
        try:
            products = self._read_products_from_json(json_file_path)
            return products
        except Exception as e:
            logger.error(f"Error loading products from JSON: {e}")
            return self._get_fallback_products()

    def _get_json_file_path(self) -> Path:
        """Get the path to the data/products.json file."""
        current_dir = Path(__file__).parent.parent.parent
        return current_dir / "data" / "products.json"


    def _read_products_from_json(self, json_file_path: Path) -> List[Dict]:
        """Reads and parses the JSON file, handling different encodings and potential BOM."""
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
                            "description": product.get('description', ''),
                            "price": product.get('price', 0.0),
                            "image_url": product.get('image_url', ''),
                            "additional_images": product.get('additional_images', []),
                            "variants": product.get('variants', []),
                            "specifications": product.get('specifications', {}),
                            "rating": product.get('rating', 0.0),
                            "num_reviews": product.get('num_reviews', 0),
                            "availability": product.get('availability', True),
                            "free_shipping": product.get('free_shipping', False),
                            "options": product.get('options', [])
                        }
                        transformed_products.append(transformed_product)
                    
                    return transformed_products
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON with encoding {encoding}. Trying next encoding.")
            except Exception as e:
                logger.error(f"Error reading file with encoding {encoding}: {e}")

        raise Exception("Failed to read products from JSON with all attempted encodings.")


    def _get_fallback_products(self) -> List[Dict]:
        """Return fallback/default products"""
        logger.warning("Returning fallback products")
        return [
            {"id": "default-1", "name": "Default Product 1", "category": "Default"},
            {"id": "default-2", "name": "Default Product 2", "category": "Default"}
        ]
```

**Refactoring Improvement:**

The main refactoring is **Extraction of the `_read_products_from_json` function** and `_get_json_file_path` function. This significantly improves the readability and maintainability of the `_load_local_products` function.  By extracting the complex JSON reading and parsing logic, including the encoding handling and BOM removal, into a separate function, `_load_local_products` becomes much easier to understand at a glance.  It now focuses solely on orchestrating the process: getting the file path, reading the products, and handling potential errors. The new function has a clear single responsibility: reading products from the JSON file.  The path retrieval has also been extracted for better readability.

**Explanation:**

1.  **`_read_products_from_json(self, json_file_path: Path) -> List[Dict]`:** This new function encapsulates the logic for reading the JSON file, handling different encodings, removing the BOM, parsing the JSON, and transforming the data. It takes the file path as an argument, making it more testable and reusable.  Error handling is improved by logging warnings for JSON decoding errors with specific encodings before moving on to the next. A final exception is raised if all encodings fail.
2.  **`_get_json_file_path(self) -> Path`:** This function encapsulates the logic for getting the file path. This reduces the cognitive load in `_load_local_products`.
3.  **`_load_local_products(self) -> List[Dict]`:** The original function is now simplified to orchestrate the file path retrieval, the process of reading and parsing the JSON with the new function and handles general exceptions.  It calls the helper function and handles fallback if needed.
4.  **Exception Handling:**  The `_load_local_products` function now includes a `try...except` block to catch any exceptions that occur during the JSON loading process. If any exception is caught, it logs an error message and returns the fallback products.  This makes the service more robust by preventing it from crashing if there are any issues with the JSON file.

This refactoring adheres to the Single Responsibility Principle, making the code cleaner, more readable, easier to test, and more maintainable.

---
*Generated by Smart AI Bot*
