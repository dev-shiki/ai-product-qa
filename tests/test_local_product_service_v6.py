import pytest
from unittest.mock import patch, mock_open, MagicMock
import json
import logging
from pathlib import Path
import random
import re
import sys

# Add the 'app' directory to sys.path to allow imports like 'from services...'
# This assumes the test file is located at project_root/test_services/test_local_product_service.py
# and the source file is at project_root/app/services/local_product_service.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from services.local_product_service import LocalProductService

# Configure logging for tests to capture log messages
@pytest.fixture(autouse=True)
def setup_logging():
    logging.getLogger('app.services.local_product_service').setLevel(logging.INFO)
    # Ensure logs are captured by caplog fixture
    logging.getLogger('app.services.local_product_service').propagate = True


@pytest.fixture
def mock_path_and_open(mocker):
    """
    Mocks Path.exists and builtins.open to control file loading behavior.
    The mock ensures that the internal Path calculations in LocalProductService
    lead to a controlled mock file object.

    Returns: (mock_json_file_path_obj, mock_open_func)
    """
    mock_json_file_path_obj = MagicMock(spec=Path)
    # Default to file existing, tests can override this.
    mock_json_file_path_obj.exists.return_value = True

    # Mock the Path object that represents the result of
    # `current_dir / "data" / "products.json"`.
    # This mock represents the file itself.
    mock_current_dir = MagicMock(spec=Path)
    mock_data_dir = MagicMock(spec=Path)
    # When `current_dir / "data"` is called, return mock_data_dir.
    mock_current_dir.__truediv__.side_effect = lambda x: mock_data_dir if x == "data" else MagicMock(spec=Path)
    # When `mock_data_dir / "products.json"` is called, return mock_json_file_path_obj.
    mock_data_dir.__truediv__.side_effect = lambda x: mock_json_file_path_obj if x == "products.json" else MagicMock(spec=Path)

    # Mock the base Path(__file__) object's parent chain to lead to mock_current_dir.
    mock_file_path_part = MagicMock(spec=Path)
    mock_file_path_part.parent.parent.parent.return_value = mock_current_dir

    # Patch the Path class itself so `Path(__file__)` returns our mock.
    mocker.patch("app.services.local_product_service.Path", return_value=mock_file_path_part)

    # Mock builtins.open.
    mock_opener = mock_open()
    mocker.patch("builtins.open", mock_opener)

    return mock_json_file_path_obj, mock_opener

@pytest.fixture
def mock_random_randint(mocker):
    """Mocks random.randint to return a predictable value (500) for 'sold' counts."""
    mocker.patch("app.services.local_product_service.random.randint", return_value=500)

@pytest.fixture
def fallback_products_data():
    """Returns the expected hardcoded fallback products as a list of dicts."""
    return [
        {"id": "1", "name": "iPhone 15 Pro Max", "category": "Smartphone", "brand": "Apple", "price": 25000000, "currency": "IDR", "description": "iPhone 15 Pro Max dengan chip A17 Pro, kamera 48MP, dan layar 6.7 inch Super Retina XDR. Dilengkapi dengan titanium design dan performa gaming yang luar biasa.", "specifications": {"rating": 4.8, "sold": 1250, "stock": 50, "condition": "Baru", "shop_location": "Jakarta", "shop_name": "Apple Store Indonesia", "storage": "256GB", "color": "Titanium Natural", "warranty": "1 Tahun", "processor": "A17 Pro", "camera": "48MP Main + 12MP Ultra Wide + 12MP Telephoto", "display": "6.7 inch Super Retina XDR"}, "images": ["https://example.com/iphone15.jpg"], "url": "https://shopee.co.id/iphone-15-pro-max"},
        {"id": "2", "name": "Samsung Galaxy S24 Ultra", "category": "Smartphone", "brand": "Samsung", "price": 22000000, "currency": "IDR", "description": "Samsung Galaxy S24 Ultra dengan S Pen, kamera 200MP, dan AI features canggih. Dilengkapi dengan Snapdragon 8 Gen 3 dan layar AMOLED 6.8 inch.", "specifications": {"rating": 4.7, "sold": 980, "stock": 35, "condition": "Baru", "shop_location": "Surabaya", "shop_name": "Samsung Store", "storage": "512GB", "color": "Titanium Gray", "warranty": "1 Tahun", "processor": "Snapdragon 8 Gen 3", "camera": "200MP Main + 12MP Ultra Wide + 50MP Telephoto + 10MP Telephoto", "display": "6.8 inch Dynamic AMOLED 2X"}, "images": ["https://example.com/s24-ultra.jpg"], "url": "https://shopee.co.id/samsung-s24-ultra"},
        {"id": "3", "name": "MacBook Pro 14 inch M3", "category": "Laptop", "brand": "Apple", "price": 35000000, "currency": "IDR", "description": "MacBook Pro dengan chip M3, layar 14 inch Liquid Retina XDR, dan performa tinggi untuk profesional. Cocok untuk video editing, programming, dan gaming.", "specifications": {"rating": 4.9, "sold": 450, "stock": 25, "condition": "Baru", "shop_location": "Jakarta", "shop_name": "Apple Store Indonesia", "storage": "1TB", "color": "Space Gray", "warranty": "1 Tahun", "processor": "Apple M3", "ram": "16GB Unified Memory", "display": "14 inch Liquid Retina XDR"}, "images": ["https://example.com/macbook-pro.jpg"], "url": "https://shopee.co.id/macbook-pro-m3"},
        {"id": "4", "name": "AirPods Pro 2nd Gen", "category": "Audio", "brand": "Apple", "price": 4500000, "currency": "IDR", "description": "AirPods Pro dengan Active Noise Cancellation dan Spatial Audio. Dilengkapi dengan chip H2 untuk performa audio yang lebih baik dan fitur Find My.", "specifications": {"rating": 4.6, "sold": 2100, "stock": 100, "condition": "Baru", "shop_location": "Bandung", "shop_name": "Apple Store Indonesia", "color": "White", "warranty": "1 Tahun", "battery": "6 jam dengan ANC, 30 jam dengan case", "features": "Active Noise Cancellation, Spatial Audio, Find My"}, "images": ["https://example.com/airpods-pro.jpg"], "url": "https://shopee.co.id/airpods-pro-2"},
        {"id": "5", "name": "iPad Air 5th Gen", "category": "Tablet", "brand": "Apple", "price": 12000000, "currency": "IDR", "description": "iPad Air dengan chip M1, layar 10.9 inch Liquid Retina, dan Apple Pencil support. Cocok untuk kreativitas, note-taking, dan entertainment.", "specifications": {"rating": 4.5, "sold": 750, "stock": 40, "condition": "Baru", "shop_location": "Medan", "shop_name": "Apple Store Indonesia", "storage": "256GB", "color": "Blue", "warranty": "1 Tahun", "processor": "Apple M1", "display": "10.9 inch Liquid Retina", "features": "Apple Pencil support, Magic Keyboard support"}, "images": ["https://example.com/ipad-air.jpg"], "url": "https://shopee.co.id/ipad-air-5"},
        {"id": "6", "name": "ASUS ROG Strix G15", "category": "Laptop", "brand": "ASUS", "price": 18000000, "currency": "IDR", "description": "Laptop gaming ASUS ROG Strix G15 dengan RTX 4060, AMD Ryzen 7, dan layar 15.6 inch 144Hz. Dilengkapi dengan RGB keyboard dan cooling system yang powerful.", "specifications": {"rating": 4.4, "sold": 320, "stock": 15, "condition": "Baru", "shop_location": "Jakarta", "shop_name": "ASUS Store", "storage": "512GB SSD", "color": "Black", "warranty": "2 Tahun", "processor": "AMD Ryzen 7 7735HS", "gpu": "NVIDIA RTX 4060 8GB", "ram": "16GB DDR5", "display": "15.6 inch FHD 144Hz"}, "images": ["https://example.com/rog-strix.jpg"], "url": "https://shopee.co.id/asus-rog-strix-g15"},
        {"id": "7", "name": "Sony WH-1000XM5", "category": "Audio", "brand": "Sony", "price": 5500000, "currency": "IDR", "description": "Headphone wireless Sony WH-1000XM5 dengan noise cancellation terbaik di kelasnya. Dilengkapi dengan 30 jam battery life dan quick charge.", "specifications": {"rating": 4.8, "sold": 890, "stock": 30, "condition": "Baru", "shop_location": "Surabaya", "shop_name": "Sony Store", "color": "Black", "warranty": "1 Tahun", "battery": "30 jam dengan ANC", "features": "Industry-leading noise cancellation, Quick Charge, Multipoint connection"}, "images": ["https://example.com/sony-wh1000xm5.jpg"], "url": "https://shopee.co.id/sony-wh1000xm5"},
        {"id": "8", "name": "Samsung Galaxy Tab S9", "category": "Tablet", "brand": "Samsung", "price": 15000000, "currency": "IDR", "description": "Samsung Galaxy Tab S9 dengan S Pen, layar AMOLED 11 inch, dan Snapdragon 8 Gen 2. Cocok untuk productivity dan entertainment.", "specifications": {"rating": 4.3, "sold": 280, "stock": 20, "condition": "Baru", "shop_location": "Bandung", "shop_name": "Samsung Store", "storage": "256GB", "color": "Graphite", "warranty": "1 Tahun", "processor": "Snapdragon 8 Gen 2", "display": "11 inch Dynamic AMOLED 2X", "features": "S Pen included, DeX mode, Multi-window"}, "images": ["https://example.com/galaxy-tab-s9.jpg"], "url": "https://shopee.co.id/samsung-galaxy-tab-s9"}
    ]

@pytest.fixture
def mock_products_json_data():
    """A sample raw JSON data structure mimicking products.json content for successful loading."""
    return {
        "products": [
            {
                "id": "mock_id_1",
                "name": "Mock Product A",
                "category": "Electronics",
                "brand": "MockBrand",
                "price": 100000,
                "currency": "IDR",
                "description": "This is a mock product A.",
                "rating": 4.0,
                "stock_count": 100,
                "specifications": {"weight": "1kg", "color": "Black"},
                "availability": "in_stock",
                "reviews_count": 50
            },
            {
                "id": "mock_id_2",
                "name": "Mock Product B",
                "category": "Clothing",
                "brand": "AnotherBrand",
                "price": 50000,
                "description": "Another mock product.",
                "rating": 3.5,
                "stock_count": 200,
            },
            {
                "id": "mock_id_3",
                "name": "Product with only ID", # Missing category, brand, etc. to test defaults
            },
            {
                "id": "mock_id_4",
                "name": "Product for Search",
                "category": "Smartphone",
                "brand": "Xiaomi",
                "price": 3000000,
                "description": "Smartphone with good camera.",
                "rating": 4.2,
                "stock_count": 50,
                "specifications": {"ram": "8GB", "storage": "128GB"}
            },
            {
                "id": "mock_id_5",
                "name": "Gaming Laptop Pro",
                "category": "Laptop",
                "brand": "ASUS",
                "price": 15000000,
                "description": "Powerful gaming laptop.",
                "rating": 4.7,
                "stock_count": 10,
                "specifications": {"gpu": "RTX 3060", "display": "15.6 inch"}
            },
            {
                "id": "mock_id_6",
                "name": "Mid-Range Smartphone",
                "category": "Smartphone",
                "brand": "Oppo",
                "price": 2500000,
                "description": "Affordable smartphone.",
                "rating": 3.9,
                "stock_count": 70,
            },
            {
                "id": "mock_id_7",
                "name": "Expensive Gadget",
                "category": "Electronics",
                "brand": "Premium",
                "price": 12000000,
                "description": "High-end electronics.",
                "rating": 4.9,
                "stock_count": 5,
            },
            {
                "id": "mock_id_8",
                "name": "Cheap Accessory",
                "category": "Accessories",
                "brand": "Budget",
                "price": 500000,
                "description": "Affordable accessory.",
                "rating": 3.0,
                "stock_count": 200,
            }
        ]
    }

@pytest.fixture
def expected_transformed_products(mock_products_json_data, mock_random_randint):
    """
    Returns the expected transformed product list based on mock_products_json_data
    and mock_random_randint (which returns 500).
    """
    products = mock_products_json_data["products"]
    transformed = []
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
                "sold": 500,  # From mock_random_randint
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
        transformed.append(transformed_product)
    return transformed


@pytest.fixture
def service_with_mocked_products(mock_path_and_open, mock_products_json_data, mock_random_randint):
    """
    Fixture to create a LocalProductService instance with controlled local products
    loaded successfully from mock_products_json_data.
    """
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    mock_json_file_path_obj.exists.return_value = True # Ensure file is found
    mock_opener.return_value.__enter__.return_value.read.return_value = json.dumps(mock_products_json_data)
    
    service = LocalProductService()
    return service

@pytest.fixture
def service_with_fallback_products(mock_path_and_open, fallback_products_data, caplog):
    """
    Fixture to create a LocalProductService instance that falls back to default products.
    This simulates file not found, or decode/json errors during initialization.
    """
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    mock_json_file_path_obj.exists.return_value = False # Simulate file not found by default for fallback tests
    
    with caplog.at_level(logging.WARNING):
        service = LocalProductService()
    
    assert "Using fallback products due to JSON file loading error" in caplog.text
    assert service.products == fallback_products_data
    return service

# --- Tests for __init__ ---
def test_init_loads_products_successfully(service_with_mocked_products, expected_transformed_products, caplog):
    """Test that __init__ correctly loads products and logs info."""
    # service_with_mocked_products fixture already initializes the service
    # and has its products attribute set to expected_transformed_products.
    service = service_with_mocked_products
    assert service.products == expected_transformed_products
    assert f"Loaded {len(expected_transformed_products)} local products from JSON file" in caplog.text

def test_init_falls_back_on_load_failure(service_with_fallback_products, fallback_products_data, caplog):
    """Test that __init__ correctly falls back to default products on load failure."""
    # service_with_fallback_products fixture already initializes the service
    # and asserts its products attribute against fallback_products_data.
    service = service_with_fallback_products
    assert service.products == fallback_products_data
    # The fallback message is asserted within the fixture
    assert "Loaded 8 local products from JSON file" in caplog.text # Fallback products count

# --- Tests for _load_local_products ---
def test_load_local_products_success_default_encoding(mock_path_and_open, mock_products_json_data, expected_transformed_products, caplog):
    """Test _load_local_products with default encoding (utf-16-le) success."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    mock_opener.return_value.__enter__.return_value.read.return_value = json.dumps(mock_products_json_data)
    
    service = LocalProductService() # This calls _load_local_products
    
    # Check that the first encoding attempt was utf-16-le
    mock_opener.assert_called_with(mock_json_file_path_obj, 'r', encoding='utf-16-le')
    assert service.products == expected_transformed_products
    assert f"Successfully loaded {len(expected_transformed_products)} products from JSON file using utf-16-le encoding" in caplog.text

def test_load_local_products_success_with_bom(mock_path_and_open, mock_products_json_data, expected_transformed_products, caplog):
    """Test _load_local_products handles UTF-8 BOM correctly with utf-8-sig."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    # Simulate first two encodings failing, then utf-8-sig succeeding with BOM
    mock_opener.side_effect = [
        MagicMock(side_effect=UnicodeDecodeError("codec", b"", 0, 1, "test")), # utf-16-le fails
        MagicMock(side_effect=UnicodeDecodeError("codec", b"", 0, 1, "test")), # utf-16 fails
        MagicMock(side_effect=UnicodeDecodeError("codec", b"", 0, 1, "test")), # utf-8 fails
        mock_open(read_data='\ufeff' + json.dumps(mock_products_json_data)).return_value # utf-8-sig succeeds
    ]

    service = LocalProductService()
    assert service.products == expected_transformed_products
    assert "Failed to load with utf-16-le encoding" in caplog.text
    assert "Failed to load with utf-16 encoding" in caplog.text
    assert "Failed to load with utf-8 encoding" in caplog.text
    assert "Successfully loaded" in caplog.text
    assert "utf-8-sig encoding" in caplog.text

def test_load_local_products_success_different_encoding(mock_path_and_open, mock_products_json_data, expected_transformed_products, caplog):
    """Test _load_local_products trying multiple encodings until one works (e.g., utf-8)."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    # Simulate first two encodings failing, third succeeding
    mock_opener.side_effect = [
        MagicMock(side_effect=UnicodeDecodeError("codec", b"", 0, 1, "test")), # utf-16-le fails
        MagicMock(side_effect=UnicodeDecodeError("codec", b"", 0, 1, "test")), # utf-16 fails
        mock_open(read_data=json.dumps(mock_products_json_data)).return_value # utf-8 succeeds
    ]

    service = LocalProductService()
    assert service.products == expected_transformed_products
    assert "Failed to load with utf-16-le encoding" in caplog.text
    assert "Failed to load with utf-16 encoding" in caplog.text
    assert "Successfully loaded" in caplog.text
    assert "utf-8 encoding" in caplog.text

def test_load_local_products_file_not_found(mock_path_and_open, fallback_products_data, caplog):
    """Test _load_local_products falls back when file is not found."""
    mock_json_file_path_obj, _ = mock_path_and_open
    mock_json_file_path_obj.exists.return_value = False # File does not exist
    
    service = LocalProductService()
    assert service.products == fallback_products_data
    assert f"Products JSON file not found at: {mock_json_file_path_obj}" in caplog.text
    assert "Using fallback products due to JSON file loading error" in caplog.text

def test_load_local_products_all_encodings_fail_unicode_error(mock_path_and_open, fallback_products_data, caplog):
    """Test _load_local_products falls back when all encodings fail with UnicodeDecodeError."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    mock_opener.side_effect = [
        MagicMock(side_effect=UnicodeDecodeError("codec", b"", 0, 1, "test")) for _ in range(6) # All 6 encodings fail
    ]

    service = LocalProductService()
    assert service.products == fallback_products_data
    assert "All encoding attempts failed, using fallback products" in caplog.text
    assert "Using fallback products due to JSON file loading error" in caplog.text
    assert caplog.text.count("Failed to load with") == 6 # Check for warnings for each encoding failure

def test_load_local_products_all_encodings_fail_json_error(mock_path_and_open, fallback_products_data, caplog):
    """Test _load_local_products falls back when all encodings fail with json.JSONDecodeError."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    # Simulate opening succeeds but content is malformed JSON, leading to JSONDecodeError
    mock_opener.side_effect = [
        mock_open(read_data="malformed json").return_value for _ in range(6)
    ]

    service = LocalProductService()
    assert service.products == fallback_products_data
    assert "All encoding attempts failed, using fallback products" in caplog.text
    assert "Using fallback products due to JSON file loading error" in caplog.text
    assert caplog.text.count("Failed to load with") == 6 # Check for warnings for each encoding failure

def test_load_local_products_generic_exception(mock_path_and_open, fallback_products_data, caplog):
    """Test _load_local_products falls back on a generic exception during file operations."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    mock_opener.side_effect = Exception("Permission denied")

    service = LocalProductService()
    assert service.products == fallback_products_data
    assert "Error loading products from JSON file: Permission denied" in caplog.text
    assert "Using fallback products due to JSON file loading error" in caplog.text

def test_load_local_products_empty_products_list_in_json(mock_path_and_open, mock_random_randint, caplog):
    """Test _load_local_products handles JSON with an empty 'products' list."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    mock_opener.return_value.__enter__.return_value.read.return_value = json.dumps({"products": []})

    service = LocalProductService()
    assert service.products == []
    assert "Successfully loaded 0 products from JSON file" in caplog.text

def test_load_local_products_missing_products_key_in_json(mock_path_and_open, mock_random_randint, caplog):
    """Test _load_local_products handles JSON missing the 'products' key."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    mock_opener.return_value.__enter__.return_value.read.return_value = json.dumps({"other_key": "value"})

    service = LocalProductService()
    assert service.products == []
    assert "Successfully loaded 0 products from JSON file" in caplog.text

def test_load_local_products_product_transformation_defaults(mock_path_and_open, mock_random_randint):
    """Test product transformation applies default values correctly when fields are missing."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    json_content = json.dumps({
        "products": [
            {"id": "test_id", "name": "Test Product"} # Only ID and Name provided, rest should use defaults
        ]
    })
    mock_opener.return_value.__enter__.return_value.read.return_value = json_content

    service = LocalProductService()
    product = service.products[0]
    assert product['id'] == "test_id"
    assert product['name'] == "Test Product"
    assert product['category'] == ""
    assert product['brand'] == ""
    assert product['price'] == 0
    assert product['currency'] == "IDR"
    assert product['description'] == ""
    assert product['specifications']['rating'] == 0
    assert product['specifications']['sold'] == 500 # From mock_random_randint fixture
    assert product['specifications']['stock'] == 0
    assert product['specifications']['condition'] == "Baru"
    assert product['specifications']['shop_location'] == "Indonesia"
    assert product['specifications']['shop_name'] == "Unknown Store" # Default brand when 'brand' is missing
    assert "extra_spec" not in product['specifications'] # Ensure no unexpected specs
    assert product['availability'] == "in_stock"
    assert product['reviews_count'] == 0
    assert product['images'] == ["https://example.com/test_id.jpg"]
    assert product['url'] == "https://shopee.co.id/test_id"

def test_load_local_products_product_transformation_specs_merge(mock_path_and_open, mock_random_randint):
    """Test product transformation merges 'specifications' correctly, prioritizing explicit specs."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    json_content = json.dumps({
        "products": [
            {
                "id": "test_spec_id",
                "name": "Product With Specs",
                "brand": "AwesomeBrand",
                "rating": 4.5, # This rating will be used instead of default 0
                "stock_count": 20, # This stock will be used instead of default 0
                "specifications": {"material": "plastic", "color": "red", "rating": 5.0} # `rating` here should be overridden by top-level `rating`
            }
        ]
    })
    mock_opener.return_value.__enter__.return_value.read.return_value = json_content

    service = LocalProductService()
    product = service.products[0]
    assert product['id'] == "test_spec_id"
    assert product['specifications']['rating'] == 4.5 # Top-level 'rating' takes precedence
    assert product['specifications']['sold'] == 500
    assert product['specifications']['stock'] == 20
    assert product['specifications']['condition'] == "Baru"
    assert product['specifications']['shop_location'] == "Indonesia"
    assert product['specifications']['shop_name'] == "AwesomeBrand Store"
    assert product['specifications']['material'] == "plastic"
    assert product['specifications']['color'] == "red"


# --- Tests for _get_fallback_products ---
def test_get_fallback_products_returns_correct_data(service_with_fallback_products, fallback_products_data, caplog):
    """Test _get_fallback_products returns the correct hardcoded list and logs a warning."""
    service = service_with_fallback_products
    # The fixture already asserts the products are the fallback ones.
    # Calling it again directly to ensure the method itself logs.
    caplog.clear() # Clear previous logs from fixture setup
    result = service._get_fallback_products()
    assert result == fallback_products_data
    assert "Using fallback products due to JSON file loading error" in caplog.text


# --- Tests for search_products ---
def test_search_products_by_name(service_with_mocked_products):
    """Test searching products by name (case-insensitive)."""
    service = service_with_mocked_products
    results = service.search_products(keyword="mock product A")
    assert len(results) == 1
    assert results[0]['id'] == 'mock_id_1'

def test_search_products_by_category(service_with_mocked_products):
    """Test searching products by category (case-insensitive)."""
    service = service_with_mocked_products
    results = service.search_products(keyword="smartphone")
    assert any(p['id'] == 'mock_id_4' for p in results) # Xiaomi
    assert any(p['id'] == 'mock_id_6' for p in results) # Oppo
    assert len(results) == 2 # Only these two should directly match 'smartphone' in category

def test_search_products_by_brand(service_with_mocked_products):
    """Test searching products by brand (case-insensitive)."""
    service = service_with_mocked_products
    results = service.search_products(keyword="xiaomi")
    assert len(results) == 1
    assert results[0]['id'] == 'mock_id_4'

def test_search_products_by_description(service_with_mocked_products):
    """Test searching products by description."""
    service = service_with_mocked_products
    results = service.search_products(keyword="powerful gaming")
    assert len(results) == 1
    assert results[0]['id'] == 'mock_id_5'

def test_search_products_by_specifications(service_with_mocked_products):
    """Test searching products by specifications."""
    service = service_with_mocked_products
    results = service.search_products(keyword="8GB") # From mock_id_4 ram: "8GB"
    assert len(results) == 1
    assert results[0]['id'] == 'mock_id_4'

def test_search_products_limit(service_with_mocked_products):
    """Test search products limit functionality."""
    service = service_with_mocked_products
    # Search for a broad term that matches multiple products and limit it
    results = service.search_products(keyword="product", limit=2)
    assert len(results) == 2
    # Due to relevance scoring (name match is high) and default sort behavior of fixtures,
    # 'Mock Product A' and 'Mock Product B' should be first.
    assert results[0]['id'] == 'mock_id_1'
    assert results[1]['id'] == 'mock_id_2'

def test_search_products_no_match(service_with_mocked_products):
    """Test searching with a keyword that yields no matches."""
    service = service_with_mocked_products
    results = service.search_products(keyword="nonexistent product")
    assert len(results) == 0

def test_search_products_empty_keyword(service_with_mocked_products):
    """Test searching with an empty keyword returns all products up to limit."""
    service = service_with_mocked_products
    results = service.search_products(keyword="", limit=3)
    assert len(results) == 3
    # When keyword is empty, all products are considered a match and sorted by relevance_score.
    # Since prices are different and other factors, it should still sort.
    # With a mock_random_randint, the original order of products in the fixture generally dictates order for equal scores.
    assert results[0]['id'] == 'mock_id_7' # Highest rating
    assert results[1]['id'] == 'mock_id_5'
    assert results[2]['id'] == 'mock_id_4'

def test_search_products_price_range_exact_match(service_with_mocked_products):
    """Test searching products by exact price range keyword (e.g., "laptop 15 juta")."""
    service = service_with_mocked_products
    results = service.search_products(keyword="laptop 15 juta")
    assert len(results) == 1
    assert results[0]['id'] == 'mock_id_5' # Gaming Laptop Pro (15M)

def test_search_products_price_range_upper_bound(service_with_mocked_products):
    """Test searching products by price upper bound (e.g., "smartphone 4 juta")."""
    service = service_with_mocked_products
    # mock_id_4 (3M), mock_id_6 (2.5M) are smartphones <= 4M
    results = service.search_products(keyword="smartphone 4 juta") 
    assert len(results) == 2
    # Verify both relevant IDs are present. Order might vary based on other scoring.
    assert {p['id'] for p in results} == {'mock_id_4', 'mock_id_6'}
    # With budget search, lower price gets higher score. So 'mock_id_6' (2.5M) should be first.
    assert results[0]['id'] == 'mock_id_6'
    assert results[1]['id'] == 'mock_id_4'

def test_search_products_price_range_budget_keyword(service_with_mocked_products):
    """Test searching products with a budget keyword like 'murah'."""
    service = service_with_mocked_products
    # 'murah' -> 5,000,000
    # Products with prices 100k, 50k, 3M, 15M, 2.5M, 12M, 500k
    # For 'murah' (<= 5M): mock_id_1 (100k), mock_id_2 (50k), mock_id_4 (3M), mock_id_6 (2.5M), mock_id_8 (500k)
    results = service.search_products(keyword="smartphone murah")
    assert len(results) == 2 # Only smartphone products within budget
    assert {p['id'] for p in results} == {'mock_id_4', 'mock_id_6'}
    # Order for budget search: lower price first (mock_id_6: 2.5M vs mock_id_4: 3M)
    assert results[0]['id'] == 'mock_id_6'
    assert results[1]['id'] == 'mock_id_4'

def test_search_products_relevance_scoring_exact_match(service_with_mocked_products):
    """Test relevance scoring prioritizes name/brand exact matches."""
    service = service_with_mocked_products
    # Searching for "Mock" should prioritize "Mock Product A" (name match) over "Mock Product B" (name match, but B is alphabetically after A, and scores are same without specific budget/rating)
    # The default order from fixture is A then B, so A is expected first.
    results = service.search_products(keyword="mock") 
    assert len(results) == 2
    assert results[0]['id'] == 'mock_id_1' 
    assert results[1]['id'] == 'mock_id_2'

def test_search_products_relevance_scoring_combined(service_with_mocked_products):
    """Test relevance scoring with mixed keyword and price considerations."""
    service = service_with_mocked_products
    # 'product' keyword would match many.
    # Products: mock_id_1 (100k), mock_id_2 (50k), mock_id_3 (0), mock_id_4 (3M), mock_id_5 (15M), mock_id_6 (2.5M), mock_id_7 (12M), mock_id_8 (500k)
    # Keyword: "product" (all have "product" in name or description implicitly or explicitly)
    # Budget word: "murah" (max_price 5M)
    results = service.search_products(keyword="product murah", limit=5)
    # Expected matches within 5M: mock_id_1, mock_id_2, mock_id_4, mock_id_6, mock_id_8
    # Sorted by relevance: budget scoring (lower price higher score) + keyword scoring.
    # All get a score for 'product'.
    # mock_id_2 (50k) - high budget score
    # mock_id_1 (100k) - high budget score
    # mock_id_8 (500k) - high budget score
    # mock_id_6 (2.5M) - medium budget score
    # mock_id_4 (3M) - medium budget score
    
    # Check that they are the expected 5 products
    expected_ids = {'mock_id_1', 'mock_id_2', 'mock_id_4', 'mock_id_6', 'mock_id_8'}
    actual_ids = {p['id'] for p in results}
    assert actual_ids == expected_ids
    
    # Check sort order based on price (descending score for price)
    # Lower price gets higher score, so 50k > 100k > 500k > 2.5M > 3M
    assert results[0]['id'] == 'mock_id_2' # 50k
    assert results[1]['id'] == 'mock_id_1' # 100k
    assert results[2]['id'] == 'mock_id_8' # 500k
    assert results[3]['id'] == 'mock_id_6' # 2.5M
    assert results[4]['id'] == 'mock_id_4' # 3M

def test_search_products_error_handling(service_with_mocked_products, mocker, caplog):
    """Test search_products error handling."""
    # Simulate an error accessing self.products within search_products
    mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Data access error"))
    results = service_with_mocked_products.search_products("test")
    assert results == []
    assert "Error searching products: Data access error" in caplog.text

# --- Tests for _extract_price_from_keyword ---
@pytest.mark.parametrize("keyword, expected_price", [
    ("handphone 2 juta", 2000000),
    ("laptop rp 15000000", 15000000),
    ("tablet 500 ribu", 500000),
    ("pc 10m", 10000000),
    ("tv 4k", 4000), # Test 'k' suffix for thousands
    ("baju murah", 5000000), # From budget_keywords
    ("tv budget", 5000000),
    ("speaker hemat", 3000000),
    ("aksesoris terjangkau", 4000000),
    ("charger ekonomis", 2000000),
    ("product x", None), # No price keyword
    ("12345", None), # Just numbers, no unit
    ("rp", None), # Just 'rp'
    ("10 juta rupiah", 10000000), # Contains "juta"
    ("Rp. 1.000.000", None), # Current regex doesn't handle dots or commas
    ("harga 5 juta", 5000000),
    ("under 1jt", 1000000), # Test 'jt' for juta
])
def test_extract_price_from_keyword_success(service_with_mocked_products, keyword, expected_price):
    """Test _extract_price_from_keyword for various price patterns and budget keywords."""
    service = service_with_mocked_products
    assert service._extract_price_from_keyword(keyword) == expected_price

def test_extract_price_from_keyword_no_match(service_with_mocked_products):
    """Test _extract_price_from_keyword when no price or budget keyword is found."""
    service = service_with_mocked_products
    assert service._extract_price_from_keyword("no price here") is None

def test_extract_price_from_keyword_error_handling(service_with_mocked_products, mocker, caplog):
    """Test _extract_price_from_keyword error handling."""
    # Simulate an error within re.search call
    mocker.patch("re.search", side_effect=Exception("Regex processing error"))
    service = service_with_mocked_products
    result = service._extract_price_from_keyword("test 1 juta")
    assert result is None
    assert "Error extracting price from keyword: Regex processing error" in caplog.text


# --- Tests for get_product_details ---
def test_get_product_details_found(service_with_mocked_products):
    """Test get_product_details returns correct product when ID is found."""
    service = service_with_mocked_products
    product = service.get_product_details("mock_id_1")
    assert product is not None
    assert product['id'] == 'mock_id_1'
    assert product['name'] == 'Mock Product A'

def test_get_product_details_not_found(service_with_mocked_products):
    """Test get_product_details returns None when ID is not found."""
    service = service_with_mocked_products
    product = service.get_product_details("nonexistent_id")
    assert product is None

def test_get_product_details_empty_products(service_with_mocked_products, mocker):
    """Test get_product_details with an empty product list."""
    mocker.patch.object(service_with_mocked_products, 'products', [])
    product = service_with_mocked_products.get_product_details("mock_id_1")
    assert product is None

def test_get_product_details_error_handling(service_with_mocked_products, mocker, caplog):
    """Test get_product_details error handling."""
    # Simulate an error accessing self.products within get_product_details
    mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Access error"))
    result = service_with_mocked_products.get_product_details("any_id")
    assert result is None
    assert "Error getting product details: Access error" in caplog.text

# --- Tests for get_categories ---
def test_get_categories(service_with_mocked_products):
    """Test get_categories returns unique sorted categories."""
    service = service_with_mocked_products
    categories = service.get_categories()
    # Includes empty string from mock_id_3 (product with only ID)
    expected_categories = ['Accessories', 'Clothing', 'Electronics', 'Laptop', 'Smartphone', '']
    assert sorted(categories) == sorted(expected_categories) # Sorted for comparison

def test_get_categories_empty_products(service_with_mocked_products, mocker):
    """Test get_categories returns empty list when no products."""
    mocker.patch.object(service_with_mocked_products, 'products', [])
    categories = service_with_mocked_products.get_categories()
    assert categories == []

def test_get_categories_product_missing_category_key(service_with_mocked_products):
    """Test get_categories handles products missing 'category' key by using empty string."""
    # mock_products_json_data already includes mock_id_3 which misses 'category'
    service = service_with_mocked_products
    categories = service.get_categories()
    assert '' in categories # Should include empty string for missing category


# --- Tests for get_brands ---
def test_get_brands(service_with_mocked_products):
    """Test get_brands returns unique sorted brands."""
    service = service_with_mocked_products
    brands = service.get_brands()
    # Includes empty string from mock_id_3
    expected_brands = ['AnotherBrand', 'ASUS', 'Budget', 'MockBrand', 'Oppo', 'Premium', 'Xiaomi', '']
    assert sorted(brands) == sorted(expected_brands)

def test_get_brands_empty_products(service_with_mocked_products, mocker):
    """Test get_brands returns empty list when no products."""
    mocker.patch.object(service_with_mocked_products, 'products', [])
    brands = service_with_mocked_products.get_brands()
    assert brands == []

def test_get_brands_product_missing_brand_key(service_with_mocked_products):
    """Test get_brands handles products missing 'brand' key by using empty string."""
    # mock_products_json_data already includes mock_id_3 which misses 'brand'
    service = service_with_mocked_products
    brands = service.get_brands()
    assert '' in brands # Should include empty string for missing brand

# --- Tests for get_products_by_category ---
def test_get_products_by_category_found(service_with_mocked_products):
    """Test get_products_by_category returns products for an existing category."""
    service = service_with_mocked_products
    results = service.get_products_by_category("Smartphone")
    assert len(results) == 2
    assert {p['id'] for p in results} == {'mock_id_4', 'mock_id_6'}

def test_get_products_by_category_not_found(service_with_mocked_products):
    """Test get_products_by_category returns empty list for non-existent category."""
    service = service_with_mocked_products
    results = service.get_products_by_category("NonExistent")
    assert results == []

def test_get_products_by_category_case_insensitivity(service_with_mocked_products):
    """Test get_products_by_category handles case-insensitivity."""
    service = service_with_mocked_products
    results = service.get_products_by_category("smartphone")
    assert len(results) == 2
    assert {p['id'] for p in results} == {'mock_id_4', 'mock_id_6'}

def test_get_products_by_category_error_handling(service_with_mocked_products, mocker, caplog):
    """Test get_products_by_category error handling."""
    # Simulate an error accessing self.products within get_products_by_category
    mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Access error"))
    results = service_with_mocked_products.get_products_by_category("test")
    assert results == []
    assert "Error getting products by category: Access error" in caplog.text

# --- Tests for get_products_by_brand ---
def test_get_products_by_brand_found(service_with_mocked_products):
    """Test get_products_by_brand returns products for an existing brand."""
    service = service_with_mocked_products
    results = service.get_products_by_brand("Xiaomi")
    assert len(results) == 1
    assert results[0]['id'] == 'mock_id_4'

def test_get_products_by_brand_not_found(service_with_mocked_products):
    """Test get_products_by_brand returns empty list for non-existent brand."""
    service = service_with_mocked_products
    results = service.get_products_by_brand("NonExistentBrand")
    assert results == []

def test_get_products_by_brand_case_insensitivity(service_with_mocked_products):
    """Test get_products_by_brand handles case-insensitivity."""
    service = service_with_mocked_products
    results = service.get_products_by_brand("xiaomi")
    assert len(results) == 1
    assert results[0]['id'] == 'mock_id_4'

def test_get_products_by_brand_error_handling(service_with_mocked_products, mocker, caplog):
    """Test get_products_by_brand error handling."""
    # Simulate an error accessing self.products within get_products_by_brand
    mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Access error"))
    results = service_with_mocked_products.get_products_by_brand("test")
    assert results == []
    assert "Error getting products by brand: Access error" in caplog.text

# --- Tests for get_top_rated_products ---
def test_get_top_rated_products_default_limit(service_with_mocked_products):
    """Test get_top_rated_products with default limit."""
    service = service_with_mocked_products
    results = service.get_top_rated_products()
    assert len(results) == 5
    # Order based on mock data ratings (descending):
    # mock_id_7 (4.9), mock_id_5 (4.7), mock_id_4 (4.2), mock_id_1 (4.0), mock_id_6 (3.9)
    # Remaining: mock_id_2 (3.5), mock_id_8 (3.0), mock_id_3 (0)
    expected_order_ids = ['mock_id_7', 'mock_id_5', 'mock_id_4', 'mock_id_1', 'mock_id_6']
    assert [p['id'] for p in results] == expected_order_ids

def test_get_top_rated_products_custom_limit(service_with_mocked_products):
    """Test get_top_rated_products with custom limit."""
    service = service_with_mocked_products
    results = service.get_top_rated_products(limit=2)
    assert len(results) == 2
    assert results[0]['id'] == 'mock_id_7'
    assert results[1]['id'] == 'mock_id_5'

def test_get_top_rated_products_limit_exceeds_available(service_with_mocked_products):
    """Test get_top_rated_products with limit greater than available products."""
    service = service_with_mocked_products
    results = service.get_top_rated_products(limit=100)
    assert len(results) == len(service.products) # All products should be returned

def test_get_top_rated_products_empty_products(service_with_mocked_products, mocker):
    """Test get_top_rated_products with empty product list."""
    mocker.patch.object(service_with_mocked_products, 'products', [])
    results = service_with_mocked_products.get_top_rated_products()
    assert results == []

def test_get_top_rated_products_missing_rating_or_specs(mock_path_and_open, mock_random_randint):
    """Test get_top_rated_products handles products missing 'rating' or 'specifications' gracefully (defaults to 0)."""
    mock_json_file_path_obj, mock_opener = mock_path_and_open
    json_content = json.dumps({
        "products": [
            {"id": "a", "name": "Product A", "specifications": {"sold": 100}}, # No rating
            {"id": "b", "name": "Product B", "rating": 5.0, "stock_count": 10, "specifications": {"sold": 200}}, # Explicit rating
            {"id": "c", "name": "Product C"}, # No specs or rating
            {"id": "d", "name": "Product D", "rating": 2.0, "stock_count": 5, "specifications": {"sold": 50}} # Explicit rating
        ]
    })
    mock_opener.return_value.__enter__.return_value.read.return_value = json_content
    service = LocalProductService()
    results = service.get_top_rated_products(limit=4)
    # Expected order (by rating descending, then by original order for ties):
    # b (5.0), d (2.0), a (0.0), c (0.0)
    assert [p['id'] for p in results] == ['b', 'd', 'a', 'c']

def test_get_top_rated_products_error_handling(service_with_mocked_products, mocker, caplog):
    """Test get_top_rated_products error handling."""
    # Simulate an error accessing self.products within get_top_rated_products
    mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Access error"))
    results = service_with_mocked_products.get_top_rated_products()
    assert results == []
    assert "Error getting top rated products: Access error" in caplog.text


# --- Tests for get_best_selling_products ---
def test_get_best_selling_products_default_limit(service_with_mocked_products, caplog):
    """Test get_best_selling_products with default limit."""
    service = service_with_mocked_products
    results = service.get_best_selling_products()
    assert len(results) == 5
    # Since mock_random_randint is 500 for all 'sold' count during product loading,
    # the sorting key 'sold' will be equal for all, maintaining original load order.
    assert results == service.products[:5]
    assert "Getting best selling products, limit: 5" in caplog.text
    assert "Returning 5 best selling products" in caplog.text

def test_get_best_selling_products_custom_limit(service_with_mocked_products):
    """Test get_best_selling_products with custom limit."""
    service = service_with_mocked_products
    results = service.get_best_selling_products(limit=2)
    assert len(results) == 2
    assert results == service.products[:2]

def test_get_best_selling_products_limit_exceeds_available(service_with_mocked_products):
    """Test get_best_selling_products with limit greater than available products."""
    service = service_with_mocked_products
    results = service.get_best_selling_products(limit=100)
    assert len(results) == len(service.products)

def test_get_best_selling_products_empty_products(service_with_mocked_products, mocker):
    """Test get_best_selling_products with empty product list."""
    mocker.patch.object(service_with_mocked_products, 'products', [])
    results = service_with_mocked_products.get_best_selling_products()
    assert results == []

def test_get_best_selling_products_error_handling(service_with_mocked_products, mocker, caplog):
    """Test get_best_selling_products error handling."""
    # Simulate an error accessing self.products within get_best_selling_products
    mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Access error"))
    results = service_with_mocked_products.get_best_selling_products()
    assert results == []
    assert "Error getting best selling products: Access error" in caplog.text

# --- Tests for get_products ---
def test_get_products_default_limit(service_with_mocked_products, caplog):
    """Test get_products with default limit."""
    service = service_with_mocked_products
    results = service.get_products()
    # Default limit is 10, but our mock data only has 8 products, so all 8 should be returned.
    assert len(results) == len(service.products)
    assert results == service.products
    assert "Getting all products, limit: 10" in caplog.text

def test_get_products_custom_limit(service_with_mocked_products):
    """Test get_products with custom limit."""
    service = service_with_mocked_products
    results = service.get_products(limit=3)
    assert len(results) == 3
    assert results == service.products[:3]

def test_get_products_limit_exceeds_available(service_with_mocked_products):
    """Test get_products with limit greater than available products."""
    service = service_with_mocked_products
    results = service.get_products(limit=100)
    assert len(results) == len(service.products)

def test_get_products_empty_products(service_with_mocked_products, mocker):
    """Test get_products with empty product list."""
    mocker.patch.object(service_with_mocked_products, 'products', [])
    results = service_with_mocked_products.get_products()
    assert results == []

def test_get_products_error_handling(service_with_mocked_products, mocker, caplog):
    """Test get_products error handling."""
    # Simulate an error accessing self.products within get_products
    mocker.patch.object(service_with_mocked_products, 'products', side_effect=Exception("Access error"))
    results = service_with_mocked_products.get_products()
    assert results == []
    assert "Error getting products: Access error" in caplog.text

# --- Tests for smart_search_products ---
def test_smart_search_best_request_no_category(service_with_mocked_products):
    """Test smart_search for 'terbaik' keyword without specific category, returns top-rated general products."""
    service = service_with_mocked_products
    # Expected top 3 rated products from mock data:
    # mock_id_7 (4.9), mock_id_5 (4.7), mock_id_4 (4.2)
    products, message = service.smart_search_products(keyword="terbaik", limit=3)
    assert len(products) == 3
    assert products[0]['id'] == 'mock_id_7'
    assert products[1]['id'] == 'mock_id_5'
    assert products[2]['id'] == 'mock_id_4'
    assert message == "Berikut produk terbaik berdasarkan rating:"

def test_smart_search_best_request_with_category(service_with_mocked_products):
    """Test smart_search for 'terbaik' keyword with a specific category, returns top-rated from that category."""
    service = service_with_mocked_products
    # Smartphones in mock data: mock_id_4 (4.2), mock_id_6 (3.9)
    products, message = service.smart_search_products(keyword="best phone", category="Smartphone", limit=3)
    assert len(products) == 2
    assert products[0]['id'] == 'mock_id_4'
    assert products[1]['id'] == 'mock_id_6'
    assert message == "Berikut Smartphone terbaik berdasarkan rating:"

def test_smart_search_best_request_category_not_found_fallback_to_general_best(service_with_mocked_products):
    """Test smart_search for 'terbaik' with non-existent category, falls back to general best products."""
    service = service_with_mocked_products
    products, message = service.smart_search_products(keyword="best book", category="Books", limit=3)
    assert len(products) == 3
    # Should fall back to general best products (mock_id_7, mock_id_5, mock_id_4)
    assert products[0]['id'] == 'mock_id_7'
    assert message == "Tidak ada produk kategori Books, berikut produk terbaik secara umum:"

def test_smart_search_all_criteria_match(service_with_mocked_products):
    """Test smart_search with keyword, category, and max_price all matching."""
    service = service_with_mocked_products
    # Find smartphones (mock_id_4, mock_id_6) with price <= 3M. Both match.
    products, message = service.smart_search_products(keyword="smartphone", category="Smartphone", max_price=3000000, limit=5)
    
    assert len(products) == 2
    assert {p['id'] for p in products} == {'mock_id_4', 'mock_id_6'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_keyword_only(service_with_mocked_products):
    """Test smart_search with only keyword, should return relevant matches."""
    service = service_with_mocked_products
    products, message = service.smart_search_products(keyword="product a", limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'mock_id_1'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_category_only(service_with_mocked_products):
    """Test smart_search with only category, should return matches in that category."""
    service = service_with_mocked_products
    products, message = service.smart_search_products(category="Electronics", limit=10)
    assert len(products) == 2
    assert {p['id'] for p in products} == {'mock_id_1', 'mock_id_7'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_max_price_only(service_with_mocked_products):
    """Test smart_search with only max_price, should return products within budget."""
    service = service_with_mocked_products
    products, message = service.smart_search_products(max_price=1000000, limit=10)
    # Products within 1M: mock_id_1 (100k), mock_id_2 (50k), mock_id_8 (500k)
    assert len(products) == 3
    assert {p['id'] for p in products} == {'mock_id_1', 'mock_id_2', 'mock_id_8'}
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."

def test_smart_search_fallback_category_only_if_no_exact_match(service_with_mocked_products):
    """Test smart_search fallback to category products (sorted by price) if combined criteria yield no results."""
    service = service_with_mocked_products
    # Search for "very expensive" (no keyword match) in "Smartphone" (category match) under 1M (no price match within category).
    # This combination yields no direct results.
    # Should fall back to "Smartphone" category products, sorted by price (cheapest first).
    products, message = service.smart_search_products(keyword="very expensive", category="Smartphone", max_price=1000000, limit=5)
    
    # Expected fallback: mock_id_6 (2.5M), mock_id_4 (3M)
    assert len(products) == 2
    assert products[0]['id'] == 'mock_id_6' # Cheapest smartphone
    assert products[1]['id'] == 'mock_id_4'
    assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

def test_smart_search_fallback_budget_only_if_no_category_match(service_with_mocked_products):
    """Test smart_search fallback to budget products if no category match and other criteria fail."""
    service = service_with_mocked_products
    # Search for "unmatched product" (no keyword match) in "NonExistentCategory" (no category match) under 1M (price match).
    # Category search fails, falls back to max_price.
    products, message = service.smart_search_products(keyword="unmatched product", category="NonExistentCategory", max_price=1000000, limit=5)
    
    # Expected fallback: products with price <= 1M (mock_id_1, mock_id_2, mock_id_8), sorted by relevance (price for budget)
    assert len(products) == 3
    assert {p['id'] for p in products} == {'mock_id_1', 'mock_id_2', 'mock_id_8'}
    assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

def test_smart_search_fallback_popular_if_nothing_matches(service_with_mocked_products):
    """Test smart_search fallback to popular products if no criteria yield results."""
    service = service_with_mocked_products
    # Search for "xyz" (no keyword match) in "abc" (no category match) under 10k (no price match).
    # Nothing matches, so it should fall back to popular products.
    products, message = service.smart_search_products(keyword="xyz", category="abc", max_price=10000, limit=3)
    
    # Expected fallback: Best selling products (all mocked products have 'sold': 500 from mock_random_randint,
    # so they are effectively sorted by original loading order due to stable sort, or by rating/price if keywords are present).
    # Since no criteria is met, it resorts to the final fallback: sorted by 'sold' (which is constant 500 for all)
    # The sort key for popular products is 'sold', which is 500 for all in mocked data. So it defaults to list order.
    assert len(products) == 3
    assert products == service.products[:3] 
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." 

def test_smart_search_empty_product_list(service_with_mocked_products, mocker):
    """Test smart_search with an empty product list."""
    mocker.patch.object(service_with_mocked_products, 'products', [])
    products, message = service_with_mocked_products.smart_search_products(keyword="any")
    assert products == []
    # Even with empty products, the fallback message path is taken
    assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

def test_smart_search_limit_parameter(service_with_mocked_products):
    """Test smart_search respects the limit parameter."""
    service = service_with_mocked_products
    products, _ = service.smart_search_products(keyword="product", limit=1)
    assert len(products) == 1
    assert products[0]['id'] == 'mock_id_1'

def test_smart_search_no_input_returns_general_matches(service_with_mocked_products):
    """Test smart_search with no input parameters (empty keyword, no category, no max_price)."""
    service = service_with_mocked_products
    products, message = service.smart_search_products(limit=3)
    # With no criteria, all products satisfy `(not category or ...)`, etc.
    # So it hits the initial `results` calculation and returns the first 'limit' products
    # sorted by relevance score (which in this case will be based on price and rating by default, since no keyword gives relevance score).
    assert len(products) == 3
    # Based on general relevance score (rating, price if budget search, but no budget keyword here)
    assert products[0]['id'] == 'mock_id_7' # Highest rated
    assert products[1]['id'] == 'mock_id_5'
    assert products[2]['id'] == 'mock_id_4'
    assert message == "Berikut produk yang sesuai dengan kriteria Anda."