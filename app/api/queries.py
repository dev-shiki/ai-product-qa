import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.product_data_service import ProductDataService
from app.services.ai_service import AIService

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

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Ask a question about products and get recommendations"""
    try:
        # Get AI response
        ai_response = await ai_service.get_response(request.question)
        
        # Get relevant products
        products = await product_service.search_products(request.question, limit=5)
        
        return QueryResponse(
            answer=ai_response,
            products=products,
            question=request.question
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
        "Produk skincare untuk kulit berminyak",
        "Headphone wireless dengan kualitas bagus",
        "Sepatu olahraga yang nyaman",
        "Produk untuk rumah tangga",
        "Gadget untuk produktivitas"
    ]
    return {"suggestions": suggestions}

@router.get("/categories")
def get_categories():
    """Get available product categories"""
    try:
        categories = product_service.get_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting categories")

@router.get("/brands")
def get_brands():
    """Get available product brands"""
    try:
        brands = product_service.get_brands()
        return {"brands": brands}
    except Exception as e:
        logger.error(f"Error getting brands: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting brands")

@router.get("/products/search")
def search_products(keyword: str, limit: int = 10, source: str = "fakestoreapi"):
    """Search products directly"""
    try:
        products = product_service.search_products(keyword, limit, source)
        return {
            "products": products,
            "count": len(products),
            "keyword": keyword,
            "source": source
        }
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching products")

@router.get("/products/category/{category}")
def get_products_by_category(category: str, source: str = "fakestoreapi"):
    """Get products by category"""
    try:
        # Search for products in the category
        products = product_service.search_products(category, limit=20, source=source)
        # Filter by exact category match
        filtered_products = [p for p in products if category.lower() in p.get('category', '').lower()]
        return {
            "products": filtered_products,
            "count": len(filtered_products),
            "category": category,
            "source": source
        }
    except Exception as e:
        logger.error(f"Error getting products by category: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting products by category")

@router.get("/products/brand/{brand}")
def get_products_by_brand(brand: str, source: str = "fakestoreapi"):
    """Get products by brand"""
    try:
        # Search for products with the brand
        products = product_service.search_products(brand, limit=20, source=source)
        # Filter by exact brand match
        filtered_products = [p for p in products if brand.lower() in p.get('brand', '').lower()]
        return {
            "products": filtered_products,
            "count": len(filtered_products),
            "brand": brand,
            "source": source
        }
    except Exception as e:
        logger.error(f"Error getting products by brand: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting products by brand")

@router.get("/products/top-rated")
def get_top_rated_products(limit: int = 5, source: str = "fakestoreapi"):
    """Get top rated products"""
    try:
        # Get products and sort by rating
        products = product_service.search_products("", limit=50, source=source)
        sorted_products = sorted(
            products, 
            key=lambda x: x.get('specifications', {}).get('rating', 0), 
            reverse=True
        )
        return {
            "products": sorted_products[:limit],
            "count": len(sorted_products[:limit]),
            "source": source
        }
    except Exception as e:
        logger.error(f"Error getting top rated products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting top rated products")

@router.get("/products/best-selling")
def get_best_selling_products(limit: int = 5, source: str = "fakestoreapi"):
    """Get best selling products"""
    try:
        # Get products and sort by sold count
        products = product_service.search_products("", limit=50, source=source)
        sorted_products = sorted(
            products, 
            key=lambda x: x.get('specifications', {}).get('sold', 0), 
            reverse=True
        )
        return {
            "products": sorted_products[:limit],
            "count": len(sorted_products[:limit]),
            "source": source
        }
    except Exception as e:
        logger.error(f"Error getting best selling products: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting best selling products")

@router.get("/products/{product_id}")
def get_product_details(product_id: str, source: str = "fakestoreapi"):
    """Get detailed information about a specific product"""
    try:
        product = product_service.get_product_details(product_id, source)
        if product:
            return {"product": product, "source": source}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting product details")

@router.get("/test-connection")
def test_connection():
    """Test connection to FakeStoreAPI"""
    try:
        success = product_service.test_connection()
        return {
            "success": success,
            "message": "Connection test completed",
            "source": "fakestoreapi"
        }
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "source": "fakestoreapi"
        } 