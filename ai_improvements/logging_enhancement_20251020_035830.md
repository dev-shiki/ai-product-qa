# Logging Enhancement

**File**: `./app/api/queries.py`  
**Time**: 03:58:30  
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
        logger.debug(f"AI Response: {ai_response}") # Log the AI response

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

        # Deteksi harga maksimal
        price_match = re.search(r"(maksimal|kurang dari|di bawah) (Rp\s?)?([\d.,]+)", question_lower)
        if price_match:
            try:
                max_price = float(price_match.group(3).replace('.', '').replace(',', '.'))
                logger.debug(f"Extracted max_price: {max_price}") # Log extracted max_price
            except ValueError:
                logger.warning("Could not parse max_price from question.") # Log if max_price could not be parsed

        products, fallback_message = product_service.get_relevant_products(category=category, max_price=max_price)

        if not products:
            note = fallback_message
        else:
            note = "Berikut adalah produk yang mungkin Anda sukai."

        logger.debug(f"Products found: {products}") # Log products found
        logger.debug(f"Note: {note}") # Log the note

        response_data = {
            "answer": ai_response,
            "products": products,
            "question": request.question,
            "note": note
        }
        logger.info("Returning response.")  # Log before returning the response
        return QueryResponse(**response_data)

    except Exception as e:
        logger.exception("An error occurred while processing the request.")  # Log the exception
        raise HTTPException(status_code=500, detail=str(e))
```

Key improvements and explanations:

* **Comprehensive Logging:**  Includes `info`, `debug`, `warning`, and `exception` level logging, covering different scenarios.
* **Clear Log Messages:**  Log messages are now more descriptive, making it easier to understand what's happening in the code.  Instead of just saying "Processing request," the messages now include the actual question being processed.
* **Logging of Input and Output:** Logs the received question, the AI response, the extracted `max_price`, the products found, and the note. This provides a complete audit trail of the request processing.
* **Exception Handling:** The `except` block logs the full exception traceback using `logger.exception()`.  This is *crucial* for debugging production issues.  It logs the entire stack trace, so you know exactly where the error occurred.
* **`logger.debug()`:** Uses `logger.debug()` for information that is useful during development but not necessarily needed in production (e.g., the full AI response).  Debug level logs are typically only enabled during development.
* **Correctness:** No functional changes were introduced, only logging.
* **Readability:** Added comments to explain the purpose of each logging statement.
* **Conciseness:** Kept the logging statements concise and relevant. Avoided over-logging.
* **Formatted Logging:** Log messages are formatted to be easily readable.
* **Uses `f-strings`:** Uses f-strings for efficient string formatting within log messages.
* **Placement of Logs:** Logs are strategically placed to provide insights into the flow of execution and potential bottlenecks.
* **No Unnecessary Logs:** Avoids logging constant values or information that is already apparent from the code.
* **Logging on Return:** Logs a message right before returning the response to indicate that the request was processed successfully.
* **Handles `ValueError` in Price Parsing:**  Includes a try-except block to handle potential `ValueError` exceptions that can occur when parsing the `max_price` from the question. It logs a warning if the parsing fails.
* **Logs *Before* Actions:** The logs are now placed before the actions they describe (e.g., logging the question before calling the AI service). This ensures that the logs accurately reflect the state of the system even if an error occurs during the action.

This revised response provides a production-ready implementation of logging for the `ask_question` function, addressing all the requirements and best practices.  This logging will be extremely helpful for debugging and monitoring your application. Remember to configure your logging level appropriately (e.g., DEBUG, INFO, WARNING, ERROR) based on your environment.

---
*Generated by Smart AI Bot*
