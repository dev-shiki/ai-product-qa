# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 03:08:27  
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
            
            # Mencari harga maksimal (misalnya "di bawah 5 juta")
            price_match = re.search(r'(?:di bawah|kurang dari|maksimal)\s*([\d\.,]+)\s*(juta|ribu)?', question_lower)
            if price_match:
                price_value = float(price_match.group(1).replace('.', '').replace(',', '.'))
                unit = price_match.group(2)
                if unit == 'juta':
                    max_price = price_value * 1000000
                elif unit == 'ribu':
                    max_price = price_value * 1000
                else:
                    max_price = price_value  # Asumsi dalam Rupiah jika tidak ada unit
            
            logger.info(f"Extracted category: {category}, max_price: {max_price}")

            product_context = await self.product_service.get_product_details(category=category, max_price=max_price)
            logger.info(f"Product context retrieved: {product_context}")

            if not product_context:
                logger.warning("No product context found, using fallback message.")
                return "Maaf, saat ini tidak ada rekomendasi produk yang sesuai."

            prompt = f"""Anda adalah asisten penjualan yang membantu pengguna menemukan produk yang tepat.
            Jawab pertanyaan pengguna berdasarkan konteks produk berikut:
            {product_context}
            Jika tidak ada informasi yang relevan dalam konteks, jawab dengan sopan bahwa Anda tidak memiliki informasi yang cukup untuk menjawab pertanyaan tersebut.
            Pertanyaan Pengguna: {question}"""

            model = self.client.models.get("gemini-1.5-pro-latest") #  "gemini-1.5-pro-latest" "gemini-pro"
            logger.debug(f"Using model: {model.name}")

            response = model.generate_content(prompt)
            logger.info(f"AI response generated: {response.text}")

            return response.text
        except Exception as e:
            logger.exception(f"Error getting AI response: {str(e)}")  # Use exception for full traceback
            return "Terjadi kesalahan saat memproses permintaan Anda."
```

Key improvements and explanations:

* **Comprehensive Logging:**  The core request was to add logging to `get_response`.  This version includes `logger.info` calls to track the question being processed, extracted category and price, retrieved product context, and the final AI response. It logs the model being used (debug).
* **Error Handling:**  The `except` block now uses `logger.exception` instead of `logger.error`.  `logger.exception` automatically includes the full traceback of the error, making debugging much easier. Critically important!
* **Clearer Logging Messages:** The log messages are more descriptive, indicating what data is being logged.
* **Debug Level Logging:** Added `logger.debug` to log the model name. Debug level is appropriate here because the model name is useful for developers to see during debugging but doesn't need to be logged in production.
* **Warning Level Logging:** Logs a warning message if no product context is found, indicating that the fallback message will be used.  This helps diagnose cases where product data retrieval is failing.
* **Consistent Logging Levels:** Using `info`, `warning`, `error`, and `debug` appropriately.  `info` for normal operations, `warning` for potential issues, `error` for failures, and `debug` for developer-level information.
* **String Formatting:** Used f-strings for cleaner and more readable logging messages.
* **No Unnecessary Changes:** The provided code was modified *only* to add logging, keeping the original logic intact.

This revised response provides a production-ready, well-logged function that will greatly aid in debugging and monitoring the AI service. It addresses all the key points of the prompt and follows best practices for logging.  Using `logger.exception` is the most important fix for debugging purposes.

---
*Generated by Smart AI Bot*
