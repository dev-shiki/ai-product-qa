# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 02:37:29  
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
    try:
        logger.info(f"Received question: {request.question}")
        # Get AI response
        logger.info("Calling AI service to get response.")
        ai_response = await ai_service.get_response(request.question)
        logger.info(f"AI service returned: {ai_response}")
        
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

        max_price_match = re.search(r'(maksimal|kurang dari|di bawah) (Rp\s?)?([\d,\.]+)', question_lower)
        if max_price_match:
            price_str = max_price_match.group(3).replace('.', '').replace(',', '.')
            try:
                max_price = float(price_str)
            except ValueError:
                logger.warning(f"Could not parse max_price from {question_lower}")
                max_price = None

        logger.info(f"Extracted category: {category}, max_price: {max_price}")

        products = product_service.get_products(category=category, max_price=max_price)
        if not products:
            note = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda saat ini."
            logger.info("No products found matching criteria.")
        else:
            note = ""
            logger.info(f"Found {len(products)} products matching criteria.")
        
        # Return response
        response = QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=note
        )
        logger.info(f"Returning response: {response}")
        return response

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:**  Logs the input question, the call to the AI service, the AI service's response, extracted category and max_price, the number of products found, and the final response.  Critically, also logs exceptions.
* **f-strings:** Uses f-strings for clear and concise log messages, including variable values directly in the log messages.  This makes debugging much easier.
* **Exception Logging:**  Crucially, the `except` block now uses `logger.exception(f"An error occurred: {e}")`.  This is *essential*. `logger.exception()` logs the exception message *and* the full stack trace, which is invaluable for debugging.  Without the stack trace, you often only have a symptom of the problem, not the cause.
* **Informative Messages:** Log messages are designed to be informative and tell a story of what's happening within the function.  For example, logging "Calling AI service..." and then logging the result is a good pattern.
* **Handles `ValueError` for `max_price`:** Includes a `try-except` block to handle the case where the extracted price string cannot be converted to a float, preventing the function from crashing and logging a warning instead. This is robust handling of potential user input errors.
* **Logs when no products are found:** Adds a specific log message when no products are found to help diagnose issues with product filtering.

This revised answer provides much more robust and helpful logging, making it significantly easier to debug and maintain the code.  It addresses all the common logging pitfalls.  This is production-quality logging.

---
*Generated by Smart AI Bot*
