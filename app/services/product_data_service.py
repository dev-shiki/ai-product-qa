import logging
import requests
import json
import random
from typing import List, Dict, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class ProductDataService:
    """
    Service untuk mengambil data produk dari berbagai sumber eksternal
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Mock data untuk fallback
        self.mock_products = self._load_mock_data()
    
    def _load_mock_data(self) -> List[Dict]:
        """Load mock product data"""
        return [
            {
                "id": "1",
                "name": "iPhone 15 Pro Max",
                "category": "Smartphone",
                "brand": "Apple",
                "price": 25000000,
                "currency": "IDR",
                "description": "iPhone 15 Pro Max dengan chip A17 Pro, kamera 48MP, dan layar 6.7 inch Super Retina XDR",
                "specifications": {
                    "rating": 4.8,
                    "sold": 1250,
                    "stock": 50,
                    "condition": "Baru",
                    "shop_location": "Jakarta",
                    "shop_name": "Apple Store Indonesia",
                    "storage": "256GB",
                    "color": "Titanium Natural",
                    "warranty": "1 Tahun"
                },
                "images": ["https://example.com/iphone15.jpg"],
                "url": "https://shopee.co.id/iphone-15-pro-max"
            },
            {
                "id": "2", 
                "name": "Samsung Galaxy S24 Ultra",
                "category": "Smartphone",
                "brand": "Samsung",
                "price": 22000000,
                "currency": "IDR",
                "description": "Samsung Galaxy S24 Ultra dengan S Pen, kamera 200MP, dan AI features",
                "specifications": {
                    "rating": 4.7,
                    "sold": 980,
                    "stock": 35,
                    "condition": "Baru",
                    "shop_location": "Surabaya",
                    "shop_name": "Samsung Store",
                    "storage": "512GB",
                    "color": "Titanium Gray",
                    "warranty": "1 Tahun"
                },
                "images": ["https://example.com/s24-ultra.jpg"],
                "url": "https://shopee.co.id/samsung-s24-ultra"
            },
            {
                "id": "3",
                "name": "MacBook Pro 14 inch M3",
                "category": "Laptop",
                "brand": "Apple",
                "price": 35000000,
                "currency": "IDR",
                "description": "MacBook Pro dengan chip M3, layar 14 inch Liquid Retina XDR, dan performa tinggi",
                "specifications": {
                    "rating": 4.9,
                    "sold": 450,
                    "stock": 25,
                    "condition": "Baru",
                    "shop_location": "Jakarta",
                    "shop_name": "Apple Store Indonesia",
                    "storage": "1TB",
                    "color": "Space Gray",
                    "warranty": "1 Tahun"
                },
                "images": ["https://example.com/macbook-pro.jpg"],
                "url": "https://shopee.co.id/macbook-pro-m3"
            },
            {
                "id": "4",
                "name": "AirPods Pro 2nd Gen",
                "category": "Audio",
                "brand": "Apple",
                "price": 4500000,
                "currency": "IDR",
                "description": "AirPods Pro dengan Active Noise Cancellation dan Spatial Audio",
                "specifications": {
                    "rating": 4.6,
                    "sold": 2100,
                    "stock": 100,
                    "condition": "Baru",
                    "shop_location": "Bandung",
                    "shop_name": "Apple Store Indonesia",
                    "color": "White",
                    "warranty": "1 Tahun"
                },
                "images": ["https://example.com/airpods-pro.jpg"],
                "url": "https://shopee.co.id/airpods-pro-2"
            },
            {
                "id": "5",
                "name": "iPad Air 5th Gen",
                "category": "Tablet",
                "brand": "Apple",
                "price": 12000000,
                "currency": "IDR",
                "description": "iPad Air dengan chip M1, layar 10.9 inch Liquid Retina, dan Apple Pencil support",
                "specifications": {
                    "rating": 4.5,
                    "sold": 750,
                    "stock": 40,
                    "condition": "Baru",
                    "shop_location": "Medan",
                    "shop_name": "Apple Store Indonesia",
                    "storage": "256GB",
                    "color": "Blue",
                    "warranty": "1 Tahun"
                },
                "images": ["https://example.com/ipad-air.jpg"],
                "url": "https://shopee.co.id/ipad-air-5"
            }
        ]
    
    async def search_products(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search products with automatic fallback"""
        try:
            # Try FakeStoreAPI first
            products = self.search_products_fakestoreapi(keyword, limit)
            
            # If no products found, use mock data
            if not products:
                products = self.search_products_mock(keyword, limit)
            
            return products[:limit]
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return self.search_products_mock(keyword, limit)
    
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
            return self.mock_products[:limit]
    
    async def get_categories(self) -> List[str]:
        """Get available categories"""
        return ["Smartphone", "Laptop", "Audio", "Tablet", "Gaming", "Fashion", "Health", "Home"]
    
    async def get_top_rated_products(self, limit: int = 10) -> List[Dict]:
        """Get top rated products"""
        try:
            products = self.search_products_fakestoreapi("", limit * 2)
            if not products:
                products = self.mock_products
            
            # Sort by rating
            products.sort(key=lambda x: x.get('specifications', {}).get('rating', 0), reverse=True)
            return products[:limit]
        except Exception as e:
            logger.error(f"Error getting top rated products: {str(e)}")
            return self.mock_products[:limit]
    
    async def get_best_selling_products(self, limit: int = 10) -> List[Dict]:
        """Get best selling products"""
        try:
            products = self.search_products_fakestoreapi("", limit * 2)
            if not products:
                products = self.mock_products
            
            # Sort by sold count
            products.sort(key=lambda x: x.get('specifications', {}).get('sold', 0), reverse=True)
            return products[:limit]
        except Exception as e:
            logger.error(f"Error getting best selling products: {str(e)}")
            return self.mock_products[:limit]
    
    def search_products_fakestoreapi(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search products using FakeStoreAPI"""
        try:
            logger.info(f"Searching products with keyword: {keyword} using FakeStoreAPI")
            
            url = "https://fakestoreapi.com/products"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            products = response.json()
            
            # Filter by keyword if provided
            if keyword:
                keyword_lower = keyword.lower()
                products = [
                    p for p in products 
                    if (keyword_lower in p.get('title', '').lower() or 
                        keyword_lower in p.get('description', '').lower() or
                        keyword_lower in p.get('category', '').lower())
                ]
            
            # Transform to our format
            transformed_products = []
            for product in products[:limit]:
                transformed_product = {
                    "id": str(product.get('id')),
                    "name": product.get('title', ''),
                    "category": product.get('category', ''),
                    "brand": "Unknown",
                    "price": float(product.get('price', 0)) * 15000,  # Convert USD to IDR
                    "currency": "IDR",
                    "description": product.get('description', ''),
                    "specifications": {
                        "rating": float(product.get('rating', {}).get('rate', 0)),
                        "sold": random.randint(100, 2000),
                        "stock": random.randint(10, 100),
                        "condition": "Baru",
                        "shop_location": "Indonesia",
                        "shop_name": "Online Store"
                    },
                    "images": [product.get('image', '')],
                    "url": f"https://fakestoreapi.com/products/{product.get('id')}"
                }
                transformed_products.append(transformed_product)
            
            logger.info(f"Found {len(transformed_products)} products from FakeStoreAPI")
            return transformed_products
            
        except Exception as e:
            logger.error(f"Error searching products with FakeStoreAPI: {str(e)}")
            return []
    
    def search_products_mock(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search products in mock data"""
        try:
            keyword_lower = keyword.lower()
            filtered_products = []
            
            for product in self.mock_products:
                if (keyword_lower in product.get('name', '').lower() or 
                    keyword_lower in product.get('description', '').lower() or
                    keyword_lower in product.get('category', '').lower() or
                    keyword_lower in product.get('brand', '').lower()):
                    filtered_products.append(product)
            
            return filtered_products[:limit]
        except Exception as e:
            logger.error(f"Error searching mock products: {str(e)}")
            return self.mock_products[:limit]
    
    def get_products_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Get products by category"""
        try:
            category_lower = category.lower()
            filtered_products = []
            
            # Try FakeStoreAPI first
            products = self.search_products_fakestoreapi("", limit * 2)
            for product in products:
                if category_lower in product.get('category', '').lower():
                    filtered_products.append(product)
            
            # If no products found, use mock data
            if not filtered_products:
                for product in self.mock_products:
                    if category_lower in product.get('category', '').lower():
                        filtered_products.append(product)
            
            return filtered_products[:limit]
        except Exception as e:
            logger.error(f"Error getting products by category: {str(e)}")
            return self.mock_products[:limit]
    
    def get_all_products(self, limit: int = 20) -> List[Dict]:
        """Get all products"""
        try:
            products = self.search_products_fakestoreapi("", limit)
            if not products:
                products = self.mock_products
            return products[:limit]
        except Exception as e:
            logger.error(f"Error getting all products: {str(e)}")
            return self.mock_products[:limit] 