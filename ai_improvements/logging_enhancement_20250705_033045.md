# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 03:30:45  
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
        logger.info(f"AI service returned response: {ai_response}")
        
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
        
        # Simple price extraction
        price_match = re.search(r'(?:harga\s?)(kurang dari|di bawah|maksimal)\s?([0-9]+(?:[.,][0-9]+)?)', question_lower)
        if price_match:
            max_price = float(price_match.group(2).replace(',', '.'))

        logger.info(f"Extracted category: {category}, max_price: {max_price}")

        products = product_service.get_products(category=category, max_price=max_price)

        logger.info(f"Found {len(products)} products matching the criteria.")

        fallback_message = "Berikut adalah beberapa produk yang mungkin Anda sukai:"

        # Craft response
        response = {
            "answer": ai_response,
            "products": products,
            "question": request.question,
            "note": fallback_message if products else "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
        }
        logger.info(f"Returning response: {response}")

        return QueryResponse(**response)

    except Exception as e:
        logger.exception("An error occurred during processing:")  # Log the full exception
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **`logger.info(f"Received question: {request.question}")`**: Logs the incoming question immediately, so you know what's being processed.  Crucially uses an f-string for clarity.
* **`logger.info("Calling AI service to get response.")`**:  Indicates the start of the AI service call.
* **`logger.info(f"AI service returned response: {ai_response}")`**: Logs the response received from the AI service.  This is essential for debugging AI-related issues.
* **`logger.info(f"Extracted category: {category}, max_price: {max_price}")`**: Logs the extracted category and price, so you can verify if the regex and category mapping are working correctly.
* **`logger.info(f"Found {len(products)} products matching the criteria.")`**: Logs the number of products found. This is a good indicator of whether the product filtering is working as expected.
* **`logger.info(f"Returning response: {response}")`**: Logs the complete response before it's sent back to the client.  This gives you a final snapshot of the data being returned.
* **`logger.exception("An error occurred during processing:")`**:  This is the most important change.  Using `logger.exception()` logs the *entire* exception, including the traceback.  This is crucial for debugging because it tells you exactly where the error occurred.  This is significantly better than `logger.error(str(e))` which only logs the error message and loses the context.
* **Clarity and Consistency**:  Used f-strings for logging messages for better readability and incorporated consistent logging throughout the function.
* **Error Handling**:  The `try...except` block is already there; the key is to use `logger.exception` *inside* the `except` block.
* **Placement**: Logging statements are placed strategically to track the flow of execution and the values of important variables.

This revised solution provides much more detailed and useful logging, making it significantly easier to debug issues in your `ask_question` function.  Remember to configure your logging level (e.g., `logging.basicConfig(level=logging.INFO)`) to actually see these log messages.

---
*Generated by Smart AI Bot*
