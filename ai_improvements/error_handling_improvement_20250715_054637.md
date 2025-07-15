# Error Handling Improvement

**File**: `./app/api/queries.py`  
**Time**: 05:46:37  
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
                break  # Stop after finding the first matching category

        # Deteksi harga maksimum (contoh sederhana)
        price_match = re.search(r"maksimal ([\d\.]+)", question_lower)
        if price_match:
            try:
                max_price = float(price_match.group(1).replace('.', '')) #Remove thousand separator if any
            except ValueError:
                logger.warning(f"Invalid price format in question: {request.question}")
                max_price = None  # Or handle the error as appropriate
        
        products = product_service.get_products(category=category, max_price=max_price)

        if not products:
            note = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
        else:
            note = "Berikut adalah beberapa produk yang mungkin Anda sukai."

        return QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=note
        )
    except ValueError as ve:
        logger.error(f"Value Error during request processing: {ve}", exc_info=True) # Include exc_info for traceback
        raise HTTPException(status_code=400, detail=f"Invalid input: {ve}")
    except HTTPException as he:
        #Re-raise the HTTPException. It might have come from the ai_service.
        raise he
    except Exception as e:
        logger.exception(f"Unexpected error during request processing: {e}") # Use logger.exception for traceback
        raise HTTPException(status_code=500, detail="Internal server error")
```

Key improvements and explanations:

* **Comprehensive Exception Handling:** The `try...except` block now covers the entire logic within the `ask_question` function, including the AI service call, product service call, and the category/price extraction.  This ensures that any error during the process is caught.
* **Specific Exception Types:**  Instead of catching just `Exception`, we now catch specific exception types:
    * `ValueError`:  Handles errors related to invalid input data, particularly during price parsing.  A warning is also logged if the price format is invalid, to aid in debugging.
    * `HTTPException`: This is important. The original code did not handle HTTPExceptions that might arise from the `ai_service.get_response` function. Now, if an HTTPException occurs, it is re-raised so FastAPI can handle it correctly (e.g., return a 400 or 500 error to the client).
    * `Exception`: Catches all other unexpected exceptions. This is the catch-all, and it's crucial to include it.
* **Logging with Tracebacks:**  The `logger.error` and `logger.exception` calls now include `exc_info=True`.  This is *critical* for debugging.  It ensures that the full traceback of the exception is logged, making it much easier to pinpoint the source of the error.  `logger.exception` is used for the general `Exception` case because it is designed to automatically log exception information.
* **User-Friendly Error Messages:** The `HTTPException` now includes a `detail` message that provides more information about the error to the client. This is better than a generic "Internal server error". If a `ValueError` occurs, the detail will indicate the problem.
* **HTTP Status Codes:** Appropriate HTTP status codes are returned based on the type of error:
    * `400 Bad Request`:  Used for `ValueError`, indicating that the client sent invalid input.
    * `500 Internal Server Error`: Used for unexpected exceptions, indicating a problem on the server-side.
* **Price Parsing Error Handling**:  Added a `try-except` block specifically within the price parsing logic. This allows to catch `ValueError` exceptions when the extracted price cannot be converted to a float (e.g., due to invalid characters).  If a `ValueError` occurs during price parsing, a warning is logged, and `max_price` is set to `None` so the code can continue execution gracefully.
* **No Suppression of AI Service Errors:** The AI service is assumed to raise HTTPExceptions if something goes wrong. This is now handled correctly.

This revised error handling strategy will make your application more robust, easier to debug, and more informative for clients when errors occur. Remember to configure your logging appropriately to capture the logged messages in a useful way (e.g., to a file or console).

---
*Generated by Smart AI Bot*
