import logging
import json
import random
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LocalProductService:
    """
    Service untuk data produk lokal yang reliable dan tidak bergantung pada API eksternal
    """
    
    def __init__(self):
        self.products = self._load_local_products()
        logger.info(f"Loaded {len(self.products)} local products")
    
    def _load_local_products(self) -> List[Dict]:
        """Load produk dari data lokal"""
        return [
            {
                "id": "1",
                "name": "iPhone 15 Pro Max",
                "category": "Smartphone",
                "brand": "Apple",
                "price": 25000000,
                "currency": "IDR",
                "description": "iPhone 15 Pro Max dengan chip A17 Pro, kamera 48MP, dan layar 6.7 inch Super Retina XDR. Dilengkapi dengan titanium design dan performa gaming yang luar biasa.",
                "specifications": {
                    "rating": 4.8,
                    "sold": 1250,
                    "stock": 50,
                    "condition": "Baru",
                    "shop_location": "Jakarta",
                    "shop_name": "Apple Store Indonesia",
                    "storage": "256GB",
                    "color": "Titanium Natural",
                    "warranty": "1 Tahun",
                    "processor": "A17 Pro",
                    "camera": "48MP Main + 12MP Ultra Wide + 12MP Telephoto",
                    "display": "6.7 inch Super Retina XDR"
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
                "description": "Samsung Galaxy S24 Ultra dengan S Pen, kamera 200MP, dan AI features canggih. Dilengkapi dengan Snapdragon 8 Gen 3 dan layar AMOLED 6.8 inch.",
                "specifications": {
                    "rating": 4.7,
                    "sold": 980,
                    "stock": 35,
                    "condition": "Baru",
                    "shop_location": "Surabaya",
                    "shop_name": "Samsung Store",
                    "storage": "512GB",
                    "color": "Titanium Gray",
                    "warranty": "1 Tahun",
                    "processor": "Snapdragon 8 Gen 3",
                    "camera": "200MP Main + 12MP Ultra Wide + 50MP Telephoto + 10MP Telephoto",
                    "display": "6.8 inch Dynamic AMOLED 2X"
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
                "description": "MacBook Pro dengan chip M3, layar 14 inch Liquid Retina XDR, dan performa tinggi untuk profesional. Cocok untuk video editing, programming, dan gaming.",
                "specifications": {
                    "rating": 4.9,
                    "sold": 450,
                    "stock": 25,
                    "condition": "Baru",
                    "shop_location": "Jakarta",
                    "shop_name": "Apple Store Indonesia",
                    "storage": "1TB",
                    "color": "Space Gray",
                    "warranty": "1 Tahun",
                    "processor": "Apple M3",
                    "ram": "16GB Unified Memory",
                    "display": "14 inch Liquid Retina XDR"
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
                "description": "AirPods Pro dengan Active Noise Cancellation dan Spatial Audio. Dilengkapi dengan chip H2 untuk performa audio yang lebih baik dan fitur Find My.",
                "specifications": {
                    "rating": 4.6,
                    "sold": 2100,
                    "stock": 100,
                    "condition": "Baru",
                    "shop_location": "Bandung",
                    "shop_name": "Apple Store Indonesia",
                    "color": "White",
                    "warranty": "1 Tahun",
                    "battery": "6 jam dengan ANC, 30 jam dengan case",
                    "features": "Active Noise Cancellation, Spatial Audio, Find My"
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
                "description": "iPad Air dengan chip M1, layar 10.9 inch Liquid Retina, dan Apple Pencil support. Cocok untuk kreativitas, note-taking, dan entertainment.",
                "specifications": {
                    "rating": 4.5,
                    "sold": 750,
                    "stock": 40,
                    "condition": "Baru",
                    "shop_location": "Medan",
                    "shop_name": "Apple Store Indonesia",
                    "storage": "256GB",
                    "color": "Blue",
                    "warranty": "1 Tahun",
                    "processor": "Apple M1",
                    "display": "10.9 inch Liquid Retina",
                    "features": "Apple Pencil support, Magic Keyboard support"
                },
                "images": ["https://example.com/ipad-air.jpg"],
                "url": "https://shopee.co.id/ipad-air-5"
            },
            {
                "id": "6",
                "name": "ASUS ROG Strix G15",
                "category": "Laptop",
                "brand": "ASUS",
                "price": 18000000,
                "currency": "IDR",
                "description": "Laptop gaming ASUS ROG Strix G15 dengan RTX 4060, AMD Ryzen 7, dan layar 15.6 inch 144Hz. Dilengkapi dengan RGB keyboard dan cooling system yang powerful.",
                "specifications": {
                    "rating": 4.4,
                    "sold": 320,
                    "stock": 15,
                    "condition": "Baru",
                    "shop_location": "Jakarta",
                    "shop_name": "ASUS Store",
                    "storage": "512GB SSD",
                    "color": "Black",
                    "warranty": "2 Tahun",
                    "processor": "AMD Ryzen 7 7735HS",
                    "gpu": "NVIDIA RTX 4060 8GB",
                    "ram": "16GB DDR5",
                    "display": "15.6 inch FHD 144Hz"
                },
                "images": ["https://example.com/rog-strix.jpg"],
                "url": "https://shopee.co.id/asus-rog-strix-g15"
            },
            {
                "id": "7",
                "name": "Sony WH-1000XM5",
                "category": "Audio",
                "brand": "Sony",
                "price": 5500000,
                "currency": "IDR",
                "description": "Headphone wireless Sony WH-1000XM5 dengan noise cancellation terbaik di kelasnya. Dilengkapi dengan 30 jam battery life dan quick charge.",
                "specifications": {
                    "rating": 4.8,
                    "sold": 890,
                    "stock": 30,
                    "condition": "Baru",
                    "shop_location": "Surabaya",
                    "shop_name": "Sony Store",
                    "color": "Black",
                    "warranty": "1 Tahun",
                    "battery": "30 jam dengan ANC",
                    "features": "Industry-leading noise cancellation, Quick Charge, Multipoint connection"
                },
                "images": ["https://example.com/sony-wh1000xm5.jpg"],
                "url": "https://shopee.co.id/sony-wh1000xm5"
            },
            {
                "id": "8",
                "name": "Samsung Galaxy Tab S9",
                "category": "Tablet",
                "brand": "Samsung",
                "price": 15000000,
                "currency": "IDR",
                "description": "Samsung Galaxy Tab S9 dengan S Pen, layar AMOLED 11 inch, dan Snapdragon 8 Gen 2. Cocok untuk productivity dan entertainment.",
                "specifications": {
                    "rating": 4.3,
                    "sold": 280,
                    "stock": 20,
                    "condition": "Baru",
                    "shop_location": "Bandung",
                    "shop_name": "Samsung Store",
                    "storage": "256GB",
                    "color": "Graphite",
                    "warranty": "1 Tahun",
                    "processor": "Snapdragon 8 Gen 2",
                    "display": "11 inch Dynamic AMOLED 2X",
                    "features": "S Pen included, DeX mode, Multi-window"
                },
                "images": ["https://example.com/galaxy-tab-s9.jpg"],
                "url": "https://shopee.co.id/samsung-galaxy-tab-s9"
            }
        ]
    
    def search_products(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search products berdasarkan keyword
        """
        try:
            logger.info(f"Searching products with keyword: {keyword}")
            
            keyword_lower = keyword.lower()
            filtered_products = []
            
            for product in self.products:
                # Search in name, description, category, brand, and specifications
                searchable_text = (
                    product.get('name', '') + ' ' +
                    product.get('description', '') + ' ' +
                    product.get('category', '') + ' ' +
                    product.get('brand', '') + ' ' +
                    str(product.get('specifications', {}))
                ).lower()
                
                if keyword_lower in searchable_text:
                    filtered_products.append(product)
            
            # Sort by relevance (exact matches first)
            def relevance_score(product):
                score = 0
                if keyword_lower in product.get('name', '').lower():
                    score += 10
                if keyword_lower in product.get('brand', '').lower():
                    score += 5
                if keyword_lower in product.get('category', '').lower():
                    score += 3
                return score
            
            filtered_products.sort(key=relevance_score, reverse=True)
            
            logger.info(f"Found {len(filtered_products)} products")
            return filtered_products[:limit]
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def get_product_details(self, product_id: str) -> Optional[Dict]:
        """
        Get detail produk berdasarkan ID
        """
        try:
            for product in self.products:
                if product.get('id') == product_id:
                    return product
            return None
        except Exception as e:
            logger.error(f"Error getting product details: {str(e)}")
            return None
    
    def get_categories(self) -> List[str]:
        """
        Get daftar kategori produk
        """
        categories = set()
        for product in self.products:
            categories.add(product.get('category', ''))
        return sorted(list(categories))
    
    def get_brands(self) -> List[str]:
        """
        Get daftar brand produk
        """
        brands = set()
        for product in self.products:
            brands.add(product.get('brand', ''))
        return sorted(list(brands))
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """
        Get produk berdasarkan kategori
        """
        try:
            category_lower = category.lower()
            filtered_products = []
            
            for product in self.products:
                if category_lower in product.get('category', '').lower():
                    filtered_products.append(product)
            
            return filtered_products
        except Exception as e:
            logger.error(f"Error getting products by category: {str(e)}")
            return []
    
    def get_products_by_brand(self, brand: str) -> List[Dict]:
        """
        Get produk berdasarkan brand
        """
        try:
            brand_lower = brand.lower()
            filtered_products = []
            
            for product in self.products:
                if brand_lower in product.get('brand', '').lower():
                    filtered_products.append(product)
            
            return filtered_products
        except Exception as e:
            logger.error(f"Error getting products by brand: {str(e)}")
            return []
    
    def get_top_rated_products(self, limit: int = 5) -> List[Dict]:
        """
        Get produk dengan rating tertinggi
        """
        try:
            sorted_products = sorted(
                self.products, 
                key=lambda x: x.get('specifications', {}).get('rating', 0), 
                reverse=True
            )
            return sorted_products[:limit]
        except Exception as e:
            logger.error(f"Error getting top rated products: {str(e)}")
            return []
    
    def get_best_selling_products(self, limit: int = 5) -> List[Dict]:
        """
        Get produk terlaris
        """
        try:
            sorted_products = sorted(
                self.products, 
                key=lambda x: x.get('specifications', {}).get('sold', 0), 
                reverse=True
            )
            return sorted_products[:limit]
        except Exception as e:
            logger.error(f"Error getting best selling products: {str(e)}")
            return [] 