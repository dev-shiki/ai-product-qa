import pytest
from unittest.mock import patch, mock_open, MagicMock
import json
import logging
from pathlib import Path # Used for type hinting and patching Path class

# We import LocalProductService inside the fixtures/tests to ensure
# that patching of 'pathlib.Path' and 'builtins.open' takes effect before
# the class is initialized, especially for the __init__ method's call to _load_local_products.

# Set up logging for test introspection if needed
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Sample Data for Mocks ---
SAMPLE_RAW_PRODUCTS_JSON = {
    "products": [
        {"id": "p1", "name": "Test Product 1", "category": "Electronics", "brand": "BrandA", "price": 1000000, "currency": "IDR", "description": "Desc 1", "rating": 4.5, "stock_count": 10, "availability": "in_stock", "reviews_count": 50, "specifications": {"color": "red"}},
        {"id": "p2", "name": "Test Product 2", "category": "Books", "brand": "BrandB", "price": 50000, "currency": "IDR", "description": "Desc 2", "rating": 3.8, "stock_count": 20, "availability": "out_of_stock", "reviews_count": 10},
        {"id": "p3", "name": "Another Product", "category": "Electronics", "brand": "BrandC", "price": 2500000, "currency": "IDR", "description": "High-end product", "rating": 4.9, "stock_count": 5, "reviews_count": 100}, # Missing availability
        {"id": "p4", "name": "Budget Phone", "category": "Electronics", "brand": "BrandA", "price": 2000000, "currency": "IDR", "description": "Affordable phone", "rating": 4.0, "stock_count": 30, "reviews_count": 20, "specifications": {"storage": "64GB", "processor": "Snapdragon"}},
        {"id": "p5", "name": "Laptop Pro", "category": "Laptop", "brand": "BrandD", "price": 15000000, "currency": "IDR", "description": "Powerful laptop", "rating": 4.7, "stock_count": 8, "reviews_count": 80, "specifications": {"ram": "16GB"}},
    ]
}

# The transformed products will have 'sold' count set by mocked random.randint
# and default values for any missing keys.
TRANSFORMED_PRODUCTS_MOCK_SOLD = [
    {
        "id": "p1", "name": "Test Product 1", "category": "Electronics", "brand": "BrandA", "price": 1000000, "currency": "IDR", "description": "Desc 1",
        "specifications": {"rating": 4.5, "sold": 500, "stock": 10, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandA Store", "color": "red"},
        "availability": "in_stock", "reviews_count": 50, "images": ["https://example.com/p1.jpg"], "url": "https://shopee.co.id/p1"
    },
    {
        "id": "p2", "name": "Test Product 2", "category": "Books", "brand": "BrandB", "price": 50000, "currency": "IDR", "description": "Desc 2",
        "specifications": {"rating": 3.8, "sold": 500, "stock": 20, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandB Store"},
        "availability": "out_of_stock", "reviews_count": 10, "images": ["https://example.com/p2.jpg"], "url": "https://shopee.co.id/p2"
    },
    {
        "id": "p3", "name": "Another Product", "category": "Electronics", "brand": "BrandC", "price": 2500000, "currency": "IDR", "description": "High-end product",
        "specifications": {"rating": 4.9, "sold": 500, "stock": 5, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandC Store"},
        "availability": "in_stock", "reviews_count": 100, "images": ["https://example.com/p3.jpg"], "url": "https://shopee.co.id/p3"
    },
    {
        "id": "p4", "name": "Budget Phone", "category": "Electronics", "brand": "BrandA", "price": 2000000, "currency": "IDR", "description": "Affordable phone",
        "specifications": {"rating": 4.0, "sold": 500, "stock": 30, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandA Store", "storage": "64GB", "processor": "Snapdragon"},
        "availability": "in_stock", "reviews_count": 20, "images": ["https://example.com/p4.jpg"], "url": "https://shopee.co.id/p4"
    },
    {
        "id": "p5", "name": "Laptop Pro", "category": "Laptop", "brand": "BrandD", "price": 15000000, "currency": "IDR", "description": "Powerful laptop",
        "specifications": {"rating": 4.7, "sold": 500, "stock": 8, "condition": "Baru", "shop_location": "Indonesia", "shop_name": "BrandD Store", "ram": "16GB"},
        "availability": "in_stock", "reviews_count": 80, "images": ["https://example.com/p5.jpg"], "url": "https://shopee.co.id/p5"
    }
]

# --- Pytest Fixtures ---

@pytest.fixture
def mock_logger():
    """Mocks the application's logger to capture log messages."""
    with patch('app.services.local_product_service.logger') as mock_log:
        yield mock_log

@pytest.fixture
def mock_path_setup():
    """
    Sets up a mock Path object structure to simulate `Path(__file__).parent.parent.parent / "data" / "products.json"`.
    Yields the mock object representing the `products.json` file, whose `exists()` method
    and string representation can be controlled by individual tests/fixtures.
    """
    # These mocks represent: Path(__file__), Path(__file__).parent, Path(__file__).parent.parent, etc.
    mock_file_path = MagicMock(spec=Path, name="Path(__file__)")
    mock_parent_app_services = MagicMock(spec=Path, name="app/services")
    mock_parent_app = MagicMock(spec=Path, name="app")
    mock_project_root = MagicMock(spec=Path, name="project_root")

    # Chain parents to simulate `Path(__file__).parent.parent.parent`
    mock_file_path.parent = mock_parent_app_services
    mock_parent_app_services.parent = mock_parent_app
    mock_parent_app.parent = mock_project_root

    # Mocks for the path joining (`/` operator) to construct `data/products.json`
    mock_data_dir = MagicMock(spec=Path, name="data_dir")
    mock_products_json_path = MagicMock(spec=Path, name="products.json")

    # Define side effects for the `/` operator (`__truediv__`) to return specific mocks
    def truediv_side_effect_root(part):
        if str(part) == "data":
            return mock_data_dir
        # Return a generic mock for any other path part joined to root
        return MagicMock(spec=Path, name=f"{mock_project_root.name}/{part}")

    def truediv_side_effect_data(part):
        if str(part) == "products.json":
            return mock_products_json_path
        # Return a generic mock for any other path part joined to data dir
        return MagicMock(spec=Path, name=f"{mock_data_dir.name}/{part}")

    mock_project_root.__truediv__.side_effect = truediv_side_effect_root
    mock_data_dir.__truediv__.side_effect = truediv_side_effect_data
    
    # Patch `pathlib.Path` globally within the module under test
    # so that any `Path(...)` call returns our controlled mock_file_path.
    with patch('app.services.local_product_service.Path', return_value=mock_file_path) as mock_path_class:
        yield mock_products_json_path # Yield the mock representing the products.json file

@pytest.fixture
def mock_randint():
    """Mocks `random.randint` to return a predictable value (500) for 'sold' counts."""
    with patch('random.randint', return_value=500) as mock_rand:
        yield mock_rand

@pytest.fixture
def local_product_service_instance_success(mock_path_setup, mock_randint):
    """Provides a `LocalProductService` instance with successfully loaded products from a mocked JSON file."""
    mock_products_json_path = mock_path_setup
    mock_products_json_path.exists.return_value = True # Simulate file exists
    
    json_content = json.dumps(SAMPLE_RAW_PRODUCTS_JSON)
    with patch('builtins.open', mock_open(read_data=json_content)):
        from app.services.local_product_service import LocalProductService
        yield LocalProductService()

@pytest.fixture
def local_product_service_empty_products_file(mock_path_setup, mock_randint):
    """Provides a `LocalProductService` instance where `products.json` exists but contains an empty product list."""
    mock_products_json_path = mock_path_setup
    mock_products_json_path.exists.return_value = True
    
    json_content = json.dumps({"products": []})
    with patch('builtins.open', mock_open(read_data=json_content)):
        from app.services.local_product_service import LocalProductService
        yield LocalProductService()

@pytest.fixture
def local_product_service_fallback(mock_path_setup, mock_logger, mock_randint):
    """Provides a `LocalProductService` instance where `products.json` is not found, triggering fallback."""
    mock_products_json_path = mock_path_setup
    mock_products_json_path.exists.return_value = False # Simulate file not found
    
    # `open` might not be called if `exists()` returns False, but patch defensively
    with patch('builtins.open', side_effect=IOError("Simulated file not found")):
        from app.services.local_product_service import LocalProductService
        yield LocalProductService()

@pytest.fixture
def local_product_service_json_decode_error(mock_path_setup, mock_logger, mock_randint):
    """Provides a `LocalProductService` instance where JSON parsing fails, triggering fallback."""
    mock_products_json_path = mock_path_setup
    mock_products_json_path.exists.return_value = True
    
    mock_read_data = "invalid json {" # Invalid JSON content
    # Simulate `json.JSONDecodeError` for all encoding attempts
    def mock_json_loads_side_effect(*args, **kwargs):
        raise json.JSONDecodeError("Expecting value", "doc", 0)

    with patch('builtins.open', mock_open(read_data=mock_read_data)), \
         patch('json.loads', side_effect=mock_json_loads_side_effect):
        from app.services.local_product_service import LocalProductService
        yield LocalProductService()

@pytest.fixture
def local_product_service_unicode_decode_error(mock_path_setup, mock_logger, mock_randint):
    """Provides a `LocalProductService` instance where Unicode decoding fails for all encodings, triggering fallback."""
    mock_products_json_path = mock_path_setup
    mock_products_json_path.exists.return_value = True

    # Simulate `UnicodeDecodeError` for all encoding attempts
    def mock_open_side_effect(*args, **kwargs):
        # We raise UnicodeDecodeError if 'encoding' is specified (as it would be by the service)
        if 'encoding' in kwargs:
            raise UnicodeDecodeError("utf-8", b'\x00', 0, 1, "invalid start byte")
        # Fallback to a normal mock_open if encoding isn't specified (shouldn't happen here)
        return mock_open(read_data="dummy_content").return_value

    with patch('builtins.open', side_effect=mock_open_side_effect):
        from app.services.local_product_service import LocalProductService
        yield LocalProductService()

@pytest.fixture
def local_product_service_generic_load_exception(mock_path_setup, mock_logger, mock_randint):
    """Provides a `LocalProductService` instance where a generic exception occurs during file loading, triggering fallback."""
    mock_products_json_path = mock_path_setup
    # Simulate an exception when `exists()` is called on the file path
    mock_products_json_path.exists.side_effect = Exception("Simulated general I/O error during exists check")

    with patch('builtins.open'): # Patch `open` defensively, though it might not be called
        from app.services.local_product_service import LocalProductService
        yield LocalProductService()

# --- Tests for LocalProductService Initialization and _load_local_products ---

def test_init_success(local_product_service_instance_success, mock_logger):
    """Test successful initialization and product loading from a valid JSON file."""
    service = local_product_service_instance_success
    assert len(service.products) == len(TRANSFORMED_PRODUCTS_MOCK_SOLD)
    assert service.products[0]['id'] == 'p1'
    # Check logger calls
    mock_logger.info.assert_any_call(f"Loaded {len(TRANSFORMED_PRODUCTS_MOCK_SOLD)} local products from JSON file")
    # The default successful encoding attempt is the first one in the list ('utf-16-le')
    mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_PRODUCTS_MOCK_SOLD)} products from JSON file using utf-16-le encoding")

def test_init_file_not_found_fallback(local_product_service_fallback, mock_logger):
    """Test initialization when the products JSON file is not found, leading to fallback products."""
    service = local_product_service_fallback
    assert len(service.products) > 0 # Should load fallback products
    # The path string will be the mocked Path object's name
    mock_logger.error.assert_any_call(f"Products JSON file not found at: {service.products[0]['id']}") # Fix: this is not the path, it's the id of a fallback product.
    # The Path mock's `name` attribute is used for its string representation, or `str(mock_products_json_path)`
    mock_logger.error.assert_any_call(f"Products JSON file not found at: mock_products.json")
    mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")
    mock_logger.info.assert_any_call(f"Loaded {len(service.products)} local products from JSON file")

def test_init_json_decode_error_fallback(local_product_service_json_decode_error, mock_logger):
    """Test initialization when JSON parsing fails for all encodings, leading to fallback."""
    service = local_product_service_json_decode_error
    assert len(service.products) > 0 # Should load fallback products
    # Check for warning messages for each failed encoding attempt
    for encoding in ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        mock_logger.warning.assert_any_call(f"Failed to load with {encoding} encoding: Expecting value at document start: line 1 column 1 (char 0)")
    mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
    mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")
    mock_logger.info.assert_any_call(f"Loaded {len(service.products)} local products from JSON file")

def test_init_unicode_decode_error_fallback(local_product_service_unicode_decode_error, mock_logger):
    """Test initialization when Unicode decoding fails for all encodings, leading to fallback."""
    service = local_product_service_unicode_decode_error
    assert len(service.products) > 0 # Should load fallback products
    # Check for warning messages for each failed encoding attempt
    for encoding in ['utf-16-le', 'utf-16', 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        mock_logger.warning.assert_any_call(f"Failed to load with {encoding} encoding: invalid start byte")
    mock_logger.error.assert_any_call("All encoding attempts failed, using fallback products")
    mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")
    mock_logger.info.assert_any_call(f"Loaded {len(service.products)} local products from JSON file")

def test_init_generic_exception_during_load_fallback(local_product_service_generic_load_exception, mock_logger):
    """Test initialization when a generic exception occurs during `_load_local_products`, leading to fallback."""
    service = local_product_service_generic_load_exception
    assert len(service.products) > 0 # Should load fallback products
    mock_logger.error.assert_any_call("Error loading products from JSON file: Simulated general I/O error during exists check")
    mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")
    mock_logger.info.assert_any_call(f"Loaded {len(service.products)} local products from JSON file")

def test_load_local_products_with_bom(mock_path_setup, mock_randint, mock_logger):
    """Test `_load_local_products` correctly handles JSON content containing a Byte Order Mark (BOM)."""
    mock_products_json_path = mock_path_setup
    mock_products_json_path.exists.return_value = True
    
    json_content_with_bom = '\ufeff' + json.dumps(SAMPLE_RAW_PRODUCTS_JSON)
    with patch('builtins.open', mock_open(read_data=json_content_with_bom)):
        from app.services.local_product_service import LocalProductService
        service = LocalProductService()
        assert len(service.products) == len(TRANSFORMED_PRODUCTS_MOCK_SOLD)
        assert service.products[0]['name'] == 'Test Product 1'
        mock_logger.info.assert_any_call(f"Successfully loaded {len(TRANSFORMED_PRODUCTS_MOCK_SOLD)} products from JSON file using utf-16-le encoding")

# --- Tests for _get_fallback_products ---

def test_get_fallback_products(local_product_service_fallback, mock_logger):
    """Test `_get_fallback_products` returns the expected hardcoded fallback data."""
    # The `local_product_service_fallback` fixture already loads fallback products
    service = local_product_service_fallback
    fallback_products = service._get_fallback_products() # Call it explicitly
    assert len(fallback_products) == 8 # Based on the source code's fallback list size
    assert fallback_products[0]['id'] == "1"
    assert fallback_products[0]['name'] == "iPhone 15 Pro Max"
    mock_logger.warning.assert_any_call("Using fallback products due to JSON file loading error")

# --- Tests for search_products ---

def test_search_products_by_name(local_product_service_instance_success, mock_logger):
    """Test searching products by exact name keyword."""
    service = local_product_service_instance_success
    results = service.search_products("Test Product 1")
    assert len(results) == 1
    assert results[0]['id'] == 'p1'
    mock_logger.info.assert_any_call("Searching products with keyword: Test Product 1")
    mock_logger.info.assert_any_call("Found 1 products")

def test_search_products_by_brand_case_insensitive(local_product_service_instance_success):
    """Test searching products by brand, case-insensitively."""
    service = local_product_service_instance_success
    results = service.search_products("branda")
    assert len(results) == 2
    assert {p['id'] for p in results} == {'p1', 'p4'}

def test_search_products_by_category(local_product_service_instance_success):
    """Test searching products by category keyword."""
    service = local_product_service_instance_success
    results = service.search_products("electronics")
    assert len(results) == 3
    assert {p['id'] for p in results} == {'p1', 'p3', 'p4'}

def test_search_products_by_description(local_product_service_instance_success):
    """Test searching products by description keyword."""
    service = local_product_service_instance_success
    results = service.search_products("high-end")
    assert len(results) == 1
    assert results[0]['id'] == 'p3'

def test_search_products_by_specifications(local_product_service_instance_success):
    """Test searching products by content within specifications."""
    service = local_product_service_instance_success
    results = service.search_products("storage")
    assert len(results) == 1
    assert results[0]['id'] == 'p4'

def test_search_products_no_match(local_product_service_instance_success):
    """Test searching products with a keyword that yields no matches."""
    service = local_product_service_instance_success
    results = service.search_products("xyz_non_existent_product")
    assert len(results) == 0

def test_search_products_empty_keyword(local_product_service_instance_success):
    """Test searching products with an empty keyword, should return results sorted by relevance."""
    service = local_product_service_instance_success
    # With empty keyword, relevance score defaults to 0, so stable sort based on initial load order.
    results = service.search_products("", limit=2)
    assert len(results) == 2
    assert [p['id'] for p in results] == ['p1', 'p2']

def test_search_products_limit(local_product_service_instance_success):
    """Test search results are limited correctly."""
    service = local_product_service_instance_success
    results = service.search_products("product", limit=2) # "Product" matches p1, p2, p3
    assert len(results) == 2
    # p1, p2, p3 all contain "product" in their name/description/specs.
    # All get score 10 for name match. With same scores, Python's sort is stable,
    # preserving original order: p1, p2.
    assert [p['id'] for p in results] == ['p1', 'p2']

def test_search_products_max_price_extracted_from_keyword(local_product_service_instance_success):
    """Test searching with price range extracted from keyword, combined with other keywords."""
    service = local_product_service_instance_success
    results = service.search_products("laptop under 2 juta")
    # _extract_price_from_keyword will get max_price=2,000,000 from "2 juta".
    # Products matching price: p1, p2, p4.
    # Products matching keyword "laptop": p5.
    # The logic adds product if it matches price range OR keyword. So, all p1,p2,p4,p5 will be included.
    # Relevance sorting: p5 gets higher score for "laptop" in name.
    # Others get 0 base score. If "budget" or similar keywords are not present, price doesn't affect score.
    # So p5 is first, then p1, p2, p4 in their original order (due to stable sort for same score).
    assert len(results) == 4
    assert results[0]['id'] == 'p5'
    assert {p['id'] for p in results} == {'p1', 'p2', 'p4', 'p5'}

def test_search_products_budget_keyword_influences_relevance(local_product_service_instance_success):
    """Test searching with a budget keyword (like 'murah') correctly influences relevance sorting."""
    service = local_product_service_instance_success
    results = service.search_products("murah", limit=3) # 'murah' implies max_price 5M
    # Products with price <= 5M: p1, p2, p3, p4.
    # The keyword 'murah' applies a price factor to the relevance score, preferring lower prices.
    # Scores (relative price component):
    # p2: 50,000 (highest price score)
    # p1: 1,000,000
    # p4: 2,000,000
    # p3: 2,500,000
    # p5: 15,000,000 (filtered out by max_price from 'murah')
    # Expected order based on price factor: p2, p1, p4 (then p3 if limit was higher)
    assert len(results) == 3
    assert [p['id'] for p in results] == ['p2', 'p1', 'p4']

def test_search_products_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `search_products` method."""
    service = local_product_service_instance_success
    with patch.object(service, '_extract_price_from_keyword', side_effect=Exception("Simulated price extraction error")):
        results = service.search_products("test")
        assert len(results) == 0
        mock_logger.error.assert_called_with("Error searching products: Simulated price extraction error")

# --- Tests for _extract_price_from_keyword ---

@pytest.mark.parametrize("keyword, expected_price", [
    ("hp 2 juta", 2000000),
    ("laptop 5ribu", 5000),
    ("Rp 100000", 100000),
    ("25000 Rp", 25000),
    ("monitor 300k", 300000),
    ("tv 10m", 10000000),
    ("harga murah", 5000000),
    ("budget pc", 5000000),
    ("promo hemat", 3000000),
    ("terjangkau smartphone", 4000000),
    ("ekonomis headset", 2000000),
    ("no price here", None),
    ("1000k rupiah", 1000000), # Combination test
    ("hp dibawah 1000000", 1000000), # Test for numerical patterns without price units
    ("sampai rp50000", 50000),
    ("price up to 1m", 1000000),
    ("max 7juta", 7000000),
])
def test_extract_price_from_keyword_success(local_product_service_instance_success, keyword, expected_price):
    """Test successful price extraction from various keyword patterns."""
    service = local_product_service_instance_success
    assert service._extract_price_from_keyword(keyword) == expected_price

def test_extract_price_from_keyword_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `_extract_price_from_keyword`."""
    service = local_product_service_instance_success
    # Simulate an error during regex search
    with patch('re.search', side_effect=Exception("Simulated regex error")):
        price = service._extract_price_from_keyword("1 juta")
        assert price is None
        mock_logger.error.assert_called_with("Error extracting price from keyword: Simulated regex error")

# --- Tests for get_product_details ---

def test_get_product_details_found(local_product_service_instance_success):
    """Test retrieving details for an existing product ID."""
    service = local_product_service_instance_success
    product = service.get_product_details("p1")
    assert product is not None
    assert product['id'] == 'p1'
    assert product['name'] == 'Test Product 1'

def test_get_product_details_not_found(local_product_service_instance_success):
    """Test retrieving details for a non-existing product ID."""
    service = local_product_service_instance_success
    product = service.get_product_details("non_existent_id")
    assert product is None

def test_get_product_details_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `get_product_details`."""
    service = local_product_service_instance_success
    # Simulate an error during iteration over `self.products`
    with patch.object(service, 'products', side_effect=Exception("Simulated product access error")):
        product = service.get_product_details("p1")
        assert product is None
        mock_logger.error.assert_called_with("Error getting product details: Simulated product access error")

# --- Tests for get_categories ---

def test_get_categories_success(local_product_service_instance_success):
    """Test retrieving unique product categories."""
    service = local_product_service_instance_success
    categories = service.get_categories()
    assert sorted(categories) == ['Books', 'Electronics', 'Laptop']

def test_get_categories_empty_products(local_product_service_empty_products_file):
    """Test retrieving categories when no products are loaded from the file."""
    service = local_product_service_empty_products_file
    categories = service.get_categories()
    assert categories == []

# --- Tests for get_brands ---

def test_get_brands_success(local_product_service_instance_success):
    """Test retrieving unique product brands."""
    service = local_product_service_instance_success
    brands = service.get_brands()
    assert sorted(brands) == ['BrandA', 'BrandB', 'BrandC', 'BrandD']

def test_get_brands_empty_products(local_product_service_empty_products_file):
    """Test retrieving brands when no products are loaded from the file."""
    service = local_product_service_empty_products_file
    brands = service.get_brands()
    assert brands == []

# --- Tests for get_products_by_category ---

def test_get_products_by_category_found(local_product_service_instance_success):
    """Test retrieving products for an existing category."""
    service = local_product_service_instance_success
    products = service.get_products_by_category("electronics")
    assert len(products) == 3
    assert {p['id'] for p in products} == {'p1', 'p3', 'p4'}

def test_get_products_by_category_not_found(local_product_service_instance_success):
    """Test retrieving products for a non-existing category."""
    service = local_product_service_instance_success
    products = service.get_products_by_category("Fashion")
    assert len(products) == 0

def test_get_products_by_category_case_insensitivity(local_product_service_instance_success):
    """Test category search is case-insensitive."""
    service = local_product_service_instance_success
    products_upper = service.get_products_by_category("Electronics")
    assert len(products_upper) == 3
    products_mixed = service.get_products_by_category("eLeCtRoNiCs")
    assert len(products_mixed) == 3
    assert {p['id'] for p in products_upper} == {p['id'] for p in products_mixed}

def test_get_products_by_category_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `get_products_by_category`."""
    service = local_product_service_instance_success
    with patch.object(service, 'products', side_effect=Exception("Simulated product access error")):
        products = service.get_products_by_category("Electronics")
        assert len(products) == 0
        mock_logger.error.assert_called_with("Error getting products by category: Simulated product access error")

# --- Tests for get_products_by_brand ---

def test_get_products_by_brand_found(local_product_service_instance_success):
    """Test retrieving products for an existing brand."""
    service = local_product_service_instance_success
    products = service.get_products_by_brand("BrandA")
    assert len(products) == 2
    assert {p['id'] for p in products} == {'p1', 'p4'}

def test_get_products_by_brand_not_found(local_product_service_instance_success):
    """Test retrieving products for a non-existing brand."""
    service = local_product_service_instance_success
    products = service.get_products_by_brand("NonExistentBrand")
    assert len(products) == 0

def test_get_products_by_brand_case_insensitivity(local_product_service_instance_success):
    """Test brand search is case-insensitive."""
    service = local_product_service_instance_success
    products_lower = service.get_products_by_brand("branda")
    assert len(products_lower) == 2
    assert {p['id'] for p in products_lower} == {'p1', 'p4'}

def test_get_products_by_brand_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `get_products_by_brand`."""
    service = local_product_service_instance_success
    with patch.object(service, 'products', side_effect=Exception("Simulated product access error")):
        products = service.get_products_by_brand("BrandA")
        assert len(products) == 0
        mock_logger.error.assert_called_with("Error getting products by brand: Simulated product access error")

# --- Tests for get_top_rated_products ---

def test_get_top_rated_products_success(local_product_service_instance_success):
    """Test retrieving top-rated products with default limit."""
    service = local_product_service_instance_success
    # Expected order based on rating: p3 (4.9), p5 (4.7), p1 (4.5), p4 (4.0), p2 (3.8)
    expected_order_ids = ['p3', 'p5', 'p1', 'p4', 'p2']
    products = service.get_top_rated_products() # default limit 5
    assert len(products) == 5
    assert [p['id'] for p in products] == expected_order_ids

def test_get_top_rated_products_with_limit(local_product_service_instance_success):
    """Test retrieving top-rated products with a specified limit."""
    service = local_product_service_instance_success
    products = service.get_top_rated_products(limit=2)
    assert len(products) == 2
    assert [p['id'] for p in products] == ['p3', 'p5']

def test_get_top_rated_products_empty(local_product_service_empty_products_file):
    """Test retrieving top-rated products when no products are available."""
    service = local_product_service_empty_products_file
    products = service.get_top_rated_products()
    assert len(products) == 0

def test_get_top_rated_products_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `get_top_rated_products`."""
    service = local_product_service_instance_success
    with patch.object(service, 'products', side_effect=Exception("Simulated product access error")):
        products = service.get_top_rated_products()
        assert len(products) == 0
        mock_logger.error.assert_called_with("Error getting top rated products: Simulated product access error")

# --- Tests for get_best_selling_products ---

def test_get_best_selling_products_success(local_product_service_instance_success, mock_logger):
    """Test retrieving best-selling products with default limit."""
    service = local_product_service_instance_success
    # Since all mock sold counts are 500, the sort order will be stable, maintaining original order.
    expected_order_ids = ['p1', 'p2', 'p3', 'p4', 'p5']
    products = service.get_best_selling_products() # default limit 5
    assert len(products) == 5
    assert [p['id'] for p in products] == expected_order_ids
    mock_logger.info.assert_any_call("Getting best selling products, limit: 5")
    mock_logger.info.assert_any_call("Returning 5 best selling products")


def test_get_best_selling_products_with_limit(local_product_service_instance_success):
    """Test retrieving best-selling products with a specified limit."""
    service = local_product_service_instance_success
    products = service.get_best_selling_products(limit=2)
    assert len(products) == 2
    assert [p['id'] for p in products] == ['p1', 'p2'] # Stable sort based on original order

def test_get_best_selling_products_empty(local_product_service_empty_products_file):
    """Test retrieving best-selling products when no products are available."""
    service = local_product_service_empty_products_file
    products = service.get_best_selling_products()
    assert len(products) == 0

def test_get_best_selling_products_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `get_best_selling_products`."""
    service = local_product_service_instance_success
    with patch.object(service, 'products', side_effect=Exception("Simulated product access error")):
        products = service.get_best_selling_products()
        assert len(products) == 0
        mock_logger.error.assert_called_with("Error getting best selling products: Simulated product access error")

# --- Tests for get_products ---

def test_get_products_success(local_product_service_instance_success, mock_logger):
    """Test retrieving all products with default limit."""
    service = local_product_service_instance_success
    products = service.get_products() # default limit 10
    assert len(products) == len(TRANSFORMED_PRODUCTS_MOCK_SOLD)
    assert products == TRANSFORMED_PRODUCTS_MOCK_SOLD # Should return all 5 since limit is 10
    mock_logger.info.assert_any_call(f"Getting all products, limit: 10")

def test_get_products_with_limit(local_product_service_instance_success):
    """Test retrieving products with a specified limit."""
    service = local_product_service_instance_success
    products = service.get_products(limit=2)
    assert len(products) == 2
    assert products == TRANSFORMED_PRODUCTS_MOCK_SOLD[:2]

def test_get_products_empty(local_product_service_empty_products_file):
    """Test retrieving products when no products are available."""
    service = local_product_service_empty_products_file
    products = service.get_products()
    assert len(products) == 0

def test_get_products_error_handling(local_product_service_instance_success, mock_logger):
    """Test error handling in `get_products`."""
    service = local_product_service_instance_success
    with patch.object(service, 'products', side_effect=Exception("Simulated product access error")):
        products = service.get_products()
        assert len(products) == 0
        mock_logger.error.assert_called_with("Error getting products: Simulated product access error")

# --- Tests for smart_search_products (Hybrid Fallback Search) ---

def test_smart_search_products_best_general_request(local_product_service_instance_success):
    """Test `smart_search_products` for 'terbaik' keyword without a specific category."""
    service = local_product_service_instance_success
    products, message = service.smart_search_products(keyword="produk terbaik")
    assert "Berikut produk terbaik berdasarkan rating:" in message
    assert len(products) == 5 # All products, sorted by rating
    # Expected order: p3 (4.9), p5 (4.7), p1 (4.5), p4 (4.0), p2 (3.8)
    assert [p['id'] for p in products] == ['p3', 'p5', 'p1', 'p4', 'p2']

def test_smart_search_products_best_category_found(local_product_service_instance_success):
    """Test `smart_search_products` for 'terbaik' with an existing specific category."""
    service = local_product_service_instance_success
    products, message = service.smart_search_products(keyword="hp terbaik", category="Electronics")
    assert "Berikut Electronics terbaik berdasarkan rating:" in message
    assert len(products) == 3
    # Electronics products: p1 (4.5), p3 (4.9), p4 (4.0). Sorted by rating: p3, p1, p4.
    assert [p['id'] for p in products] == ['p3', 'p1', 'p4']

def test_smart_search_products_best_category_not_found_fallback(local_product_service_instance_success):
    """Test `smart_search_products` for 'terbaik' with a non-existing category, falling back to general best."""
    service = local_product_service_instance_success
    products, message = service.smart_search_products(keyword="sepatu terbaik", category="Footwear")
    assert "Tidak ada produk kategori Footwear, berikut produk terbaik secara umum:" in message
    assert len(products) == 5 # Should fallback to general best products
    assert [p['id'] for p in products] == ['p3', 'p5', 'p1', 'p4', 'p2']

def test_smart_search_products_all_criteria_match(local_product_service_instance_success):
    """Test `smart_search_products` where all provided criteria (keyword, category, price) match."""
    service = local_product_service_instance_success
    # Keyword "Test Product": p1, p2
    # Category "Electronics": p1, p3, p4
    # Max price 1,500,000: p1, p2, p4
    # Intersection of all: only p1
    products, message = service.smart_search_products(keyword="Test Product", category="Electronics", max_price=1500000)
    assert "Berikut produk yang sesuai dengan kriteria Anda." in message
    assert len(products) == 1
    assert products[0]['id'] == 'p1'

def test_smart_search_products_fallback_to_category_only(local_product_service_instance_success):
    """Test `smart_search_products` fallback: no full match, but matches category (price/keyword filter removed)."""
    service = local_product_service_instance_success
    # Keyword "NonExistent" (no match), Category "Electronics" (matches p1, p3, p4), Max price 500,000 (only p2).
    # No product matches all three. It should fall back to just category.
    products, message = service.smart_search_products(keyword="NonExistent", category="Electronics", max_price=500000)
    assert "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut." in message
    assert len(products) == 3
    # Electronics products sorted by price: p1 (1M), p4 (2M), p3 (2.5M)
    assert [p['id'] for p in products] == ['p1', 'p4', 'p3']

def test_smart_search_products_fallback_to_budget_only(local_product_service_instance_success):
    """Test `smart_search_products` fallback: no full match, no category match, but matches budget."""
    service = local_product_service_instance_success
    # Keyword "NonExistent", Category "NonExistentCategory", Max price 1,000,000.
    # No full match. No category match. But products under 1M: p1, p2.
    products, message = service.smart_search_products(keyword="NonExistent", category="NonExistentCategory", max_price=1000000)
    assert "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda." in message
    assert len(products) == 2
    # Products <= 1M: p1, p2. Order is based on original list due to stable sort.
    assert {p['id'] for p in products} == {'p1', 'p2'}

def test_smart_search_products_fallback_to_popular(local_product_service_instance_success):
    """Test `smart_search_products` fallback: no criteria match, falls back to popular products."""
    service = local_product_service_instance_success
    # Keyword "NoMatch", Category "NoCategory", Max price 1.
    # Nothing will match any criteria.
    products, message = service.smart_search_products(keyword="NoMatch", category="NoCategory", max_price=1)
    assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message
    assert len(products) == 5 # All products, sorted by sold count (which is 500 for all in mock)
    # Since sold count is mocked to be same for all, order is stable sort
    assert [p['id'] for p in products] == ['p1', 'p2', 'p3', 'p4', 'p5']

def test_smart_search_products_empty_results_no_fallbacks_possible(local_product_service_empty_products_file):
    """Test `smart_search_products` when no products are loaded at all."""
    service = local_product_service_empty_products_file
    products, message = service.smart_search_products(keyword="any", category="any", max_price=1000000)
    # The final fallback path will still be hit, but it will return an empty list of products.
    assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message
    assert len(products) == 0

def test_smart_search_products_limit_applied_in_all_scenarios(local_product_service_instance_success):
    """Test `smart_search_products` applies the limit correctly across different fallback scenarios."""
    service = local_product_service_instance_success
    
    # Scenario 1: Best general (limit 2)
    products, _ = service.smart_search_products(keyword="terbaik", limit=2)
    assert len(products) == 2
    assert [p['id'] for p in products] == ['p3', 'p5']

    # Scenario 2: Best category (limit 1)
    products, _ = service.smart_search_products(keyword="terbaik", category="Electronics", limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'p3'

    # Scenario 3: All criteria match (limit 1)
    products, _ = service.smart_search_products(keyword="Product", category="Electronics", limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'p1'

    # Scenario 4: Fallback to category only (limit 2)
    products, _ = service.smart_search_products(keyword="NonExistent", category="Electronics", max_price=500000, limit=2)
    assert len(products) == 2
    assert [p['id'] for p in products] == ['p1', 'p4']

    # Scenario 5: Fallback to budget only (limit 1)
    products, _ = service.smart_search_products(keyword="NonExistent", category="NonExistentCategory", max_price=1000000, limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'p1'

    # Scenario 6: Fallback to popular (limit 3)
    products, _ = service.smart_search_products(keyword="NoMatch", category="NoCategory", max_price=1, limit=3)
    assert len(products) == 3
    assert [p['id'] for p in products] == ['p1', 'p2', 'p3'] # Stable sort for same 'sold' count