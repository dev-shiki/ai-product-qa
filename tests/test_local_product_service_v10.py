import pytest
from unittest import mock
from pathlib import Path
import json
import logging
import random

# Adjust the import path based on your project structure.
# Assuming tests are run from the project root and the file is app/services/local_product_service.py
from app.services.local_product_service import LocalProductService

# Suppress actual logging during tests to avoid clutter unless explicitly needed for debugging
@pytest.fixture(autouse=True)
def cap_logging(caplog):
    caplog.set_level(logging.DEBUG)


# Sample raw product data for mocking the JSON file content.
# This represents the structure of 'products.json' before transformation.
@pytest.fixture
def sample_raw_products_data():
    return {
        "products": [
            {
                "id": "prod1", "name": "Smartphone X", "category": "Electronics", "brand": "Brand A",
                "price": 10000000, "description": "High-end smartphone.", "rating": 4.5, "stock_count": 50,
                "reviews_count": 10, "specifications": {"processor": "XYZ", "memory": "8GB"}
            },
            {
                "id": "prod2", "name": "Laptop Y", "category": "Electronics", "brand": "Brand B",
                "price": 15000000, "description": "Powerful laptop for professionals.", "rating": 4.8,
                "stock_count": 30, "reviews_count": 12, "specifications": {"gpu": "ABC"}
            },
            {
                "id": "prod3", "name": "Headphones Z", "category": "Audio", "brand": "Brand A",
                "price": 2000000, "description": "Noise-cancelling headphones.", "rating": 4.2,
                "stock_count": 100, "reviews_count": 5, "sold": 1500 # Explicitly set sold for testing
            },
            {
                "id": "prod4", "name": "Tablet P", "category": "Electronics", "brand": "Brand C",
                "price": 7500000, "description": "Portable tablet.", "rating": 4.0,
                "stock_count": 20, "reviews_count": 7
            },
            {
                "id": "prod5", "name": "Smartwatch Q", "category": "Wearables", "brand": "Brand B",
                "price": 3000000, "description": "Fitness tracking smartwatch.", "rating": 4.1,
                "stock_count": 70, "reviews_count": 8, "sold": 1800 # Explicitly set sold for testing
            },
            {
                "id": "prod6", "name": "Smartphone G", "category": "Electronics", "brand": "Brand D",
                "price": 4000000, "description": "Mid-range smartphone.", "rating": 3.9,
                "stock_count": 60, "reviews_count": 3
            },
            {
                "id": "prod7", "name": "Smartphone H", "category": "Electronics", "brand": "Brand D",
                "price": 6000000, "description": "Entry-level smartphone.", "rating": 3.5,
                "stock_count": 60, "reviews_count": 2
            },
             {
                "id": "prod8", "name": "Super Speaker", "category": "Audio", "brand": "Brand E",
                "price": 1000000, "description": "Portable bluetooth speaker with amazing bass.", "rating": 4.3,
                "stock_count": 200, "reviews_count": 15, "sold": 2000 # Explicitly set sold for testing
            }
        ]
    }

# Fixture to provide a LocalProductService instance with pre-loaded (mocked) products
@pytest.fixture
def local_product_service(mocker, sample_raw_products_data):
    # Patch random.randint to ensure deterministic 'sold' values for products
    mocker.patch('random.randint', return_value=500)

    # Simulate the transformation logic that happens inside _load_local_products
    def _simulate_product_transformation(raw_products_list):
        transformed_products = []
        for product in raw_products_list:
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
                    # Use explicit 'sold' if provided in raw data, otherwise the patched random.randint value
                    "sold": product.get('sold', random.randint(100, 2000)),
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
        return transformed_products

    # Calculate the expected transformed products based on sample_raw_products_data
    mock_loaded_products = _simulate_product_transformation(sample_raw_products_data['products'])

    # Patch _load_local_products in the class to return our controlled transformed data.
    # This ensures that when LocalProductService is initialized, it gets our known product set.
    mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_loaded_products)

    # Initialize the service, which will now use the mocked _load_local_products
    service = LocalProductService()
    return service


class TestLocalProductService:

    # Test initialization and successful product loading from JSON file
    def test_init_loads_products_successfully(self, mocker, sample_raw_products_data, caplog):
        # Mock Path.exists to indicate the JSON file exists
        mocker.patch('pathlib.Path.exists', return_value=True)

        # Mock the content of the file. Provide a valid JSON string.
        # mocker.mock_open will ensure file.read() returns this string regardless of encoding.
        mock_file_content = json.dumps(sample_raw_products_data)
        mock_open_func = mocker.mock_open(read_data=mock_file_content)
        mocker.patch('pathlib.Path.open', mock_open_func)
        
        # Patch random.randint to ensure deterministic 'sold' counts during transformation
        mocker.patch('random.randint', return_value=500)

        # Initialize the service
        service = LocalProductService()

        # Assertions
        assert len(service.products) == len(sample_raw_products_data['products'])
        # Check that product transformation includes default values and random.randint mock
        # 'prod1' did not have 'sold' in raw data, so it should get the mocked random value (500)
        assert service.products[0]['specifications']['sold'] == 500
        # 'prod3' had an explicit 'sold' value (1500) in raw data, which should be preserved
        assert service.products[2]['specifications']['sold'] == 1500
        assert "Loaded 8 local products from JSON file" in caplog.text
        # Check that a success message is logged for one of the encodings
        assert any("Successfully loaded 8 products from JSON file using" in m for m in caplog.messages)


    # Test initialization when the JSON product file is not found
    def test_init_uses_fallback_when_file_not_found(self, mocker, caplog):
        mocker.patch('pathlib.Path.exists', return_value=False)
        
        # Mock the _get_fallback_products method directly to control its output for this test
        mocker.patch.object(LocalProductService, '_get_fallback_products', 
                            return_value=[{"id": "fallback_test_prod", "name": "Fallback Product"}])

        service = LocalProductService()

        assert len(service.products) == 1
        assert service.products[0]['id'] == "fallback_test_prod"
        assert "Products JSON file not found at:" in caplog.text
        assert "Loaded 1 local products from JSON file" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text # Log from _get_fallback_products


    # Test _load_local_products handling UnicodeDecodeError for all encoding attempts
    def test_load_local_products_unicode_decode_error_all_encodings(self, mocker, caplog):
        mocker.patch('pathlib.Path.exists', return_value=True)
        
        # Simulate an `open` call that returns a file handle where `read()` always raises UnicodeDecodeError
        mock_file_handle = mock.MagicMock()
        mock_file_handle.read.side_effect = UnicodeDecodeError('test_codec', b'\x80', 0, 1, 'invalid start byte')
        mocker.patch('pathlib.Path.open', return_value=mock_file_handle)
        
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback_unicode"}])
        
        service = LocalProductService()

        assert len(service.products) == 1
        assert service.products[0]['id'] == "fallback_unicode"
        # Verify that an error log for each encoding attempt is present
        assert caplog.messages.count("Failed to load with utf-16-le encoding") == 1
        assert caplog.messages.count("Failed to load with utf-16 encoding") == 1
        assert caplog.messages.count("Failed to load with utf-8 encoding") == 1
        assert caplog.messages.count("Failed to load with utf-8-sig encoding") == 1
        assert caplog.messages.count("Failed to load with latin-1 encoding") == 1
        assert caplog.messages.count("Failed to load with cp1252 encoding") == 1
        assert "All encoding attempts failed, using fallback products" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text


    # Test _load_local_products handling json.JSONDecodeError for all encoding attempts
    def test_load_local_products_json_decode_error_all_encodings(self, mocker, caplog):
        mocker.patch('pathlib.Path.exists', return_value=True)
        
        # Simulate a file that contains valid characters but invalid JSON structure.
        # `mocker.mock_open` will return this string, and `json.loads` will then fail.
        mock_invalid_json_content = "{ this is not json array"
        mock_open_func = mocker.mock_open(read_data=mock_invalid_json_content)
        mocker.patch('pathlib.Path.open', mock_open_func)

        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback_json"}])
        
        service = LocalProductService()

        assert len(service.products) == 1
        assert service.products[0]['id'] == "fallback_json"
        # Verify that an error log for each encoding attempt (where JSON parsing fails) is present
        assert caplog.messages.count("Failed to load with utf-16-le encoding") == 1
        assert caplog.messages.count("Failed to load with utf-8 encoding") == 1 # Assuming these pass read but fail json.loads
        assert "All encoding attempts failed, using fallback products" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text


    # Test _load_local_products handling a general exception during file operations
    def test_load_local_products_general_exception(self, mocker, caplog):
        mocker.patch('pathlib.Path.exists', side_effect=Exception("Simulated FS error"))
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback_general_exception"}])
        
        service = LocalProductService()

        assert len(service.products) == 1
        assert service.products[0]['id'] == "fallback_general_exception"
        assert "Error loading products from JSON file: Simulated FS error" in caplog.text
        assert "Using fallback products due to JSON file loading error" in caplog.text

    # Test _load_local_products correctly handles Byte Order Mark (BOM)
    def test_load_local_products_with_bom(self, mocker, sample_raw_products_data, caplog):
        # Simulate a file content that starts with a UTF-8 BOM character
        bom_content_str = '\ufeff' + json.dumps(sample_raw_products_data)
        
        # mock_open with read_data as string means file.read() returns this string directly.
        # The BOM stripping logic in `_load_local_products` should then correctly remove it.
        mock_open_func = mocker.mock_open(read_data=bom_content_str)
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('pathlib.Path.open', mock_open_func)
        mocker.patch('random.randint', return_value=500)
        
        service = LocalProductService()

        assert len(service.products) == len(sample_raw_products_data['products'])
        # Verify that a success message is logged, indicating the file was loaded.
        # The specific encoding reported might vary depending on mock_open's internal string handling.
        assert any("Successfully loaded 8 products from JSON file using" in m for m in caplog.messages)
        # Implicitly, if the products are loaded correctly, the BOM stripping was successful,
        # otherwise, json.loads would have failed for non-utf-8-sig encodings.


    # Test _get_fallback_products method
    def test_get_fallback_products(self, local_product_service, caplog):
        fallback_products = local_product_service._get_fallback_products()
        assert isinstance(fallback_products, list)
        assert len(fallback_products) > 0
        assert all(isinstance(p, dict) for p in fallback_products)
        assert "Using fallback products due to JSON file loading error" in caplog.text


    # Test search_products method
    def test_search_products_by_name(self, local_product_service):
        results = local_product_service.search_products("Smartphone X")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_case_insensitive(self, local_product_service):
        results = local_product_service.search_products("smartphone x")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_by_description(self, local_product_service):
        results = local_product_service.search_products("powerful laptop")
        assert len(results) == 1
        assert results[0]['id'] == "prod2"
    
    def test_search_products_by_category(self, local_product_service):
        results = local_product_service.search_products("Audio")
        assert len(results) == 2 # Headphones Z, Super Speaker
        # Order is based on relevance score (which is 0 for products not matching keyword)
        # and then potentially stable sort from input order if scores are tied.
        # Prod8 (Super Speaker) has higher rating and higher reviews count, though those aren't in `relevance_score` directly
        # For 'Audio', it will just be added if category matches. No specific keyword.
        # Order should be maintained as they appear in the original list.
        assert {p['id'] for p in results} == {'prod3', 'prod8'}

    def test_search_products_by_brand(self, local_product_service):
        results = local_product_service.search_products("Brand A")
        assert len(results) == 2 # Smartphone X, Headphones Z
        assert results[0]['id'] == 'prod1' # 'Smartphone X' gets higher relevance for name match
        assert results[1]['id'] == 'prod3'

    def test_search_products_by_specifications(self, local_product_service):
        results = local_product_service.search_products("processor XYZ")
        assert len(results) == 1
        assert results[0]['id'] == "prod1"

    def test_search_products_limit(self, local_product_service):
        results = local_product_service.search_products("smartphone", limit=1)
        assert len(results) == 1
        assert results[0]['id'] == 'prod1' # 'Smartphone X' has highest relevance score for 'smartphone'

    def test_search_products_no_match(self, local_product_service):
        results = local_product_service.search_products("nonexistent product")
        assert len(results) == 0

    def test_search_products_empty_keyword(self, local_product_service):
        # Should return products sorted by relevance score (which is 0 for all without keyword), then limited.
        results = local_product_service.search_products("", limit=3)
        assert len(results) == 3
        # Should return the first 3 products from the list, due to stable sort with tied scores (0)
        assert results[0]['id'] == 'prod1'
        assert results[1]['id'] == 'prod2'
        assert results[2]['id'] == 'prod3'

    def test_search_products_price_from_keyword_and_relevance(self, local_product_service):
        # Search for "smartphone 5 juta" (max_price = 5,000,000)
        # Products matching keyword "smartphone": prod1 (10M), prod6 (4M), prod7 (6M)
        # Products matching price <= 5M: prod3 (2M), prod5 (3M), prod6 (4M), prod8 (1M)
        # Combined filtered products: prod1, prod3, prod5, prod6, prod7, prod8 (6 products)
        # Relevance scores (higher is better, lower price if budget keywords detected):
        # prod6 (Smartphone G, 4M): 10 (name) + (10M-4M)/1M = 16
        # prod7 (Smartphone H, 6M): 10 (name) + (10M-6M)/1M = 14
        # prod1 (Smartphone X, 10M): 10 (name) + (10M-10M)/1M = 10
        # prod8 (Super Speaker, 1M): 0 (no name/brand/cat match) + (10M-1M)/1M = 9
        # prod3 (Headphones Z, 2M): 0 (no name/brand/cat match) + (10M-2M)/1M = 8
        # prod5 (Smartwatch Q, 3M): 0 (no name/brand/cat match) + (10M-3M)/1M = 7
        # Expected order: prod6, prod7, prod1, prod8, prod3, prod5
        results = local_product_service.search_products("smartphone 5 juta")
        assert len(results) == 6
        assert results[0]['id'] == 'prod6'
        assert results[1]['id'] == 'prod7'
        assert results[2]['id'] == 'prod1'
        assert results[3]['id'] == 'prod8'
        assert results[4]['id'] == 'prod3'
        assert results[5]['id'] == 'prod5'


    def test_search_products_budget_keywords_and_relevance(self, local_product_service):
        # Search for "laptop murah" (keyword 'murah' implies max_price of 5M)
        # Products matching "laptop": prod2 (15M)
        # Products matching price <= 5M (from 'murah'): prod3 (2M), prod5 (3M), prod6 (4M), prod8 (1M)
        # Combined filtered products: prod2, prod3, prod5, prod6, prod8 (5 products)
        # Relevance scores for 'laptop murah':
        # prod2 (Laptop Y, 15M): 10 (name) + (10M-15M)/1M = 5 (price part makes score lower as price is high)
        # prod8 (Super Speaker, 1M): 0 + (10M-1M)/1M = 9
        # prod3 (Headphones Z, 2M): 0 + (10M-2M)/1M = 8
        # prod5 (Smartwatch Q, 3M): 0 + (10M-3M)/1M = 7
        # prod6 (Smartphone G, 4M): 0 + (10M-4M)/1M = 6
        # Expected order: prod8, prod3, prod5, prod6, prod2
        results = local_product_service.search_products("laptop murah")
        assert len(results) == 5
        assert results[0]['id'] == 'prod8'
        assert results[1]['id'] == 'prod3'
        assert results[2]['id'] == 'prod5'
        assert results[3]['id'] == 'prod6'
        assert results[4]['id'] == 'prod2'

    def test_search_products_error_handling(self, local_product_service, mocker, caplog):
        mocker.patch.object(local_product_service, '_extract_price_from_keyword', side_effect=Exception("Price extraction failure"))
        results = local_product_service.search_products("any keyword")
        assert len(results) == 0
        assert "Error searching products: Price extraction failure" in caplog.text


    # Test _extract_price_from_keyword method
    @pytest.mark.parametrize("keyword, expected_price", [
        ("iphone 10 juta", 10000000),
        ("harga 2 juta", 2000000), # Using `(\d+) juta`, "2.5 juta" would extract "2"
        ("Rp 500000", 500000),
        ("laptop 1500k", 1500000),
        ("camera 2m", 2000000),
        ("TV 300 ribu", 300000),
        ("murah", 5000000),
        ("budget gaming", 5000000),
        ("hemat energi", 3000000),
        ("terjangkau nih", 4000000),
        ("ekonomis banget", 2000000),
        ("no price here", None),
        ("1000", None), # Should not detect just a number without context
        ("Rp10000", 10000), # No space after Rp
        ("10000rp", 10000), # No space before rp
        ("1juta", 1000000), # No space between number and suffix
        ("2ribu", 2000),   # No space between number and suffix
    ])
    def test_extract_price_from_keyword_success(self, local_product_service, keyword, expected_price):
        price = local_product_service._extract_price_from_keyword(keyword)
        assert price == expected_price

    def test_extract_price_from_keyword_error_handling(self, local_product_service, mocker, caplog):
        # Mock re.search to raise an error to simulate an internal failure
        mocker.patch('re.search', side_effect=Exception("Regex search failed"))
        price = local_product_service._extract_price_from_keyword("1 juta")
        assert price is None
        assert "Error extracting price from keyword: Regex search failed" in caplog.text


    # Test get_product_details method
    def test_get_product_details_found(self, local_product_service):
        product = local_product_service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == "prod1"
        assert product['name'] == "Smartphone X"

    def test_get_product_details_not_found(self, local_product_service):
        product = local_product_service.get_product_details("nonexistent")
        assert product is None

    def test_get_product_details_empty_products(self, mocker):
        # Patch _load_local_products to ensure the service initializes with an empty list
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        product = service.get_product_details("prod1")
        assert product is None

    def test_get_product_details_error_handling(self, local_product_service, mocker, caplog):
        # Force `self.products` to be an object that will raise an error upon iteration
        local_product_service.products = None
        product = local_product_service.get_product_details("prod1")
        assert product is None
        assert "Error getting product details: 'NoneType' object is not iterable" in caplog.text


    # Test get_categories method
    def test_get_categories_success(self, local_product_service):
        categories = local_product_service.get_categories()
        # Based on sample_raw_products_data: Electronics, Audio, Wearables
        assert sorted(categories) == ["Audio", "Electronics", "Wearables"]

    def test_get_categories_empty_products(self, mocker):
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        categories = service.get_categories()
        assert categories == []

    def test_get_categories_with_missing_category_key(self, mocker):
        # Mock `_load_local_products` to return products with some missing 'category' keys.
        # The transformation ensures a 'category' key exists (defaults to '').
        transformed_products = [
            {"id": "p1", "name": "No Category Product", "category": "", "specifications":{}},
            {"id": "p2", "name": "Has Category", "category": "TestCat", "specifications":{}}
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=transformed_products)
        service = LocalProductService()
        categories = service.get_categories()
        assert sorted(categories) == ["", "TestCat"]


    # Test get_brands method
    def test_get_brands_success(self, local_product_service):
        brands = local_product_service.get_brands()
        # Based on sample_raw_products_data: Brand A, Brand B, Brand C, Brand D, Brand E
        assert sorted(brands) == ["Brand A", "Brand B", "Brand C", "Brand D", "Brand E"]

    def test_get_brands_empty_products(self, mocker):
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        brands = service.get_brands()
        assert brands == []

    def test_get_brands_with_missing_brand_key(self, mocker):
        # Mock `_load_local_products` to return products with some missing 'brand' keys.
        # The transformation ensures a 'brand' key exists (defaults to '').
        transformed_products = [
            {"id": "p1", "name": "No Brand Product", "brand": "", "specifications":{}},
            {"id": "p2", "name": "Has Brand", "brand": "TestBrand", "specifications":{}}
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=transformed_products)
        service = LocalProductService()
        brands = service.get_brands()
        assert sorted(brands) == ["", "TestBrand"]


    # Test get_products_by_category method
    def test_get_products_by_category_found(self, local_product_service):
        products = local_product_service.get_products_by_category("electronics")
        assert len(products) == 5 # prod1, prod2, prod4, prod6, prod7
        assert all(p['category'] == 'Electronics' for p in products)

    def test_get_products_by_category_no_match(self, local_product_service):
        products = local_product_service.get_products_by_category("nonexistent")
        assert len(products) == 0

    def test_get_products_by_category_empty_category_name(self, local_product_service):
        # Mock `products` directly to include a product with an empty category
        mocker.patch.object(local_product_service, 'products', [
            {'id': 'p1', 'category': 'Electronics', 'name': 'P1', 'specifications':{}},
            {'id': 'p2', 'category': '', 'name': 'P2', 'specifications':{}}
        ])
        products = local_product_service.get_products_by_category("")
        assert len(products) == 1
        assert products[0]['id'] == 'p2'

    def test_get_products_by_category_error_handling(self, local_product_service, mocker, caplog):
        local_product_service.products = None
        products = local_product_service.get_products_by_category("electronics")
        assert len(products) == 0
        assert "Error getting products by category: 'NoneType' object is not iterable" in caplog.text


    # Test get_products_by_brand method
    def test_get_products_by_brand_found(self, local_product_service):
        products = local_product_service.get_products_by_brand("brand a")
        assert len(products) == 2 # prod1, prod3
        assert all(p['brand'] == 'Brand A' for p in products)

    def test_get_products_by_brand_no_match(self, local_product_service):
        products = local_product_service.get_products_by_brand("nonexistent brand")
        assert len(products) == 0

    def test_get_products_by_brand_empty_brand_name(self, local_product_service):
        # Mock `products` directly to include a product with an empty brand
        mocker.patch.object(local_product_service, 'products', [
            {'id': 'p1', 'brand': 'Brand A', 'name': 'P1', 'specifications':{}},
            {'id': 'p2', 'brand': '', 'name': 'P2', 'specifications':{}}
        ])
        products = local_product_service.get_products_by_brand("")
        assert len(products) == 1
        assert products[0]['id'] == 'p2'

    def test_get_products_by_brand_error_handling(self, local_product_service, mocker, caplog):
        local_product_service.products = None
        products = local_product_service.get_products_by_brand("brand a")
        assert len(products) == 0
        assert "Error getting products by brand: 'NoneType' object is not iterable" in caplog.text


    # Test get_top_rated_products method
    def test_get_top_rated_products_success(self, local_product_service):
        # Expected order by rating (highest first): prod2 (4.8), prod1 (4.5), prod8 (4.3)
        top_products = local_product_service.get_top_rated_products(limit=3)
        assert len(top_products) == 3
        assert top_products[0]['id'] == 'prod2'
        assert top_products[1]['id'] == 'prod1'
        assert top_products[2]['id'] == 'prod8'

    def test_get_top_rated_products_no_limit(self, local_product_service):
        top_products = local_product_service.get_top_rated_products() # Default limit is 5
        assert len(top_products) == 5

    def test_get_top_rated_products_limit_greater_than_total(self, local_product_service):
        top_products = local_product_service.get_top_rated_products(limit=100)
        assert len(top_products) == 8 # All products from sample data

    def test_get_top_rated_products_empty_products(self, mocker):
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        top_products = service.get_top_rated_products()
        assert top_products == []

    def test_get_top_rated_products_missing_rating_key(self, mocker):
        # Mock `_load_local_products` to return products where 'rating' might be missing.
        # The transformation ensures `specifications` and `rating` exist (defaults to 0).
        transformed_products = [
            {'id': 'p1', 'name': 'P1', 'specifications': {'stock': 10, 'sold': 500}}, # No rating
            {'id': 'p2', 'name': 'P2', 'specifications': {'rating': 5.0, 'sold': 500}},
            {'id': 'p3', 'name': 'P3', 'specifications': {'stock': 10, 'sold': 500}} # No rating here either
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=transformed_products)
        service = LocalProductService()
        top_products = service.get_top_rated_products(limit=2)
        assert len(top_products) == 2
        assert top_products[0]['id'] == 'p2' # 5.0 rating
        # The other products will have default rating 0. Order between them depends on stability.
        assert top_products[1]['id'] == 'p1' # Assuming 'p1' comes before 'p3' and stable sort


    def test_get_top_rated_products_error_handling(self, local_product_service, mocker, caplog):
        local_product_service.products = None
        products = local_product_service.get_top_rated_products()
        assert len(products) == 0
        assert "Error getting top rated products: 'NoneType' object is not iterable" in caplog.text


    # Test get_best_selling_products method
    def test_get_best_selling_products_success(self, local_product_service, caplog):
        # Products sorted by 'sold' count (highest first):
        # prod8 (2000), prod5 (1800), prod3 (1500), then the rest (prod1, prod2, prod4, prod6, prod7) all have 500
        best_products = local_product_service.get_best_selling_products(limit=4)
        assert len(best_products) == 4
        assert best_products[0]['id'] == 'prod8'
        assert best_products[1]['id'] == 'prod5'
        assert best_products[2]['id'] == 'prod3'
        assert best_products[3]['specifications']['sold'] == 500 # The fourth one should be one of the products with 500 sold

        assert "Getting best selling products, limit: 4" in caplog.text
        assert "Returning 4 best selling products" in caplog.text

    def test_get_best_selling_products_empty_products(self, mocker):
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        best_products = service.get_best_selling_products()
        assert best_products == []

    def test_get_best_selling_products_missing_sold_key(self, mocker):
        # Mock `_load_local_products` to return products with some missing 'sold' keys.
        # The transformation ensures `specifications` and `sold` exist (defaults to random value, here patched to 500).
        transformed_products = [
            {'id': 'p1', 'name': 'P1', 'specifications': {'stock': 10, 'sold': 500}}, # From random.randint patch
            {'id': 'p2', 'name': 'P2', 'specifications': {'stock': 10, 'sold': 1000}}, # Explicit 1000
            {'id': 'p3', 'name': 'P3', 'specifications': {'stock': 10}} # No sold, gets 500 from random.randint patch
        ]
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=transformed_products)
        service = LocalProductService()
        best_products = service.get_best_selling_products(limit=2)
        assert len(best_products) == 2
        assert best_products[0]['id'] == 'p2' # 1000 sold
        # Between p1 and p3, if both have 500 sold, their relative order is maintained due to stable sort.
        assert best_products[1]['id'] == 'p1' # based on their original order in transformed_products


    def test_get_best_selling_products_error_handling(self, local_product_service, mocker, caplog):
        local_product_service.products = None
        products = local_product_service.get_best_selling_products()
        assert len(products) == 0
        assert "Error getting best selling products: 'NoneType' object is not iterable" in caplog.text


    # Test get_products method
    def test_get_products_success(self, local_product_service, caplog):
        products = local_product_service.get_products(limit=5)
        assert len(products) == 5
        assert products[0]['id'] == 'prod1'
        assert "Getting all products, limit: 5" in caplog.text

    def test_get_products_no_limit_specified(self, local_product_service):
        products = local_product_service.get_products() # Default limit is 10
        assert len(products) == 8 # All 8 products from sample data

    def test_get_products_limit_greater_than_total(self, local_product_service):
        products = local_product_service.get_products(limit=100)
        assert len(products) == 8

    def test_get_products_empty_products(self, mocker):
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        products = service.get_products()
        assert products == []

    def test_get_products_error_handling(self, local_product_service, mocker, caplog):
        local_product_service.products = None
        products = local_product_service.get_products()
        assert len(products) == 0
        assert "Error getting products: 'NoneType' object is not iterable" in caplog.text


    # Test smart_search_products method (complex multi-stage fallback search)

    # Path 1: "best"/"terbaik" keyword without specific category
    def test_smart_search_best_general(self, local_product_service):
        products, message = local_product_service.smart_search_products(keyword="terbaik")
        # Should return top 5 rated products overall
        assert len(products) == 5
        assert products[0]['id'] == 'prod2' # Rating 4.8
        assert products[1]['id'] == 'prod1' # Rating 4.5
        assert products[2]['id'] == 'prod8' # Rating 4.3
        assert "Berikut produk terbaik berdasarkan rating:" in message

    # Path 2: "best"/"terbaik" keyword with a specific, existing category
    def test_smart_search_best_with_category(self, local_product_service):
        products, message = local_product_service.smart_search_products(keyword="best", category="Electronics")
        # Filter 'Electronics' products and sort by rating: prod2 (4.8), prod1 (4.5), prod4 (4.0), prod6 (3.9), prod7 (3.5)
        assert len(products) == 5
        assert products[0]['id'] == 'prod2'
        assert products[1]['id'] == 'prod1'
        assert "Berikut Electronics terbaik berdasarkan rating:" in message

    # Path 2b: "best"/"terbaik" keyword with a non-existent category (fallback to general best)
    def test_smart_search_best_with_nonexistent_category(self, local_product_service):
        products, message = local_product_service.smart_search_products(keyword="terbaik", category="Furniture")
        # Should fallback to general best products if category not found
        assert len(products) == 5
        assert products[0]['id'] == 'prod2'
        assert "Tidak ada produk kategori Furniture, berikut produk terbaik secara umum:" in message
    
    # Path 3: All criteria (keyword, category, max_price) match
    def test_smart_search_all_criteria_match(self, local_product_service):
        products, message = local_product_service.smart_search_products(
            keyword="smartphone", category="Electronics", max_price=5000000, limit=2
        )
        # Only 'Smartphone G' (prod6) matches all: it's a smartphone, in electronics, and price (4M) <= 5M.
        assert len(products) == 1
        assert products[0]['id'] == 'prod6'
        assert "Berikut produk yang sesuai dengan kriteria Anda." in message

    # Path 4: Initial full search fails, fallback to category only (sorted by price)
    def test_smart_search_fallback_to_category_only_by_price(self, local_product_service):
        # Search for "nonexistent" keyword in "Electronics" category with max_price 1M (too low).
        # Initial search (keyword, category, price) will yield 0 results.
        # Fallback will then search by category only, and sort by price.
        products, message = local_product_service.smart_search_products(
            keyword="nonexistent", category="Electronics", max_price=1000000
        )
        # Electronics products sorted by price: prod6(4M), prod7(6M), prod4(7.5M), prod1(10M), prod2(15M)
        assert len(products) == 5 # Returns top 'limit' products within category
        assert products[0]['id'] == 'prod6' # Cheapest in electronics category
        assert products[1]['id'] == 'prod7'
        assert "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut." in message

    # Path 5: Initial search and category-only fallback fail, fallback to max_price only
    def test_smart_search_fallback_to_budget_only(self, local_product_service):
        # Search for "nonexistent_monitor" (no match) with max_price 3M. No category provided.
        # Initial search fails. Category-only fallback not applicable.
        # Fallback to max_price only.
        products, message = local_product_service.smart_search_products(
            keyword="nonexistent_monitor", max_price=3000000
        )
        # Products with price <= 3M: prod3 (2M), prod5 (3M), prod8 (1M)
        assert len(products) == 3
        # The order here depends on the original `self.products` list order.
        assert products[0]['id'] == 'prod3'
        assert products[1]['id'] == 'prod5'
        assert products[2]['id'] == 'prod8'
        assert "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda." in message
        
    # Path 6: All specific search and fallback paths fail, fallback to popular products
    def test_smart_search_fallback_to_popular_products(self, local_product_service):
        # Search for something entirely nonexistent, with no matching category or price range.
        products, message = local_product_service.smart_search_products(keyword="xyz_nonexistent", category="NoCategory", max_price=100)
        # Should fallback to best-selling products as the last resort.
        # Best-selling products (based on explicit 'sold' values in sample data):
        # prod8 (2000), prod5 (1800), prod3 (1500), then others with 500.
        assert len(products) == 5 # Returns top 'limit' of popular products
        assert products[0]['id'] == 'prod8'
        assert products[1]['id'] == 'prod5'
        assert products[2]['id'] == 'prod3'
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message

    # Test smart_search_products with empty input (should fallback to popular)
    def test_smart_search_empty_input(self, local_product_service):
        products, message = local_product_service.smart_search_products()
        assert len(products) == 5
        assert products[0]['id'] == 'prod8'
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message

    # Test smart_search_products with custom limit
    def test_smart_search_with_limit(self, local_product_service):
        products, message = local_product_service.smart_search_products(keyword="smartphone", limit=1)
        assert len(products) == 1
        assert products[0]['id'] == 'prod1' # "Smartphone X" matches and has highest relevance score for 'smartphone'

    # Test smart_search_products with empty product list
    def test_smart_search_empty_product_list(self, mocker):
        mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
        service = LocalProductService()
        products, message = service.smart_search_products(keyword="any")
        assert products == []
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message

    # Test smart_search_products error handling (exceptions should propagate as it has no internal try-except)
    def test_smart_search_products_general_exception_propagates(self, local_product_service, mocker):
        # Force an exception to be raised when accessing `self.products`
        mocker.patch.object(local_product_service, 'products', new_callable=mock.PropertyMock, side_effect=Exception("Simulated processing error"))
        
        # smart_search_products does not have a top-level try-except, so the exception should propagate
        with pytest.raises(Exception, match="Simulated processing error"):
            local_product_service.smart_search_products(keyword="test")