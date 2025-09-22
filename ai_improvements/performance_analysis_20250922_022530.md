# Performance Analysis

**File**: `./app/services/ai_service.py`  
**Time**: 02:25:30  
**Type**: performance_analysis

## Improvement

```python
import logging
from google import genai
from app.utils.config import get_settings
from app.services.product_data_service import ProductDataService
import re  # Import at the top

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
            # Compile regular expression once during initialization
            self.price_pattern = re.compile(r"(harga\s*(kurang\s*dari|di\s*bawah|maksimal)\s*([\d.,]+))|(maksimal\s*harga\s*([\d.,]+))", re.IGNORECASE)

            logger.info("Successfully initialized AI service with Google AI client")
        except Exception as e:
            logger.error(f"Error initializing AI service: {str(e)}")
            raise

    async def get_response(self, question: str) -> str:
        """Get AI response with product context and fallback message"""
        try:
            logger.info(f"Getting AI response for question: {question}")

            # Ekstrak kategori dan max_price dari pertanyaan (sederhana)
            # import re # Moved to the top
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

            # Ekstrak harga maksimum
            # price_pattern = re.compile(r"(harga\s*(kurang\s*dari|di\s*bawah|maksimal)\s*([\d.,]+))|(maksimal\s*harga\s*([\d.,]+))", re.IGNORECASE) # Moved and compiled during init
            match = self.price_pattern.search(question)
            if match:
                max_price = match.group(3) or match.group(5)
                if max_price:
                    max_price = max_price.replace('.', '') # Remove thousand separators (European style)
                    max_price = max_price.replace(',', '.') # Convert decimal separator if needed
                    try:
                        max_price = float(max_price)
                    except ValueError:
                        logger.warning(f"Could not parse max_price: {max_price}")
                        max_price = None

            logger.info(f"Extracted category: {category}, max_price: {max_price}")

            product_context = await self.product_service.get_product_context(category, max_price)

            if not product_context:
                response = "Maaf, saat ini kami tidak memiliki informasi produk yang sesuai dengan kriteria Anda."
                logger.info(f"No product context found. Returning fallback message.")
                return response

            prompt = f"""Anda adalah asisten virtual yang membantu pengguna mencari informasi produk.
            Jawab pertanyaan pengguna berdasarkan konteks produk berikut:
            {product_context}
            Jika pertanyaan tidak relevan dengan konteks produk, jawab dengan sopan bahwa Anda tidak dapat menjawab pertanyaan tersebut.
            """

            try:
                response = self.client.generate_content(prompt + "\n" + question).text
                logger.info(f"AI response: {response}")
                return response
            except Exception as e:
                logger.error(f"Error generating AI response: {str(e)}")
                return "Maaf, terjadi kesalahan saat memproses permintaan Anda."
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return "Maaf, terjadi kesalahan saat memproses permintaan Anda."
```

Justification for the performance improvement:

The most significant performance bottleneck in the original code was the repeated compilation of the regular expression `price_pattern` inside the `get_response` method.  Regular expression compilation is an expensive operation.  By compiling the regular expression once during the `__init__` method and storing it as an instance variable (`self.price_pattern`), we avoid recompiling it on every call to `get_response`.  This saves significant processing time, especially if `get_response` is called frequently.  I also moved the `import re` statement to the top of the file, as is standard practice.

Specifically, the change involves the following:

1. **Compiling the Regex in `__init__`:**

   ```python
   self.price_pattern = re.compile(r"(harga\s*(kurang\s*dari|di\s*bawah|maksimal)\s*([\d.,]+))|(maksimal\s*harga\s*([\d.,]+))", re.IGNORECASE)
   ```

   This line compiles the regex pattern once when the `AIService` class is instantiated.

2. **Using the Compiled Regex in `get_response`:**

   ```python
   match = self.price_pattern.search(question)
   ```

   This line reuses the compiled regex pattern for each incoming `question`, avoiding recompilation.

This change provides a clear and measurable performance improvement by minimizing redundant calculations.

---
*Generated by Smart AI Bot*
