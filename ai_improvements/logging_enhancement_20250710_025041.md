# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 02:50:41  
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
    logger.info(f"Received question: {request.question}")  # Log the incoming question
    try:
        # Get AI response
        logger.info(f"Calling AI service with question: {request.question}")
        ai_response = await ai_service.get_response(request.question)
        logger.info(f"Received AI response: {ai_response}")
        
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
        
        # Deteksi harga maksimum (sederhana)
        match = re.search(r"(?:kurang dari|di bawah) (Rp\s?)?([\d,\.]+)", question_lower)
        if match:
            max_price_str = match.group(2).replace('.', '').replace(',', '.')
            try:
                max_price = float(max_price_str)
            except ValueError:
                logger.warning(f"Could not parse max_price from: {match.group(2)}")
                max_price = None
        
        logger.info(f"Extracted category: {category}, max_price: {max_price}")

        products = product_service.get_products(category=category, max_price=max_price)
        
        if not products:
            note = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
            logger.warning("No products found matching the criteria.")
        else:
            note = "Berikut adalah beberapa produk yang mungkin Anda sukai."
            logger.info(f"Found {len(products)} products matching the criteria.")
            
        # Create response
        response = QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=note
        )
        logger.info(f"Returning response: {response}")
        return response
    except Exception as e:
        logger.exception("An error occurred while processing the request.")  # Log the exception
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:**  I've added logging statements at the beginning, end, and key steps of the function:
    * `logger.info(f"Received question: {request.question}")`: Logs the incoming question right away.  This is crucial for debugging and understanding what the function is processing.
    * `logger.info(f"Calling AI service with question: {request.question}")`: Logs before the call to the AI service, indicating that the service call is about to happen.
    * `logger.info(f"Received AI response: {ai_response}")`: Logs the AI response.  This is very important to check if the AI service returned the expected data.
    * `logger.info(f"Extracted category: {category}, max_price: {max_price}")`: Logs the extracted category and max price after they are parsed.  This confirms that the parsing logic is working as expected.
    * `logger.info(f"Found {len(products)} products matching the criteria.")`: Logs the number of matching products found, which is useful for tracking the effectiveness of the product filtering.
    * `logger.warning("No products found matching the criteria.")`: Logs a warning if no products are found, indicating a possible issue with the query or the product database.
    * `logger.info(f"Returning response: {response}")`: Logs the final response object before returning it. This is essential for verifying the structure and content of the response.
    * `logger.exception("An error occurred while processing the request.")`:  This logs the *entire* exception, including the traceback.  This is the *most important* logging statement when handling exceptions.  Using `logger.exception` is far better than `logger.error(str(e))` because it includes the stack trace.
* **Error Handling and Logging:** The `try...except` block now includes `logger.exception`.  Critically, it logs the full exception traceback. This makes debugging significantly easier because you can see exactly where the error occurred. The `detail` in `HTTPException` also includes the error message for the API consumer.
* **Informative Messages:** The logging messages are designed to be clear and informative. They include the relevant data being processed, such as the question, AI response, extracted parameters, and number of products found.
* **Log Levels:**  I've used `logger.info` for general information and `logger.warning` for situations where something might be wrong but isn't necessarily an error (e.g., no products found).  `logger.exception` is used for actual errors.  Choosing the correct log level is important for filtering and analyzing logs.
* **F-strings:** Using f-strings (e.g., `f"Received question: {request.question}"`) makes the logging statements much more readable and efficient.
* **Conciseness:** The logging is added without significantly cluttering the code.

This revised response provides much more effective and useful logging for debugging and monitoring the `ask_question` function.  It follows best practices for logging exceptions and provides context at each step of the function's execution.  This will allow you to easily diagnose issues and understand the behavior of the function in production.

---
*Generated by Smart AI Bot*
