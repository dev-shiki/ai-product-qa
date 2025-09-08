# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 02:22:27  
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
        
        # Deteksi harga maksimum (contoh sederhana, perlu ditingkatkan)
        match = re.search(r"(maksimal|kurang dari|di bawah) (\d+(?:\.\d+)?)", question_lower)
        if match:
            try:
                max_price = float(match.group(2))
            except ValueError:
                logger.warning(f"Could not parse max price from question: {request.question}")
                max_price = None
        
        logger.info(f"Extracted category: {category}, max_price: {max_price} from question")

        products = product_service.get_products(category=category, max_price=max_price)
        logger.info(f"Found {len(products)} products based on the extracted information")

        fallback_message = "Maaf, saya tidak menemukan produk yang sesuai dengan kriteria Anda." if not products else ""
        
        # Format the response
        response_data = {
            "answer": ai_response,
            "products": products,
            "question": request.question,
            "note": fallback_message
        }
        logger.info(f"Returning response: {response_data}")
        return QueryResponse(**response_data)
    except Exception as e:
        logger.exception(f"An error occurred while processing the question: {e}") # log the full exception including traceback
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:**  Crucially, the code now logs at several key points:
    * **Incoming Question:** Logs the `request.question` at the beginning of the function using `logger.info`.  This provides a record of what the user asked.
    * **AI Service Call:** Logs a message *before* calling the `ai_service`, indicating the question being sent to the AI.  Logs the AI response *after* receiving it. This helps isolate issues with the AI service itself.
    * **Extracted Information:** Logs the `category` and `max_price` extracted from the question. This is crucial for debugging product filtering.
    * **Product Retrieval:** Logs the number of products found after calling `product_service.get_products`.  This helps determine if the filtering is working correctly.
    * **Response Logging:** Logs the entire `response_data` before returning it.  This is the final state of the data being sent back to the user.
    * **Exception Handling:**  Includes a `try...except` block that catches *any* exception during processing. It logs the *full exception* using `logger.exception()`.  `logger.exception()` is vital because it includes the traceback, which is invaluable for debugging.  It then re-raises the exception as an `HTTPException` to provide an error response to the client.  This is the *most* important addition for debugging production issues.
* **Log Levels:**  `logger.info` is used for general informational messages. `logger.warning` is used when there's a problem that doesn't necessarily break the code (e.g., failing to parse the max price). `logger.exception` is used for unhandled exceptions.  Using the correct log level makes filtering logs much easier.
* **String Formatting:**  Uses f-strings (e.g., `f"Received question: {request.question}"`) for more readable and efficient string formatting.
* **Error Handling:** Wraps the core logic in a `try...except` block to catch potential exceptions and log them appropriately.  Critically, it *re-raises* the exception as an `HTTPException` to signal an error to the client.  This prevents the API from silently failing.
* **Clear and Specific Messages:**  The log messages are written to be clear and informative, explaining what's happening at each step.

This revised solution addresses all the previous points and provides a robust logging and error handling strategy for the `ask_question` function.  It's now much easier to diagnose issues in this function. Remember to configure your logging (e.g., to a file or a logging service) to actually see these messages.

---
*Generated by Smart AI Bot*
