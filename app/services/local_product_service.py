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
        logger.info(f"Loaded {len(self.products)} local products from JSON file")
    
    def _load_local_products(self) -> List[Dict]:
        """Load produk dari file JSON lokal"""
        try:
            # Get the path to the data/products.json file
            current_dir = Path(__file__).parent.parent.parent
            json_file_path = current_dir / "data" / "products.json"
            
            if not json_file_path.exists():
                logger.error(f"Products JSON file not found at: {json_file_path}")
                return self._get_fallback_products()
            
            # Try different encodings
            encodings = ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(json_file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        # Remove BOM if present
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        
                        data = json.loads(content)
                        products = data.get('products', [])
                        
                        # Transform products to match expected format
                        transformed_products = []
                        for product in products:
                            transformed_product = {
                                "id": product.get('id', ''),
                                "name": product.get('name', ''),
                                "category": product.get('category', ''),
                                "brand": product.get('brand', ''),
                                "price": product.get('price', 0),
                                "currency": product.get('currency', 'IDR'),
                                "description": product.get('description', ''),
                                "specifications": {
                                    "rating": product.get('rating', 0),
                                    "sold": random.randint(100, 2000),  # Add random sold count
                                    "stock": product.get('stock_count', 0),
                                    "condition": "Baru",
                                    "shop_location": "Indonesia",
                                    "shop_name": f"{product.get('brand', 'Unknown')} Store",
                                    **product.get('specifications', {})
                                },
                                "availability": product.get('availability', 'in_stock'),
                                "reviews_count": product.get('reviews_count', 0),
                                "images": [f"https://example.com/{product.get('id', 'product')}.jpg"],
                                "url": f"https://shopee.co.id/{product.get('id', 'product')}"
                            }
                            transformed_products.append(transformed_product)
                        
                        logger.info(f"Successfully loaded {len(transformed_products)} products from JSON file using {encoding} encoding")
                        return transformed_products
                        
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    logger.warning(f"Failed to load with {encoding} encoding: {str(e)}")
                    continue
            
            # If all encodings fail, use fallback
            logger.error("All encoding attempts failed, using fallback products")
            return self._get_fallback_products()
                
        except Exception as e:
            logger.error(f"Error loading products from JSON file: {str(e)}")
            return self._get_fallback_products()
    
    def _get_fallback_products(self) -> List[Dict]:
        """Fallback products if JSON file cannot be loaded"""
        logger.warning("Using fallback products due to JSON file loading error")
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
            
            # Extract price range from keyword
            max_price = self._extract_price_from_keyword(keyword)
            
            for product in self.products:
                product_price = product.get('price', 0)
                
                # Check if product matches price range
                if max_price and product_price <= max_price:
                    filtered_products.append(product)
                    continue
                
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
            
            # Sort by relevance (exact matches first, then by price if budget search)
            def relevance_score(product):
                score = 0
                if keyword_lower in product.get('name', '').lower():
                    score += 10
                if keyword_lower in product.get('brand', '').lower():
                    score += 5
                if keyword_lower in product.get('category', '').lower():
                    score += 3
                
                # For budget searches, prefer lower prices
                if max_price or any(word in keyword_lower for word in ['murah', 'budget', 'hemat', 'terjangkau']):
                    score += (10000000 - product.get('price', 0)) / 1000000  # Higher score for lower prices
                
                return score
            
            filtered_products.sort(key=relevance_score, reverse=True)
            
            logger.info(f"Found {len(filtered_products)} products")
            return filtered_products[:limit]
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def _extract_price_from_keyword(self, keyword: str) -> Optional[int]:
        """
        Extract maximum price from keyword
        """
        try:
            keyword_lower = keyword.lower()
            
            # Common price patterns
            price_patterns = [
                (r'(\d+)\s*juta', lambda x: int(x) * 1000000),
                (r'(\d+)\s*ribu', lambda x: int(x) * 1000),
                (r'rp\s*(\d+)', lambda x: int(x)),
                (r'(\d+)\s*rp', lambda x: int(x)),
                (r'(\d+)\s*k', lambda x: int(x) * 1000),
                (r'(\d+)\s*m', lambda x: int(x) * 1000000),
            ]
            
            import re
            for pattern, converter in price_patterns:
                match = re.search(pattern, keyword_lower)
                if match:
                    return converter(match.group(1))
            
            # Budget keywords
            budget_keywords = {
                'murah': 5000000,  # 5 juta
                'budget': 5000000,
                'hemat': 3000000,  # 3 juta
                'terjangkau': 4000000,  # 4 juta
                'ekonomis': 2000000,  # 2 juta
            }
            
            for word, max_price in budget_keywords.items():
                if word in keyword_lower:
                    return max_price
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting price from keyword: {str(e)}")
            return None
    
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
        """Get produk dengan penjualan tertinggi"""
        try:
            logger.info(f"Getting best selling products, limit: {limit}")
            
            # Sort berdasarkan sold count
            sorted_products = sorted(self.products, key=lambda x: x.get('specifications', {}).get('sold', 0), reverse=True)
            
            logger.info(f"Returning {min(limit, len(sorted_products))} best selling products")
            return sorted_products[:limit]
            
        except Exception as e:
            logger.error(f"Error getting best selling products: {str(e)}")
            return []
    
    def get_products(self, limit: int = 10) -> List[Dict]:
        """Get semua produk"""
        try:
            logger.info(f"Getting all products, limit: {limit}")
            return self.products[:limit]
        except Exception as e:
            logger.error(f"Error getting products: {str(e)}")
            return []
    
    def smart_search_products(self, keyword: str = '', category: str = None, max_price: int = None, limit: int = 5):
        """
        Hybrid fallback search: cari produk sesuai kriteria, lalu fallback bertingkat dengan notifikasi.
        Return: (list produk, pesan)
        """
        keyword_lower = (keyword or '').lower()
        
        # Deteksi permintaan "terbaik"
        is_best_request = 'terbaik' in keyword_lower or 'best' in keyword_lower
        
        # 1. Jika user minta "terbaik" tanpa kategori spesifik
        if is_best_request and not category:
            # Tampilkan produk terbaik secara umum (top 5 berdasarkan rating)
            best_products = sorted(self.products, 
                                 key=lambda x: x.get('specifications', {}).get('rating', 0), 
                                 reverse=True)
            return best_products[:limit], "Berikut produk terbaik berdasarkan rating:"
        
        # 2. Jika user minta "terbaik" dengan kategori spesifik
        if is_best_request and category:
            category_products = [p for p in self.products 
                               if category.lower() in p.get('category', '').lower()]
            if category_products:
                category_products.sort(key=lambda x: x.get('specifications', {}).get('rating', 0), reverse=True)
                return category_products[:limit], f"Berikut {category} terbaik berdasarkan rating:"
            else:
                # Fallback ke produk terbaik secara umum jika kategori tidak ditemukan
                best_products = sorted(self.products, 
                                     key=lambda x: x.get('specifications', {}).get('rating', 0), 
                                     reverse=True)
                return best_products[:limit], f"Tidak ada produk kategori {category}, berikut produk terbaik secara umum:"
        
        # 3. Cari produk yang memenuhi semua kriteria (non-terbaik)
        results = [
            p for p in self.products
            if (not category or category.lower() in p.get('category', '').lower())
            and (not max_price or p.get('price', 0) <= max_price)
            and (not keyword or keyword_lower in (p.get('name', '') + ' ' + p.get('description', '') + ' ' + p.get('category', '') + ' ' + p.get('brand', '') + str(p.get('specifications', {}))).lower())
        ]
        if results:
            return results[:limit], "Berikut produk yang sesuai dengan kriteria Anda."

        # 4. Jika tidak ada, cari produk di kategori yang sama (tanpa filter harga)
        if category:
            category_results = [
                p for p in self.products
                if category.lower() in p.get('category', '').lower()
            ]
            if category_results:
                category_results.sort(key=lambda x: x.get('price', 0))
                return category_results[:limit], "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

        # 5. Jika tetap tidak ada, tampilkan produk lain yang sesuai budget
        if max_price:
            budget_results = [
                p for p in self.products
                if p.get('price', 0) <= max_price
            ]
            if budget_results:
                return budget_results[:limit], "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

        # 6. Jika tetap tidak ada, tampilkan produk terpopuler/terlaris
        popular_results = sorted(self.products, key=lambda x: x.get('specifications', {}).get('sold', 0), reverse=True)
        return popular_results[:limit], "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." 