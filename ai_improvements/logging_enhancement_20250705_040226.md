# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 04:02:26  
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
        logger.info(f"AI Service returned response: {ai_response}") # Log the AI's response
        
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
        
        # Deteksi harga maksimum
        price_match = re.search(r"(maksimal|kurang dari|di bawah) (\d+(?:\.\d+)?(?:ribu|juta)?)", question_lower)
        if price_match:
            max_price_str = price_match.group(2)
            max_price_str = max_price_str.replace("ribu", "000").replace("juta", "000000")
            max_price = float(max_price_str)
        
        products = product_service.get_products(category=category, max_price=max_price)
        
        if products:
            note = "Here are some products that might be helpful:"
        else:
            products = product_service.get_products() # Fallback to all products
            note = "I couldn't find products matching your specific criteria, but here are some popular products:"

        logger.info(f"Found {len(products)} products.")  # Log the number of products found

        response_data = {
            "answer": ai_response,
            "products": products,
            "question": request.question,
            "note": note
        }

        logger.info(f"Returning response: {response_data}")  # Log the complete response

        return response_data

    except Exception as e:
        logger.exception(f"An error occurred: {e}")  # Log the exception with traceback
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:**  The code now includes logging statements at critical points:
    * **`logger.info(f"Received question: {request.question}")`**: Logs the incoming question from the request.  This is crucial for understanding what the API is being asked.
    * **`logger.info(f"AI Service returned response: {ai_response}")`**: Logs the raw response from the AI service. This is important to debug any issues with the AI itself.
    * **`logger.info(f"Found {len(products)} products.")`**: Logs the number of products returned by the `product_service`.  This helps verify that the product filtering logic is working as expected.
    * **`logger.info(f"Returning response: {response_data}")`**:  Logs the complete response before it's sent back to the client. This allows you to see exactly what data is being returned.
    * **`logger.exception(f"An error occurred: {e}")`**:  Logs any exceptions that occur within the `try...except` block.  Crucially, `logger.exception()` includes the full traceback, making debugging much easier. This is the most important logging statement, as it will help you identify and fix errors.  It's important to use `logger.exception()` here, rather than `logger.error(str(e))`, to get the traceback.

* **Clear Log Messages:**  The log messages are formatted to be easily readable and informative.  They include the variable names and values, so you can quickly understand the context.

* **Error Handling with Logging:**  The `try...except` block is essential for robust error handling.  The `logger.exception()` statement ensures that any errors are logged with their full traceback, making debugging much easier.  The `HTTPException` is raised to return a proper error response to the client.

* **Placement of Logging:** Logging is strategically placed at the beginning and end of key operations, as well as within the exception handler.  This gives you a good overview of what's happening in the function.

* **Uses `f-strings`:**  Uses f-strings for more concise and readable log messages.

This revised answer provides a much more complete and useful implementation of logging within the `ask_question` function.  It covers the key steps of the function, logs important data, and includes comprehensive error handling with traceback logging. Remember to configure the logging level in your application to see these log messages (e.g., set it to `logging.INFO` or `logging.DEBUG`).

---
*Generated by Smart AI Bot*
