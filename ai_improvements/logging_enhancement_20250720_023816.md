# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 02:38:16  
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

            # Extract max price using regex
            match = re.search(r'maksimal\s*(\d+(?:\.\d+)?(?:ribu|juta)?)', question_lower)
            if match:
                price_str = match.group(1)
                price_str = price_str.replace('ribu', '000').replace('juta', '000000').replace('.', '')
                try:
                    max_price = int(price_str)
                except ValueError:
                    logger.warning(f"Could not parse max price from string: {price_str}")
                    max_price = None

            logger.info(f"Extracted category: {category}, max_price: {max_price} from question")  # Log extracted values

            products = await self.product_service.get_products(category=category, max_price=max_price)

            if not products:
                logger.warning("No products found matching the criteria, using fallback message.")
                return "Maaf, saat ini tidak ada produk yang sesuai dengan kriteria Anda."
                
            # Format product data for AI context
            product_details = "\n".join([f"{p.name} - Harga: {p.price} - Rating: {p.rating} - Link: {p.link}" for p in products])
            context = f"""Anda adalah asisten belanja. Jawab pertanyaan pengguna berdasarkan daftar produk berikut ini.
            {product_details}
            Jika tidak ada produk yang cocok, berikan jawaban yang sesuai. Jangan mengarang informasi.
            """
            
            prompt = f"{context}\n\nPertanyaan: {question}\nJawaban:"
            logger.debug(f"AI Prompt: {prompt}")
            
            model = self.client.genai_models.get_model(model="gemini-1.5-pro-latest")  # Specify the model
            response = model.generate_content(prompt)
            
            logger.info(f"AI response: {response.text}")
            return response.text

        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return "Maaf, terjadi kesalahan dalam memproses permintaan Anda."
```

Key improvements and explanations:

* **Comprehensive Logging:**  Added `logger.info`, `logger.warning`, `logger.debug`, and `logger.error` calls at various points within the function to track the flow of execution, the values of important variables, and potential errors.

* **Category and Price Logging:** Logs the extracted `category` and `max_price` immediately after they are determined. This is crucial for debugging incorrect extractions.

* **Product Search Logging:** Logs a warning if no products are found.  This helps identify situations where the query is too restrictive or there is no matching data.

* **Prompt Logging (DEBUG level):** Logs the full prompt being sent to the AI model at `DEBUG` level.  This is extremely helpful for understanding how the context and question are being formatted and can reveal issues with the prompt itself.  Using `logger.debug` ensures that this detailed logging is only enabled when needed, as prompts can be quite long.

* **AI Response Logging:** Logs the raw AI response before returning it. This is vital for analyzing the quality and accuracy of the AI's answer.

* **Error Handling Logging:** The `except` block logs the exception message, ensuring that any errors during the AI response generation are captured.

* **Clear Log Messages:** The log messages are designed to be informative and easy to understand, making it easier to diagnose problems.

How to use this effectively:

1.  **Configure Logging:** Make sure your application's logging is properly configured (e.g., using a `logging.basicConfig` call or a `logging.config.fileConfig` call).  Crucially, you need to set the logging level appropriately (e.g., `logging.INFO`, `logging.DEBUG`, `logging.WARNING`, `logging.ERROR`). If you want to see the prompt, set the level to `logging.DEBUG`.

2.  **Analyze Logs:** When you encounter issues, examine the logs carefully. Look for error messages, warnings, unexpected variable values, or AI responses that don't make sense.

3.  **Adjust Logging:** Based on your analysis, you may need to adjust the logging levels or add more logging statements to pinpoint the root cause of the problem.  For example, you might temporarily add `logger.debug` statements to inspect the contents of a list or dictionary that you suspect is causing issues.

This revised solution provides a much more robust and informative logging strategy for debugging your AI service.  It covers the critical parts of the function and provides the necessary context for understanding how the AI is being used and where potential problems might lie.

---
*Generated by Smart AI Bot*
