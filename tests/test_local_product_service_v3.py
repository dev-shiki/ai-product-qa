import pytest
import json
import logging
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import os
import sys

# Add the parent directory of 'app' to the sys.path to allow imports
# This is typically handled by how pytest is run, but explicitly doing it for robustness.
current_file_dir = Path(__file__).parent
project_root = current_file_dir.parent.parent
sys.path.insert(0, str(project_root))

from app.services.local_product_service import LocalProductService

# --- Mock Data ---

@pytest.fixture
def mock_products_raw_data():
    """Returns a dictionary of raw product data as it would appear in products.json."""
    return {
        "products": [
            {
                "id": "prod1",
                "name": "Smartphone X",
                "category": "Electronics",
                "brand": "BrandA",
                "price": 10000000,
                "currency": "IDR",
                "description": "High-end smartphone.",
                "rating": 4.5,
                "stock_count": 50,
                "specifications": {"storage": "256GB", "camera": "64MP"},
                "reviews_count": 100,
                "availability": "in_stock"
            },
            {
                "id": "prod2",
                "name": "Laptop Y",
                "category": "Computers",
                "brand": "BrandB",
                "price": 15000000,
                "currency": "IDR",
                "description": "Powerful gaming laptop.",
                "rating": 4.8,
                "stock_count": 30,
                "specifications": {"RAM": "16GB", "GPU": "RTX 3060"},
                "reviews_count": 150,
                "availability": "in_stock"
            },
            {
                "id": "prod3",
                "name": "Headphones Z",
                "category": "Audio",
                "brand": "BrandA",
                "price": 2000000,
                "currency": "IDR",
                "description": "Noise-cancelling headphones.",
                "rating": 4.2,
                "stock_count": 80,
                "reviews_count": 50,
                "availability": "in_stock"
            },
            {
                "id": "prod4",
                "name": "Smartwatch A",
                "category": "Wearables",
                "brand": "BrandC",
                "price": 3000000,
                "currency": "IDR",
                "description": "Feature-rich smartwatch.",
                "rating": 3.9,
                "stock_count": 20,
                "reviews_count": 20,
                "availability": "out_of_stock"
            },
            { # Product with missing fields to test defaults
                "id": "prod5",
                "name": "Minimal Product",
                "description": "This product has minimal data.",
                # No category, brand, price, rating, stock_count, reviews_count
            },
            { # Product for specific ID match with fallback list
                "id": "1",
                "name": "Local iPhone 15",
                "category": "Smartphone",
                "brand": "Apple",
                "price": 20000000,
                "description": "A local iPhone.",
                "rating": 4.7,
                "stock_count": 40
            }
        ]
    }

@pytest.fixture
def expected_transformed_products(mock_products_raw_data):
    """
    Returns the expected transformed product list after LocalProductService loads it.
    Uses a fixed random seed for 'sold' count for deterministic tests.
    """
    transformed = []
    # Patch random.randint to a fixed value for deterministic testing of 'sold' count
    with patch('random.randint', side_effect=lambda a, b: 1000):
        for p in mock_products_raw_data['products']:
            transformed_product = {
                "id": p.get('id', ''),
                "name": p.get('name', ''),
                "category": p.get('category', ''),
                "brand": p.get('brand', ''),
                "price": p.get('price', 0),
                "currency": p.get('currency', 'IDR'),
                "description": p.get('description', ''),
                "specifications": {
                    "rating": p.get('rating', 0),
                    "sold": 1000,  # Fixed by the random.randint patch
                    "stock": p.get('stock_count', 0),
                    "condition": "Baru",
                    "shop_location": "Indonesia",
                    "shop_name": f"{p.get('brand', 'Unknown')} Store",
                    **p.get('specifications', {})
                },
                "availability": p.get('availability', 'in_stock'),
                "reviews_count": p.get('reviews_count', 0),
                "images": [f"https://example.com/{p.get('id', 'product')}.jpg"],
                "url": f"https://shopee.co.id/{p.get('id', 'product')}"
            }
            transformed.append(transformed_product)
    return transformed

@pytest.fixture
def mock_open_json_success(mock_products_raw_data):
    """Mocks builtins.open to simulate a successful JSON file read with UTF-8."""
    json_content = json.dumps(mock_products_raw_data)
    m = mock_open(read_data=json_content)
    with patch('builtins.open', m):
        yield m

@pytest.fixture
def mock_open_json_success_with_bom(mock_products_raw_data):
    """Mocks builtins.open to simulate a successful JSON file read with BOM (UTF-8-SIG)."""
    json_content = json.dumps(mock_products_raw_data)
    # Simulate content that would be read by a non-BOM aware utf-8 reader, then manually stripped
    # Or, that utf-8-sig would handle transparently. The code tries utf-8-sig.
    json_content_with_bom = '\ufeff' + json_content
    m = mock_open(read_data=json_content_with_bom)
    with patch('builtins.open', m):
        yield m

@pytest.fixture
def mock_path_exists_true():
    """Mocks Path.exists() to always return True."""
    with patch('pathlib.Path.exists', return_value=True):
        yield

@pytest.fixture
def mock_path_exists_false():
    """Mocks Path.exists() to always return False."""
    with patch('pathlib.Path.exists', return_value=False):
        yield

@pytest.fixture
def mock_load_local_products_success(expected_transformed_products):
    """Mocks _load_local_products to return predefined successful data directly."""
    with patch.object(LocalProductService, '_load_local_products', return_value=expected_transformed_products):
        yield

@pytest.fixture
def service_with_mocked_products(mock_load_local_products_success):
    """Provides a LocalProductService instance with _load_local_products mocked to return valid data."""
    return LocalProductService()

# --- Tests for LocalProductService Initialization and Loading ---

class TestLocalProductServiceInitAndLoad:

    @patch('random.randint', side_effect=lambda a, b: 1000) # Ensure deterministic 'sold' counts
    def test_init_success_loads_products_utf8(self, mock_randint, mock_path_exists_true, mock_open_json_success, expected_transformed_products, caplog):
        """Test that __init__ successfully loads products from a valid UTF-8 JSON file."""
        with caplog.at_level(logging.INFO):
            service = LocalProductService()
            assert len(service.products) == len(expected_transformed_products)
            assert service.products == expected_transformed_products # Deep comparison
            assert "Loaded 6 local products from JSON file" in caplog.text
            assert "Successfully loaded 6 products from JSON file using utf-8 encoding" in caplog.text

    @patch('random.randint', side_effect=lambda a, b: 1000)
    def test_init_success_loads_products_utf8_sig(self, mock_randint, mock_path_exists_true, mock_open_json_success_with_bom, expected_transformed_products, caplog):
        """Test that __init__ successfully loads products from a UTF-8-SIG JSON file (with BOM)."""
        with caplog.at_level(logging.INFO):
            service = LocalProductService()
            assert len(service.products) == len(expected_transformed_products)
            assert service.products == expected_transformed_products
            assert "Loaded 6 local products from JSON file" in caplog.text
            assert "Successfully loaded 6 products from JSON file using utf-8-sig encoding" in caplog.text

    def test_init_file_not_found_uses_fallback(self, mock_path_exists_false, caplog):
        """Test that __init__ uses fallback products if the JSON file is not found."""
        with caplog.at_level(logging.ERROR):
            service = LocalProductService()
            assert len(service.products) > 0 # Fallback products exist
            assert service.products[0]['id'] == '1' # Check first fallback product ID
            assert "Products JSON file not found at:" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text
            assert "Loaded 8 local products from JSON file" in caplog.text # Init log for fallback count

    def test_init_json_decode_error_uses_fallback(self, mock_path_exists_true, caplog):
        """Test that __init__ uses fallback products if JSON decoding fails for all encodings."""
        # This mock will cause JSONDecodeError for all encoding attempts
        mock_read_data = "this is not json"
        m = mock_open(read_data=mock_read_data)
        with patch('builtins.open', m):
            with caplog.at_level(logging.WARNING):
                service = LocalProductService()
                assert len(service.products) > 0
                assert service.products[0]['id'] == '1'
                assert "Failed to load with utf-16-le encoding:" in caplog.text
                assert "Failed to load with utf-16 encoding:" in caplog.text
                assert "Failed to load with utf-8 encoding:" in caplog.text
                assert "Failed to load with utf-8-sig encoding:" in caplog.text
                assert "Failed to load with latin-1 encoding:" in caplog.text
                assert "Failed to load with cp1252 encoding:" in caplog.text
                assert "All encoding attempts failed, using fallback products" in caplog.text
                assert "Loaded 8 local products from JSON file" in caplog.text

    def test_init_unicode_decode_error_all_encodings_fail_uses_fallback(self, mock_path_exists_true, caplog):
        """Test that __init__ uses fallback if all encoding attempts fail with UnicodeDecodeError."""
        # Simulates content that cannot be decoded by any standard text encoding
        def open_side_effect(*args, **kwargs):
            mock_file_handle = MagicMock()
            # Simulate a read that is problematic for most text encodings
            mock_file_handle.read.side_effect = UnicodeDecodeError('utf-8', b'\xff\xfe', 0, 2, 'invalid start byte')
            return mock_file_handle

        with patch('builtins.open', side_effect=open_side_effect):
            with caplog.at_level(logging.ERROR):
                service = LocalProductService()
                assert len(service.products) > 0
                assert service.products[0]['id'] == '1'
                assert "All encoding attempts failed, using fallback products" in caplog.text
                assert "Loaded 8 local products from JSON file" in caplog.text
                assert "Failed to load with" in caplog.text # Multiple warnings for each failed encoding

    def test_init_general_exception_during_load_uses_fallback(self, mock_path_exists_true, caplog):
        """Test that __init__ uses fallback products if a general exception occurs during file operations."""
        m = mock_open()
        m.side_effect = IOError("Simulated IO error during open") # Raise error during open
        with patch('builtins.open', m):
            with caplog.at_level(logging.ERROR):
                service = LocalProductService()
                assert len(service.products) > 0
                assert service.products[0]['id'] == '1'
                assert "Error loading products from JSON file: Simulated IO error during open" in caplog.text
                assert "Loaded 8 local products from JSON file" in caplog.text

    @patch('random.randint', side_effect=lambda a, b: 1000)
    def test_init_product_transformation_defaults_and_random_sold(self, mock_randint, mock_path_exists_true, mock_open_json_success, expected_transformed_products):
        """Test that products are correctly transformed, including default values and fixed 'sold' count."""
        service = LocalProductService()
        assert len(service.products) == len(expected_transformed_products)
        assert service.products == expected_transformed_products # Ensure full transformation matches

        # Specifically check a product with missing data (prod5)
        minimal_product = next(p for p in service.products if p['id'] == 'prod5')
        assert minimal_product['name'] == "Minimal Product"
        assert minimal_product['category'] == ""
        assert minimal_product['brand'] == ""
        assert minimal_product['price'] == 0
        assert minimal_product['currency'] == "IDR"
        assert minimal_product['description'] == "This product has minimal data."
        assert minimal_product['specifications']['rating'] == 0
        assert minimal_product['specifications']['sold'] == 1000 # Fixed by mock_randint
        assert minimal_product['specifications']['stock'] == 0
        assert minimal_product['reviews_count'] == 0
        assert minimal_product['images'] == ["https://example.com/prod5.jpg"]
        assert minimal_product['url'] == "https://shopee.co.id/prod5"

    def test_get_fallback_products(self):
        """Test the _get_fallback_products method directly."""
        service = LocalProductService()
        fallback_products = service._get_fallback_products()
        assert len(fallback_products) == 8
        assert fallback_products[0]['id'] == '1'
        assert fallback_products[0]['name'] == 'iPhone 15 Pro Max'
        assert fallback_products[-1]['id'] == '8'
        assert fallback_products[-1]['name'] == 'Samsung Galaxy Tab S9'


# --- Tests for Public Methods (using mocked loaded products) ---

class TestLocalProductServicePublicMethods:

    @pytest.fixture(autouse=True)
    def setup_service(self, service_with_mocked_products):
        self.service = service_with_mocked_products
        self.products = self.service.products # Reference to the mocked products list

    # --- search_products ---
    def test_search_products_by_name_keyword(self, caplog):
        """Test searching products by name keyword."""
        results = self.service.search_products("Smartphone", limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'prod1' # Smartphone X
        assert results[1]['id'] == '1' # Local iPhone 15
        assert "Searching products with keyword: Smartphone" in caplog.text
        assert "Found 2 products" in caplog.text

    def test_search_products_case_insensitive(self):
        """Test searching products with case-insensitive keyword."""
        results = self.service.search_products("smartphone x")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_search_products_by_description(self):
        """Test searching products by description keyword."""
        results = self.service.search_products("gaming laptop")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2'

    def test_search_products_by_category(self):
        """Test searching products by category keyword."""
        results = self.service.search_products("Computers")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2' # Only Laptop Y is in "Computers" from mock_products_raw_data

    def test_search_products_by_brand(self):
        """Test searching products by brand keyword."""
        results = self.service.search_products("BrandA")
        assert len(results) == 2
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod3' for p in results)

    def test_search_products_by_specifications(self):
        """Test searching products by specifications keyword."""
        results = self.service.search_products("64MP")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_no_match(self):
        """Test searching products with a keyword that yields no matches."""
        results = self.service.search_products("NonExistentProduct")
        assert len(results) == 0

    def test_search_products_empty_keyword(self):
        """Test searching with an empty keyword (should return all products up to limit, sorted by default)."""
        results = self.service.search_products("", limit=3)
        assert len(results) == 3
        # When keyword is empty and no price is extracted, relevance score is 0 for all
        # Pytest will use the order from the `self.products` which is the `expected_transformed_products` order.
        assert results[0]['id'] == 'prod1'
        assert results[1]['id'] == 'prod2'
        assert results[2]['id'] == 'prod3'

    def test_search_products_with_limit(self):
        """Test search products with a specified limit."""
        results = self.service.search_products("BrandA", limit=1)
        assert len(results) == 1
        assert results[0]['id'] == 'prod1' # Smartphone X (higher relevance for 'BrandA' because it has 'BrandA' in its specs, if it had more specific relevance, it would be clearer)

    def test_search_products_relevance_sorting_exact_match(self):
        """Test that products with exact matches in name/brand get higher relevance."""
        results = self.service.search_products("Smartphone", limit=2)
        # prod1 name "Smartphone X" vs prod_local "Local iPhone 15" category "Smartphone"
        # Should rank prod1 higher due to 'Smartphone' in its name.
        assert results[0]['id'] == 'prod1'
        assert results[1]['id'] == '1'

    def test_search_products_relevance_sorting_budget_keyword(self):
        """Test that products with lower prices are preferred for budget keywords."""
        # Patch extract_price to ensure 'budget' effect
        with patch.object(self.service, '_extract_price_from_keyword', return_value=5000000):
            results = self.service.search_products("laptop budget", limit=2)
            # Products within budget: prod3 (2M), prod4 (3M)
            # Products not within budget: prod1 (10M), prod2 (15M), prod_local (20M)
            # But the search is for 'laptop budget'. 'laptop' keyword match will be used.
            # Only prod2 is a laptop (15M). It would normally be excluded by price.
            # Let's ensure the `max_price` filter works correctly first.
            results_filtered_by_price = [p for p in self.products if p['price'] <= 5000000]
            assert any(p['id'] == 'prod3' for p in results_filtered_by_price)
            assert any(p['id'] == 'prod4' for p in results_filtered_by_price)

            # Re-run the actual test with a keyword that results in a price, but also matches something.
            # Example: "gaming laptop 10 juta" -> max_price 10M, matches "gaming laptop" (prod2 is 15M, so no match).
            # If no product matches price, it won't be added to filtered_products due to `if max_price and product_price <= max_price`
            # and then also won't be added by text search if it was filtered out by price first.
            # The relevance score function only applies to products that *were* added to filtered_products.

            # Test an item that gets past the price filter AND has 'budget' keyword
            results = self.service.search_products("murah", limit=2) # 'murah' -> 5M
            assert len(results) == 2
            # Prod3 (2M), Prod4 (3M) both qualify for price, and both get bonus for 'murah' in keyword
            # Sorting for relevance score (10000000 - price) / 1000000, higher for lower price.
            # Prod3 (2M): (10-2)/1 = 8. Prod4 (3M): (10-3)/1 = 7.
            assert results[0]['id'] == 'prod3'
            assert results[1]['id'] == 'prod4'

    def test_search_products_error_handling(self, caplog):
        """Test error handling in search_products."""
        # Simulate an error by making self.products not iterable
        with patch.object(self.service, 'products', new=None):
            with caplog.at_level(logging.ERROR):
                results = self.service.search_products("any")
                assert results == []
                assert "Error searching products: 'NoneType' object is not iterable" in caplog.text

    # --- _extract_price_from_keyword ---
    @pytest.mark.parametrize("keyword, expected_price", [
        ("harga 10 juta", 10000000),
        ("200 ribu", 200000),
        ("rp 500000", 500000),
        ("1000000 rp", 1000000),
        ("30k", 30000),
        ("250 k", 250000),
        ("1m", 1000000),
        ("hp murah", 5000000),
        ("laptop budget", 5000000),
        ("tablet hemat", 3000000),
        ("aksesoris terjangkau", 4000000),
        ("monitor ekonomis", 2000000),
        ("just a keyword", None),
        ("", None),
        ("murah 1 juta", 1000000), # Regex match takes precedence
        ("10k murah", 10000),     # Regex match takes precedence
        ("laptop 5.5 juta", None) # Only integer juta is handled by current regex
    ])
    def test_extract_price_from_keyword(self, keyword, expected_price):
        """Test extraction of various price patterns and budget keywords."""
        assert self.service._extract_price_from_keyword(keyword) == expected_price

    def test_extract_price_from_keyword_error_handling(self, caplog):
        """Test error handling in _extract_price_from_keyword."""
        with patch('re.search', side_effect=Exception("Simulated regex error")):
            with caplog.at_level(logging.ERROR):
                result = self.service._extract_price_from_keyword("10 juta")
                assert result is None
                assert "Error extracting price from keyword: Simulated regex error" in caplog.text

    # --- get_product_details ---
    def test_get_product_details_existing(self):
        """Test getting details for an existing product ID."""
        product = self.service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == "prod1"
        assert product['name'] == "Smartphone X"

    def test_get_product_details_non_existing(self):
        """Test getting details for a non-existent product ID."""
        product = self.service.get_product_details("nonexistent_id")
        assert product is None

    def test_get_product_details_empty_products_list(self):
        """Test getting product details when the products list is empty."""
        self.service.products = []
        product = self.service.get_product_details("prod1")
        assert product is None

    def test_get_product_details_error_handling(self, caplog):
        """Test error handling in get_product_details."""
        # Simulate an error by making self.products raise an error during iteration
        def broken_iterator():
            yield self.products[0]
            raise Exception("Simulated iteration error")
        
        with patch.object(self.service, 'products', new=broken_iterator()):
            with caplog.at_level(logging.ERROR):
                product = self.service.get_product_details("prod2")
                assert product is None
                assert "Error getting product details: Simulated iteration error" in caplog.text

    # --- get_categories ---
    def test_get_categories(self):
        """Test getting a sorted list of unique categories."""
        categories = self.service.get_categories()
        expected_categories = ['Audio', 'Computers', 'Electronics', 'Smartphone', 'Wearables', ''] # '' for prod5
        assert sorted(categories) == sorted(expected_categories)
        assert "" in categories # Ensure empty category is included

    def test_get_categories_empty_products(self):
        """Test getting categories when the products list is empty."""
        self.service.products = []
        categories = self.service.get_categories()
        assert categories == []

    # --- get_brands ---
    def test_get_brands(self):
        """Test getting a sorted list of unique brands."""
        brands = self.service.get_brands()
        expected_brands = ['Apple', 'BrandA', 'BrandB', 'BrandC', 'Unknown'] # 'Unknown' from prod5
        assert sorted(brands) == sorted(expected_brands)
        assert "Unknown" in brands # Ensure 'Unknown' is included for products without brand

    def test_get_brands_empty_products(self):
        """Test getting brands when the products list is empty."""
        self.service.products = []
        brands = self.service.get_brands()
        assert brands == []

    # --- get_products_by_category ---
    def test_get_products_by_category_existing(self):
        """Test getting products for an existing category."""
        results = self.service.get_products_by_category("Electronics")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_get_products_by_category_case_insensitive(self):
        """Test getting products by category with case-insensitive match."""
        results = self.service.get_products_by_category("electronics")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_get_products_by_category_non_existing(self):
        """Test getting products for a non-existent category."""
        results = self.service.get_products_by_category("Books")
        assert len(results) == 0

    def test_get_products_by_category_empty_products_list(self):
        """Test getting products by category when the products list is empty."""
        self.service.products = []
        results = self.service.get_products_by_category("Electronics")
        assert results == []

    def test_get_products_by_category_error_handling(self, caplog):
        """Test error handling in get_products_by_category."""
        def broken_iterator():
            yield {"category": "Electronics"}
            raise Exception("Simulated iteration error")
        
        with patch.object(self.service, 'products', new=broken_iterator()):
            with caplog.at_level(logging.ERROR):
                results = self.service.get_products_by_category("Electronics")
                assert results == []
                assert "Error getting products by category: Simulated iteration error" in caplog.text

    # --- get_products_by_brand ---
    def test_get_products_by_brand_existing(self):
        """Test getting products for an existing brand."""
        results = self.service.get_products_by_brand("BrandA")
        assert len(results) == 2
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod3' for p in results)

    def test_get_products_by_brand_case_insensitive(self):
        """Test getting products by brand with case-insensitive match."""
        results = self.service.get_products_by_brand("branda")
        assert len(results) == 2
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod3' for p in results)

    def test_get_products_by_brand_non_existing(self):
        """Test getting products for a non-existent brand."""
        results = self.service.get_products_by_brand("Nike")
        assert len(results) == 0

    def test_get_products_by_brand_empty_products_list(self):
        """Test getting products by brand when the products list is empty."""
        self.service.products = []
        results = self.service.get_products_by_brand("BrandA")
        assert results == []

    def test_get_products_by_brand_error_handling(self, caplog):
        """Test error handling in get_products_by_brand."""
        def broken_iterator():
            yield {"brand": "BrandA"}
            raise Exception("Simulated iteration error")
        
        with patch.object(self.service, 'products', new=broken_iterator()):
            with caplog.at_level(logging.ERROR):
                results = self.service.get_products_by_brand("BrandA")
                assert results == []
                assert "Error getting products by brand: Simulated iteration error" in caplog.text

    # --- get_top_rated_products ---
    def test_get_top_rated_products(self):
        """Test getting top rated products."""
        # Expected ratings: prod1(4.5), prod2(4.8), prod3(4.2), prod4(3.9), prod5(0), 1(4.7)
        # Order: prod2(4.8), 1(4.7), prod1(4.5), prod3(4.2), prod4(3.9), prod5(0)
        results = self.service.get_top_rated_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == 'prod2' # 4.8
        assert results[1]['id'] == '1'     # 4.7
        assert results[2]['id'] == 'prod1' # 4.5

    def test_get_top_rated_products_less_than_limit(self):
        """Test getting top rated products when available products are less than the limit."""
        self.service.products = [self.products[0], self.products[1]] # Only prod1 and prod2
        results = self.service.get_top_rated_products(limit=5)
        assert len(results) == 2
        assert results[0]['id'] == 'prod2'
        assert results[1]['id'] == 'prod1'

    def test_get_top_rated_products_empty_list(self):
        """Test getting top rated products when the list is empty."""
        self.service.products = []
        results = self.service.get_top_rated_products(limit=5)
        assert results == []

    def test_get_top_rated_products_no_rating_field(self):
        """Test getting top rated products when some products lack 'rating' field."""
        # prod5 has 0 rating by default transformation
        results = self.service.get_top_rated_products(limit=6) # Get all products
        assert any(p['id'] == 'prod5' and p['specifications']['rating'] == 0 for p in results)
        assert results[-1]['id'] == 'prod5' # Should be last due to 0 rating

    def test_get_top_rated_products_error_handling(self, caplog):
        """Test error handling in get_top_rated_products."""
        # Simulate an error by making a product's specs access cause an error
        broken_product = MagicMock()
        broken_product.get.side_effect = Exception("Simulated access error") # Error when accessing 'specifications'
        
        with patch.object(self.service, 'products', new=[broken_product]):
            with caplog.at_level(logging.ERROR):
                results = self.service.get_top_rated_products(limit=1)
                assert results == []
                assert "Error getting top rated products: Simulated access error" in caplog.text

    # --- get_best_selling_products ---
    def test_get_best_selling_products_actual_sold_values(self, caplog):
        """Test getting best selling products with custom sold values."""
        # Manually modify `self.service.products` for this test
        self.service.products = [
            {"id": "s1", "name": "Prod 1", "specifications": {"sold": 5000, "rating": 4.0}},
            {"id": "s2", "name": "Prod 2", "specifications": {"sold": 1000, "rating": 3.0}},
            {"id": "s3", "name": "Prod 3", "specifications": {"sold": 7000, "rating": 5.0}},
            {"id": "s4", "name": "Prod 4", "specifications": {"sold": 2000, "rating": 4.5}},
            {"id": "s5", "name": "Prod 5", "specifications": {}, "price": 100} # No sold count -> 0 sold
        ]
        
        with caplog.at_level(logging.INFO):
            results = self.service.get_best_selling_products(limit=3)
            assert len(results) == 3
            assert results[0]['id'] == 's3' # 7000 sold
            assert results[1]['id'] == 's1' # 5000 sold
            assert results[2]['id'] == 's4' # 2000 sold
            assert "Getting best selling products, limit: 3" in caplog.text
            assert "Returning 3 best selling products" in caplog.text

        results_all = self.service.get_best_selling_products(limit=5)
        assert results_all[-1]['id'] == 's5' # Should be last due to 0 sold count

    def test_get_best_selling_products_empty_list(self):
        """Test getting best selling products when the list is empty."""
        self.service.products = []
        results = self.service.get_best_selling_products(limit=5)
        assert results == []

    def test_get_best_selling_products_error_handling(self, caplog):
        """Test error handling in get_best_selling_products."""
        # Simulate an error by making a product's specs access cause an error
        broken_product = MagicMock()
        broken_product.get.side_effect = Exception("Simulated access error")
        
        with patch.object(self.service, 'products', new=[broken_product]):
            with caplog.at_level(logging.ERROR):
                results = self.service.get_best_selling_products(limit=1)
                assert results == []
                assert "Error getting best selling products: Simulated access error" in caplog.text

    # --- get_products ---
    def test_get_products(self):
        """Test getting all products with default limit."""
        results = self.service.get_products() # Default limit 10
        assert len(results) == 6 # All 6 mocked products are returned
        assert results[0]['id'] == 'prod1' # Check first product

    def test_get_products_with_custom_limit(self):
        """Test getting all products with a custom limit."""
        results = self.service.get_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == 'prod1'
        assert results[1]['id'] == 'prod2'
        assert results[2]['id'] == 'prod3'

    def test_get_products_limit_exceeds_available(self):
        """Test getting all products with limit exceeding available products."""
        results = self.service.get_products(limit=100)
        assert len(results) == 6 # Still only 6 available
        assert results[0]['id'] == 'prod1'

    def test_get_products_empty_list(self):
        """Test getting products when the list is empty."""
        self.service.products = []
        results = self.service.get_products()
        assert results == []

    def test_get_products_error_handling(self, caplog):
        """Test error handling in get_products."""
        # Simulate an error by making self.products cause an error during slicing
        class ErrorList(list):
            def __getitem__(self, key):
                if isinstance(key, slice):
                    raise Exception("Simulated slice error")
                return super().__getitem__(key)
        
        with patch.object(self.service, 'products', new=ErrorList([{"id": "test"}])):
            with caplog.at_level(logging.ERROR):
                results = self.service.get_products(limit=1)
                assert results == []
                assert "Error getting products: Simulated slice error" in caplog.text


# --- Tests for smart_search_products ---

class TestLocalProductServiceSmartSearch:

    @pytest.fixture(autouse=True)
    def setup_service(self, service_with_mocked_products):
        self.service = service_with_mocked_products
        self.products = self.service.products # Reference to the mocked products list

    def test_smart_search_best_overall(self, caplog):
        """Test smart_search for 'terbaik' or 'best' without specific category."""
        # Products ratings: prod1(4.5), prod2(4.8), prod3(4.2), prod4(3.9), prod5(0), 1(4.7)
        # Expected order (top 3): prod2(4.8), 1(4.7), prod1(4.5)
        with caplog.at_level(logging.INFO):
            results, message = self.service.smart_search_products(keyword="produk terbaik", limit=3)
            assert len(results) == 3
            assert results[0]['id'] == 'prod2'
            assert results[1]['id'] == '1'
            assert results[2]['id'] == 'prod1'
            assert message == "Berikut produk terbaik berdasarkan rating:"
            assert "Error" not in caplog.text

    def test_smart_search_best_in_category_found(self, caplog):
        """Test smart_search for 'terbaik' in a specific, existing category."""
        # Electronics products: prod1 (4.5)
        with caplog.at_level(logging.INFO):
            results, message = self.service.smart_search_products(keyword="elektronik terbaik", category="Electronics", limit=2)
            assert len(results) == 1
            assert results[0]['id'] == 'prod1' # Smartphone X (4.5)
            assert message == "Berikut Electronics terbaik berdasarkan rating:"

    def test_smart_search_best_in_category_not_found_fallback(self, caplog):
        """Test smart_search for 'terbaik' in a non-existent category, leading to general fallback."""
        # Should fallback to overall best products
        with caplog.at_level(logging.INFO):
            results, message = self.service.smart_search_products(keyword="baju terbaik", category="Fashion", limit=2)
            assert len(results) == 2
            assert results[0]['id'] == 'prod2' # Laptop Y (4.8)
            assert results[1]['id'] == '1' # Local iPhone 15 (4.7)
            assert message == "Tidak ada produk kategori Fashion, berikut produk terbaik secara umum:"

    def test_smart_search_all_criteria_match(self):
        """Test smart_search when all keyword, category, and max_price criteria match."""
        # Search for "smartphone" (keyword), category "Electronics", max_price 12M
        # prod1 (Electronics, 10M) should match
        results, message = self.service.smart_search_products(keyword="smartphone", category="Electronics", max_price=12000000, limit=5)
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_keyword_only(self):
        """Test smart_search with only keyword."""
        results, message = self.service.smart_search_products(keyword="headphones")
        assert len(results) == 1
        assert results[0]['id'] == 'prod3'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_category_only(self):
        """Test smart_search with only category."""
        results, message = self.service.smart_search_products(category="Computers")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_max_price_only(self):
        """Test smart_search with only max_price."""
        # Products <= 5M: prod3 (2M), prod4 (3M)
        results, message = self.service.smart_search_products(max_price=5000000, limit=2)
        assert len(results) == 2
        # Order is not guaranteed without relevance score, but both should be present
        assert any(p['id'] == 'prod3' for p in results)
        assert any(p['id'] == 'prod4' for p in results)
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_fallback_category_no_price_or_keyword_match(self):
        """Test fallback: category matched, but keyword/price didn't fully narrow down."""
        # Search for keyword "xyz", category "Computers", max_price 1000
        # prod2 is "Computers" (15M), so it won't match price or keyword.
        # Fallback to category only, sorted by price.
        results, message = self.service.smart_search_products(keyword="xyz", category="Computers", max_price=1000, limit=2)
        assert len(results) == 1
        assert results[0]['id'] == 'prod2' # Laptop Y (15M)
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_fallback_max_price_no_category_or_keyword_match(self):
        """Test fallback: max_price matched, but keyword/category didn't fully narrow down."""
        # Search for "xyz" (keyword), category "Footwear" (non-existent), max_price 5M
        # Fallback should be products under 5M, ignoring category and keyword.
        results, message = self.service.smart_search_products(keyword="xyz", category="Footwear", max_price=5000000, limit=2)
        assert len(results) == 2
        assert any(p['id'] == 'prod3' for p in results) # Headphones Z (2M)
        assert any(p['id'] == 'prod4' for p in results) # Smartwatch A (3M)
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_fallback_no_match_popular(self):
        """Test fallback: no criteria matched, fall back to popular products."""
        # Override self.products to have distinct 'sold' counts for predictable popular sort
        self.service.products = [
            {"id": "p1", "name": "Prod A", "specifications": {"sold": 1000, "rating": 3.0}},
            {"id": "p2", "name": "Prod B", "specifications": {"sold": 5000, "rating": 4.0}},
            {"id": "p3", "name": "Prod C", "specifications": {"sold": 2000, "rating": 3.5}},
            {"id": "p4", "name": "Prod D", "specifications": {"sold": 8000, "rating": 4.2}}, # Most sold
        ]
        results, message = self.service.smart_search_products(keyword="nonexistent", category="nonexistent", max_price=100, limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'p4' # Most sold
        assert results[1]['id'] == 'p2' # Second most sold
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_empty_products_list(self):
        """Test smart_search with an empty products list."""
        self.service.products = []
        results, message = self.service.smart_search_products(keyword="any")
        assert len(results) == 0
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_no_parameters(self):
        """Test smart_search with no parameters, should return all matching criteria."""
        # With no keyword, category, max_price, all products initially match the first 'results' filter.
        results, message = self.service.smart_search_products(limit=3)
        assert len(results) == 3
        assert results[0]['id'] == 'prod1'
        assert results[1]['id'] == 'prod2'
        assert results[2]['id'] == 'prod3'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_limit_functionality(self):
        """Test smart_search adheres to the limit."""
        results, _ = self.service.smart_search_products(keyword="BrandA", limit=1)
        assert len(results) == 1
        assert results[0]['id'] == 'prod1' # Smartphone X