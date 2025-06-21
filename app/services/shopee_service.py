import logging
from typing import List, Dict, Optional
from datetime import datetime
import time
import random
import traceback
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

# Setup logging
logger = logging.getLogger(__name__)

class ShopeeService:
    def __init__(self):
        self.base_url = "https://shopee.co.id"
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    def _init_browser(self):
        """Initialize Playwright browser"""
        try:
            logger.info("Starting Playwright")
            self.playwright = sync_playwright().start()
            
            logger.info("Launching browser")
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer'
                ]
            )
            
            logger.info("Creating browser context")
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_https_errors=True
            )
            
            logger.info("Creating new page")
            self.page = self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(30000)  # 30 seconds
            
            logger.info("Successfully initialized Playwright browser")
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            raise

    def __enter__(self):
        self._init_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def search_products(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search products from Shopee using Playwright
        """
        try:
            if not self.page:
                self._init_browser()

            logger.info(f"Searching products with keyword: {keyword}")
            
            # Construct search URL
            search_url = f"{self.base_url}/search?keyword={keyword}"
            logger.info(f"Navigating to: {search_url}")
            
            # Load the page
            self.page.goto(search_url, wait_until="networkidle")
            
            # Wait for products to load
            logger.info("Waiting for products to load")
            try:
                self.page.wait_for_selector("[data-sqe='item']", timeout=30000)
            except PlaywrightTimeoutError:
                logger.warning("Timeout waiting for products, trying to continue anyway")
            
            # Add small delay to ensure all content is loaded
            self.page.wait_for_timeout(5000)
            
            # Get page content and parse with BeautifulSoup
            logger.info("Getting page content")
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            product_elements = soup.select("[data-sqe='item']")[:limit]
            
            logger.info(f"Found {len(product_elements)} product elements")
            
            # Transform data to our product format
            products = []
            for element in product_elements:
                try:
                    # Extract product information
                    name = element.select_one(".ie3A\+n").text.strip()
                    price_element = element.select_one(".ZEgDH9")
                    price = float(price_element.text.strip().replace("Rp", "").replace(".", "")) if price_element else 0
                    
                    # Get product link for more details
                    product_link = element.select_one("a")["href"]
                    product_url = f"{self.base_url}{product_link}"
                    
                    logger.info(f"Getting details for product: {name}")
                    
                    # Get additional details
                    self.page.goto(product_url, wait_until="networkidle")
                    try:
                        self.page.wait_for_selector(".product-detail", timeout=30000)
                    except PlaywrightTimeoutError:
                        logger.warning(f"Timeout waiting for product details: {name}")
                        continue
                    
                    self.page.wait_for_timeout(2000)
                    
                    detail_content = self.page.content()
                    detail_soup = BeautifulSoup(detail_content, 'html.parser')
                    
                    # Extract additional information
                    description = detail_soup.select_one(".product-detail").text.strip() if detail_soup.select_one(".product-detail") else ""
                    brand = detail_soup.select_one(".product-brand").text.strip() if detail_soup.select_one(".product-brand") else ""
                    category = detail_soup.select_one(".product-category").text.strip() if detail_soup.select_one(".product-category") else ""
                    
                    product = {
                        "name": name,
                        "category": category,
                        "brand": brand,
                        "price": price,
                        "currency": "IDR",
                        "description": description,
                        "specifications": {
                            "rating": float(detail_soup.select_one(".rating-score").text.strip()) if detail_soup.select_one(".rating-score") else 0,
                            "sold": int(detail_soup.select_one(".sold-count").text.strip().replace("Terjual", "").replace("+", "")) if detail_soup.select_one(".sold-count") else 0,
                            "stock": int(detail_soup.select_one(".stock-count").text.strip()) if detail_soup.select_one(".stock-count") else 0,
                            "condition": detail_soup.select_one(".condition").text.strip() if detail_soup.select_one(".condition") else "",
                            "shop_location": detail_soup.select_one(".shop-location").text.strip() if detail_soup.select_one(".shop-location") else "",
                            "shop_name": detail_soup.select_one(".shop-name").text.strip() if detail_soup.select_one(".shop-name") else ""
                        }
                    }
                    products.append(product)
                    logger.info(f"Successfully processed product: {name}")
                    
                except Exception as e:
                    logger.error(f"Error processing product: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
            
            logger.info(f"Found {len(products)} products")
            return products
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_product_details(self, product_url: str) -> Optional[Dict]:
        """
        Get detailed information about a specific product
        """
        try:
            if not self.page:
                self._init_browser()

            logger.info(f"Getting details for product: {product_url}")
            
            # Load the product page
            self.page.goto(product_url, wait_until="networkidle")
            
            # Wait for product details to load
            try:
                self.page.wait_for_selector(".product-detail", timeout=30000)
            except PlaywrightTimeoutError:
                logger.warning("Timeout waiting for product details")
            
            # Add small delay to ensure all content is loaded
            self.page.wait_for_timeout(5000)
            
            # Get page content and parse
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract product information
            name = soup.select_one(".product-name").text.strip() if soup.select_one(".product-name") else ""
            price_element = soup.select_one(".product-price")
            price = float(price_element.text.strip().replace("Rp", "").replace(".", "")) if price_element else 0
            description = soup.select_one(".product-detail").text.strip() if soup.select_one(".product-detail") else ""
            brand = soup.select_one(".product-brand").text.strip() if soup.select_one(".product-brand") else ""
            category = soup.select_one(".product-category").text.strip() if soup.select_one(".product-category") else ""
            
            product = {
                "name": name,
                "category": category,
                "brand": brand,
                "price": price,
                "currency": "IDR",
                "description": description,
                "specifications": {
                    "rating": float(soup.select_one(".rating-score").text.strip()) if soup.select_one(".rating-score") else 0,
                    "sold": int(soup.select_one(".sold-count").text.strip().replace("Terjual", "").replace("+", "")) if soup.select_one(".sold-count") else 0,
                    "stock": int(soup.select_one(".stock-count").text.strip()) if soup.select_one(".stock-count") else 0,
                    "condition": soup.select_one(".condition").text.strip() if soup.select_one(".condition") else "",
                    "shop_location": soup.select_one(".shop-location").text.strip() if soup.select_one(".shop-location") else "",
                    "shop_name": soup.select_one(".shop-name").text.strip() if soup.select_one(".shop-name") else "",
                    "attributes": [attr.text.strip() for attr in soup.select(".product-attributes .attribute")] if soup.select(".product-attributes .attribute") else [],
                    "tier_variations": [var.text.strip() for var in soup.select(".product-variations .variation")] if soup.select(".product-variations .variation") else []
                }
            }
            
            return product
            
        except Exception as e:
            logger.error(f"Error getting product details: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise 