# Error Handling Improvement

**File**: `./app/models/product.py`  
**Time**: 04:02:39  
**Type**: error_handling_improvement

## Improvement

```python
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Optional, List

class ProductSpecifications(BaseModel):
    rating: Optional[float] = 0.0
    sold: Optional[int] = 0
    stock: Optional[int] = 0
    condition: Optional[str] = "Baru"
    shop_location: Optional[str] = "Indonesia"
    shop_name: Optional[str] = "Online Store"
    storage: Optional[str] = None
    color: Optional[str] = None
    warranty: Optional[str] = None

class Product(BaseModel):
    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    brand: str = Field(..., description="Product brand")
    price: int = Field(..., description="Product price in IDR")
    currency: str = Field(default="IDR", description="Currency code")
    description: str = Field(..., description="Product description")
    specifications: ProductSpecifications = Field(..., description="Product specifications")
    images: Optional[List[str]] = Field(default=[], description="Product images")
    url: Optional[str] = Field(default="", description="Product URL")

    @classmethod
    def create_product(cls, data: Dict) -> 'Product':
        """
        Creates a Product object from a dictionary, handling potential validation errors.
        """
        try:
            return cls(**data)
        except ValidationError as e:
            # Log the detailed validation errors.  Important for debugging.
            print(f"Validation Error: {e}")
            # Raise a custom exception with more context. This is better than just returning None.
            raise ValueError(f"Invalid product data: {e}") from e # Preserve original exception info
        except Exception as e:  # Catch any other unexpected errors
            print(f"Unexpected error during product creation: {e}")
            raise ValueError(f"Error creating product: {e}") from e


class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    price: int
    currency: str = "IDR"
    description: str
    specifications: Dict
    images: List[str] = []
    url: str = ""

class QueryResponse(BaseModel):
    answer: str
    products: List[dict]
    question: str
    note: Optional[str] = None
```

Key improvements:

* **`Product.create_product` class method:**  Encapsulates the creation logic for `Product` objects.  This centralizes error handling and makes the code more maintainable.
* **`try...except` block:**  Wraps the `Product(**data)` call to catch potential `ValidationError` exceptions.
* **`ValidationError` Handling:**  Crucially, it *logs* the `ValidationError` (`print(f"Validation Error: {e}")`).  This is **essential** for debugging why data might be failing validation.  The `ValidationError` contains detailed information about which fields are invalid and why.  Simply ignoring the validation error is a very bad practice.
* **Custom Exception:**  Instead of returning `None` or simply printing an error, a `ValueError` is raised. This is a more robust approach because it forces the calling code to handle the error explicitly. The custom error message provides more context (e.g., "Invalid product data") than a generic `ValueError`.
* **Exception Chaining ( `from e`)**: Preserves the original exception's traceback. This makes debugging much easier, as you can trace back to the root cause of the error. Without `from e`, you lose the context of the original validation error, making it harder to diagnose problems.
* **General Exception Handling:** Includes a catch-all `except Exception as e:` block to handle any other unexpected errors during product creation. This prevents the application from crashing due to unforeseen issues.  It *also* uses exception chaining.

Why this is better:

* **Explicit Error Handling:** The calling code is now *required* to handle the potential `ValueError`. This makes the code more reliable.
* **Informative Error Messages:** The error messages are more specific and include the details of the validation error. This helps developers quickly identify and fix problems.
* **Centralized Error Handling:** All error handling logic for `Product` creation is now in one place, making the code easier to maintain.
* **Debugging Aid:** Logging the `ValidationError` provides invaluable information for debugging.

How to use it:

```python
product_data = {
    "id": "123",
    "name": "Example Product",
    "category": "Electronics",
    "brand": "Generic",
    "price": 100000,
    "description": "A great product",
    "specifications": {"rating": 4.5},
    "images": ["image1.jpg", "image2.jpg"],
    "url": "http://example.com"
}

try:
    product = Product.create_product(product_data)
    print(f"Product created successfully: {product}")
except ValueError as e:
    print(f"Failed to create product: {e}")  # Handle the error appropriately
```

This improved error handling makes the code more robust, reliable, and easier to debug.  It's a much more production-ready approach.

---
*Generated by Smart AI Bot*
