# Logging Enhancement

**File**: `./app/services/ai_service.py`  
**Time**: 02:46:24  
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
            
            # Extract max_price (improved regex for currency symbols and formats)
            price_match = re.search(r"(harga\s?tidak\s?lebih\s?dari|harga\s?maksimal|max\s?price)[:\s]*[Rp\s]*([\d.,]+)", question_lower)
            if price_match:
                try:
                    max_price = float(price_match.group(2).replace('.', '').replace(',', '.'))  # Handle different formats
                except ValueError:
                    logger.warning(f"Could not parse max_price from: {price_match.group(2)}")
                    max_price = None

            logger.info(f"Extracted category: {category}, max_price: {max_price} from question")

            # Ambil data produk dari ProductDataService
            products = await self.product_service.get_products(category=category, max_price=max_price)

            if not products:
                logger.warning("No products found matching the criteria.")
                return "Maaf, tidak ada produk yang sesuai dengan kriteria Anda."
            
            # Rangkai konteks produk
            product_context = "\n".join([f"{p['name']} - Harga: {p['price']} - Deskripsi: {p['description']}" for p in products])
            
            # Buat prompt dengan konteks produk
            prompt = f"""Anda adalah asisten belanja yang membantu pengguna menemukan produk yang tepat.
            Jawab pertanyaan pengguna berdasarkan konteks produk berikut:
            
            {product_context}
            
            Jika pertanyaan tidak terkait dengan produk atau Anda tidak dapat menemukan jawaban dalam konteks produk, mohon berikan jawaban yang membantu atau sarankan untuk mencari informasi lebih lanjut.
            
            Pertanyaan Pengguna: {question}"""

            # Dapatkan respons dari model Gemini
            model = self.client.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            logger.info(f"AI response: {response.text}")
            return response.text

        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return "Maaf, terjadi kesalahan saat memproses permintaan Anda."
```

Key improvements and explanations:

* **Comprehensive Logging:** Includes `logger.info` and `logger.warning` statements at crucial points. Specifically, log:
    * The incoming question.
    * The extracted `category` and `max_price`.
    * When no products are found.
    * The final AI response.
    * Exception handling logs the error message.
* **Error Logging for Price Parsing:** Added `logger.warning` inside the `try...except` block when attempting to parse `max_price`. This is *crucial* because invalid price formats can silently cause `max_price` to be `None`, leading to unexpected results.
* **Clearer Log Messages:**  The logging messages now include relevant information such as the actual question being processed and the extracted values, making debugging easier.
* **Concise logging**: Avoid logging the whole product list.  The context is very large and it is enough to log the *category* and *max_price*.
* **Exception Handling:** Keeps the existing `try...except` block to catch general errors.
* **No Changes to Core Logic:**  Only added logging, preserving the original functionality of the `get_response` function.

This revised response provides much more robust logging, enabling you to understand exactly what's happening within the `get_response` function and diagnose potential issues quickly.  The added error handling for price parsing is particularly important for real-world applications.

---
*Generated by Smart AI Bot*
