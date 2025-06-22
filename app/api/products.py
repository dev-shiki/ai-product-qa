from fastapi import APIRouter, HTTPException
from app.services.product_data_service import ProductDataService
from app.models.product import ProductResponse
from typing import List, Optional

router = APIRouter()
product_service = ProductDataService()

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    limit: Optional[int] = 20,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Get products from local data source"""
    try:
        products = await product_service.get_products(
            limit=limit,
            category=category,
            search=search
        )
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories():
    """Get available product categories"""
    try:
        categories = await product_service.get_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_products(query: str, limit: Optional[int] = 10):
    """Search products by query"""
    try:
        products = await product_service.search_products(query, limit)
        return {"products": products, "query": query, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-rated")
async def get_top_rated_products(limit: Optional[int] = 10):
    """Get top rated products"""
    try:
        products = await product_service.get_top_rated_products(limit)
        return {"products": products, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/best-selling")
async def get_best_selling_products(limit: Optional[int] = 10):
    """Get best selling products"""
    try:
        products = await product_service.get_best_selling_products(limit)
        return {"products": products, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brands")
async def get_brands():
    """Get available product brands"""
    try:
        brands = product_service.get_brands()
        return {"brands": brands, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category}")
async def get_products_by_category(category: str, limit: Optional[int] = 20):
    """Get products by category"""
    try:
        products = product_service.get_products_by_category(category, limit)
        return {"products": products, "category": category, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brand/{brand}")
async def get_products_by_brand(brand: str, limit: Optional[int] = 20):
    """Get products by brand"""
    try:
        products = product_service.get_products_by_brand(brand, limit)
        return {"products": products, "brand": brand, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}")
async def get_product_details(product_id: str):
    """Get product details by ID"""
    try:
        product = product_service.get_product_details(product_id)
        if product:
            return {"product": product, "source": "local"}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 