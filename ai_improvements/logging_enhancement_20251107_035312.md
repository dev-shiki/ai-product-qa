# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 03:53:12  
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
        logger.info(f"Received question: {request.question}") # Log the incoming question
        # Get AI response
        ai_response = await ai_service.get_response(request.question)
        logger.debug(f"AI Service Response: {ai_response}") # Log the AI response for debugging
        
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

        # Ekstraksi harga maksimum (contoh sederhana)
        match = re.search(r"maksimal\s*(\d+)", request.question, re.IGNORECASE)
        if match:
            try:
                max_price = int(match.group(1))
            except ValueError:
                logger.warning("Could not parse max price, using default.") # Handle potential errors
                max_price = None

        # Get products based on extracted information
        products = product_service.get_products(category=category, max_price=max_price)
        logger.debug(f"Products retrieved: {products}") # Log the retrieved products

        # Buat fallback message jika tidak ada produk yang ditemukan
        if not products:
            note = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
        else:
            note = ""

        # Return response
        response = QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=note
        )
        logger.info(f"Response sent: {response}") # Log the response being sent
        return response
    except Exception as e:
        logger.exception("An error occurred during the ask_question process.") # Log any exceptions
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:** Logs the incoming request, AI service response, retrieved products, the final response, and any exceptions that occur.  This covers all important stages of the function.
* **Log Levels:**  Uses different log levels (INFO, DEBUG, WARNING, EXCEPTION) appropriately.  `logger.info` is used for general information, `logger.debug` for more detailed debugging information (e.g., the AI response or the products fetched), and `logger.exception` for catching and logging exceptions, including the traceback. `logger.warning` is used when potential errors are encountered, but don't halt execution.
* **Clear Log Messages:** Log messages are formatted to be informative and easily understandable.  Includes the question, the response, the products retrieved, etc.
* **Exception Handling:**  The `except` block catches all exceptions, logs them using `logger.exception` (which includes a traceback), and then re-raises the exception as an `HTTPException` to provide a meaningful error response to the client.  This is crucial for debugging and handling unexpected situations.
* **String Formatting:** Uses f-strings for cleaner and more readable log messages.
* **`logger.debug` for detailed data:** The `logger.debug` statements provide detailed information about the AI response and the retrieved products, which is incredibly helpful for debugging.  Debug level logs are only shown when the logging level is set to debug, so they won't clutter the logs in a production environment.
* **Handles potential errors when parsing the max price:** Added a `try-except` block when attempting to convert the matched group to an integer.  This handles the case where the user enters a non-numeric value for the price, preventing a crash.  It also logs a warning message.

This revised answer provides a robust and well-integrated logging system for the `ask_question` function.  It provides excellent visibility into the function's execution and makes debugging significantly easier.  Remember to configure your logging level (e.g., DEBUG, INFO, WARNING, ERROR) appropriately in your application's logging configuration to control the amount of log output.

---
*Generated by Smart AI Bot*
