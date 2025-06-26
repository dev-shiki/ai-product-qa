import pytest
import sys
import json
import logging
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Add the parent directory to the sys.path to allow imports from app.services
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.local_product_service import LocalProductService

@pytest.fixture
def mock_products_data():
    """Returns a list of mock product dictionaries."""
    return [
        {
            "id": "1",
            "name": "Smartphone A",
            "category": "Smartphone",
            "brand": "BrandX",
            "price": 10000000,
            "currency": "IDR",
            "description": "Powerful smartphone.",
            "specifications": {"rating": 4.5, "sold": 100, "stock": 50, "condition": "Baru", "storage": "128GB"},
            "availability": "in_stock",
            "reviews_count": 10,
            "images": [],
            "url": ""
        },
        {
            "id": "2",
            "name": "Laptop B",
            "category": "Laptop",
            "brand": "BrandY",
            "price": 15000000,
            "currency": "IDR",
            "description": "High-performance laptop.",
            "specifications": {"rating": 4.8, "sold": 200, "stock": 20, "condition": "Baru", "ram": "16GB"},
            "availability": "in_stock",
            "reviews_count": 20,
            "images": [],
            "url": ""
        },
        {
            "id": "3",
            "name": "Headphones C",
            "category": "Audio",
            "brand": "BrandZ",
            "price": 2000000,
            "currency": "IDR",
            "description": "Noise-cancelling headphones.",
            "specifications": {"rating": 4.0, "sold": 50, "stock": 100, "condition": "Baru"},
            "availability": "out_of_stock",
            "reviews_count": 5,
            "images": [],
            "url": ""
        },
        {
            "id": "4",
            "name": "Smartphone X PRO",
            "category": "Smartphone",
            "brand": "BrandX",
            "price": 12000000,
            "currency": "IDR",
            "description": "Next-gen smartphone from BrandX.",
            "specifications": {"rating": 4.7, "sold": 150, "stock": 30, "condition": "Baru", "processor": "Snapdragon"},
            "availability": "in_stock",
            "reviews_count": 15,
            "images": [],
            "url": ""
        },
        {
            "id": "5",
            "name": "Earbuds D",
            "category": "Audio",
            "brand": "BrandA",
            "price": 500000,
            "currency": "IDR",
            "description": "Affordable earbuds.",
            "specifications": {"rating": 3.9, "sold": 300, "stock": 200, "condition": "Baru"},
            "availability": "in_stock",
            "reviews_count": 25,
            "images": [],
            "url": ""
        },
        {
            "id": "6",
            "name": "Tablet Y",
            "category": "Tablet",
            "brand": "BrandY",
            "price": 7000000,
            "currency": "IDR",
            "description": "Portable tablet for work and play.",
            "specifications": {"rating": 4.2, "sold": 80, "stock": 40, "condition": "Baru", "display": "10 inch"},
            "availability": "in_stock",
            "reviews_count": 8,
            "images": [],
            "url": ""
        },
        {
            "id": "7",
            "name": "Gaming Laptop Z",
            "category": "Laptop",
            "brand": "BrandG",
            "price": 25000000,
            "currency": "IDR",
            "description": "Ultimate gaming machine.",
            "specifications": {"rating": 4.9, "sold": 70, "stock": 10, "condition": "Baru", "gpu": "RTX 4090"},
            "availability": "in_stock",
            "reviews_count": 30,
            "images": [],
            "url": ""
        },
        {
            "id": "8",
            "name": "Budget Phone",
            "category": "Smartphone",
            "brand": "BudgetBrand",
            "price": 1500000,
            "currency": "IDR",
            "description": "Good phone for everyday use.",
            "specifications": {"rating": 3.5, "sold": 500, "stock": 60, "condition": "Baru"},
            "availability": "in_stock",
            "reviews_count": 40,
            "images": [],
            "url": ""
        },
        {
            "id": "9",
            "name": "Mystery Item",
            "description": "No category or brand.",
            "price": 10000,
            "specifications": {}
        }
    ]

@pytest.fixture
def service_with_mock_products(mock_products_data):
    """
    Fixture to create LocalProductService instance with a pre-defined list of products.
    This avoids file I/O for most tests.
    """
    with patch('app.services.local_product_service.LocalProductService._load_local_products') as mock_load:
        mock_load.return_value = mock_products_data
        service = LocalProductService()
        return service

@pytest.fixture(autouse=True)
def mock_random_randint():
    """Fixture to ensure random.randint is predictable for tests."""
    with patch('random.randint', return_value=1000):
        yield

@pytest.fixture(autouse=True)
def cap_logs(caplog):
    """Capture logs for testing log messages."""
    caplog.set_level(logging.INFO)
    return caplog

class TestLocalProductServiceInitialization:
    """Tests for the LocalProductService __init__ method."""

    def test_init_success(self, mock_products_data, cap_logs):
        """Test successful initialization and product loading."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products') as mock_load:
            mock_load.return_value = mock_products_data
            service = LocalProductService()
            mock_load.assert_called_once()
            assert service.products == mock_products_data
            assert f"Loaded {len(mock_products_data)} local products from JSON file" in cap_logs.text

    def test_init_load_failure_uses_fallback(self, cap_logs):
        """Test initialization when _load_local_products fails."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', side_effect=Exception("Loading error")) as mock_load:
            with patch('app.services.local_product_service.LocalProductService._get_fallback_products') as mock_fallback:
                mock_fallback.return_value = [{"id": "fallback"}]
                service = LocalProductService()
                mock_load.assert_called_once()
                mock_fallback.assert_called_once()
                assert service.products == [{"id": "fallback"}]
                assert "Error loading products from JSON file" in cap_logs.text
                assert "Using fallback products due to JSON file loading error" in cap_logs.text

class TestLoadLocalProducts:
    """Tests for the _load_local_products method."""

    @pytest.fixture(autouse=True)
    def setup_path_mock(self):
        """Mock Path.__truediv__ to return a dummy path object for all _load_local_products tests."""
        with patch('pathlib.Path.__truediv__', new_callable=MagicMock) as mock_div:
            mock_path_obj = MagicMock()
            mock_div.return_value = mock_path_obj
            yield mock_path_obj

    def test_load_local_products_file_not_found(self, cap_logs, setup_path_mock):
        """Test _load_local_products when the JSON file does not exist."""
        setup_path_mock.exists.return_value = False
        service = LocalProductService()
        with patch.object(service, '_get_fallback_products') as mock_fallback:
            mock_fallback.return_value = [{"id": "fallback_prod"}]
            products = service._load_local_products()
            setup_path_mock.exists.assert_called_once()
            mock_fallback.assert_called_once()
            assert products == [{"id": "fallback_prod"}]
            assert "Products JSON file not found at:" in cap_logs.text

    def test_load_local_products_success_utf8(self, cap_logs, mock_products_data, setup_path_mock):
        """Test successful loading with UTF-8 encoding."""
        setup_path_mock.exists.return_value = True
        json_content = json.dumps({"products": mock_products_data})
        with patch('builtins.open', mock_open(read_data=json_content)) as m_open:
            service = LocalProductService()
            products = service._load_local_products()
            # It will try utf-16-le, utf-16, then utf-8 (which succeeds here)
            assert m_open.call_args_list[0].kwargs['encoding'] == 'utf-16-le'
            assert m_open.call_args_list[1].kwargs['encoding'] == 'utf-16'
            assert m_open.call_args_list[2].kwargs['encoding'] == 'utf-8'
            assert len(products) == len(mock_products_data)
            assert products[0]['id'] == mock_products_data[0]['id']
            assert "Successfully loaded" in cap_logs.text
            assert "using utf-8 encoding" in cap_logs.text
            assert products[0]['specifications']['sold'] == 1000 # Mocked random.randint
            assert products[0]['images'] == [f"https://example.com/{products[0]['id']}.jpg"]
            assert products[0]['url'] == f"https://shopee.co.id/{products[0]['id']}"
            assert products[0]['specifications']['condition'] == "Baru"
            assert products[0]['specifications']['shop_location'] == "Indonesia"
            assert products[0]['specifications']['shop_name'] == f"{mock_products_data[0].get('brand')} Store"
            assert products[8]['specifications']['rating'] == 0 # Product 9 has no rating

    def test_load_local_products_success_with_bom(self, cap_logs, mock_products_data, setup_path_mock):
        """Test successful loading with UTF-8 BOM, handled by utf-8-sig or explicit strip."""
        setup_path_mock.exists.return_value = True
        json_content = '\ufeff' + json.dumps({"products": mock_products_data})
        with patch('builtins.open', mock_open(read_data=json_content)) as m_open:
            # Simulate earlier encodings failing
            m_open.side_effect = [
                UnicodeDecodeError('utf-16-le', b'', 0, 1, 'reason'),
                UnicodeDecodeError('utf-16', b'', 0, 1, 'reason'),
                UnicodeDecodeError('utf-8', b'', 0, 1, 'reason'),
                mock_open(read_data=json_content).return_value # utf-8-sig should succeed
            ]
            service = LocalProductService()
            products = service._load_local_products()
            assert len(products) == len(mock_products_data)
            assert products[0]['name'] == mock_products_data[0]['name']
            assert "Successfully loaded" in cap_logs.text
            assert "using utf-8-sig encoding" in cap_logs.text # Check which encoding succeeded

    def test_load_local_products_empty_json_file(self, cap_logs, setup_path_mock):
        """Test loading an empty JSON file (should return empty list)."""
        setup_path_mock.exists.return_value = True
        json_content = '{"products": []}'
        with patch('builtins.open', mock_open(read_data=json_content)) as m_open:
            service = LocalProductService()
            products = service._load_local_products()
            assert products == []
            assert "Successfully loaded 0 products from JSON file" in cap_logs.text

    def test_load_local_products_malformed_json_fallback(self, cap_logs, setup_path_mock):
        """Test _load_local_products with malformed JSON, leading to JSONDecodeError and fallback."""
        setup_path_mock.exists.return_value = True
        bad_json_content = '{"products": [ { "id": "1", "name": "Test", } ]' # malformed
        with patch('builtins.open', mock_open(read_data=bad_json_content)) as m_open:
            m_open.side_effect = [
                UnicodeDecodeError('utf-16-le', b'', 0, 1, 'reason'),
                UnicodeDecodeError('utf-16', b'', 0, 1, 'reason'),
                mock_open(read_data=bad_json_content).return_value, # for utf-8, will cause JSONDecodeError
                mock_open(read_data=bad_json_content).return_value, # for utf-8-sig
                mock_open(read_data=bad_json_content).return_value, # for latin-1
                mock_open(read_data=bad_json_content).return_value, # for cp1252
            ]

            service = LocalProductService()
            with patch.object(service, '_get_fallback_products') as mock_fallback:
                mock_fallback.return_value = [{"id": "fallback_prod"}]
                products = service._load_local_products()
                assert products == [{"id": "fallback_prod"}]
                assert "Failed to load with utf-16-le encoding" in cap_logs.text
                assert "Failed to load with utf-8 encoding" in cap_logs.text
                assert "All encoding attempts failed, using fallback products" in cap_logs.text
                mock_fallback.assert_called_once()

    def test_load_local_products_unicode_decode_error_for_all_encodings(self, cap_logs, setup_path_mock):
        """Test _load_local_products when all encoding attempts fail with UnicodeDecodeError."""
        setup_path_mock.exists.return_value = True
        with patch('builtins.open', mock_open(read_data='')) as m_open:
            m_open.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'reason') # Make all attempts fail
            service = LocalProductService()
            with patch.object(service, '_get_fallback_products') as mock_fallback:
                mock_fallback.return_value = [{"id": "fallback_prod"}]
                products = service._load_local_products()
                assert products == [{"id": "fallback_prod"}]
                assert "Failed to load with utf-16-le encoding" in cap_logs.text
                assert "Failed to load with cp1252 encoding" in cap_logs.text
                assert "All encoding attempts failed, using fallback products" in cap_logs.text
                mock_fallback.assert_called_once()

    def test_load_local_products_general_exception(self, cap_logs, setup_path_mock):
        """Test _load_local_products handles a general Exception during file loading."""
        setup_path_mock.exists.return_value = True
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            service = LocalProductService()
            with patch.object(service, '_get_fallback_products') as mock_fallback:
                mock_fallback.return_value = [{"id": "fallback_prod"}]
                products = service._load_local_products()
                assert products == [{"id": "fallback_prod"}]
                assert "Error loading products from JSON file: Permission denied" in cap_logs.text
                mock_fallback.assert_called_once()

class TestGetFallbackProducts:
    """Tests for the _get_fallback_products method."""

    def test_get_fallback_products(self, cap_logs):
        """Test that _get_fallback_products returns the expected hardcoded list."""
        service = LocalProductService()
        products = service._get_fallback_products()
        assert isinstance(products, list)
        assert len(products) > 0
        assert "iPhone 15 Pro Max" in [p['name'] for p in products]
        assert "Using fallback products due to JSON file loading error" in cap_logs.text

class TestSearchProducts:
    """Tests for the search_products method."""

    def test_search_products_by_name(self, service_with_mock_products):
        """Test searching products by name keyword."""
        results = service_with_mock_products.search_products(keyword="smartphone")
        assert len(results) == 3
        assert all("smartphone" in p['name'].lower() for p in results)

    def test_search_products_by_description(self, service_with_mock_products):
        """Test searching products by description keyword."""
        results = service_with_mock_products.search_products(keyword="high-performance")
        assert len(results) == 1
        assert results[0]['name'] == "Laptop B"

    def test_search_products_by_category(self, service_with_mock_products):
        """Test searching products by category keyword."""
        results = service_with_mock_products.search_products(keyword="audio")
        assert len(results) == 2
        assert all("audio" in p['category'].lower() for p in results)

    def test_search_products_by_brand(self, service_with_mock_products):
        """Test searching products by brand keyword."""
        results = service_with_mock_products.search_products(keyword="brandx")
        assert len(results) == 2

    def test_search_products_by_specifications(self, service_with_mock_products):
        """Test searching products by specification keyword."""
        results = service_with_mock_products.search_products(keyword="snapdragon")
        assert len(results) == 1
        assert results[0]['name'] == "Smartphone X PRO"

    def test_search_products_case_insensitive(self, service_with_mock_products):
        """Test search is case-insensitive."""
        results = service_with_mock_products.search_products(keyword="smartPhone")
        assert len(results) == 3

    def test_search_products_limit(self, service_with_mock_products):
        """Test the limit parameter."""
        results = service_with_mock_products.search_products(keyword="smartphone", limit=2)
        assert len(results) == 2

    def test_search_products_no_match(self, service_with_mock_products):
        """Test searching for a keyword with no matches."""
        results = service_with_mock_products.search_products(keyword="nonexistent")
        assert len(results) == 0

    def test_search_products_empty_keyword_returns_all_limited(self, service_with_mock_products):
        """Test searching with an empty keyword returns all products up to limit."""
        results = service_with_mock_products.search_products(keyword="", limit=3)
        assert len(results) == 3

    def test_search_products_with_price_range_keyword(self, service_with_mock_products):
        """Test searching with a price range keyword like 'smartphone 11 juta'."""
        results = service_with_mock_products.search_products(keyword="smartphone 11 juta")
        assert len(results) == 2
        assert "Smartphone A" in [p['name'] for p in results]
        assert "Budget Phone" in [p['name'] for p in results]
        assert "Smartphone X PRO" not in [p['name'] for p in results]

    def test_search_products_relevance_sorting(self, service_with_mock_products):
        """Test product relevance sorting."""
        results = service_with_mock_products.search_products(keyword="BrandX", limit=3)
        assert results[0]['name'] == "Smartphone A"
        assert results[1]['name'] == "Smartphone X PRO"

    def test_search_products_relevance_sorting_budget(self, service_with_mock_products):
        """Test product relevance sorting for budget keywords (lower price preferred)."""
        results = service_with_mock_products.search_products(keyword="phone murah", limit=2)
        assert results[0]['name'] == "Budget Phone"
        assert results[1]['name'] == "Smartphone A"
        assert results[0]['price'] < results[1]['price']

    def test_search_products_error_handling(self, service_with_mock_products, cap_logs):
        """Test error handling in search_products."""
        with patch.object(service_with_mock_products, '_extract_price_from_keyword', side_effect=Exception("Price extract error")):
            results = service_with_mock_products.search_products(keyword="test")
            assert results == []
            assert "Error searching products: Price extract error" in cap_logs.text

class TestExtractPriceFromKeyword:
    """Tests for the _extract_price_from_keyword method."""

    @pytest.fixture
    def service_for_price_extraction(self):
        """Fixture for an instance of LocalProductService (does not need products loaded)."""
        return LocalProductService()

    @pytest.mark.parametrize("keyword, expected_price", [
        ("smartphone 10 juta", 10000000),
        ("laptop 5 ribu", 5000),
        ("rp 250000 headphones", 250000),
        ("300000rp speaker", 300000),
        ("monitor 2k", 2000),
        ("camera 1m", 1000000),
        ("mouse murah", 5000000),
        ("tablet budget", 5000000),
        ("keyboard hemat", 3000000),
        ("tv terjangkau", 4000000),
        ("smartwatch ekonomis", 2000000),
        ("no price here", None),
        ("10 juta 5 ribu", 10000000),
        ("5 ribu 10 juta", 5000),
    ])
    def test_extract_price_from_keyword_valid_patterns(self, service_for_price_extraction, keyword, expected_price):
        """Test various valid price extraction patterns."""
        assert service_for_price_extraction._extract_price_from_keyword(keyword) == expected_price

    def test_extract_price_from_keyword_no_match(self, service_for_price_extraction):
        """Test when no price or budget keyword is found."""
        assert service_for_price_extraction._extract_price_from_keyword("some random text") is None

    def test_extract_price_from_keyword_error_handling(self, service_for_price_extraction, cap_logs):
        """Test error handling in _extract_price_from_keyword."""
        with patch('re.search', side_effect=Exception("Regex error")):
            result = service_for_price_extraction._extract_price_from_keyword("10 juta")
            assert result is None
            assert "Error extracting price from keyword: Regex error" in cap_logs.text

class TestGetProductDetails:
    """Tests for the get_product_details method."""

    def test_get_product_details_existing_id(self, service_with_mock_products):
        """Test retrieving details for an existing product ID."""
        product = service_with_mock_products.get_product_details("1")
        assert product is not None
        assert product['name'] == "Smartphone A"

    def test_get_product_details_non_existent_id(self, service_with_mock_products):
        """Test retrieving details for a non-existent product ID."""
        product = service_with_mock_products.get_product_details("999")
        assert product is None

    def test_get_product_details_empty_id(self, service_with_mock_products):
        """Test retrieving details with an empty product ID."""
        product = service_with_mock_products.get_product_details("")
        assert product is None

    def test_get_product_details_error_handling(self, service_with_mock_products, cap_logs):
        """Test error handling in get_product_details."""
        with patch.object(service_with_mock_products, 'products', new_callable=MagicMock) as mock_products_list:
            mock_products_list.__iter__.side_effect = Exception("Iteration error")
            result = service_with_mock_products.get_product_details("1")
            assert result is None
            assert "Error getting product details: Iteration error" in cap_logs.text

class TestGetCategories:
    """Tests for the get_categories method."""

    def test_get_categories_success(self, service_with_mock_products):
        """Test successful retrieval of unique sorted categories."""
        categories = service_with_mock_products.get_categories()
        expected_categories = sorted(['Smartphone', 'Laptop', 'Audio', 'Tablet', ''])
        assert categories == expected_categories

    def test_get_categories_empty_product_list(self):
        """Test get_categories with an empty product list."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            categories = service.get_categories()
            assert categories == []

class TestGetBrands:
    """Tests for the get_brands method."""

    def test_get_brands_success(self, service_with_mock_products):
        """Test successful retrieval of unique sorted brands."""
        brands = service_with_mock_products.get_brands()
        expected_brands = sorted(['BrandX', 'BrandY', 'BrandZ', 'BrandA', 'BrandG', 'BudgetBrand', ''])
        assert brands == expected_brands

    def test_get_brands_empty_product_list(self):
        """Test get_brands with an empty product list."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            brands = service.get_brands()
            assert brands == []

class TestGetProductsByCategory:
    """Tests for the get_products_by_category method."""

    def test_get_products_by_category_valid(self, service_with_mock_products):
        """Test retrieving products by a valid category."""
        products = service_with_mock_products.get_products_by_category("Smartphone")
        assert len(products) == 3
        assert all("smartphone" in p['category'].lower() for p in products)
        assert "Smartphone A" in [p['name'] for p in products]

    def test_get_products_by_category_case_insensitive(self, service_with_mock_products):
        """Test category search is case-insensitive."""
        products = service_with_mock_products.get_products_by_category("smartphone")
        assert len(products) == 3

    def test_get_products_by_category_non_existent(self, service_with_mock_products):
        """Test retrieving products for a non-existent category."""
        products = service_with_mock_products.get_products_by_category("Electronics")
        assert products == []

    def test_get_products_by_category_empty_string(self, service_with_mock_products):
        """Test retrieving products with an empty category string."""
        products = service_with_mock_products.get_products_by_category("")
        assert len(products) == 1
        assert products[0]['id'] == "9"

    def test_get_products_by_category_error_handling(self, service_with_mock_products, cap_logs):
        """Test error handling in get_products_by_category."""
        with patch.object(service_with_mock_products, 'products', new_callable=MagicMock) as mock_products_list:
            mock_products_list.__iter__.side_effect = Exception("Category iteration error")
            results = service_with_mock_products.get_products_by_category("Laptop")
            assert results == []
            assert "Error getting products by category: Category iteration error" in cap_logs.text

class TestGetProductsByBrand:
    """Tests for the get_products_by_brand method."""

    def test_get_products_by_brand_valid(self, service_with_mock_products):
        """Test retrieving products by a valid brand."""
        products = service_with_mock_products.get_products_by_brand("BrandX")
        assert len(products) == 2
        assert all("brandx" in p['brand'].lower() for p in products)
        assert "Smartphone A" in [p['name'] for p in products]

    def test_get_products_by_brand_case_insensitive(self, service_with_mock_products):
        """Test brand search is case-insensitive."""
        products = service_with_mock_products.get_products_by_brand("brandx")
        assert len(products) == 2

    def test_get_products_by_brand_non_existent(self, service_with_mock_products):
        """Test retrieving products for a non-existent brand."""
        products = service_with_mock_products.get_products_by_brand("NoBrand")
        assert products == []

    def test_get_products_by_brand_empty_string(self, service_with_mock_products):
        """Test retrieving products with an empty brand string."""
        products = service_with_mock_products.get_products_by_brand("")
        assert len(products) == 1
        assert products[0]['id'] == "9"

    def test_get_products_by_brand_error_handling(self, service_with_mock_products, cap_logs):
        """Test error handling in get_products_by_brand."""
        with patch.object(service_with_mock_products, 'products', new_callable=MagicMock) as mock_products_list:
            mock_products_list.__iter__.side_effect = Exception("Brand iteration error")
            results = service_with_mock_products.get_products_by_brand("BrandX")
            assert results == []
            assert "Error getting products by brand: Brand iteration error" in cap_logs.text

class TestGetTopRatedProducts:
    """Tests for the get_top_rated_products method."""

    def test_get_top_rated_products_success(self, service_with_mock_products):
        """Test retrieving top-rated products with default limit."""
        products = service_with_mock_products.get_top_rated_products()
        assert len(products) == 5
        assert products[0]['name'] == "Gaming Laptop Z"
        assert products[1]['name'] == "Laptop B"
        assert products[2]['name'] == "Smartphone X PRO"
        assert products[3]['name'] == "Smartphone A"
        assert products[4]['name'] == "Tablet Y"

    def test_get_top_rated_products_custom_limit(self, service_with_mock_products):
        """Test retrieving top-rated products with a custom limit."""
        products = service_with_mock_products.get_top_rated_products(limit=2)
        assert len(products) == 2
        assert products[0]['name'] == "Gaming Laptop Z"
        assert products[1]['name'] == "Laptop B"

    def test_get_top_rated_products_limit_greater_than_available(self, service_with_mock_products):
        """Test limit greater than available products."""
        products = service_with_mock_products.get_top_rated_products(limit=20)
        assert len(products) == 9

    def test_get_top_rated_products_no_rating(self, service_with_mock_products):
        """Test products without a rating key are handled (default to 0)."""
        products = service_with_mock_products.get_top_rated_products(limit=9)
        assert products[-1]['id'] == "9"

    def test_get_top_rated_products_empty_list(self):
        """Test when product list is empty."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            products = service.get_top_rated_products()
            assert products == []

    def test_get_top_rated_products_error_handling(self, service_with_mock_products, cap_logs):
        """Test error handling in get_top_rated_products."""
        with patch.object(service_with_mock_products, 'products', new_callable=MagicMock) as mock_products_list:
            mock_products_list.sort.side_effect = Exception("Sort error")
            results = service_with_mock_products.get_top_rated_products()
            assert results == []
            assert "Error getting top rated products: Sort error" in cap_logs.text

class TestGetBestSellingProducts:
    """Tests for the get_best_selling_products method."""

    def test_get_best_selling_products_success(self, service_with_mock_products, cap_logs):
        """Test retrieving best-selling products with default limit."""
        products = service_with_mock_products.get_best_selling_products()
        assert len(products) == 5
        assert products[0]['name'] == "Budget Phone"
        assert products[1]['name'] == "Earbuds D"
        assert products[2]['name'] == "Laptop B"
        assert products[3]['name'] == "Smartphone X PRO"
        assert products[4]['name'] == "Smartphone A"
        assert "Getting best selling products, limit: 5" in cap_logs.text
        assert "Returning 5 best selling products" in cap_logs.text

    def test_get_best_selling_products_custom_limit(self, service_with_mock_products):
        """Test retrieving best-selling products with a custom limit."""
        products = service_with_mock_products.get_best_selling_products(limit=2)
        assert len(products) == 2
        assert products[0]['name'] == "Budget Phone"
        assert products[1]['name'] == "Earbuds D"

    def test_get_best_selling_products_limit_greater_than_available(self, service_with_mock_products):
        """Test limit greater than available products."""
        products = service_with_mock_products.get_best_selling_products(limit=20)
        assert len(products) == 9

    def test_get_best_selling_products_no_sold_count(self, service_with_mock_products):
        """Test products without a sold count key are handled (default to 0)."""
        products = service_with_mock_products.get_best_selling_products(limit=9)
        assert products[-1]['id'] == "9"

    def test_get_best_selling_products_empty_list(self):
        """Test when product list is empty."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            products = service.get_best_selling_products()
            assert products == []

    def test_get_best_selling_products_error_handling(self, service_with_mock_products, cap_logs):
        """Test error handling in get_best_selling_products."""
        with patch.object(service_with_mock_products, 'products', new_callable=MagicMock) as mock_products_list:
            mock_products_list.sort.side_effect = Exception("Sort error")
            results = service_with_mock_products.get_best_selling_products()
            assert results == []
            assert "Error getting best selling products: Sort error" in cap_logs.text

class TestGetProducts:
    """Tests for the get_products method."""

    def test_get_products_success_default_limit(self, service_with_mock_products, cap_logs):
        """Test retrieving all products with default limit."""
        products = service_with_mock_products.get_products()
        assert len(products) == min(10, len(service_with_mock_products.products))
        assert products[0]['name'] == "Smartphone A"
        assert "Getting all products, limit: 10" in cap_logs.text

    def test_get_products_custom_limit(self, service_with_mock_products):
        """Test retrieving all products with a custom limit."""
        products = service_with_mock_products.get_products(limit=3)
        assert len(products) == 3
        assert products[0]['name'] == "Smartphone A"
        assert products[2]['name'] == "Headphones C"

    def test_get_products_limit_greater_than_available(self, service_with_mock_products):
        """Test limit greater than available products."""
        products = service_with_mock_products.get_products(limit=20)
        assert len(products) == 9

    def test_get_products_empty_list(self):
        """Test when product list is empty."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            products = service.get_products()
            assert products == []

    def test_get_products_error_handling(self, service_with_mock_products, cap_logs):
        """Test error handling in get_products."""
        with patch.object(service_with_mock_products, 'products', side_effect=Exception("Product list error")):
            results = service_with_mock_products.get_products()
            assert results == []
            assert "Error getting products: Product list error" in cap_logs.text

class TestSmartSearchProducts:
    """Tests for the smart_search_products method, covering all fallback scenarios."""

    def test_smart_search_best_no_category(self, service_with_mock_products):
        """Test smart search for 'terbaik' without category, returns top-rated general."""
        products, message = service_with_mock_products.smart_search_products(keyword="produk terbaik")
        assert len(products) == 5
        assert products[0]['name'] == "Gaming Laptop Z"
        assert message == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_best_with_category_found(self, service_with_mock_products):
        """Test smart search for 'terbaik' with existing category, returns top-rated in category."""
        products, message = service_with_mock_products.smart_search_products(keyword="smartphone terbaik", category="Smartphone")
        assert len(products) == 3
        assert products[0]['name'] == "Smartphone X PRO"
        assert products[1]['name'] == "Smartphone A"
        assert products[2]['name'] == "Budget Phone"
        assert message == "Berikut Smartphone terbaik berdasarkan rating:"

    def test_smart_search_best_with_category_not_found_fallback(self, service_with_mock_products):
        """Test smart search for 'terbaik' with non-existent category, falls back to general top-rated."""
        products, message = service_with_mock_products.smart_search_products(keyword="terbaik tv", category="Television")
        assert len(products) == 5
        assert products[0]['name'] == "Gaming Laptop Z"
        assert message == "Tidak ada produk kategori Television, berikut produk terbaik secara umum:"

    def test_smart_search_all_criteria_match(self, service_with_mock_products):
        """Test smart search with keyword, category, and max_price matching."""
        products, message = service_with_mock_products.smart_search_products(
            keyword="smartphone", category="Smartphone", max_price=11000000, limit=2
        )
        assert len(products) == 2
        assert "Smartphone A" in [p['name'] for p in products]
        assert "Budget Phone" in [p['name'] for p in products]
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_fallback_to_category_only(self, service_with_mock_products):
        """Test smart search when keyword/price criteria don't match, falls back to category."""
        products, message = service_with_mock_products.smart_search_products(
            keyword="nonexistent", category="Laptop", max_price=1000000
        )
        assert len(products) == 2
        assert products[0]['name'] == "Laptop B"
        assert products[1]['name'] == "Gaming Laptop Z"
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_fallback_to_budget_only(self, service_with_mock_products):
        """Test smart search when category criteria doesn't match, falls back to budget."""
        products, message = service_with_mock_products.smart_search_products(
            keyword="nonexistent", category="UnknownCategory", max_price=2000000
        )
        assert len(products) == 2
        assert products[0]['name'] == "Earbuds D"
        assert products[1]['name'] == "Headphones C"
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_fallback_to_popular(self, service_with_mock_products):
        """Test smart search when no specific criteria match, falls back to popular products."""
        products, message = service_with_mock_products.smart_search_products(
            keyword="completely_unmatched", category="AnotherUnknown", max_price=100
        )
        assert len(products) == 5
        assert products[0]['name'] == "Budget Phone"
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_empty_inputs_fallback_to_popular(self, service_with_mock_products):
        """Test smart search with all empty/None inputs, falls back to popular."""
        products, message = service_with_mock_products.smart_search_products(
            keyword="", category=None, max_price=None, limit=3
        )
        assert len(products) == 3
        assert products[0]['name'] == "Budget Phone"
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_limit_parameter(self, service_with_mock_products):
        """Test limit parameter works across smart search scenarios."""
        products, message = service_with_mock_products.smart_search_products(keyword="smartphone", limit=1)
        assert len(products) == 1
        assert products[0]['name'] in ["Smartphone A", "Smartphone X PRO", "Budget Phone"]

    def test_smart_search_keyword_only_match(self, service_with_mock_products):
        """Test smart search with only keyword, behaving like search_products."""
        products, message = service_with_mock_products.smart_search_products(keyword="Laptop")
        assert len(products) == 2
        assert "Laptop B" in [p['name'] for p in products]
        assert "Gaming Laptop Z" in [p['name'] for p in products]
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_no_match_but_category_present_for_relevance_sort(self, service_with_mock_products):
        """
        Test scenario where keyword doesn't match price but category is given.
        Should fall into "category only" fallback and sort by price.
        """
        products, message = service_with_mock_products.smart_search_products(
            keyword="expensive gadget", category="Audio", max_price=50000
        )
        assert len(products) == 2
        assert products[0]['name'] == "Earbuds D"
        assert products[1]['name'] == "Headphones C"
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_no_match_category_but_price_present_for_relevance_sort(self, service_with_mock_products):
        """
        Test scenario where category doesn't match, but max_price is given.
        Should fall into "budget only" fallback.
        """
        products, message = service_with_mock_products.smart_search_products(
            keyword="rare item", category="NonExistent", max_price=1000000
        )
        assert len(products) == 2
        assert products[0]['name'] == "Mystery Item"
        assert products[1]['name'] == "Earbuds D"
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_only_category_and_price_no_keyword(self, service_with_mock_products):
        """Test smart search with category and max_price but no keyword."""
        products, message = service_with_mock_products.smart_search_products(
            category="Smartphone", max_price=11000000, limit=2
        )
        assert len(products) == 2
        assert products[0]['name'] == "Smartphone A"
        assert products[1]['name'] == "Budget Phone"
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_initial_load_empty_products(self, cap_logs):
        """Test smart search when initial product load is empty (e.g., file not found)."""
        with patch('app.services.local_product_service.LocalProductService._load_local_products', return_value=[]):
            service = LocalProductService()
            products, message = service.smart_search_products(keyword="any")
            assert products == []
            assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_all_inputs_none_or_empty(self, service_with_mock_products):
        """Test smart search when all search inputs are None/empty strings, should return popular products."""
        products, message = service_with_mock_products.smart_search_products(
            keyword=None, category=None, max_price=None, limit=3
        )
        assert len(products) == 3
        assert products[0]['name'] == "Budget Phone"
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."