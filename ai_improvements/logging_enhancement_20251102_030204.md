# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 03:02:04  
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
            
            # Mencari angka (harga) menggunakan regular expression
            price_match = re.search(r'harga\s*(\d+(?:\.\d{3})*(?:,\d+)?)', question_lower)
            if price_match:
                # Menghapus titik sebagai pemisah ribuan dan mengganti koma dengan titik untuk desimal
                price_str = price_match.group(1).replace('.', '').replace(',', '.')
                try:
                    max_price = float(price_str)
                except ValueError:
                    logger.warning(f"Could not convert price string '{price_str}' to float.")
                    max_price = None  # Set to None if conversion fails
            
            products = await self.product_service.get_products(category=category, max_price=max_price)
            
            if products:
                product_names = ", ".join([product.name for product in products])
                context = f"The user is asking a question related to these products: {product_names}. " \
                          f"Here's additional information about these products that may be relevant in answering the question."
                logger.info(f"Found products for context: {product_names}")
            else:
                context = "The user is asking a question about electronic products. " \
                          "If you don't know the answer, respond politely."
                logger.info("No specific products found. Using general context.")

            prompt = f"""You are a helpful assistant who answers user questions related to electronic products.
            Use the following context when generating your response:
            {context}

            Question: {question}
            """

            model = self.client.models.get("gemini-1.5-pro-latest")
            response = model.generate_content(prompt)
            logger.info(f"AI response generated: {response.text}")

            return response.text

        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."
```

Key improvements and explanations:

* **Comprehensive Logging:**  The `get_response` function now logs the following:
    * The incoming question using `logger.info(f"Getting AI response for question: {question}")`. This is the most important log, as it tells us what the function is processing.
    * Whether products were found, including a list of the product names if they were using `logger.info(f"Found products for context: {product_names}")` and `logger.info("No specific products found. Using general context.")`. This helps understand the context used by the AI.
    * The generated AI response `logger.info(f"AI response generated: {response.text}")`. This allows verifying what the AI is generating.
    * Any exceptions that occur during the process using `logger.error(f"Error getting AI response: {str(e)}")`.  Crucially, this now includes the exception message, making debugging much easier.
    * Added logging within the price extraction to handle potential conversion errors:  `logger.warning(f"Could not convert price string '{price_str}' to float.")` This is important because errors during price extraction would lead to incorrect filtering or no filtering at all, potentially impacting the AI response.

* **Error Handling:** The `try...except` block catches potential exceptions and logs them using `logger.error()`. This is crucial for debugging and preventing the application from crashing. The error message is included in the log, providing valuable information about what went wrong.

* **Clear Log Messages:** The log messages are formatted to be informative and easy to understand. They clearly indicate the event being logged and include relevant data, such as the question, product names, and error messages.

* **Correct Placement:** The logging statements are placed at strategic points in the code to provide a comprehensive overview of the function's execution.

This revised response provides much more complete and useful logging, covering all the critical parts of the function and greatly aiding in debugging and monitoring.  It also addresses the potential error during price extraction, making it more robust.

---
*Generated by Smart AI Bot*
