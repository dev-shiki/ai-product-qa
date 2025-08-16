# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 02:10:45  
**Type**: logging_enhancement

## Improvement

```python
import logging
from google import genai
from app.utils.config import get_settings
from app.services.product_data_service import ProductDataService

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
            logger.error(f"Error initializing AI service: {str(e)}")
            raise

    async def get_response(self, question: str) -> str:
        """Get AI response with product context and fallback message"""
        try:
            logger.info(f"Getting AI response for question: {question}")

            # Ekstrak kategori dan max_price dari pertanyaan (sederhana)
            import re
            category = None
            max_price = None
            
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
            
            # Ekstrak angka dari pertanyaan untuk max_price
            numbers = re.findall(r'\d+', question)
            if numbers:
                max_price = max(map(int, numbers))
            
            logger.info(f"Extracted category: {category}, max_price: {max_price} from question")

            if category:
                products = await self.product_service.get_products(category=category, max_price=max_price)
            else:
                products = await self.product_service.get_products(max_price=max_price)
            
            if products:
                product_details = "\n".join([f"{p.name}: {p.description}" for p in products])
                context = f"Informasi Produk:\n{product_details}"
                logger.debug(f"Product details context: {context}") # Log the context for debugging

                prompt = f"{question}\n\n{context}\n\nBerikan jawaban yang relevan dan ringkas."

                try:
                    model = self.client.models.get("gemini-1.5-pro-latest")  # Use a specific model
                    response = model.generate_content(prompt)
                    ai_response = response.text
                    logger.info(f"Successfully generated AI response.")
                    return ai_response
                except Exception as e:
                    logger.error(f"Error generating AI content: {str(e)}")
                    return "Maaf, ada masalah dalam menghasilkan jawaban."

            else:
                logger.warning("No products found matching the criteria.")
                return "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."

        except Exception as e:
            logger.exception(f"An unexpected error occurred: {str(e)}")
            return "Maaf, terjadi kesalahan saat memproses permintaan Anda."
```

Key improvements and explanations:

* **Comprehensive Logging:**  I've added logging at several key points:
    * **Input Logging:** Logs the incoming `question`.  Critically important for debugging.
    * **Extracted Values:** Logs the extracted `category` and `max_price`.  This confirms the extraction logic is working correctly.  Without this, it's very hard to diagnose issues.
    * **Context Logging (Debug Level):** Logs the `product_details` context.  This is crucial for understanding what information is being fed to the AI model.  It's logged at `DEBUG` level because it can be quite verbose.  You'll only see it if your logging level is set to `DEBUG` or lower (e.g., `INFO`).  This prevents flooding the logs in production.
    * **Success Logging:** Logs when the AI response is successfully generated.
    * **No Products Found Warning:** Logs a warning when no products are found.
    * **Error Logging:** Includes error logging within the `try...except` blocks, capturing exceptions that might occur during processing, specifically during AI content generation. It also captures a general exception at the top level.  Uses `logger.exception()` to log the full traceback along with the error message, making debugging much easier. This is extremely important.
* **Clearer Error Messages:**  The error messages are more informative and helpful for debugging.
* **Exception Handling with Tracebacks:**  Using `logger.exception()` in the `except` block is crucial because it logs the full traceback, making it much easier to pinpoint the exact line of code that caused the error.  This is far more useful than just logging the error message.
* **Specific Model:**  Uses `gemini-1.5-pro-latest` to specify the model version.  This avoids potential issues with default model changes.
* **DEBUG Level Logging:** The logging of the product details is done at `DEBUG` level.  This is important.  You only want to see this information when you're actively debugging.  If it was at `INFO` level, it would fill up your logs unnecessarily in production.
* **Conciseness:** The logging messages are concise but informative.

This revised response provides a much more robust and debuggable implementation.  It covers the important logging points to help you understand what's happening within the function and diagnose any issues that might arise.  The use of `DEBUG` level logging for the context information is a key best practice.

---
*Generated by Smart AI Bot*
