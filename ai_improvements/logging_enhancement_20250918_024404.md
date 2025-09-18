# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 02:44:04  
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
        logger.info(f"Received question: {request.question}")  # Log the incoming question
        # Get AI response
        ai_response = await ai_service.get_response(request.question)
        logger.debug(f"AI Response: {ai_response}")  # Log the AI response for debugging
        
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
        
        # Coba ekstrak harga maksimum dari pertanyaan
        match = re.search(r"(harga kurang dari|harga dibawah|maksimal) ([\d\.]+)", question_lower)
        if match:
            try:
                max_price = float(match.group(2))
                logger.debug(f"Extracted max_price: {max_price}") # Log the extracted price
            except ValueError:
                logger.warning("Could not parse max_price from question.") # Log if parsing fails
                max_price = None
                
        products = product_service.get_products(category=category, max_price=max_price)
        logger.debug(f"Products found: {products}") # Log the products found
        
        fallback_message = "Berikut adalah beberapa produk yang mungkin Anda sukai:"
        
        # Buat respons
        response = QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=fallback_message
        )
        logger.info("Question processed successfully.") # Log success
        return response

    except Exception as e:
        logger.exception(f"Error processing question: {e}") # Log any exceptions
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:** The code now logs the following:
    * The incoming question (`request.question`) at the `INFO` level. This is crucial for understanding what users are asking.
    * The AI response (`ai_response`) at the `DEBUG` level.  `DEBUG` is appropriate for information that is useful during development but not necessarily in production.
    * The extracted `max_price` at the `DEBUG` level.  This is logged *after* it's successfully parsed.
    * A warning if parsing the `max_price` fails. This is very important for debugging and identifying issues with price extraction.
    * The list of `products` found at the `DEBUG` level.  This helps verify that the filtering is working correctly.
    * A success message "Question processed successfully." at the `INFO` level when the function completes successfully.
    * Any exceptions that occur during processing, using `logger.exception`.  This is *critical* because it automatically includes the traceback, making debugging much easier. The exception message is also included in the `HTTPException` raised to the client.

* **Correct Log Levels:**  Using the correct log levels (`INFO`, `DEBUG`, `WARNING`, `EXCEPTION`) is essential for filtering and managing logs effectively.  `DEBUG` is for detailed information, `INFO` is for normal operation, `WARNING` is for potential problems, and `EXCEPTION` is for errors.

* **Clear Log Messages:** The log messages are now more descriptive, clearly indicating what is being logged (e.g., "Received question:", "AI Response:").

* **Exception Handling:** The `try...except` block catches any exceptions that might occur during the processing and logs them *with* the traceback.  This is the most important addition for debugging. It also re-raises an `HTTPException` to ensure the client receives an error response.

* **Efficiency:** No unnecessary logging is added.  Only the most important parts of the function are logged.

* **No Functional Changes:** The logging code does not alter the original functionality of the function.

This revised solution provides a robust and informative logging system for the `ask_question` function, making it much easier to debug and monitor in production.  Remember to configure your logging levels appropriately in your application's logging configuration.  For example, you might set the default level to `INFO` in production and `DEBUG` during development.

---
*Generated by Smart AI Bot*
