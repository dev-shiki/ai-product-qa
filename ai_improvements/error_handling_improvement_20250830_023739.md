# Error Handling Improvement

**File**: `./app/api/queries.py`  
**Time**: 02:37:39  
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

        # Deteksi harga maksimum
        price_match = re.search(r"maksimal\s*(\d+)", question_lower)
        if price_match:
            try:
                max_price = int(price_match.group(1))
            except ValueError:
                logger.warning(f"Could not parse max price from query: {request.question}")
                max_price = None  # Handle cases where the parsed value isn't a valid integer

        # Get products based on extracted category and price
        products = product_service.get_products(category=category, max_price=max_price)

        # Determine fallback message
        note = "Berikut adalah rekomendasi produk yang relevan."
        if not products:
            note = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."

        return QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=note
        )

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly, as they are already handled.
        raise http_exc
    except Exception as e:
        logger.exception(f"An unexpected error occurred while processing the request: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal saat memproses permintaan Anda.")
```

Key improvements in error handling:

* **Specific Exception Handling:**  The code now explicitly catches `HTTPException`.  This is crucial. If the `ai_service` or `product_service` raises an `HTTPException` (which they should do when encountering API errors, database issues, etc.), we re-raise it.  This allows FastAPI's built-in exception handlers to correctly return the appropriate HTTP error code and message to the client.  This is the most important change.
* **Generic Exception Handling:** The `except Exception as e:` block catches *any* other exception that might occur.  This is a safety net to prevent the API from crashing and returning a 500 Internal Server Error to the client.
* **Logging:**  Inside the generic exception handler, `logger.exception()` is used.  This logs the *full* traceback of the exception, which is invaluable for debugging.  It's much better than `logger.error()` because it includes the context of the error.  Crucially, we log *before* raising the `HTTPException`.
* **Clear Error Message:** The generic exception handler now raises an `HTTPException` with a status code of 500 and a user-friendly message in Indonesian: "Terjadi kesalahan internal saat memproses permintaan Anda."  This is much better than a generic or technical error message.
* **Max Price Parsing Error Handling:** A `try-except` block is included within the `if price_match` block to handle potential `ValueError` exceptions that may occur if the matched price value cannot be converted to an integer.  This prevents the code from crashing if the user provides invalid input. A warning message is logged if the price cannot be parsed.

This improved error handling makes the API more robust, provides better debugging information, and returns more informative error messages to the client. It follows best practices for exception handling in FastAPI.

---
*Generated by Smart AI Bot*
