# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 02:38:57  
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

            logger.info(f"Extracted category: {category} from question: {question}")
            
            match = re.search(r'(\d+(?:\.\d+)?(?:k|rb|juta)?)', question_lower)
            if match:
                price_str = match.group(1)
                price_str = price_str.replace('rb', '000000').replace('juta', '000000')
                price_str = price_str.replace('k', '000')
                max_price = float(price_str)

            logger.info(f"Extracted max_price: {max_price} from question: {question}")
            
            # Dapatkan data produk dari service
            products = self.product_service.get_products(category=category, max_price=max_price)
            logger.info(f"Retrieved {len(products)} products from product service.")

            if not products:
                logger.warning("No products found matching the criteria.")
                return "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."

            # Format data produk menjadi string
            product_details = "\n".join([f"{p['name']} - Rp{p['price']}" for p in products])
            logger.debug(f"Product details: {product_details}")


            # Buat prompt untuk AI
            prompt = f"Anda adalah asisten penjualan. Jawab pertanyaan berikut berdasarkan daftar produk berikut:\n{product_details}\n\nPertanyaan: {question}\n\nJawaban:"
            logger.debug(f"Prompt sent to AI model: {prompt}")

            # Kirim prompt ke model AI
            model = self.client.generative_model(model_name="gemini-1.5-flash-001")
            response = model.generate_content(prompt)

            logger.info(f"Received response from AI model.")
            
            # Kembalikan jawaban AI
            return response.text

        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
            return "Maaf, terjadi kesalahan saat memproses permintaan Anda."
```

Key changes and explanations:

*   **Detailed Logging:** Added `logger.info()` statements to log the extracted `category` and `max_price` from the user's question.  This is crucial for debugging and understanding the AI's decision-making process.
*   **Product Retrieval Logging:** Added `logger.info(f"Retrieved {len(products)} products from product service.")` to track how many products were fetched from the `ProductDataService`. This helps identify if the product data service is working correctly and returning relevant results.
*   **No Product Found Logging:** Added `logger.warning("No products found matching the criteria.")` to indicate when the product service returns an empty list.  This is important because the AI will likely provide a canned response in this case.
*   **Product Details Logging:** Added `logger.debug(f"Product details: {product_details}")` to log the formatted product details *before* they are sent to the AI model.  This allows you to inspect the exact data being used as context.  `logger.debug` is appropriate because this is detailed information not always needed in normal operation.
*   **Prompt Logging:** Added `logger.debug(f"Prompt sent to AI model: {prompt}")` to log the complete prompt being sent to the AI model.  This is essential for understanding how the question and product details are combined to guide the AI's response.  Again, `logger.debug` is used as this is a verbose logging level.
*   **Response Logging:** Added `logger.info(f"Received response from AI model.")` to confirm the AI model returned a response.
*   **Error Logging with Traceback:**  In the `except` block, changed `logger.error(f"Error getting AI response: {str(e)}")` to `logger.error(f"Error getting AI response: {str(e)}", exc_info=True)`. The `exc_info=True` argument ensures that the full traceback of the exception is included in the log message.  This is absolutely critical for debugging errors in asynchronous code.
*   **Consistent Logging Level:** Used `logger.info` for important actions and `logger.debug` for detailed information useful during development or troubleshooting.
*   **Clear Message Formatting:**  Used f-strings for clear and readable log messages.

This version provides significantly more insight into the execution flow and potential issues, making debugging and monitoring much easier.  Remember to configure the logging level in your application's configuration to see the `DEBUG` level messages.

---
*Generated by Smart AI Bot*
