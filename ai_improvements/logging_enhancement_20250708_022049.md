# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 02:20:49  
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

            # Extract max_price from the question
            price_match = re.search(r'maksimal\s?(\d+(?:\.\d+)?(?:ribu|juta|miliar)?)', question_lower)
            if price_match:
                price_str = price_match.group(1)
                price_str = price_str.replace('ribu', '000').replace('juta', '000000').replace('miliar', '000000000').replace('.', '')

                try:
                    max_price = int(price_str)
                    logger.debug(f"Extracted max_price: {max_price} from question")
                except ValueError:
                    logger.warning(f"Could not convert extracted price string '{price_str}' to integer.")
                    max_price = None


            logger.debug(f"Extracted category: {category} and max_price: {max_price} from question.")
            
            product_context = await self.product_service.get_product_context(category=category, max_price=max_price)
            logger.debug(f"Product context retrieved: {product_context}")

            if not product_context:
                logger.info("No matching products found for the given criteria.")
                return "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."

            prompt = f"""Anda adalah asisten toko online. Jawab pertanyaan pelanggan berdasarkan konteks produk berikut ini. 
            Jika tidak ada dalam konteks, jawab dengan sopan bahwa Anda tidak tahu.
            Konteks Produk: {product_context}
            Pertanyaan: {question}
            """

            # Use the new Google AI client
            model = self.client.generative_model(model_name="gemini-1.5-pro-latest")

            # Set a low temperature for more deterministic responses
            response = model.generate_content(prompt, generation_config={"temperature": 0.1})
            
            logger.info(f"AI response generated: {response.text}")
            return response.text

        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return "Maaf, terjadi kesalahan saat memproses permintaan Anda."
```

Key improvements and explanations:

* **Detailed Logging:**  The logging statements now provide more information about the process.  `logger.info` is used for general progress, `logger.debug` is used for variable values, and `logger.warning` is used for potential issues that don't halt the process. `logger.error` remains for errors.
* **Category and Price Extraction Logging:** Log the extracted `category` and `max_price` for debugging purposes.  This is crucial to understanding if the extraction logic is working correctly.
* **Product Context Logging:** Log the `product_context` to see what data is being used to generate the AI response. This is essential for ensuring the context is relevant.  The `logger.debug` level is appropriate here because the content of the context might be large.
* **Error Handling Logging:** The `except` block now includes a comprehensive error message.
* **Clearer Debugging:** The use of f-strings in the logging messages makes it easier to read and understand the log output.
* **Price Conversion Logging:** Added logging for price conversion, including potential warnings for invalid price strings.
* **No Product Match Logging:** Logs when no product matches are found, explaining why the user might get a "no products" message.
* **Prompt Logging:** Consider logging the `prompt` (at the `DEBUG` level) *if* you are sure it doesn't contain sensitive user data.  Seeing the exact prompt sent to the LLM is extremely valuable for debugging the AI's behavior.  However, be very careful about PII/PHI.

This revised answer provides significantly more comprehensive logging, making it much easier to debug and monitor the `get_response` function.  Remember to adjust the logging level in your application's configuration to `DEBUG` when you need detailed logging information, and back to `INFO` or `WARNING` for production use.

---
*Generated by Smart AI Bot*
