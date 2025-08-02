# Error Handling Improvement

**File**: `./app/services/local_product_service.py`  
**Time**: 03:03:39  
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
            
            products = [] # Initialize products to avoid UnboundLocalError
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
                                "image_url": product.get('image_url', '')
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded products using encoding: {encoding}")
                        return transformed_products # Return immediately after successful load
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode JSON with encoding {encoding}: {e}")
                except UnicodeDecodeError as e:
                    logger.warning(f"Failed to decode file with encoding {encoding}: {e}")
                except Exception as e:
                    logger.exception(f"An unexpected error occurred while loading with encoding {encoding}: {e}")

            # If all encodings fail
            logger.error("Failed to load products with all tried encodings.")
            return self._get_fallback_products()

        except Exception as e:
            logger.exception(f"An unexpected error occurred during product loading: {e}")
            return self._get_fallback_products()
    
    def _get_fallback_products(self) -> List[Dict]:
        """Mengembalikan daftar produk fallback jika terjadi kesalahan."""
        logger.warning("Returning fallback products.")
        return [
            {
                "id": "fallback-1",
                "name": "Fallback Product 1",
                "category": "Fallback",
                "brand": "FallbackBrand",
                "description": "This is a fallback product.",
                "price": 10.00,
                "image_url": "https://example.com/fallback1.jpg"
            },
            {
                "id": "fallback-2",
                "name": "Fallback Product 2",
                "category": "Fallback",
                "brand": "FallbackBrand",
                "description": "This is another fallback product.",
                "price": 20.00,
                "image_url": "https://example.com/fallback2.jpg"
            }
        ]

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Mendapatkan produk berdasarkan ID."""
        for product in self.products:
            if product.get('id') == product_id:
                return product
        logger.warning(f"Product with ID {product_id} not found.")
        return None

    def get_products_by_category(self, category: str) -> List[Dict]:
        """Mendapatkan daftar produk berdasarkan kategori."""
        return [product for product in self.products if product.get('category') == category]

    def search_products(self, query: str) -> List[Dict]:
        """Mencari produk berdasarkan query."""
        query = query.lower()
        return [
            product for product in self.products
            if query in product.get('name', '').lower() or query in product.get('description', '').lower()
        ]

    def get_random_products(self, count: int = 5) -> List[Dict]:
        """Mendapatkan daftar produk acak."""
        if count > len(self.products):
            logger.warning(f"Requested {count} random products, but only {len(self.products)} available. Returning all products.")
            return self.products
        return random.sample(self.products, count)

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Example Usage
    product_service = LocalProductService()

    # Get a product by ID
    product_id = "product-1"
    product = product_service.get_product_by_id(product_id)
    if product:
        logger.info(f"Product with ID {product_id}: {product.get('name')}")
    else:
        logger.info(f"Product with ID {product_id} not found.")

    # Get products by category
    category = "Electronics"
    products_in_category = product_service.get_products_by_category(category)
    logger.info(f"Products in category {category}: {len(products_in_category)}")

    # Search for products
    search_query = "Laptop"
    search_results = product_service.search_products(search_query)
    logger.info(f"Search results for '{search_query}': {len(search_results)}")

    # Get random products
    random_products = product_service.get_random_products(3)
    logger.info(f"Random products: {len(random_products)}")
```

Key improvements in this version:

* **Robust JSON Decoding with Error Handling:** The code now catches `json.JSONDecodeError` and `UnicodeDecodeError` *separately* within the encoding loop.  This provides more specific logging about *why* a particular encoding failed. It attempts to load the file with different encodings and logs a warning for each failed attempt.
* **Exception Logging:** A general `except Exception as e` block is added within the encoding loop to catch any other unforeseen errors during file loading or JSON parsing.  Critically, `logger.exception()` is used instead of `logger.error()`. `logger.exception()` *automatically* includes the traceback in the log, which is invaluable for debugging.  This makes the logging much more helpful.
* **Clearer Error Messages:**  The log messages now include the specific encoding that was being tried when the error occurred, helping pinpoint the problem.  The message when all encodings fail is also improved.
* **Explicitly handle the case where all encodings fail:** If none of the encodings work, the code now explicitly logs an error and returns the fallback products, instead of implicitly failing.
* **Early Return on Success:** When an encoding *successfully* loads the products, the function immediately returns the transformed products. This prevents unnecessary iterations through the remaining encodings.
* **Initialized `products` variable:** Initialize `products` list before the `for` loop in the function `_load_local_products` to avoid `UnboundLocalError`.
* **Fallback Products Message:** Improved logging message when fallback products are returned.

This improved version is significantly more robust to encoding issues, provides much better logging information for debugging, and ensures that fallback products are reliably returned when data loading fails.  The use of `logger.exception()` is crucial for effective error diagnosis.

---
*Generated by Smart AI Bot*
