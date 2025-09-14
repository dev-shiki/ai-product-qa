# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 02:20:50  
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
        logger.info(f"AI Service returned: {ai_response}")  # Log the AI response

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

        # Ekstrak angka dari pertanyaan (untuk mencari max_price)
        numbers = re.findall(r'\d+', request.question)
        if numbers:
            max_price = max(map(int, numbers))

        # Get products based on category and max_price
        products = product_service.get_products(category=category, max_price=max_price)
        logger.info(f"Product Service returned {len(products)} products for category: {category}, max_price: {max_price}") #Log number of products returned
        
        fallback_message = ""
        if not products:
            fallback_message = "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
            logger.warning(f"No products found matching criteria.") #Log when no products found

        # Construct the response
        response = QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=fallback_message
        )
        logger.info(f"Returning response: {response}") #Log the complete response

        return response
    except Exception as e:
        logger.exception(f"An error occurred: {e}") #Log any exceptions that occur
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:** Added `logger.info` statements at the start to log the incoming request question.  Crucially, it logs the `ai_response` immediately after receiving it from `ai_service`. This helps in debugging AI-related issues.  It also logs the number of products returned by `product_service`, which is essential for understanding the filtering process.
* **Error Handling:** Includes a `logger.exception` statement in the `except` block to log the full stack trace of any exceptions, which is crucial for debugging.  It preserves the original exception message in the `HTTPException` so the client knows what happened.
* **Contextual Logging:** Added logging messages that include relevant context, such as the category and max_price used to query the product service. This helps in understanding how the parameters affect the results. The final `logger.info` logs the entire `QueryResponse` before it's returned, providing a complete view of the output.
* **Warning for No Products:** Added `logger.warning` when no products are found. Using `warning` level is more appropriate because it indicates a problem that might need investigation, but isn't necessarily a critical error.
* **Clear Log Messages:**  The log messages are formatted to be easily readable and understandable.
* **Placement of Logging:** Log statements are strategically placed to track the flow of execution and the values of important variables.  The log statements surround critical operations (like calling the AI service and the product service) to measure their effect.

This revised response provides robust logging that is extremely helpful for debugging and monitoring the `ask_question` function.  The different log levels (`info`, `warning`, `exception`) are used appropriately to categorize the logged events.  The consistent formatting and inclusion of relevant context make the logs easier to analyze.  The key is to log *enough* information without being overly verbose.

---
*Generated by Smart AI Bot*
