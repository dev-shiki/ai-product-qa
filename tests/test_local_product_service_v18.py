import pytest
from unittest.mock import patch, mock_open, MagicMock
from app.services.local_product_service import LocalProductService
import json
import logging
from pathlib import Path
import random

logger = logging.getLogger(__name__)

# --- Fixtures ---

@pytest.fixture(autouse=True)
def caplog_fixture(caplog):
    """Fixture to set logging level for tests for better visibility."""
    caplog.set_level(logging.INFO)

@pytest.fixture
def base_products_data_raw():
    """Sample raw product data as it would be read from products.json."""
    return {
        "products": [
            {"id": "P001", "name": "Laptop Pro", "category": "Laptop", "brand": "TechBrand", "price": 15000000, "rating": 4.8, "stock_count": 10, "description": "Powerful laptop for professionals.", "specifications": {"cpu": "M1", "ram": "16GB"}, "reviews_count": 50},
            {"id": "P002", "name": "Smartphone X", "category": "Smartphone", "brand": "MobileCorp", "price": 8000000, "rating": 4.5, "stock_count": 25, "description": "Latest smartphone with great camera.", "reviews_count": 30},
            {"id": "P003", "name": "Headphones ANC", "category": "Audio", "brand": "SoundGen", "price": 2000000, "rating": 4.2, "stock_count": 50, "description": "Noise-cancelling headphones.", "specifications": {"color": "black"}, "reviews_count": 120},
            {"id": "P004", "name": "Smart TV 50", "category": "Electronics", "brand": "ViewSonic", "price": 7000000, "rating": 4.0, "stock_count": 5, "description": "50-inch 4K Smart TV.", "reviews_count": 80},
            {"id": "P005", "name": "Budget Phone", "category": "Smartphone", "brand": "MobileCorp", "price": 2500000, "rating": 3.5, "stock_count": 30, "description": "Affordable smartphone for everyday use.", "reviews_count": 10},
            {"id": "P006", "name": "Gaming Laptop", "category": "Laptop", "brand": "GamerTech", "price": 20000000, "rating": 4.9, "stock_count": 7, "description": "High-performance gaming laptop.", "specifications": {"gpu": "RTX 4080"}, "reviews_count": 200},
            {"id": "P007", "name": "Wireless Earbuds", "category": "Audio", "brand": "SoundGen", "price": 1200000, "rating": 4.1, "stock_count": 60, "description": "Compact wireless earbuds.", "reviews_count": 70},
            {"id": "P008", "name": "Laptop Slim", "category": "Laptop", "brand": "TechBrand", "price": 12000000, "rating": 4.6, "stock_count": 12, "description": "Slim and light laptop for portability.", "reviews_count": 40}
        ]
    }

@pytest.fixture
def transformed_products_fixed_sold(base_products_data_raw):
    """Provides expected transformed product data with a fixed 'sold' value (e.g., 1000)."""
    transformed = []
    for product in base_products_data_raw['products']:
        t_product = {
            "id": product.get('id', ''),
            "name": product.get('name', ''),
            "category": product.get('category', ''),
            "brand": product.get('brand', ''),
            "price": product.get('price', 0),
            "currency": product.get('currency', 'IDR'),
            "description": product.get('description', ''),
            "specifications": {
                "rating": product.get('rating', 0),
                "sold": 1000,  # Fixed for testing
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
        transformed.append(t_product)
    return transformed

@pytest.fixture
def transformed_products_varied_sold(base_products_data_raw):
    """Provides expected transformed product data with varied 'sold' values for sorting tests."""
    sold_values_map = {
        "P001": 1500, "P002": 500, "P003": 100, "P004": 200,
        "P005": 300, "P006": 1800, "P007": 2000, "P008": 400
    }
    transformed = []
    for product in base_products_data_raw['products']:
        t_product = {
            "id": product.get('id', ''),
            "name": product.get('name', ''),
            "category": product.get('category', ''),
            "brand": product.get('brand', ''),
            "price": product.get('price', 0),
            "currency": product.get('currency', 'IDR'),
            "description": product.get('description', ''),
            "specifications": {
                "rating": product.get('rating', 0),
                "sold": sold_values_map.get(product['id'], 0),  # Varied sold for testing
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
        transformed.append(t_product)
    return transformed

@pytest.fixture
def mock_pathlib_for_loading(monkeypatch, base_products_data_raw):
    """
    Parametrized fixture to configure mocks for pathlib.Path and open for _load_local_products.
    This uses a closure to allow dynamic configuration within tests.
    """
    _mock_json_file_path = MagicMock(spec=Path) # This will be the actual mock object for products.json path
    
    class MockPathFactory(MagicMock):
        def __call__(self, *args, **kwargs):
            if "__file__" in str(args[0]):
                mock_current_file_path = MagicMock(spec=Path)
                mock_parent_path = MagicMock(spec=Path)
                mock_parent_path.__truediv__.return_value = _mock_json_file_path
                mock_current_file_path.parent.parent.parent = mock_parent_path
                return mock_current_file_path
            return MagicMock(spec=Path)

    monkeypatch.setattr('pathlib.Path', MockPathFactory())
    monkeypatch.setattr('random.randint', lambda a, b: 1000) # Default fixed sold value

    # Yield a function that can be called by tests to configure the mock
    def _configure_mocks(file_content_override=None, file_exists=True, open_side_effect=None):
        content = file_content_override if file_content_override is not None else json.dumps(base_products_data_raw)
        
        _mock_json_file_path.exists.return_value = file_exists
        _mock_json_file_path.open.reset_mock(side_effect=True) # Reset any previous side_effect
        
        if open_side_effect:
            _mock_json_file_path.open.side_effect = open_side_effect
        else:
            _mock_json_file_path.open = mock_open(read_data=content)
            
        return _mock_json_file_path

    yield _configure_mocks

@pytest.fixture
def local_product_service_fixed_sold(monkeypatch, transformed_products_fixed_sold):
    """Provides a LocalProductService instance with products having fixed 'sold' values,
    bypassing file loading for direct product injection."""
    with patch.object(LocalProductService, '_load_local_products') as mock_load:
        mock_load.return_value = transformed_products_fixed_sold
        service = LocalProductService()
        yield service

@pytest.fixture
def local_product_service_varied_sold(monkeypatch, transformed_products_varied_sold):
    """Provides a LocalProductService instance with products having varied 'sold' values."""
    with patch.object(LocalProductService, '_load_local_products') as mock_load:
        mock_load.return_value = transformed_products_varied_sold
        service = LocalProductService()
        yield service


# --- Test Cases ---

class TestLocalProductServiceInitAndLoad:
    def test_init_and_load_success(self, monkeypatch, base_products_data_raw, transformed_products_fixed_sold, caplog, mock_pathlib_for_loading):
        """Test successful initialization and product loading."""
        mock_json_file_path = mock_pathlib_for_loading() # Configure the mocks
        service = LocalProductService()
        
        assert len(service.products) == len(transformed_products_fixed_sold)
        assert service.products == transformed_products_fixed_sold # Verify content and transformation

        # Check that open was called with correct encoding (it tries utf-16-le first, then utf-16, then utf-8, etc.)
        # For simple JSON, utf-8 should typically succeed.
        # The code tries encodings in a specific order. If utf-16-le fails, it tries others.
        # Let's verify `open` was called with *some* encoding, and content was processed.
        # It's hard to predict *which* encoding will succeed first with mock_open, unless `read_data` is specific to an encoding.
        # The key is that `open` was called and data was loaded.
        mock_json_file_path.open.assert_called()
        assert f"Loaded {len(base_products_data_raw['products'])} local products from JSON file" in caplog.text
        assert "Successfully loaded" in caplog.text

    def test_load_local_products_file_not_found(self, monkeypatch, caplog, mock_pathlib_for_loading):
        """Test _load_local_products when the JSON file is not found."""
        mock_json_file_path = mock_pathlib_for_loading(file_exists=False)
        service = LocalProductService()
        assert len(service.products) > 0 # Should load fallback products
        assert "Using fallback products due to JSON file loading error" in caplog.text
        assert "Products JSON file not found at:" in caplog.text
        mock_json_file_path.exists.assert_called_once()
        mock_json_file_path.open.assert_not_called() # Open should not be called if file doesn't exist

    def test_load_local_products_json_decode_error(self, monkeypatch, caplog, mock_pathlib_for_loading):
        """Test _load_local_products when JSON content is invalid."""
        mock_json_file_path = mock_pathlib_for_loading(file_content_override="{invalid json")
        service = LocalProductService()
        assert len(service.products) > 0 # Should load fallback products
        assert "Using fallback products due to JSON file loading error" in caplog.text
        assert "Failed to load with" in caplog.text
        assert "json.JSONDecodeError" in caplog.text
        # Should try opening multiple times until all encodings fail JSON decoding
        assert mock_json_file_path.open.call_count == len(LocalProductService()._load_local_products.__defaults__[0]) # Check number of encoding attempts. It's the `encodings` list.
        # A simpler way is to check that it tried at least one open call.

    def test_load_local_products_unicode_decode_error_all_encodings_fail(self, monkeypatch, caplog, mock_pathlib_for_loading):
        """Test _load_local_products when all encoding attempts fail."""
        def failing_open(*args, **kwargs):
            raise UnicodeDecodeError("mock_codec", b'\x80', 0, 1, "mock error: invalid start byte")
            
        mock_json_file_path = mock_pathlib_for_loading(open_side_effect=failing_open)
        service = LocalProductService()
        assert len(service.products) > 0 # Should load fallback products
        assert "Using fallback products due to JSON file loading error" in caplog.text
        assert "Failed to load with" in caplog.text
        assert "UnicodeDecodeError" in caplog.text
        assert "All encoding attempts failed, using fallback products" in caplog.text
        # Expect `open` to be called for each encoding in the list
        assert mock_json_file_path.open.call_count == len(service._load_local_products.__defaults__[0]) # This value is `encodings` list

    def test_load_local_products_general_exception(self, monkeypatch, caplog):
        """Test _load_local_products when a general exception occurs during file operations."""
        # Simulate an error during path resolution or initial file check
        class MockPathFactory(MagicMock):
            def __call__(self, *args, **kwargs):
                if "__file__" in str(args[0]):
                    mock_current_file_path = MagicMock(spec=Path)
                    mock_parent_path = MagicMock(spec=Path)
                    mock_parent_path.__truediv__.side_effect = Exception("Simulated general error during path op")
                    mock_current_file_path.parent.parent.parent = mock_parent_path
                    return mock_current_file_path
                return MagicMock(spec=Path)

        monkeypatch.setattr('pathlib.Path', MockPathFactory())
        monkeypatch.setattr('random.randint', lambda a, b: 1000)
        
        service = LocalProductService()
        assert len(service.products) > 0 # Should load fallback products
        assert "Using fallback products due to JSON file loading error" in caplog.text
        assert "Error loading products from JSON file:" in caplog.text
        assert "Simulated general error during path op" in caplog.text

    def test_load_local_products_with_bom(self, monkeypatch, base_products_data_raw, transformed_products_fixed_sold, caplog, mock_pathlib_for_loading):
        """Test _load_local_products with a BOM present in the JSON file."""
        bom_content = '\ufeff' + json.dumps(base_products_data_raw)
        
        mock_json_file_path = mock_pathlib_for_loading(file_content_override=bom_content)
        service = LocalProductService()
        assert len(service.products) == len(transformed_products_fixed_sold)
        assert service.products == transformed_products_fixed_sold # Ensure data is parsed correctly after BOM removal
        assert "Successfully loaded" in caplog.text
        mock_json_file_path.open.assert_called()

    def test_load_local_products_empty_products_list(self, monkeypatch, caplog, mock_pathlib_for_loading):
        """Test _load_local_products with a JSON file containing an empty products list."""
        mock_json_file_path = mock_pathlib_for_loading(file_content_override=json.dumps({"products": []}))
        service = LocalProductService()
        assert len(service.products) == 0
        assert "Successfully loaded 0 products from JSON file" in caplog.text

    def test_load_local_products_missing_products_key(self, monkeypatch, caplog, mock_pathlib_for_loading):
        """Test _load_local_products with a JSON file missing the 'products' key."""
        mock_json_file_path = mock_pathlib_for_loading(file_content_override=json.dumps({"items": [{"id": "X001"}]}))
        service = LocalProductService()
        assert len(service.products) == 0
        assert "Successfully loaded 0 products from JSON file" in caplog.text


class TestLocalProductServiceMethods:
    def test_get_fallback_products(self, local_product_service_fixed_sold):
        """Test _get_fallback_products returns a non-empty list with expected structure."""
        fallback_products = local_product_service_fixed_sold._get_fallback_products()
        assert len(fallback_products) > 0
        assert isinstance(fallback_products[0], dict)
        assert "id" in fallback_products[0]
        assert "name" in fallback_products[0]
        assert "specifications" in fallback_products[0]
        assert "sold" in fallback_products[0]["specifications"]

    @pytest.mark.parametrize("keyword, expected_ids", [
        ("laptop", ["P001", "P006", "P008"]),
        ("smartphone", ["P002", "P005"]),
        ("headphones", ["P003", "P007"]),
        ("techbrand", ["P001", "P008"]),
        ("gaming", ["P006"]),
        ("camera", ["P002"]), # Keyword in description
        ("soundgen", ["P003", "P007"]),
        ("nonexistent", []),
        ("", ["P001", "P006", "P008", "P002", "P003", "P007", "P004", "P005"]), # Empty keyword, returns all (up to limit)
        ("P001", ["P001"]), # Search by ID (in searchable text)
    ])
    def test_search_products_basic_keyword(self, local_product_service_fixed_sold, keyword, expected_ids):
        """Test search_products with basic keywords and case-insensitivity."""
        results = local_product_service_fixed_sold.search_products(keyword)
        actual_ids = [p['id'] for p in results]
        assert sorted(actual_ids) == sorted(expected_ids[:10]) # Limit is 10 by default

        # Test case-insensitivity
        if keyword:
            results_upper = local_product_service_fixed_sold.search_products(keyword.upper())
            assert sorted([p['id'] for p in results_upper]) == sorted(expected_ids[:10])
    
    def test_search_products_limit(self, local_product_service_fixed_sold):
        """Test search_products with a specific limit."""
        results = local_product_service_fixed_sold.search_products("laptop", limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'P006' # Gaming Laptop (rating 4.9) has higher score
        assert results[1]['id'] == 'P001' # Laptop Pro (rating 4.8)

    @pytest.mark.parametrize("keyword, expected_max_price", [
        ("laptop 10 juta", 10000000),
        ("phone rp 5000000", 5000000),
        ("tv 7m", 7000000),
        ("headphone 2k", 2000000),
        ("murah", 5000000), # Budget keyword
        ("budget", 5000000), # Budget keyword
        ("hemat", 3000000),
        ("terjangkau", 4000000),
        ("economical", None), # Unknown budget keyword
        ("no price", None),
        ("rp 12345", 12345)
    ])
    def test_extract_price_from_keyword(self, local_product_service_fixed_sold, keyword, expected_max_price):
        """Test _extract_price_from_keyword extracts prices and budget keywords correctly."""
        service = local_product_service_fixed_sold
        price = service._extract_price_from_keyword(keyword)
        assert price == expected_max_price

    def test_extract_price_from_keyword_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in _extract_price_from_keyword."""
        with patch('re.search', side_effect=Exception("Simulated regex error")):
            price = local_product_service_fixed_sold._extract_price_from_keyword("laptop 10 juta")
            assert price is None
            assert "Error extracting price from keyword:" in caplog.text
            assert "Simulated regex error" in caplog.text

    def test_search_products_with_price_filter_and_relevance(self, local_product_service_fixed_sold):
        """Test search_products filtering by extracted max price and relevance sorting."""
        results = local_product_service_fixed_sold.search_products("smartphone 5 juta")
        # P005 (Budget Phone, 2.5M) will match price. P002 (Smartphone X, 8M) will match keyword.
        # Due to relevance scoring (price boost for '5 juta'), P005 should come first.
        assert len(results) == 2
        assert results[0]['id'] == 'P005'
        assert results[1]['id'] == 'P002'

    def test_search_products_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in search_products."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated products access error")):
            results = local_product_service_fixed_sold.search_products("laptop")
            assert results == []
            assert "Error searching products:" in caplog.text
            assert "Simulated products access error" in caplog.text


    def test_get_product_details_existing(self, local_product_service_fixed_sold):
        """Test get_product_details for an existing product ID."""
        product = local_product_service_fixed_sold.get_product_details("P001")
        assert product is not None
        assert product['id'] == 'P001'
        assert product['name'] == 'Laptop Pro'

    def test_get_product_details_non_existing(self, local_product_service_fixed_sold):
        """Test get_product_details for a non-existing product ID."""
        product = local_product_service_fixed_sold.get_product_details("NONEXISTENT")
        assert product is None

    def test_get_product_details_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in get_product_details."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated access error")):
            product = local_product_service_fixed_sold.get_product_details("P001")
            assert product is None
            assert "Error getting product details:" in caplog.text
            assert "Simulated access error" in caplog.text

    def test_get_categories(self, local_product_service_fixed_sold):
        """Test get_categories returns unique, sorted categories."""
        categories = local_product_service_fixed_sold.get_categories()
        expected_categories = sorted(['Laptop', 'Smartphone', 'Audio', 'Electronics'])
        assert categories == expected_categories

    def test_get_categories_empty_products(self, monkeypatch):
        """Test get_categories with no products loaded."""
        # Create a new service instance to ensure its product list can be manipulated
        service = LocalProductService() 
        monkeypatch.setattr(service, 'products', []) # Manually set products to empty
        categories = service.get_categories()
        assert categories == []

    def test_get_brands(self, local_product_service_fixed_sold):
        """Test get_brands returns unique, sorted brands."""
        brands = local_product_service_fixed_sold.get_brands()
        expected_brands = sorted(['TechBrand', 'MobileCorp', 'SoundGen', 'ViewSonic', 'GamerTech'])
        assert brands == expected_brands

    def test_get_brands_empty_products(self, monkeypatch):
        """Test get_brands with no products loaded."""
        service = LocalProductService()
        monkeypatch.setattr(service, 'products', [])
        brands = service.get_brands()
        assert brands == []

    @pytest.mark.parametrize("category, expected_ids", [
        ("laptop", ["P001", "P006", "P008"]),
        ("Smartphone", ["P002", "P005"]), # Case-insensitivity
        ("Audio", ["P003", "P007"]),
        ("nonexistent", []),
        ("", []), # Empty category string should yield no results based on logic
    ])
    def test_get_products_by_category(self, local_product_service_fixed_sold, category, expected_ids):
        """Test get_products_by_category with existing and non-existing categories."""
        results = local_product_service_fixed_sold.get_products_by_category(category)
        actual_ids = [p['id'] for p in results]
        assert sorted(actual_ids) == sorted(expected_ids)
    
    def test_get_products_by_category_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in get_products_by_category."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated access error")):
            results = local_product_service_fixed_sold.get_products_by_category("Laptop")
            assert results == []
            assert "Error getting products by category:" in caplog.text
            assert "Simulated access error" in caplog.text

    @pytest.mark.parametrize("brand, expected_ids", [
        ("techbrand", ["P001", "P008"]),
        ("MobileCorp", ["P002", "P005"]), # Case-insensitivity
        ("SoundGen", ["P003", "P007"]),
        ("nonexistent", []),
        ("", []), # Empty brand string
    ])
    def test_get_products_by_brand(self, local_product_service_fixed_sold, brand, expected_ids):
        """Test get_products_by_brand with existing and non-existing brands."""
        results = local_product_service_fixed_sold.get_products_by_brand(brand)
        actual_ids = [p['id'] for p in results]
        assert sorted(actual_ids) == sorted(expected_ids)

    def test_get_products_by_brand_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in get_products_by_brand."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated access error")):
            results = local_product_service_fixed_sold.get_products_by_brand("TechBrand")
            assert results == []
            assert "Error getting products by brand:" in caplog.text
            assert "Simulated access error" in caplog.text

    def test_get_top_rated_products(self, local_product_service_fixed_sold):
        """Test get_top_rated_products returns products sorted by rating."""
        # P006: 4.9, P001: 4.8, P008: 4.6, P002: 4.5, P003: 4.2
        results = local_product_service_fixed_sold.get_top_rated_products(limit=3)
        assert len(results) == 3
        assert [p['id'] for p in results] == ['P006', 'P001', 'P008']

    def test_get_top_rated_products_limit_all(self, local_product_service_fixed_sold):
        """Test get_top_rated_products with limit larger than available products."""
        results = local_product_service_fixed_sold.get_top_rated_products(limit=100)
        assert len(results) == 8 # All products
        assert results[0]['id'] == 'P006'

    def test_get_top_rated_products_empty(self, monkeypatch):
        """Test get_top_rated_products with no products loaded."""
        service = LocalProductService()
        monkeypatch.setattr(service, 'products', [])
        results = service.get_top_rated_products()
        assert results == []

    def test_get_top_rated_products_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in get_top_rated_products."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated access error")):
            results = local_product_service_fixed_sold.get_top_rated_products()
            assert results == []
            assert "Error getting top rated products:" in caplog.text
            assert "Simulated access error" in caplog.text

    def test_get_best_selling_products(self, local_product_service_varied_sold):
        """Test get_best_selling_products returns products sorted by sold count."""
        # Based on transformed_products_varied_sold fixture:
        # P007 (2000), P006 (1800), P001 (1500), P008 (400), P005 (300), P004 (200), P003 (100)
        service = local_product_service_varied_sold
        results = service.get_best_selling_products(limit=3)
        assert len(results) == 3
        assert [p['id'] for p in results] == ['P007', 'P006', 'P001']

    def test_get_best_selling_products_limit_all(self, local_product_service_varied_sold):
        """Test get_best_selling_products with limit larger than available products."""
        service = local_product_service_varied_sold
        results = service.get_best_selling_products(limit=100)
        assert len(results) == 8 # All products
        assert results[0]['id'] == 'P007'

    def test_get_best_selling_products_empty(self, monkeypatch):
        """Test get_best_selling_products with no products loaded."""
        service = LocalProductService()
        monkeypatch.setattr(service, 'products', [])
        results = service.get_best_selling_products()
        assert results == []

    def test_get_best_selling_products_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in get_best_selling_products."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated access error")):
            results = local_product_service_fixed_sold.get_best_selling_products()
            assert results == []
            assert "Error getting best selling products:" in caplog.text
            assert "Simulated access error" in caplog.text

    def test_get_products(self, local_product_service_fixed_sold):
        """Test get_products returns all products up to limit."""
        results = local_product_service_fixed_sold.get_products()
        assert len(results) == 8 # Default limit 10, but only 8 products
        assert all(p['id'] in [bp['id'] for bp in local_product_service_fixed_sold.products] for p in results)

    def test_get_products_with_limit(self, local_product_service_fixed_sold):
        """Test get_products with a specific limit."""
        results = local_product_service_fixed_sold.get_products(limit=3)
        assert len(results) == 3
        assert [p['id'] for p in results] == ['P001', 'P002', 'P003']
    
    def test_get_products_error_handling(self, local_product_service_fixed_sold, caplog):
        """Test error handling in get_products."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated access error")):
            results = local_product_service_fixed_sold.get_products()
            assert results == []
            assert "Error getting products:" in caplog.text
            assert "Simulated access error" in caplog.text


class TestSmartSearchProducts:
    def test_smart_search_best_no_category(self, local_product_service_fixed_sold):
        """Test smart_search_products for 'best' keyword without specific category."""
        products, message = local_product_service_fixed_sold.smart_search_products(keyword="terbaik")
        # Should return top 5 by rating
        expected_ids = ['P006', 'P001', 'P008', 'P002', 'P003']
        assert [p['id'] for p in products] == expected_ids
        assert message == "Berikut produk terbaik berdasarkan rating:"
        
        products_upper, message_upper = local_product_service_fixed_sold.smart_search_products(keyword="BEST")
        assert [p['id'] for p in products_upper] == expected_ids
        assert message_upper == "Berikut produk terbaik berdasarkan rating:"

    def test_smart_search_best_with_existing_category(self, local_product_service_fixed_sold):
        """Test smart_search_products for 'best' keyword with an existing category."""
        products, message = local_product_service_fixed_sold.smart_search_products(keyword="laptop terbaik", category="Laptop")
        # Laptop products: P001 (4.8), P006 (4.9), P008 (4.6)
        expected_ids = ['P006', 'P001', 'P008']
        assert [p['id'] for p in products] == expected_ids
        assert message == "Berikut Laptop terbaik berdasarkan rating:"
    
    def test_smart_search_best_with_non_existing_category(self, local_product_service_fixed_sold):
        """Test smart_search_products for 'best' keyword with a non-existing category (fallback to general best)."""
        products, message = local_product_service_fixed_sold.smart_search_products(keyword="abc terbaik", category="ABC")
        # Fallback to general best products
        expected_ids = ['P006', 'P001', 'P008', 'P002', 'P003']
        assert [p['id'] for p in products] == expected_ids
        assert message == "Tidak ada produk kategori ABC, berikut produk terbaik secara umum:"

    def test_smart_search_all_criteria_match(self, local_product_service_fixed_sold):
        """Test smart_search_products when all keyword, category, and max_price criteria match."""
        # Find 'Laptop' with 'Pro' in name and price <= 15M
        products, message = local_product_service_fixed_sold.smart_search_products(keyword="Pro", category="Laptop", max_price=15000000)
        assert len(products) == 1
        assert products[0]['id'] == 'P001'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_fallback_to_category_only(self, local_product_service_fixed_sold):
        """Test smart_search_products fallback: keyword/price no match, but category matches."""
        # Laptop products: P001 (15M), P006 (20M), P008 (12M)
        # Search for a cheap gaming laptop, but budget is too low
        products, message = local_product_service_fixed_sold.smart_search_products(keyword="gaming", category="Laptop", max_price=1000000)
        assert len(products) == 3 # All laptops
        # Should be sorted by price ascending for "termurah" message (explicit sort in code for this branch)
        sorted_laptop_products = sorted([p for p in local_product_service_fixed_sold.products if p['category'].lower() == 'laptop'], key=lambda x: x['price'])
        assert [p['id'] for p in products] == [p['id'] for p in sorted_laptop_products]
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    def test_smart_search_fallback_to_budget_only(self, local_product_service_fixed_sold):
        """Test smart_search_products fallback: category no match, but price matches."""
        # Search for non-existent category, but within budget
        products, message = local_product_service_fixed_sold.smart_search_products(keyword="xyz", category="NonExistent", max_price=3000000)
        # Budget products: P003 (2M), P005 (2.5M), P007 (1.2M)
        expected_ids = ['P003', 'P005', 'P007'] # Order should match original list order for products within budget
        actual_ids = [p['id'] for p in products]
        assert all(p['price'] <= 3000000 for p in products)
        # Using set comparison as the order might not be strictly preserved from `self.products` list
        assert set(actual_ids) == set(expected_ids)
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    def test_smart_search_fallback_to_popular(self, local_product_service_varied_sold):
        """Test smart_search_products fallback to popular products when no other criteria match."""
        # Search for something entirely unmatchable
        products, message = local_product_service_varied_sold.smart_search_products(keyword="xyz", category="NoCategory", max_price=100)
        # Should return top 5 by sold count (P007: 2000, P006: 1800, P001: 1500, P008: 400, P005: 300)
        expected_ids = ['P007', 'P006', 'P001', 'P008', 'P005'] # Based on varied_sold fixture
        assert [p['id'] for p in products] == expected_ids
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."
    
    def test_smart_search_empty_input(self, local_product_service_varied_sold):
        """Test smart_search_products with empty keyword, category, and max_price."""
        # Should fallback to popular products
        products, message = local_product_service_varied_sold.smart_search_products(keyword="", category=None, max_price=None)
        expected_ids = ['P007', 'P006', 'P001', 'P008', 'P005']
        assert [p['id'] for p in products] == expected_ids
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_limit_parameter(self, local_product_service_fixed_sold):
        """Test smart_search_products respects the limit parameter."""
        products, message = local_product_service_fixed_sold.smart_search_products(keyword="terbaik", limit=2)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['P006', 'P001']

    def test_smart_search_products_general_exception_propagates(self, local_product_service_fixed_sold):
        """Test that smart_search_products propagates general exceptions (as it has no internal try-except)."""
        with patch.object(local_product_service_fixed_sold, 'products', side_effect=Exception("Simulated filter error")):
            with pytest.raises(Exception, match="Simulated filter error"):
                local_product_service_fixed_sold.smart_search_products(keyword="laptop")

    def test_smart_search_products_no_products_loaded(self, monkeypatch):
        """Test smart_search_products when service has no products."""
        # Initialize service to have no products (empty list)
        service = LocalProductService()
        monkeypatch.setattr(service, 'products', [])
        
        products, message = service.smart_search_products(keyword="anything")
        assert products == []
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."