# Error Handling Improvement

**File**: `./app/api/queries.py`  
**Time**: 03:38:53  
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
        ai_response = await ai_service.get_response(request.question)
        
    except Exception as e:
        logger.exception(f"Error getting AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI response.  Please try again later.") from e # Include original exception for debugging

    try:
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

        # Deteksi harga dengan regex (lebih baik)
        price_match = re.search(r"(harga|kurang dari|di bawah) (\d+(?:\.\d+)?)", question_lower)
        if price_match:
            try:
                max_price = float(price_match.group(2))
            except ValueError:
                logger.warning(f"Invalid price format in question: {request.question}")
                max_price = None  # or a default value
                
        products = product_service.get_products(category=category, max_price=max_price)
        
        # Determine fallback note based on search results
        if not products:
            note = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
        else:
            note = "Berikut adalah produk yang mungkin Anda sukai:"

        return QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=note
        )

    except Exception as e:
        logger.exception(f"Error processing product data: {e}")
        raise HTTPException(status_code=500, detail="Error processing product data. Please try again later.") from e
```

Key improvements:

* **Try-Except around `ai_service.get_response`:**  The most important change is wrapping the call to `ai_service.get_response` in a `try...except` block.  This isolates the potentially failing external service call.
* **Logging the Exception:**  Inside the `except` block, `logger.exception(f"Error getting AI response: {e}")` is used. `logger.exception` logs the error message *and* the traceback, which is crucial for debugging.
* **Raising an `HTTPException`:** If an exception occurs during the AI service call, an `HTTPException` is raised with a status code of 500 (Internal Server Error) and a user-friendly message. This tells the client that something went wrong on the server side.  The `from e` syntax preserves the original exception's context, which is extremely helpful for debugging.
* **Separate Try-Except for Product Data:** A separate `try...except` block is now around the product data processing (category detection, price extraction, product retrieval). This allows handling errors specifically related to product data logic, distinct from AI service errors.  Crucially, it also includes logging and raising an `HTTPException` with `from e`.
* **ValueError Handling for Price Parsing:** Added a `try...except` block when converting the extracted price string to a float.  This handles cases where the user provides an invalid price format (e.g., "seratus ribu").  It logs a warning and sets `max_price` to `None` so the query can proceed without the price filter, rather than crashing.
* **More Specific Error Messages:**  The `detail` messages in the `HTTPException` now provide more context about what went wrong ("Failed to get AI response" vs. "Error processing product data").
* **`from e` for Exception Chaining:** The `from e` clause in the `raise HTTPException` statements is critical. It chains the original exception (`e`) to the new `HTTPException`. This preserves the complete traceback and makes debugging significantly easier.  Without `from e`, you lose the original exception's context.

This revised code handles errors gracefully, logs important information for debugging, and provides informative error messages to the client.  It's much more robust and maintainable.  Separating the try-except blocks also allows for more granular error handling and reporting.

---
*Generated by Smart AI Bot*
