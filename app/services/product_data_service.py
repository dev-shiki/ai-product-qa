import logging
from typing import List, Dict, Optional
from app.services.local_product_service import LocalProductService

logger = logging.getLogger(__name__)

class ProductDataService:
    """
    Service untuk mengambil data produk dari sumber lokal yang reliable
    """
    
    def __init__(self):
        # Use LocalProductService as primary data source
        self.local_service = LocalProductService()
        logger.info("ProductDataService initialized with LocalProductService")
    
    async def search_products(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search products using local data"""
        try:
            logger.info(f"Searching products with keyword: {keyword}")
            # Use awaitable wrapper for sync method
            import asyncio
            loop = asyncio.get_event_loop()
            products = await loop.run_in_executor(None, self.local_service.search_products, keyword, limit)
            logger.info(f"Found {len(products)} products for keyword: {keyword}")
            return products
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    async def get_products(self, limit: int = 20, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
        """Get products with optional filtering"""
        try:
            if search:
                return await self.search_products(search, limit)
            elif category:
                return self.get_products_by_category(category, limit)
            else:
                return self.get_all_products(limit)
        except Exception as e:
            logger.error(f"Error getting products: {str(e)}")
            return self.local_service.get_products(limit)
    
    async def get_categories(self) -> List[str]:
        """Get available categories"""
        try:
            return self.local_service.get_categories()
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []
    
    async def get_top_rated_products(self, limit: int = 10) -> List[Dict]:
        """Get top rated products"""
        try:
            return self.local_service.get_top_rated_products(limit)
        except Exception as e:
            logger.error(f"Error getting top rated products: {str(e)}")
            return []
    
    async def get_best_selling_products(self, limit: int = 10) -> List[Dict]:
        """Get best selling products"""
        try:
            return self.local_service.get_best_selling_products(limit)
        except Exception as e:
            logger.error(f"Error getting best selling products: {str(e)}")
            return []
    
    def get_products_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Get products by category"""
        try:
            return self.local_service.get_products_by_category(category)[:limit]
        except Exception as e:
            logger.error(f"Error getting products by category: {str(e)}")
            return []
    
    def get_all_products(self, limit: int = 20) -> List[Dict]:
        """Get all products"""
        try:
            return self.local_service.get_products(limit)
        except Exception as e:
            logger.error(f"Error getting all products: {str(e)}")
            return []
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get product details by ID"""
        try:
            return self.local_service.get_product_details(product_id)
        except Exception as e:
            logger.error(f"Error getting product details: {str(e)}")
            return None
    
    def get_brands(self) -> List[str]:
        """Get available brands"""
        try:
            return self.local_service.get_brands()
        except Exception as e:
            logger.error(f"Error getting brands: {str(e)}")
            return []
    
    def get_products_by_brand(self, brand: str, limit: int = 10) -> List[Dict]:
        """Get products by brand"""
        try:
            return self.local_service.get_products_by_brand(brand)[:limit]
        except Exception as e:
            logger.error(f"Error getting products by brand: {str(e)}")
            return []
    
    async def smart_search_products(self, keyword: str = '', category: str = None, max_price: int = None, limit: int = 5):
        """
        Hybrid fallback search: gunakan LocalProductService.smart_search_products secara async.
        Return: (list produk, pesan)
        """
        import asyncio
        loop = asyncio.get_event_loop()
        products, message = await loop.run_in_executor(
            None, self.local_service.smart_search_products, keyword, category, max_price, limit
        )
        return products, message 