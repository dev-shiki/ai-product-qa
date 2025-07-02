# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 05:35:17  
**Type**: logging_enhancement

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
    logger.info(f"Received question: {request.question}") # Log the incoming question
    try:
        # Get AI response
        logger.info("Calling AI service to get response.")
        ai_response = await ai_service.get_response(request.question)
        logger.info(f"AI service responded: {ai_response}")
        
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
        price_match = re.search(r"maksimal\s*([\d\.]+)|kurang dari\s*([\d\.]+)", question_lower)
        if price_match:
            max_price = float(price_match.group(1) or price_match.group(2))

        products = product_service.get_products(category=category, max_price=max_price)
        
        note = ""
        if not products:
            note = "Tidak ada produk yang sesuai dengan kriteria Anda."
            logger.warning("No products found matching the criteria.") # Log when no product matches
            products = product_service.get_products()[:5] # provide fallback products instead.
            note += " Menampilkan beberapa produk rekomendasi sebagai alternatif."

        logger.info(f"Found {len(products)} products.") # Log how many product were found

        # Create response
        response = QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=note
        )
        logger.info(f"Returning response: {response}") # Log the entire response before returning

        return response
    except Exception as e:
        logger.exception(f"An error occurred: {e}") # Log any exceptions
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:** The logging covers the entire function lifecycle:
    * **Input Logging:**  Logs the incoming question immediately.
    * **Service Call Logging:** Logs calls to external services (AI service).  Crucially, it logs the response *from* the AI service. This is essential for debugging AI-related issues.
    * **Product Search Logging:** Logs when no products are found, including a warning level message.
    * **Product Count Logging:** Logs the number of products found.  Useful for performance monitoring and verifying data retrieval.
    * **Response Logging:** Logs the complete `QueryResponse` object *before* returning it. This is the final state of the data before it leaves the function.
    * **Exception Logging:**  Logs any exceptions that occur with `logger.exception`.  This is the *most* important improvement.  Using `logger.exception` automatically includes the traceback, which is vital for debugging.  It also re-raises the `HTTPException` to ensure the API returns an error to the client.
* **Log Levels:** Uses appropriate log levels:
    * `info` for normal operation.
    * `warning` for non-critical issues (e.g., no products found).
    * `exception` for errors.
* **f-strings:** Uses f-strings for concise and readable log messages.
* **Clear Message Content:**  Provides informative messages in the logs, making it easier to understand what the function is doing and what's going wrong.
* **Error Handling:** Preserves the original error handling (raising `HTTPException`) but adds logging *before* raising the exception. This ensures errors are both logged and propagated to the client.
* **Correct exception usage:**  Using `logger.exception` logs the entire traceback.  This is essential for debugging.

This revised solution provides robust and informative logging that will be extremely helpful for debugging and monitoring the `ask_question` function.  It also adheres to best practices for logging and error handling in a production environment.  It also fixes the traceback problem - the previous version would have swallowed the traceback making debugging almost impossible.

---
*Generated by Smart AI Bot*
