# Error Handling Improvement

**File**: `./app/api/queries.py`  
**Time**: 03:29:57  
**Type**: error_handling_improvement

## Improvement

```python
import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.product_data_service import ProductDataService
from app.services.ai_service import AIService
import re

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()
product_service = ProductDataService()
ai_service = AIService()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    products: List[dict]
    question: str
    note: str

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Ask a question about products and get recommendations"""
    try:
        # Get AI response
        try:
            ai_response = await ai_service.get_response(request.question)
        except Exception as e:
            logger.exception("Error getting response from AI service")
            raise HTTPException(status_code=500, detail="Failed to get response from AI service.") from e
        
        # Get relevant products and fallback message
        # Ekstrak kategori dan max_price dari pertanyaan (sederhana)
        category = None
        max_price = None
        
        # Deteksi kategori dengan lebih lengkap
        question_lower = request.question.lower()
        category_mapping = {
            'laptop': ['laptop', 'notebook', 'komputer'],
            'smartphone': ['smartphone', 'hp', 'handphone', 'phone', 'telepon', 'ponsel'],
            'tablet': ['tablet', 'ipad'],
            'headphone': ['headphone', 'earphone', 'headset', 'audio'],
            'kamera': ['kamera', 'camera', 'fotografi'],
            'audio': ['audio', 'speaker', 'sound'],
            'tv': ['tv', 'televisi'],
            'drone': ['drone', 'quadcopter'],
            'jam': ['jam', 'watch', 'smartwatch']
        }

        for cat, keywords in category_mapping.items():
            if any(keyword in question_lower for keyword in keywords):
                category = cat
                break

        # Mencari harga maksimum
        price_match = re.search(r"(?:harga|budget) (kurang dari|dibawah|maksimal) ?([0-9.,]+)", question_lower)
        if price_match:
            max_price_str = price_match.group(2).replace('.', '')  # Remove thousands separator
            max_price_str = max_price_str.replace(',', '.') # replace comma with decimal
            try:
                max_price = float(max_price_str)
            except ValueError:
                logger.warning(f"Could not parse max price from: {price_match.group(2)}")
                max_price = None #Or set a default, depending on your use case

        # Get products based on extracted info
        products = []
        note = "Here are some recommended products based on your query."
        try:
            products = product_service.get_products(category=category, max_price=max_price)
            if not products:
                note = "No products found matching your criteria.  Please broaden your search."
                logger.info(f"No products found for category: {category}, max_price: {max_price}")
        except Exception as e:
            logger.exception("Error getting products from product service")
            note = "There was an error retrieving product recommendations.  Please try again later."
            # Instead of re-raising, we're handling the error gracefully
            # and returning a message to the user. products remains an empty list.
            products = []

        # Create response
        response = QueryResponse(
            answer=ai_response.response, # Use the response attribute
            products=products,
            question=request.question,
            note=note
        )
        return response

    except HTTPException as http_ex:
        # Re-raise HTTPExceptions to be handled by FastAPI's exception handlers
        raise http_ex
    except Exception as e:
        logger.exception("An unexpected error occurred")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from e
```

Key improvements in error handling:

* **Specific `try...except` block around `ai_service.get_response()`:** This isolates the potentially failing AI service call.  Critically, it logs the full exception (using `logger.exception()`, which includes the traceback) and raises an `HTTPException` with a 500 status code and a user-friendly error message.  The `from e` preserves the original exception's context for better debugging.
* **Specific `try...except` block around `product_service.get_products()`:** Similar to the AI service call, this isolates the database call.  If there's an error fetching products, it logs the exception, sets a user-friendly note explaining the problem, and returns an empty list of products. This prevents the API from crashing entirely. The `products = []`  ensures the response is still valid even when no products are found.
* **Handles `ValueError` in price parsing:** The code now includes a `try...except` block when converting the max price string to a float. If the string is not a valid number, it logs a warning and sets `max_price` to `None`, preventing a crash.
* **`HTTPException` re-raising:** The outer `except` block now specifically catches `HTTPException`. This is important because if the inner `try` blocks raise an `HTTPException` (meaning an error the code already anticipated), it should be re-raised to be handled by FastAPI's built-in exception handling. This ensures that appropriate error responses are sent to the client.
* **Generic `Exception` handling with `HTTPException`:** The outer `except` block catches all other exceptions (using `Exception`) and logs the exception and raises a generic 500 error to the client. This prevents the API from crashing and provides a consistent error response. The `from e` preserves the original exception's context for debugging.
* **Detailed Logging:**  `logger.exception()` is used in all `except` blocks. This logs the full traceback of the error, which is crucial for debugging.  Also added an info log when no products are found matching the search criteria.
* **User-Friendly Error Messages:**  The `HTTPException`s now include user-friendly error messages in the `detail` field. This provides the client with more information about what went wrong.
* **Clearer `note` message when no products are found:** The message is now more helpful for the user.

These changes make the code more robust, easier to debug, and provide a better user experience by returning informative error messages when something goes wrong.  They also follow best practices for exception handling in FastAPI applications.

---
*Generated by Smart AI Bot*
