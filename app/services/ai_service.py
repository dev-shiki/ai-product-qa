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
            
            # Deteksi budget
            price_match = re.search(r'(\d+)\s*juta', question_lower)
            if price_match:
                max_price = int(price_match.group(1)) * 1000000
            elif 'budget' in question_lower or 'murah' in question_lower:
                max_price = 5000000

            # Gunakan smart_search_products
            products, fallback_message = await self.product_service.smart_search_products(
                keyword=question, category=category, max_price=max_price, limit=5
            )

            # Build context
            context = f"Question: {question}\n\n"
            context += f"{fallback_message}\n\n"
            if products:
                context += "Relevant Products:\n"
                for i, product in enumerate(products, 1):
                    context += f"{i}. {product.get('name', 'Unknown')}\n"
                    context += f"   Price: Rp {product.get('price', 0):,.0f}\n"
                    context += f"   Brand: {product.get('brand', 'Unknown')}\n"
                    context += f"   Category: {product.get('category', 'Unknown')}\n"
                    context += f"   Rating: {product.get('specifications', {}).get('rating', 0)}/5\n"
                    context += f"   Description: {product.get('description', 'No description')[:200]}...\n\n"
            else:
                context += "No specific products found, but I can provide general recommendations.\n\n"

            # Create prompt
            prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n{context}\n\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision. Focus on being helpful and natural in your response."""

            # Generate response using new API format
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            logger.info("Successfully generated AI response")
            return response.text
        
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    def generate_response(self, context: str) -> str:
        """Generate response using Google AI (legacy method)"""
        try:
            logger.info("Generating AI response")
            
            # Create prompt
            prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

            # Generate response using new API format
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            logger.info("Successfully generated AI response")
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            raise 