import logging
import requests
import json
import random
from typing import List, Dict, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class ExternalProductService:
    """
    Service untuk mengambil data produk dari FakeStoreAPI (fokus utama)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Timeout untuk request
        self.timeout = 10
        
        # Fallback data jika API gagal
        self.fallback_products = self._load_fallback_data()
    
    def _load_fallback_data(self) -> List[Dict]:
        """Load fallback data jika API gagal"""
        return [
            {
                "id": "fallback_1",
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
                    "shop_name": "Apple Store Indonesia"
                }
            },
            {
                "id": "fallback_2",
                "name": "MacBook Pro 14 inch",
                "category": "Laptop",
                "brand": "Apple",
                "price": 35000000,
                "currency": "IDR",
                "description": "MacBook Pro dengan chip M3 Pro, 14 inch Liquid Retina XDR display, dan performa luar biasa",
                "specifications": {
                    "rating": 4.9,
                    "sold": 890,
                    "stock": 30,
                    "condition": "Baru",
                    "shop_location": "Jakarta",
                    "shop_name": "Apple Store Indonesia"
                }
            }
        ]
    
    def search_products_fakestoreapi(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search products menggunakan FakeStoreAPI (gratis, tidak perlu API key)
        """
        try:
            logger.info(f"Searching products with keyword: {keyword} using FakeStoreAPI")
            
            # FakeStoreAPI tidak punya search endpoint, jadi ambil semua dan filter
            url = "https://fakestoreapi.com/products"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            products = response.json()
            logger.info(f"Retrieved {len(products)} products from FakeStoreAPI")
            
            # Filter berdasarkan keyword
            filtered_products = []
            keyword_lower = keyword.lower()
            
            for product in products:
                title = product.get('title', '').lower()
                description = product.get('description', '').lower()
                category = product.get('category', '').lower()
                
                if (keyword_lower in title or 
                    keyword_lower in description or
                    keyword_lower in category):
                    filtered_products.append(product)
            
            logger.info(f"Filtered to {len(filtered_products)} products matching '{keyword}'")
            
            # Transform ke format kita
            transformed_products = []
            for product in filtered_products[:limit]:
                transformed_product = {
                    "id": str(product.get('id')),
                    "name": product.get('title', ''),
                    "category": product.get('category', ''),
                    "brand": "Unknown",  # FakeStoreAPI tidak punya brand
                    "price": float(product.get('price', 0)) * 15000,  # Convert USD ke IDR
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
            
            logger.info(f"Successfully transformed {len(transformed_products)} products")
            return transformed_products
            
        except Exception as e:
            logger.error(f"Error searching products with FakeStoreAPI: {str(e)}")
            return []
    
    def search_products(self, keyword: str, limit: int = 10, source: str = "fakestoreapi") -> List[Dict]:
        """
        Search products - fokus pada FakeStoreAPI
        source: "fakestoreapi", "fallback"
        """
        try:
            logger.info(f"Searching products with keyword: {keyword}, source: {source}")
            
            if source == "fakestoreapi":
                products = self.search_products_fakestoreapi(keyword, limit)
                if products:
                    logger.info(f"Successfully found {len(products)} products from FakeStoreAPI")
                    return products
                else:
                    logger.warning("No products found from FakeStoreAPI, using fallback")
                    return self.fallback_products[:limit]
            
            elif source == "fallback":
                logger.info("Using fallback data")
                return self.fallback_products[:limit]
            
            else:
                logger.error(f"Unknown source: {source}")
                return self.fallback_products[:limit]
                
        except Exception as e:
            logger.error(f"Error in search_products: {str(e)}")
            return self.fallback_products[:limit]
    
    def get_product_details(self, product_id: str, source: str = "fakestoreapi") -> Optional[Dict]:
        """
        Get detail produk berdasarkan ID
        """
        try:
            logger.info(f"Getting product details for ID: {product_id}, source: {source}")
            
            if source == "fakestoreapi":
                try:
                    url = f"https://fakestoreapi.com/products/{product_id}"
                    response = self.session.get(url, timeout=self.timeout)
                    response.raise_for_status()
                    
                    product = response.json()
                    return {
                        "id": str(product.get('id')),
                        "name": product.get('title', ''),
                        "category": product.get('category', ''),
                        "brand": "Unknown",
                        "price": float(product.get('price', 0)) * 15000,
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
                except Exception as e:
                    logger.warning(f"Failed to get product details from FakeStoreAPI: {str(e)}")
            
            # Fallback ke data lokal
            for product in self.fallback_products:
                if product.get('id') == product_id:
                    return product
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting product details: {str(e)}")
            return None
    
    def get_categories(self) -> List[str]:
        """
        Get daftar kategori produk dari FakeStoreAPI
        """
        try:
            logger.info("Getting categories from FakeStoreAPI")
            url = "https://fakestoreapi.com/products/categories"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            categories = response.json()
            logger.info(f"Retrieved {len(categories)} categories from FakeStoreAPI")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            # Return default categories
            return [
                "men's clothing", "women's clothing", "jewelery", 
                "electronics", "Smartphone", "Laptop", "Tablet"
            ]
    
    def get_brands(self) -> List[str]:
        """Get semua brand yang tersedia"""
        try:
            logger.info("Getting brands from FakeStoreAPI")
            
            # Ambil semua produk untuk extract brands
            url = "https://fakestoreapi.com/products"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            products = response.json()
            
            # Extract unique categories sebagai brands (karena FakeStoreAPI tidak punya brand)
            brands = list(set([product.get('category', 'Unknown') for product in products]))
            brands.sort()
            
            logger.info(f"Found {len(brands)} brands/categories")
            return brands
            
        except Exception as e:
            logger.error(f"Error getting brands: {str(e)}")
            return ["Unknown"]
    
    def get_products(self, limit: int = 10) -> List[Dict]:
        """Get semua produk (alias untuk search_products dengan keyword kosong)"""
        return self.search_products("", limit)
    
    def get_top_rated_products(self, limit: int = 5) -> List[Dict]:
        """Get produk dengan rating tertinggi"""
        try:
            logger.info(f"Getting top rated products, limit: {limit}")
            
            # Ambil semua produk dari FakeStoreAPI
            products = self.search_products_fakestoreapi("", limit * 2)  # Ambil lebih banyak untuk sorting
            
            # Sort berdasarkan rating
            sorted_products = sorted(products, key=lambda x: x.get('specifications', {}).get('rating', 0), reverse=True)
            
            logger.info(f"Returning {min(limit, len(sorted_products))} top rated products")
            return sorted_products[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top rated products: {str(e)}")
            return self.fallback_products[:limit]
    
    def get_best_selling_products(self, limit: int = 5) -> List[Dict]:
        """Get produk dengan penjualan tertinggi"""
        try:
            logger.info(f"Getting best selling products, limit: {limit}")
            
            # Ambil semua produk dari FakeStoreAPI
            products = self.search_products_fakestoreapi("", limit * 2)  # Ambil lebih banyak untuk sorting
            
            # Sort berdasarkan sold count
            sorted_products = sorted(products, key=lambda x: x.get('specifications', {}).get('sold', 0), reverse=True)
            
            logger.info(f"Returning {min(limit, len(sorted_products))} best selling products")
            return sorted_products[:limit]
            
        except Exception as e:
            logger.error(f"Error getting best selling products: {str(e)}")
            return self.fallback_products[:limit]
    
    def test_connection(self) -> bool:
        """
        Test koneksi ke FakeStoreAPI
        """
        try:
            logger.info("Testing connection to FakeStoreAPI")
            url = "https://fakestoreapi.com/products"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            products = response.json()
            logger.info(f"Connection test successful, found {len(products)} products")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False 