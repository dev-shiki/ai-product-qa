# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 03:04:21  
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
        logger.info(f"Received question: {request.question}") # Log the received question
        # Get AI response
        ai_response = await ai_service.get_response(request.question)
        logger.debug(f"AI Service Response: {ai_response}") # Log the AI service response (debug level)
        
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
        
        # Deteksi harga maksimum (contoh sederhana)
        match = re.search(r"(maksimal|kurang dari|di bawah) (\d+)", request.question)
        if match:
            try:
                max_price = int(match.group(2))
            except ValueError:
                logger.warning(f"Could not parse max_price from question: {request.question}") #Log if price could not be parsed
                max_price = None
        
        products = product_service.get_products(category=category, max_price=max_price)
        logger.debug(f"Product Service returned {len(products)} products.") # Log number of products returned

        if not products:
            note = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
        else:
            note = "Berikut adalah beberapa produk yang mungkin Anda sukai."
        
        response_data = {
            "answer": ai_response,
            "products": products,
            "question": request.question,
            "note": note
        }
        logger.info(f"Returning response with {len(products)} products.") # Log returning response, including the number of products
        return QueryResponse(**response_data)

    except Exception as e:
        logger.exception(f"An error occurred: {e}") # Log any exceptions that occur
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:**  The code now includes `logger.info`, `logger.debug`, `logger.warning`, and `logger.exception` calls at strategic points:
    * **`logger.info(f"Received question: {request.question}")`**: Logs the user's question as soon as it's received.  This is crucial for understanding what triggered the function.  It's an INFO level log, meaning you'll see it in standard logging configurations.
    * **`logger.debug(f"AI Service Response: {ai_response}")`**: Logs the raw response from the AI service.  `logger.debug` is used because this is very detailed information that you usually only need when actively debugging.  This helps you understand what the AI is saying and how it's influencing the product search.
    * **`logger.warning(f"Could not parse max_price from question: {request.question}")`**: Logs a warning if the code fails to extract a price from the user's question.  This indicates a problem with the price parsing logic.
    * **`logger.debug(f"Product Service returned {len(products)} products.")`**: Logs the number of products returned by the product service. This helps in understanding if the product service is returning expected results based on the AI or manual filtering. Debug level as this is not always crucial for high level monitoring.
    * **`logger.info(f"Returning response with {len(products)} products.")`**:  Logs just before returning the response, including the number of products being returned.  This gives you a final confirmation of the function's outcome.
    * **`logger.exception(f"An error occurred: {e}")`**: Logs any exceptions that occur within the `try...except` block.  Crucially, `logger.exception` automatically includes the full stack trace, making it much easier to diagnose errors.  This is essential for catching unexpected problems.

* **Clear Error Handling:** The `except` block now logs the full exception using `logger.exception`. This includes the stack trace, making debugging much easier.  It then re-raises an `HTTPException` to properly handle the error in the FastAPI application.

* **Correct Log Levels:** Uses appropriate log levels (INFO, DEBUG, WARNING, EXCEPTION) to ensure that the logs are useful without being overwhelming.  INFO for significant events, DEBUG for detailed information, WARNING for potential problems, and EXCEPTION for errors.

* **f-strings:** Uses f-strings for more readable and efficient log messages.

* **No Unnecessary Logging:**  Avoids logging things that are already obvious or that don't provide useful information for debugging or monitoring.

This revised answer provides a well-logged function that is helpful for debugging, monitoring, and understanding the behavior of your FastAPI application.  Remember to configure your logging level appropriately in your application's configuration (e.g., set the level to `logging.INFO` for production or `logging.DEBUG` for development).

---
*Generated by Smart AI Bot*
