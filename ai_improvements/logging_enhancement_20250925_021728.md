# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 02:17:28  
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
        logger.info("Calling AI service to get response...")
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
        
        price_match = re.search(r"(harga\s?(kurang dari|di bawah|maksimal)\s?([0-9.,]+))|(under\s?([0-9.,]+))", question_lower)
        if price_match:
            max_price_str = price_match.group(3) or price_match.group(5)
            max_price = float(max_price_str.replace('.', '').replace(',', '.'))
            
        products = []
        note = "Berikut adalah beberapa produk yang mungkin Anda sukai:"
        
        if category:
            logger.info(f"Detected category: {category}")
            products = product_service.get_products_by_category(category, max_price)
            if not products:
                note = f"Tidak ada produk {category} yang tersedia."
                logger.warning(note)

        elif max_price:
            logger.info(f"Filtering for products with max price: {max_price}")
            products = product_service.get_products_by_max_price(max_price)
            if not products:
                 note = f"Tidak ada produk di bawah harga {max_price} yang tersedia."
                 logger.warning(note)
        else:
            note = "Maaf, saya tidak mengerti pertanyaan Anda. Bisakah Anda memberikan lebih banyak detail?"
            logger.warning("Could not understand the question.")

        if not products:
          logger.info("No products found based on the criteria.")
        else:
          logger.info(f"Found {len(products)} products.")

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
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:** The code now includes logging at several crucial points:
    * **Incoming Request:**  Logs the question received in the request, which is the starting point of the entire process.
    * **AI Service Call:** Logs before and after calling the `ai_service.get_response()` to track the AI service's activity and response.  Includes the response itself to aid in debugging.
    * **Category and Price Detection:** Logs the detected category and maximum price.  This helps verify that the extraction logic is working correctly.
    * **Product Retrieval:** Logs whether products are found, the number of products found, or if no products are found, logs a warning.
    * **No Product Warning:** Logs warnings if no products of the specified category or within the price range are available.  This helps understand why the user might not be getting useful results.
    * **Fallback Message:** Logs if the question is not understood.
    * **Outgoing Response:** Logs the entire `QueryResponse` object before it's returned to the user. This provides a complete snapshot of the response.
    * **Exception Handling:**  Critically, it logs *exceptions* that occur within the `try` block.  The `logger.exception()` call *automatically* includes the traceback, which is essential for debugging errors.  This is the most important addition. The HTTPException is still raised to inform the client of the error.
* **Informative Messages:** The log messages are clear and informative, explaining what is happening at each step.  This makes it easier to follow the execution flow and identify issues.
* **Correct Log Levels:**  Uses `logger.info` for normal execution flow, `logger.warning` for potentially problematic situations (like no products found), and `logger.exception` for errors. Using the appropriate log levels makes it easier to filter and analyze logs.
* **String Formatting:** Uses f-strings (e.g., `f"Detected category: {category}"`) for cleaner and more readable log messages.
* **Conciseness:** While adding logging, the code remains relatively clean and readable.
* **Error Handling:** Preserves the error handling by raising an `HTTPException` if an unexpected error occurs. This ensures that the API returns an appropriate error response to the client.

This improved solution provides much more comprehensive and helpful logging for debugging and monitoring the `ask_question` function.  It addresses the previous shortcomings and provides a robust logging strategy.

---
*Generated by Smart AI Bot*
