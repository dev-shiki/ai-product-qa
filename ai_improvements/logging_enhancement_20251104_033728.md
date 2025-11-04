# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 03:37:28  
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
            
            # Ekstrak angka dari pertanyaan (untuk max_price)
            numbers = re.findall(r'\d+(?:\.\d+)?', question)
            if numbers:
                max_price = max([float(num) for num in numbers])

            logger.info(f"Extracted category: {category}, max_price: {max_price} from question")

            # Ambil konteks produk berdasarkan kategori dan max_price
            product_context = await self.product_service.get_product_data(category=category, max_price=max_price)

            logger.info(f"Retrieved product context: {product_context}")  # Log the context

            if not product_context:
                logger.warning("No product context found. Using fallback message.")
                return "Maaf, saat ini kami tidak memiliki informasi produk yang sesuai dengan kriteria Anda."

            prompt = f"""Anda adalah asisten penjualan e-commerce. Jawab pertanyaan berdasarkan konteks produk berikut.
            Konteks Produk: {product_context}
            Pertanyaan: {question}
            """

            logger.debug(f"Generated prompt: {prompt}")

            model = self.client.generative_model("gemini-1.5-pro-latest")  # Ganti dengan model yang sesuai
            response = model.generate_content(prompt)

            logger.info(f"Generated response: {response.text}")

            return response.text

        except Exception as e:
            logger.exception(f"Error getting AI response: {str(e)}") # Use exception for full traceback
            return "Terjadi kesalahan dalam memproses permintaan Anda. Silakan coba lagi nanti."
```

Key improvements and explanations:

* **Clear Logging Statements:**  Each logging statement provides context about what's happening at that point in the function.  `logger.info` for general progress, `logger.debug` for detailed information like the generated prompt, `logger.warning` when a potential issue is encountered (no product context), and `logger.exception` for errors, including the full traceback.
* **Contextual Information:** The logging includes relevant variables and data, such as the extracted `category`, `max_price`, and the retrieved `product_context`. This makes debugging much easier.
* **`logger.exception` for Errors:**  Critically, `logger.exception(f"Error getting AI response: {str(e)}")` is used in the `except` block. This logs the *entire* traceback, which is essential for diagnosing the root cause of errors. Just logging `str(e)` is often insufficient.  This is a *huge* improvement over just logging the error message.
* **Prompt Logging (Debug Level):** The generated `prompt` is logged at the `DEBUG` level.  This is very helpful for understanding what the AI model is receiving as input and diagnosing prompt-related issues.  Because prompts can be lengthy, using `DEBUG` is appropriate so that it's not always outputted.
* **Consistent Use of f-strings:**  Using f-strings makes the logging statements much more readable and easier to maintain.
* **Concise Logging:**  The logging is designed to be informative without being overly verbose.
* **No Redundant Logging:** Removed logging that didn't add value.
* **Correct Indentation:**  The indentation is corrected to match the original code.

How to use the logging:

1.  **Configure Logging:**  Make sure you have your logging configured correctly in your application.  This typically involves setting the logging level (e.g., `logging.INFO`, `logging.DEBUG`) and specifying where the logs should be written (e.g., to a file, to the console).
2.  **Set Logging Level:**  To see the `DEBUG` level log statements, you need to set the logging level to `DEBUG`.  Otherwise, you'll only see `INFO`, `WARNING`, `ERROR`, and `CRITICAL` level messages.

Example logging configuration (basic):

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set the desired logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

This setup will log messages to the console with a timestamp, logger name, level, and the message itself.  You can customize the `format` string to include other information as needed.  You can also configure logging to write to a file instead of or in addition to the console.

---
*Generated by Smart AI Bot*
