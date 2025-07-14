# Error Handling Improvement

**File**: `./app/models/product.py`  
**Time**: 03:14:13  
**Type**: error_handling_improvement

## Improvement

```python
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Optional, List
import logging

# Configure logging (optional, but recommended for production)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    def create_product(cls, data: Dict) -> "Product":
        """
        Creates a Product instance from a dictionary, handling potential validation errors.
        """
        try:
            return cls(**data)
        except ValidationError as e:
            logging.error(f"Validation error creating Product: {e}")
            # Optionally, raise a custom exception or return a default/error Product instance.
            # For example:
            # raise ValueError(f"Invalid product data: {e}") from e
            # Or:
            return None  # Or a default/error Product instance
        except Exception as e:
            logging.exception(f"Unexpected error creating Product: {e}")
            return None


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

Key improvements and explanations:

* **`Product.create_product(cls, data: Dict) -> "Product"`:** This is the core of the error handling improvement.  Instead of directly instantiating the `Product` class, we now use a class method to handle the creation process.  This allows us to wrap the instantiation in a `try...except` block.

* **`try...except ValidationError`:**  This specifically catches `ValidationError` exceptions raised by Pydantic when the input data doesn't conform to the model's schema (e.g., missing required fields, incorrect data types).  This is the most common type of error you'll encounter when working with Pydantic models.

* **`logging.error(f"Validation error creating Product: {e}")`:**  Logs the validation error, including the specific details of the error provided by Pydantic.  This is crucial for debugging.  Using `logging` is generally preferred to `print` statements in production code.

* **`except Exception as e:`:**  This catches any *other* exceptions that might occur during the object creation process (e.g., unexpected data formats, issues with the underlying data source).  This provides a safety net for unforeseen errors.  The `logging.exception()` call is important here, as it will log the full stack trace, which is essential for diagnosing unexpected errors.

* **`return None` (or raise ValueError):**  Inside the `except` blocks, the code currently `return None`.  This is a simple way to signal that the product creation failed.  However, a better approach might be to:

    * **Raise a custom exception:** This allows calling code to explicitly handle the error case.  For example:  `raise ValueError(f"Invalid product data: {e}") from e`  This preserves the original exception as the cause.
    * **Return a default or "error" Product instance:** This could be a `Product` object with default values or an object representing an invalid product.  This approach depends on the specific requirements of your application.

* **Clear Error Message:** Provide clear error message that helps developers/user debug the issue.

* **Logging:** Added logging statements using the `logging` module, which provides more structured and configurable logging than simple `print` statements.

How to Use:

```python
product_data = {
    "id": "123",
    "name": "Example Product",
    "category": "Electronics",
    "brand": "Generic",
    "price": 100000,
    "description": "A sample product",
    "specifications": {"rating": 4.5}  # Missing required fields will cause an error
}

product = Product.create_product(product_data)

if product:
    print("Product created successfully:", product)
else:
    print("Failed to create product.")


invalid_product_data = {
    "id": 123,  # Incorrect data type for "id"
    "name": "Example Product",
    "category": "Electronics",
    "brand": "Generic",
    "price": 100000,
    "description": "A sample product",
    "specifications": {"rating": 4.5}
}

product = Product.create_product(invalid_product_data)

if product:
    print("Product created successfully:", product)
else:
    print("Failed to create product.")
```

This revised approach provides much more robust error handling and makes it easier to debug issues related to product creation. Remember to choose the error handling strategy (returning `None`, raising an exception, or returning a default object) that best suits your application's needs.  Also, be sure to configure the `logging` module to your desired level of verbosity and output location.

---
*Generated by Smart AI Bot*
