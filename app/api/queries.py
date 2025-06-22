import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.product_data_service import ProductDataService
from app.services.ai_service import AIService
import re

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()
product_service = ProductDataService()
ai_service = AIService()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    products: List[dict]
    question: str
    note: str

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Ask a question about products and get recommendations"""
    try:
        # Get AI response
        ai_response = await ai_service.get_response(request.question)
        
        # Get relevant products and fallback message
        # Ekstrak kategori dan max_price dari pertanyaan (sederhana)
        category = None
        max_price = None
        
        # Deteksi kategori dengan lebih lengkap
        question_lower = request.question.lower()
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
            
        products, fallback_message = await product_service.smart_search_products(
            keyword=request.question, category=category, max_price=max_price, limit=5
        )
        
        return QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question,
            note=fallback_message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_suggestions():
    """Get suggested questions"""
    suggestions = [
        "Apa produk terbaik untuk gaming?",
        "Rekomendasi laptop untuk kerja",
        "Smartphone dengan kamera terbaik",
        "Headphone wireless dengan kualitas bagus",
        "Produk untuk rumah tangga",
        "Gadget untuk produktivitas",
        "Tablet untuk kreativitas",
        "Smartwatch untuk olahraga"
    ]
    return {"suggestions": suggestions}

@router.get("/categories")
async def get_categories():
    """Get available product categories"""
    try:
        categories = await product_service.get_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting categories")

@router.get("/brands")
async def get_brands():
    """Get available product brands"""
    try:
        brands = product_service.get_brands()
        return {"brands": brands}
    except Exception as e:
        logger.error(f"Error getting brands: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting brands")

@router.get("/products/search")
async def search_products(keyword: str, limit: int = 10):
    """Search products directly"""
    try:
        products = await product_service.search_products(keyword, limit)
        return {
            "products": products,
            "count": len(products),
            "keyword": keyword,
            "source": "local"
        }
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching products")

@router.get("/products/category/{category}")
async def get_products_by_category(category: str):
    """Get products by category"""
    try:
        products = product_service.get_products_by_category(category, limit=20)
        return {
            "products": products,
            "count": len(products),
            "category": category,
            "source": "local"
        }
    except Exception as e:
        logger.error(f"Error getting products by category: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting products by category")

@router.get("/products/brand/{brand}")
async def get_products_by_brand(brand: str):
    """Get products by brand"""
    try:
        products = product_service.get_products_by_brand(brand, limit=20)
        return {
            "products": products,
            "count": len(products),
            "brand": brand,
            "source": "local"
        }
    except Exception as e:
        logger.error(f"Error getting products by brand: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting products by brand")

@router.get("/products/top-rated")
async def get_top_rated_products(limit: int = 5):
    """Get top rated products"""
    try:
        products = await product_service.get_top_rated_products(limit)
        return {
            "products": products,
            "count": len(products),
            "source": "local"
        }
    except Exception as e:
        logger.error(f"Error getting top rated products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting top rated products")

@router.get("/products/best-selling")
async def get_best_selling_products(limit: int = 5):
    """Get best selling products"""
    try:
        products = await product_service.get_best_selling_products(limit)
        return {
            "products": products,
            "count": len(products),
            "source": "local"
        }
    except Exception as e:
        logger.error(f"Error getting best selling products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting best selling products")

@router.get("/products/{product_id}")
async def get_product_details(product_id: str):
    """Get detailed information about a specific product"""
    try:
        product = product_service.get_product_details(product_id)
        if product:
            return {"product": product, "source": "local"}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting product details")

@router.get("/test-connection")
async def test_connection():
    """Test connection to local data source"""
    try:
        products = product_service.get_all_products(limit=1)
        success = len(products) > 0
        return {
            "success": success,
            "message": "Local data source test completed",
            "source": "local",
            "products_count": len(product_service.local_service.products)
        }
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        return {
            "success": False,
            "message": f"Local data source test failed: {str(e)}",
            "source": "local"
        } 