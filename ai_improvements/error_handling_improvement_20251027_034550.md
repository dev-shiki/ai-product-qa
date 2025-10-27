# Error Handling Improvement

**File**: `./app/services/ai_service.py`  
**Time**: 03:45:50  
**Type**: error_handling_improvement

## Improvement

```python
import logging
from google import genai
from app.utils.config import get_settings
from app.services.product_data_service import ProductDataService
import re  # Import here, at the top of the file.

# Setup logging
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        """Initialize AI service with Google AI API"""
        try:
            settings = get_settings()
            # Use the new Google AI client
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            self.product_service = ProductDataService()
            logger.info("Successfully initialized AI service with Google AI client")
        except Exception as e:
            logger.exception("Error initializing AI service:")  # Use logger.exception to capture stack trace
            raise  # Re-raise the exception to signal failure to the caller

    async def get_response(self, question: str) -> str:
        """Get AI response with product context and fallback message"""
        logger.info(f"Getting AI response for question: {question}")
        category = None
        max_price = None
        try:  # Wrap the entire logic in a try-except block for robust error handling
            # Deteksi kategori dengan lebih lengkap (sama dengan API endpoint)
            question_lower = question.lower()
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

            # Deteksi Harga
            price_match = re.search(r"maksimal\s*(\d+)", question_lower)
            if price_match:
                try:
                    max_price = int(price_match.group(1))  # Explicitly convert to int
                except ValueError:
                    logger.warning(f"Could not convert price to integer: {price_match.group(1)}")
                    max_price = None # or some default value

            # Fetch Product Data
            product_data = await self.product_service.get_product_data(category=category, max_price=max_price)

            # Construct Prompt
            prompt = f"Berdasarkan data produk berikut: {product_data}, jawab pertanyaan: {question}"

            # Call Google AI API
            response = self.client.generate_content(prompt)
            ai_response = response.text

            logger.info(f"AI response: {ai_response}")
            return ai_response

        except genai.APIError as e:  # Specific exception for GenAI API errors
            logger.error(f"Google AI API Error: {e}")
            return "Maaf, terjadi kesalahan saat menghubungi Google AI. Coba lagi nanti." # Fallback message
        except Exception as e:  # Catch all other exceptions
            logger.exception(f"An unexpected error occurred while processing the request:")  # Log the full exception
            return "Maaf, terjadi kesalahan. Coba lagi nanti." # Generic fallback message

```

Key improvements and explanations:

* **Comprehensive Try-Except Block:**  The entire `get_response` method's core logic is now within a `try...except` block. This prevents unexpected exceptions from crashing the application.  This is crucial.
* **Specific Exception Handling for Google AI:**  A `except genai.APIError as e:` clause is added to specifically catch errors from the Google AI API.  This allows for more targeted error handling.  It logs the specific API error and provides a user-friendly fallback message.  It is very important to catch the specific API error type.
* **`logger.exception()`:** Replaced `logger.error` with `logger.exception` in the outer `except` block in `get_response`  and in `__init__`. `logger.exception` automatically includes the stack trace in the log message.  This is *essential* for debugging unexpected errors because it shows the exact sequence of function calls that led to the error.  Without a stack trace, debugging is significantly harder.
* **Value Conversion Error Handling:** The code now handles the potential `ValueError` when converting the extracted price from the regular expression to an integer.  If the string can't be converted (e.g., if the regex matches something unexpected), it logs a warning and sets `max_price` to `None` (or a default value).  This prevents the code from crashing if the price is not a valid number.  The handling includes a warning message.
* **Fallback Messages:** The code now provides more informative and user-friendly fallback messages when errors occur.  Instead of just crashing or returning a cryptic error, it informs the user that there was a problem and to try again later. This improves the user experience significantly.  The message now includes "Maaf" to indicate that the AI service failed and provide a reason.
* **Re-raising exception in `__init__`:** The `__init__` method now re-raises the exception after logging it.  This is important because it signals to the calling code (the part of the application that creates the `AIService` object) that the initialization failed. The calling code can then take appropriate action, such as retrying or shutting down gracefully.  If the exception isn't re-raised, the application might continue to run in a broken state, which can lead to further problems.
* **Explicit type conversion:** Added explicit type conversion of the price using `int()`.
* **Import `re`:** Moved the import statement for the `re` module to the top of the file, as is standard practice for code organization.

These changes make the `AIService` significantly more robust and easier to debug. The improved error handling prevents crashes, provides more informative error messages, and makes it easier to identify and fix problems.  The stack traces provided by `logger.exception` are invaluable for debugging.

---
*Generated by Smart AI Bot*
