import pytest
import json
import logging
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import random

# Import the service class from its original path
from app.services.local_product_service import LocalProductService

# --- Mock Data ---

# Sample products for mocking the JSON file content
MOCK_RAW_PRODUCTS_JSON = {
    "products": [
        {
            "id": "mock-1",
            "name": "Mock Phone X",
            "category": "Smartphone",
            "brand": "MockApple",
            "price": 10000000,
            "currency": "IDR",
            "description": "A very good mock phone.",
            "specifications": {
                "rating": 4.5,
                "stock_count": 100,
                "storage": "128GB"
            },
            "availability": "in_stock",
            "reviews_count": 50
        },
        {
            "id": "mock-2",
            "name": "Mock Laptop Pro",
            "category": "Laptop",
            "brand": "MockDell",
            "price": 15000000,
            "currency": "IDR",
            "description": "Powerful mock laptop for professionals.",
            "specifications": {
                "rating": 4.8,
                "stock_count": 50,
                "ram": "16GB"
            },
            "availability": "in_stock",
            "reviews_count": 120
        },
        {
            "id": "mock-3",
            "name": "Mock Earbuds",
            "category": "Audio",
            "brand": "MockSony",
            "price": 2000000,
            "currency": "IDR",
            "description": "Noise-cancelling earbuds.",
            "specifications": {
                "rating": 4.0,
                "stock_count": 200
            },
            "availability": "in_stock",
            "reviews_count": 30
        },
        {
            "id": "mock-4",
            "name": "Another Mock Phone",
            "category": "Smartphone",
            "brand": "MockSamsung",
            "price": 8000000,
            "currency": "IDR",
            "description": "Budget friendly mock phone.",
            "specifications": {
                "rating": 3.9,
                "stock_count": 150
            },
            "availability": "in_stock",
            "reviews_count": 70
        },
        {
            "id": "mock-5",
            "name": "Super Gaming Laptop",
            "category": "Laptop",
            "brand": "MockAsus",
            "price": 20000000,
            "currency": "IDR",
            "description": "High-end gaming laptop.",
            "specifications": {
                "rating": 4.9,
                "stock_count": 20,
                "gpu": "RTX 4090"
            },
            "availability": "in_stock",
            "reviews_count": 90
        },
        {
            "id": "mock-6",
            "name": "Empty Spec Product",
            "category": "Gadget",
            "brand": "Generic",
            "price": 500000,
            "currency": "IDR",
            "description": "Product with minimal info.",
            "reviews_count": 5
            # Missing 'specifications' key and other optional fields
        },
        {
            "id": "mock-7",
            "name": "Best TV",
            "category": "Electronics",
            "brand": "MockLG",
            "price": 12000000,
            "currency": "IDR",
            "description": "The best television in the market.",
            "specifications": {
                "rating": 5.0, # Highest rating for best_products tests
                "stock_count": 10
            },
            "reviews_count": 200
        },
        {
            "id": "mock-8",
            "name": "Cheap Phone",
            "category": "Smartphone",
            "brand": "MockXiaomi",
            "price": 1500000,
            "currency": "IDR",
            "description": "A very cheap smartphone.",
            "specifications": {
                "rating": 3.0,
                "stock_count": 300
            },
            "reviews_count": 10
        },
        {
            "id": "mock-9",
            "name": "Sold Out Item",
            "category": "Collectibles",
            "brand": "RareStuff",
            "price": 1000000,
            "currency": "IDR",
            "description": "Very rare item, now sold out.",
            "specifications": {
                "rating": 4.2,
                "stock_count": 0,
                "sold": 5000 # Highest sold count for best_selling_products
            },
            "availability": "out_of_stock",
            "reviews_count": 100
        }
    ]
}

# Helper for expected transformed products based on MOCK_RAW_PRODUCTS_JSON
# Will use a default mock_sold_value for tests
def get_expected_transformed_products(mock_sold_value=1000):
    transformed = []
    for product in MOCK_RAW_PRODUCTS_JSON['products']:
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
                "sold": mock_sold_value,  # This will be mocked by random.randint
                "stock": product.get('stock_count', 0),
                "condition": "Baru",
                "shop_location": "Indonesia",
                "shop_name": f"{product.get('brand', 'Unknown')} Store",
                **product.get('specifications', {}) # Merges existing specs, allowing 'sold' from raw to override random
            },
            "availability": product.get('availability', 'in_stock'),
            "reviews_count": product.get('reviews_count', 0),
            "images": [f"https://example.com/{product.get('id', 'product')}.jpg"],
            "url": f"https://shopee.co.id/{product.get('id', 'product')}"
        }
        # Special handling for mock-9 to ensure its sold count from raw data is preserved
        if product.get('id') == 'mock-9':
            transformed_product['specifications']['sold'] = product['specifications']['sold']

        transformed.append(transformed_product)
    return transformed


# --- Fixtures ---

@pytest.fixture(autouse=True)
def mock_logger():
    """Mocks the logger to capture logs and prevent console output during tests."""
    with patch('app.services.local_product_service.logger') as mock_log:
        yield mock_log

@pytest.fixture
def mock_random_randint():
    """Mocks random.randint to return predictable values for 'sold' count."""
    with patch('app.services.local_product_service.random.randint') as mock_rand:
        mock_rand.return_value = 1000 # Default predictable value for all but specific overrides
        yield mock_rand

@pytest.fixture
def service_with_mocked_file_loading(mock_random_randint):
    """
    Fixture for LocalProductService that allows precise control over file loading.
    It patches Path and open to simulate file system interactions.
    """
    with patch('app.services.local_product_service.Path') as MockPath:
        # Mock Path(__file__).parent.parent.parent to point to a base mock path
        # This setup ensures that the path construction `current_dir / "data" / "products.json"`
        # within `_load_local_products` works correctly against our mocks.
        mock_base_path = MagicMock()
        mock_base_path.__truediv__.return_value = mock_base_path # Allows chaining /
        mock_base_path.exists.return_value = False # Default to file not found unless specified
        
        mock_file_path_obj = MagicMock()
        mock_file_path_obj.parent.parent.parent = mock_base_path
        MockPath.return_value = mock_file_path_obj

        # The actual Path object for products.json
        mock_json_file_path = mock_base_path / "data" / "products.json"

        # Patch open globally, but capture its return value to allow configuring read_data
        with patch('app.services.local_product_service.open', new_callable=mock_open) as mock_file_open:
            yield LocalProductService(), mock_json_file_path, mock_file_open, mock_base_path

@pytest.fixture
def populated_service(mock_random_randint):
    """
    Fixture for LocalProductService with a pre-defined set of products,
    bypassing the actual file loading for most tests.
    """
    service = LocalProductService()
    # Populate products directly, ensuring 'sold' values are consistent with the mock_random_randint
    service.products = get_expected_transformed_products(mock_sold_value=mock_random_randint.return_value)
    yield service


# --- Test Cases ---

class TestLocalProductService:

    @patch('app.services.local_product_service.LocalProductService._load_local_products')
    def test_init_success(self, mock_load_products, mock_logger):
        """Test __init__ successfully loads products."""
        mock_load_products.return_value = [{"id": "test-1", "name": "Test Product"}]
        
        service = LocalProductService()
        
        mock_load_products.assert_called_once()
        assert service.products == [{"id": "test-1", "name": "Test Product"}]
        mock_logger.info.assert_called_with("Loaded 1 local products from JSON file")

    @patch('app.services.local_product_service.LocalProductService._load_local_products')
    def test_init_load_failure_handled_internally(self, mock_load_products, mock_logger):
        """Test __init__ receives fallback products if _load_local_products encounters internal issues."""
        # _load_local_products handles its own errors and returns fallback data
        mock_load_products.return_value = LocalProductService()._get_fallback_products()
        
        service = LocalProductService()
        
        mock_load_products.assert_called_once()
        assert service.products == LocalProductService()._get_fallback_products()
        mock_logger.info.assert_called_with(f"Loaded {len(service.products)} local products from JSON file")

    def test_get_fallback_products(self, mock_logger):
        """Test _get_fallback_products returns the correct hardcoded list and logs a warning."""
        service = LocalProductService() # Minimal init, we only care about _get_fallback_products logic here
        
        fallback_products = service._get_fallback_products()
        
        assert len(fallback_products) > 0 
        assert fallback_products[0]['id'] == '1' 
        mock_logger.warning.assert_called_with("Using fallback products due to JSON file loading error")

    def test_load_local_products_success(self, service_with_mocked_file_loading, mock_logger):
        """Test _load_local_products successfully loads and transforms valid JSON."""
        service, mock_json_file_path, mock_file_open, mock_base_path = service_with_mocked_file_loading
        
        mock_json_file_path.exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(MOCK_RAW_PRODUCTS_JSON)
        
        products = service._load_local_products()
        
        mock_json_file_path.exists.assert_called_once()
        mock_file_open.assert_called_with(mock_json_file_path, 'r', encoding='utf-16-le') # First attempt
        assert products == get_expected_transformed_products()
        mock_logger.info.assert_called_with(f"Successfully loaded {len(products)} products from JSON file using utf-16-le encoding")

    def test_load_local_products_file_not_found(self, service_with_mocked_file_loading, mock_logger):
        """Test _load_local_products handles file not found."""
        service, mock_json_file_path, mock_file_open, mock_base_path = service_with_mocked_file_loading
        
        mock_json_file_path.exists.return_value = False # File does not exist

        products = service._load_local_products()
        
        mock_json_file_path.exists.assert_called_once()
        mock_logger.error.assert_called_with(f"Products JSON file not found at: {mock_json_file_path}")
        assert products == service._get_fallback_products()

    def test_load_local_products_invalid_json(self, service_with_mocked_file_loading, mock_logger):
        """Test _load_local_products handles invalid JSON content."""
        service, mock_json_file_path, mock_file_open, mock_base_path = service_with_mocked_file_loading
        
        mock_json_file_path.exists.return_value = True
        mock_file_open.return_value.read.return_value = "{invalid json" # Invalid JSON

        products = service._load_local_products()
        
        # It should try all encodings and then fall back
        assert mock_file_open.call_count == 6 # Number of encodings tried
        mock_logger.warning.assert_called() # Should log warnings for each failed encoding
        mock_logger.error.assert_called_with("All encoding attempts failed, using fallback products")
        assert products == service._get_fallback_products()

    def test_load_local_products_encoding_failure_then_success(self, service_with_mocked_file_loading, mock_logger):
        """Test _load_local_products tries multiple encodings and succeeds on a later one."""
        service, mock_json_file_path, mock_file_open, mock_base_path = service_with_mocked_file_loading
        
        mock_json_file_path.exists.return_value = True

        # Simulate UnicodeDecodeError for the first encodings, then success for 'utf-8'
        mock_file_open.side_effect = [
            MagicMock(read_data=None, __enter__=MagicMock(side_effect=UnicodeDecodeError('utf-16-le', b'\x00', 0, 1, 'mock error'))),
            MagicMock(read_data=None, __enter__=MagicMock(side_effect=UnicodeDecodeError('utf-16', b'\x00', 0, 1, 'mock error'))),
            mock_open(read_data=json.dumps(MOCK_RAW_PRODUCTS_JSON)).return_value # Success on third encoding (utf-8)
        ]
        
        products = service._load_local_products()
        
        mock_logger.warning.assert_any_call("Failed to load with utf-16-le encoding: mock error")
        mock_logger.warning.assert_any_call("Failed to load with utf-16 encoding: mock error")
        mock_logger.info.assert_called_with(f"Successfully loaded {len(products)} products from JSON file using utf-8 encoding")
        assert products == get_expected_transformed_products()
        mock_logger.error.assert_not_called() # No fallback

    def test_load_local_products_with_bom(self, service_with_mocked_file_loading, mock_logger):
        """Test _load_local_products correctly handles JSON with a BOM."""
        service, mock_json_file_path, mock_file_open, mock_base_path = service_with_mocked_file_loading
        
        mock_json_file_path.exists.return_value = True

        # Simulate UTF-8 BOM, ensuring it's read correctly by one of the encodings
        bom_content = '\ufeff' + json.dumps(MOCK_RAW_PRODUCTS_JSON)
        
        mock_file_open.side_effect = [
            MagicMock(read_data=None, __enter__=MagicMock(side_effect=UnicodeDecodeError('utf-16-le', b'\x00', 0, 1, 'mock error'))),
            MagicMock(read_data=None, __enter__=MagicMock(side_effect=UnicodeDecodeError('utf-16', b'\x00', 0, 1, 'mock error'))),
            MagicMock(read_data=None, __enter__=MagicMock(side_effect=UnicodeDecodeError('utf-8', b'\x00', 0, 1, 'mock error'))),
            mock_open(read_data=bom_content).return_value # Success on utf-8-sig
        ]
        
        products = service._load_local_products()
        
        mock_logger.info.assert_called_with(f"Successfully loaded {len(products)} products from JSON file using utf-8-sig encoding")
        assert products == get_expected_transformed_products()

    def test_load_local_products_general_exception(self, service_with_mocked_file_loading, mock_logger):
        """Test _load_local_products handles general exceptions during file operations."""
        service, mock_json_file_path, mock_file_open, mock_base_path = service_with_mocked_file_loading
        
        mock_json_file_path.exists.return_value = True
        mock_file_open.side_effect = Exception("Permission denied")

        products = service._load_local_products()
        
        mock_logger.error.assert_called_with("Error loading products from JSON file: Permission denied")
        assert products == service._get_fallback_products()
    
    # --- Test search_products ---

    @pytest.mark.parametrize("keyword, expected_ids, limit", [
        ("phone", ["mock-1", "mock-4", "mock-8"], 10), # Basic keyword search
        ("mock", ["mock-5", "mock-2", "mock-1", "mock-7", "mock-4", "mock-3", "mock-8", "mock-6", "mock-9"], 10), # General keyword
        ("laptop", ["mock-5", "mock-2"], 10),
        ("mock phone x", ["mock-1"], 10), # Exact name match
        ("earbuds", ["mock-3"], 10),
        ("gaming", ["mock-5"], 10), # Search in description
        ("storage", ["mock-1", "mock-2"], 10), # Search in specifications (lowercase)
        ("MockApple", ["mock-1"], 10), # Search by brand
        ("smartphone", ["mock-1", "mock-4", "mock-8"], 10), # Search by category
        ("non-existent", [], 10), # No match
        ("", ["mock-5", "mock-2", "mock-1", "mock-7", "mock-4", "mock-3", "mock-8", "mock-6", "mock-9"], 10), # Empty keyword, returns all (sorted by relevance)
        ("phone", ["mock-1"], 1), # Test limit
        ("mock", ["mock-5", "mock-2", "mock-1", "mock-7", "mock-4"], 5) # Test limit with many results
    ])
    def test_search_products_basic_keyword(self, populated_service, mock_logger, keyword, expected_ids, limit):
        """Test search_products with various keywords and limits, verifying content and order (if relevant)."""
        results = populated_service.search_products(keyword, limit=limit)
        
        actual_ids = [p['id'] for p in results]
        
        # Ensure results are a subset of expected_ids and are in the expected order based on relevance score
        assert actual_ids == expected_ids[:limit]
        mock_logger.info.assert_any_call(f"Searching products with keyword: {keyword}")
        mock_logger.info.assert_any_call(f"Found {len(expected_ids)} products")

    @pytest.mark.parametrize("keyword, expected_top_id", [
        ("hp murah", "mock-8"), # 'murah' -> price < 5M, mock-8 is 1.5M. Prioritizes lower price if budget keyword is present.
        ("laptop budget", "mock-2"), # 'budget' does set a max price, but the relevance score also boosts lower prices.
                                     # mock-2 (15M) and mock-5 (20M) are found by "laptop" keyword.
                                     # With "budget", mock-2 gets a higher score due to lower price.
        ("phone 5 juta", "mock-8"), # mock-8 (1.5M) is <= 5M. mock-1 (10M) and mock-4 (8M) are not included by price filter.
        ("Rp 2jt", "mock-6"), # All products <= 2M: mock-6 (0.5M), mock-9 (1M), mock-8 (1.5M), mock-3 (2M).
                             # Sorted by price relevance (lower price = higher score).
        ("1000k", "mock-6"), # same as above for 1M
        ("1m", "mock-6"), # same as above for 1M
        ("laptop di bawah 15 juta", "mock-2"), # mock-2 is exactly 15M, so included. mock-5 (20M) is not.
    ])
    def test_search_products_price_extraction_and_relevance(self, populated_service, keyword, expected_top_id):
        """Test search_products with price extraction and relevance sorting, focusing on top result."""
        results = populated_service.search_products(keyword, limit=10)
        actual_ids = [p['id'] for p in results]
        
        assert actual_ids
        assert actual_ids[0] == expected_top_id

        # Verify ordering for "Rp 2jt" to ensure lowest price is preferred
        if keyword == "Rp 2jt":
            expected_order = ["mock-6", "mock-9", "mock-8", "mock-3"]
            assert actual_ids == expected_order

    def test_search_products_exception(self, populated_service, mock_logger):
        """Test search_products handles general exceptions."""
        # Force an error by tampering with products structure for price comparison
        populated_service.products = [{"id": "bad-product", "price": "not-a-number"}] 
        results = populated_service.search_products("any")
        
        assert results == []
        mock_logger.error.assert_called_with("Error searching products: '<=' not supported between instances of 'str' and 'int'")
    
    # --- Test _extract_price_from_keyword ---
    @pytest.mark.parametrize("keyword, expected_price", [
        ("cari laptop 10 juta", 10000000),
        ("handphone di bawah 500 ribu", 500000),
        ("Rp 2500000", 2500000),
        ("harga 1200000rp", 1200000),
        ("monitor 500k", 500000),
        ("pc gaming 20m", 20000000),
        ("cari yang murah", 5000000),
        ("budget terbatas", 5000000),
        ("hemat", 3000000),
        ("terjangkau", 4000000),
        ("ekonomis", 2000000),
        ("no price here", None),
        ("10 juta 500 ribu", 10000000), # Should pick the first match (10 juta)
    ])
    def test_extract_price_from_keyword(self, populated_service, mock_logger, keyword, expected_price):
        """Test _extract_price_from_keyword extracts correct prices/budget values."""
        price = populated_service._extract_price_from_keyword(keyword)
        assert price == expected_price
        mock_logger.error.assert_not_called()

    def test_extract_price_from_keyword_exception(self, populated_service, mock_logger):
        """Test _extract_price_from_keyword handles exceptions (e.g. from regex)."""
        with patch('re.search', side_effect=Exception("Regex processing error")):
            price = populated_service._extract_price_from_keyword("1 juta")
            assert price is None
            mock_logger.error.assert_called_with("Error extracting price from keyword: Regex processing error")
    
    # --- Test get_product_details ---
    def test_get_product_details_found(self, populated_service):
        """Test get_product_details returns correct product for valid ID."""
        product = populated_service.get_product_details("mock-1")
        assert product is not None
        assert product['id'] == "mock-1"
        assert product['name'] == "Mock Phone X"

    def test_get_product_details_not_found(self, populated_service):
        """Test get_product_details returns None for invalid ID."""
        product = populated_service.get_product_details("non-existent-id")
        assert product is None

    def test_get_product_details_empty_products(self, populated_service):
        """Test get_product_details on an empty product list."""
        populated_service.products = []
        product = populated_service.get_product_details("mock-1")
        assert product is None

    def test_get_product_details_exception(self, populated_service, mock_logger):
        """Test get_product_details handles general exceptions (e.g., malformed product)."""
        # Force an exception (e.g., if product.get('id') fails unexpectedly)
        populated_service.products = [{"bad_key": "value"}] # Simulate a product that doesn't have an 'id' key or fails on get()
        product = populated_service.get_product_details("some-id")
        assert product is None
        mock_logger.error.assert_called_once() # Should log an error for the exception

    # --- Test get_categories ---
    def test_get_categories(self, populated_service):
        """Test get_categories returns sorted list of unique categories."""
        categories = populated_service.get_categories()
        # Expect categories from mock data, plus empty string for products missing 'category' key if applicable
        expected_categories = sorted(list(set([p.get('category', '') for p in populated_service.products])))
        assert categories == expected_categories
        assert "Smartphone" in categories
        assert "Laptop" in categories
        assert "Audio" in categories
        assert "Gadget" in categories
        assert "Electronics" in categories
        assert "Collectibles" in categories

    def test_get_categories_empty_products(self, populated_service):
        """Test get_categories on an empty product list."""
        populated_service.products = []
        categories = populated_service.get_categories()
        assert categories == []

    def test_get_categories_product_without_category_key(self, populated_service):
        """Test get_categories handles products missing the 'category' key."""
        populated_service.products = [
            {"id": "p1", "name": "Prod 1"}, # No category key
            {"id": "p2", "name": "Prod 2", "category": "Category A"}
        ]
        categories = populated_service.get_categories()
        assert categories == ['', 'Category A'] 

    # --- Test get_brands ---
    def test_get_brands(self, populated_service):
        """Test get_brands returns sorted list of unique brands."""
        brands = populated_service.get_brands()
        expected_brands = sorted(list(set([p.get('brand', '') for p in populated_service.products])))
        assert brands == expected_brands
        assert "MockApple" in brands
        assert "MockDell" in brands
        assert "MockSony" in brands
        assert "Generic" in brands

    def test_get_brands_empty_products(self, populated_service):
        """Test get_brands on an empty product list."""
        populated_service.products = []
        brands = populated_service.get_brands()
        assert brands == []

    def test_get_brands_product_without_brand_key(self, populated_service):
        """Test get_brands handles products missing the 'brand' key."""
        populated_service.products = [
            {"id": "p1", "name": "Prod 1"}, # No brand key
            {"id": "p2", "name": "Prod 2", "brand": "Brand X"}
        ]
        brands = populated_service.get_brands()
        assert brands == ['', 'Brand X']

    # --- Test get_products_by_category ---
    @pytest.mark.parametrize("category, expected_ids", [
        ("smartphone", ["mock-1", "mock-4", "mock-8"]),
        ("Laptop", ["mock-2", "mock-5"]), # Case-insensitivity
        ("audio", ["mock-3"]),
        ("non-existent-category", []),
        ("", ["mock-6"]), # Category is empty string for 'Empty Spec Product'
    ])
    def test_get_products_by_category(self, populated_service, mock_logger, category, expected_ids):
        """Test get_products_by_category filters correctly."""
        results = populated_service.get_products_by_category(category)
        assert sorted([p['id'] for p in results]) == sorted(expected_ids)
        mock_logger.error.assert_not_called()

    def test_get_products_by_category_empty_products(self, populated_service):
        """Test get_products_by_category on an empty product list."""
        populated_service.products = []
        results = populated_service.get_products_by_category("smartphone")
        assert results == []

    def test_get_products_by_category_exception(self, populated_service, mock_logger):
        """Test get_products_by_category handles general exceptions (e.g., malformed product)."""
        populated_service.products = [{"id": "bad-product", "category": ["list-as-cat"]}]
        results = populated_service.get_products_by_category("any")
        assert results == []
        mock_logger.error.assert_called_with("Error getting products by category: argument of type 'list' is not iterable")
    
    # --- Test get_products_by_brand ---
    @pytest.mark.parametrize("brand, expected_ids", [
        ("mockapple", ["mock-1"]),
        ("MOCKDELL", ["mock-2"]), # Case-insensitivity
        ("MockSony", ["mock-3"]),
        ("non-existent-brand", []),
        ("generic", ["mock-6"]), # Brand is 'Generic' for 'Empty Spec Product'
    ])
    def test_get_products_by_brand(self, populated_service, mock_logger, brand, expected_ids):
        """Test get_products_by_brand filters correctly."""
        results = populated_service.get_products_by_brand(brand)
        assert sorted([p['id'] for p in results]) == sorted(expected_ids)
        mock_logger.error.assert_not_called()

    def test_get_products_by_brand_empty_products(self, populated_service):
        """Test get_products_by_brand on an empty product list."""
        populated_service.products = []
        results = populated_service.get_products_by_brand("apple")
        assert results == []

    def test_get_products_by_brand_exception(self, populated_service, mock_logger):
        """Test get_products_by_brand handles general exceptions (e.g., malformed product)."""
        populated_service.products = [{"id": "bad-product", "brand": ["list-as-brand"]}]
        results = populated_service.get_products_by_brand("any")
        assert results == []
        mock_logger.error.assert_called_with("Error getting products by brand: argument of type 'list' is not iterable")

    # --- Test get_top_rated_products ---
    @pytest.mark.parametrize("limit, expected_ids_prefix", [
        (1, ["mock-7"]), # Highest rating is 5.0 (mock-7)
        (2, ["mock-7", "mock-5"]), # Next is 4.9 (mock-5)
        (5, ["mock-7", "mock-5", "mock-2", "mock-1", "mock-9"]), # Order is by rating: 5.0, 4.9, 4.8, 4.5, 4.2
        (10, ["mock-7", "mock-5", "mock-2", "mock-1", "mock-9", "mock-3", "mock-4", "mock-8", "mock-6"]), # All products, 'Empty Spec Product' (mock-6) has rating 0
        (0, []), # Edge case: limit 0
    ])
    def test_get_top_rated_products(self, populated_service, mock_logger, limit, expected_ids_prefix):
        """Test get_top_rated_products returns products sorted by rating."""
        results = populated_service.get_top_rated_products(limit)
        actual_ids = [p['id'] for p in results]
        
        assert actual_ids == expected_ids_prefix[:limit]
        mock_logger.error.assert_not_called()

    def test_get_top_rated_products_empty_products(self, populated_service):
        """Test get_top_rated_products on an empty product list."""
        populated_service.products = []
        results = populated_service.get_top_rated_products()
        assert results == []

    def test_get_top_rated_products_exception(self, populated_service, mock_logger):
        """Test get_top_rated_products handles general exceptions (e.g., malformed product)."""
        populated_service.products = [{"id": "bad-product", "specifications": "not-a-dict"}]
        results = populated_service.get_top_rated_products()
        assert results == []
        mock_logger.error.assert_called_with("Error getting top rated products: 'str' object has no attribute 'get'")

    # --- Test get_best_selling_products ---
    @pytest.mark.parametrize("limit, expected_ids_prefix", [
        (1, ["mock-9"]), # Highest sold (5000)
        (2, ["mock-9", "mock-1"]), # Next highest sold (all others have 1000). Order among 1000-sold depends on stable sort, picked mock-1 as example.
        (5, ["mock-9", "mock-1", "mock-2", "mock-3", "mock-4"]), 
        (0, []),
    ])
    def test_get_best_selling_products(self, populated_service, mock_logger, limit, expected_ids_prefix):
        """Test get_best_selling_products returns products sorted by sold count."""
        # Ensure mock-9 has 5000 sold, others 1000. This is handled by `get_expected_transformed_products`.
        results = populated_service.get_best_selling_products(limit)
        actual_ids = [p['id'] for p in results]
        
        assert len(results) == min(limit, len(populated_service.products))
        if limit > 0:
            assert actual_ids[0] == "mock-9"
        
        mock_logger.info.assert_any_call(f"Getting best selling products, limit: {limit}")
        mock_logger.info.assert_any_call(f"Returning {min(limit, len(results))} best selling products")
        mock_logger.error.assert_not_called()

    def test_get_best_selling_products_empty_products(self, populated_service):
        """Test get_best_selling_products on an empty product list."""
        populated_service.products = []
        results = populated_service.get_best_selling_products()
        assert results == []

    def test_get_best_selling_products_exception(self, populated_service, mock_logger):
        """Test get_best_selling_products handles general exceptions (e.g., malformed product)."""
        populated_service.products = [{"id": "bad-product", "specifications": "not-a-dict"}]
        results = populated_service.get_best_selling_products()
        assert results == []
        mock_logger.error.assert_called_with("Error getting best selling products: 'str' object has no attribute 'get'")

    # --- Test get_products ---
    @pytest.mark.parametrize("limit, expected_count", [
        (1, 1),
        (5, 5),
        (9, 9), # All products in mock data
        (10, 9), # Requesting more than available
        (0, 0),
    ])
    def test_get_products(self, populated_service, mock_logger, limit, expected_count):
        """Test get_products returns all products up to the limit."""
        results = populated_service.get_products(limit)
        assert len(results) == min(expected_count, len(populated_service.products))
        mock_logger.info.assert_any_call(f"Getting all products, limit: {limit}")
        mock_logger.error.assert_not_called()

    def test_get_products_empty_products(self, populated_service):
        """Test get_products on an empty product list."""
        populated_service.products = []
        results = populated_service.get_products()
        assert results == []

    def test_get_products_exception(self, populated_service, mock_logger):
        """Test get_products handles general exceptions (e.g., during list access)."""
        with patch.object(populated_service, 'products', new_callable=MagicMock) as mock_products_list:
            mock_products_list.__getitem__.side_effect = Exception("List access error")
            results = populated_service.get_products()
            assert results == []
            mock_logger.error.assert_called_with("Error getting products: List access error")

    # --- Test smart_search_products ---
    @pytest.mark.parametrize("keyword, category, max_price, limit, expected_ids_prefix, expected_message_part", [
        # 1. is_best_request and no category
        ("laptop terbaik", None, None, 2, ["mock-7", "mock-5"], "Berikut produk terbaik berdasarkan rating:"),
        ("best phone", None, None, 1, ["mock-7"], "Berikut produk terbaik berdasarkan rating:"),
        # 2. is_best_request and specific category (found)
        ("smartphone terbaik", "Smartphone", None, 1, ["mock-1"], "Berikut Smartphone terbaik berdasarkan rating:"), 
        ("laptop terbaik", "Laptop", None, 1, ["mock-5"], "Berikut Laptop terbaik berdasarkan rating:"),
        # 2. is_best_request and specific category (not found) -> fallback to general best
        ("tv terbaik", "Television", None, 1, ["mock-7"], "Tidak ada produk kategori Television, berikut produk terbaik secara umum:"),
        # 3. All criteria match
        ("phone", "Smartphone", 9000000, 10, ["mock-4", "mock-8"], "Berikut produk yang sesuai dengan kriteria Anda."), 
        ("mock", "Laptop", 16000000, 10, ["mock-2"], "Berikut produk yang sesuai dengan kriteria Anda."),
        # 4. No exact match, but category provided -> cheapest in category
        ("non-existent-keyword", "Smartphone", 1000000, 10, ["mock-8"], "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."),
        # 5. No category match, but max_price provided -> other products within budget
        ("non-existent-keyword", "NonExistentCategory", 2000000, 10, ["mock-6", "mock-9", "mock-8", "mock-3"], "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."),
        # 6. No match for any specific criteria -> best-selling
        ("totally-random", "no-such-cat", 100, 10, ["mock-9", "mock-1"], "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."),
        # Empty keyword
        ("", None, None, 2, ["mock-7", "mock-5"], "Berikut produk terbaik berdasarkan rating:"), 
        ("", "Laptop", None, 1, ["mock-5"], "Berikut Laptop terbaik berdasarkan rating:"), 
        ("", None, 10000000, 2, ["mock-1", "mock-4"], "Berikut produk yang sesuai dengan kriteria Anda."),
    ])
    def test_smart_search_products(self, populated_service, mock_logger, mock_random_randint, keyword, category, max_price, limit, expected_ids_prefix, expected_message_part):
        """Test smart_search_products with various scenarios and fallbacks."""
        # Ensure 'sold' values are correct for best-selling fallback (mock-9: 5000, others 1000)
        # populated_service.products already initialized with get_expected_transformed_products,
        # which correctly sets mock-9's sold count to 5000 and others to 1000 (from random.randint mock)
        
        results, message = populated_service.smart_search_products(keyword=keyword, category=category, max_price=max_price, limit=limit)
        
        assert len(results) <= limit
        actual_ids = [p['id'] for p in results]
        
        if "produk terbaik" in expected_message_part or "terpopuler" in expected_message_part or "termurah" in expected_message_part:
            assert actual_ids == expected_ids_prefix[:len(actual_ids)] # Compare with length of actual results
        else:
            # For filtered results, set comparison is more robust as order may vary based on internal sort stability
            assert set(actual_ids) == set(expected_ids_prefix[:len(actual_ids)]) 

        assert expected_message_part in message
        mock_logger.error.assert_not_called()

    def test_smart_search_products_empty_products(self, populated_service):
        """Test smart_search_products on an empty product list."""
        populated_service.products = []
        
        results, message = populated_service.smart_search_products(keyword="any")
        assert results == []
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message 

    def test_smart_search_products_exception_in_logic(self, populated_service, mock_logger):
        """Test smart_search_products raises exception if internal logic fails (e.g. malformed data for sorting)."""
        # Note: The smart_search_products method itself does not have a top-level try-except block,
        # so internal exceptions (like TypeError during sorting due to malformed data) will propagate.
        populated_service.products = [{"id": "bad-product", "specifications": "not-a-dict"}]
        
        with pytest.raises(TypeError) as excinfo:
            populated_service.smart_search_products(keyword="terbaik")
        assert "'str' object has no attribute 'get'" in str(excinfo.value)
        mock_logger.error.assert_not_called() # The service's error logger shouldn't be called if exception propagates.