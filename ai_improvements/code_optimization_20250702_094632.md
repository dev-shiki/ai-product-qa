# Code Optimization

**File**: `./app/services/local_product_service.py`  
**Time**: 09:46:32  
**Type**: code_optimization

## Improvement

**Improvement:**

Instead of trying multiple encodings sequentially, make a best guess (likely `utf-8`) first and only try others on failure.

**Explanation:**

The code iterates through multiple encodings (`utf-16-le`, `utf-16`, `utf-8`, `utf-8-sig`, `latin-1`, `cp1252`) when reading the JSON file.  This can be slow.  In most cases, JSON files are encoded in `utf-8`.  Therefore, we can optimize by trying `utf-8` first and only falling back to other encodings if `utf-8` fails. This reduces the number of iterations in the common case.  This assumes that most files will be `utf-8`.

**Revised Code Snippet:**

```python
    def _load_local_products(self) -> List[Dict]:
        """Load produk dari file JSON lokal"""
        try:
            # Get the path to the data/products.json file
            current_dir = Path(__file__).parent.parent.parent
            json_file_path = current_dir / "data" / "products.json"
            
            if not json_file_path.exists():
                logger.error(f"Products JSON file not found at: {json_file_path}")
                return self._get_fallback_products()
            
            # Try UTF-8 first, then other encodings on failure
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
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
                            "description": product.get('description', ''),
                            "image_url": product.get('image_url', ''),
                        }
                        transformed_products.append(transformed_product)
                    
                    logger.debug(f"Successfully loaded and transformed {len(transformed_products)} products from {json_file_path}")
                    return transformed_products

            except UnicodeDecodeError:
                logger.warning("UTF-8 decoding failed, trying other encodings.")
                # Try other encodings only if UTF-8 fails
                encodings = ['utf-16-le', 'utf-16', 'utf-8-sig', 'latin-1', 'cp1252']

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
                                    "description": product.get('description', ''),
                                    "image_url": product.get('image_url', ''),
                                }
                                transformed_products.append(transformed_product)

                            logger.debug(f"Successfully loaded and transformed {len(transformed_products)} products from {json_file_path} with encoding {encoding}")
                            return transformed_products
                    except Exception as e:
                        logger.error(f"Error loading products with encoding {encoding}: {e}")

                logger.error(f"Failed to load products after trying multiple encodings.")
                return self._get_fallback_products()

        except FileNotFoundError:
            logger.error(f"Products JSON file not found at: {json_file_path}")
            return self._get_fallback_products()

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return self._get_fallback_products()

        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            return self._get_fallback_products()
```

---
*Generated by Smart AI Bot*
