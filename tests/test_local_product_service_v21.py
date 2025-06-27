import pytest
import json
import logging
from pathlib import Path
from unittest import mock

# Adjust the import path based on your project structure.
# Assuming tests are run from the project root and app is a top-level package.
from app.services.local_product_service import LocalProductService

# --- Test Data ---
# This data represents the *raw* content of data/products.json
# It will be used to simulate file reads for _load_local_products tests.
TEST_PRODUCTS_RAW_JSON_CONTENT = {
    "products": [
        {"id": "p1", "name": "Test Phone", "category": "Smartphone", "brand": "BrandX",
         "price": 10000000, "currency": "IDR", "description": "A great phone.",
         "rating": 4.5, "stock_count": 50, "reviews_count": 100, "availability": "in_stock",
         "specifications": {"storage": "128GB", "color": "Black"}},
        {"id": "p2", "name": "Test Laptop", "category": "Laptop", "brand": "BrandY",
         "price": 15000000, "currency": "IDR", "description": "Powerful laptop for work.",
         "rating": 4.8, "stock_count": 30, "reviews_count": 50, "availability": "in_stock",
         "specifications": {"ram": "16GB", "processor": "Intel i7"}},
        {"id": "p3", "name": "Earbuds A", "category": "Audio", "brand": "BrandX",
         "price": 2000000, "currency": "IDR", "description": "Wireless earbuds with ANC.",
         "rating": 4.2, "stock_count": 100, "reviews_count": 200, "availability": "in_stock",
         "specifications": {"battery": "24h"}},
        {"id": "p4", "name": "Smartwatch Z", "category": "Wearable", "brand": "BrandZ",
         "price": 5000000, "currency": "IDR", "description": "Fitness tracking smartwatch.",
         "rating": 4.0, "stock_count": 20, "reviews_count": 30, "availability": "out_of_stock",
         "specifications": {"display_size": "1.5 inch"}},
        {"id": "p5", "name": "Test Monitor", "category": "Monitor", "brand": "BrandY",
         "price": 3000000, "currency": "IDR", "description": "High refresh rate monitor.",
         "rating": 4.1, "stock_count": 70, "reviews_count": 80, "availability": "in_stock",
         "specifications": {"size": "27 inch", "resolution": "QHD"}},
        {"id": "p6", "name": "Budget Phone", "category": "Smartphone", "brand": "BrandA",
         "price": 1500000, "currency": "IDR", "description": "Affordable smartphone.",
         "rating": 3.9, "stock_count": 200, "reviews_count": 150, "availability": "in_stock"},
        {"id": "p7", "name": "Premium Phone", "category": "Smartphone", "brand": "BrandX",
         "price": 25000000, "currency": "IDR", "description": "High-end smartphone.",
         "rating": 4.9, "stock_count": 10, "reviews_count": 500, "availability": "in_stock"}
    ]
}

# This is what LocalProductService.products should look like after _load_local_products
# (with mocked random.randint for 'sold' fixed at 500)
TRANSFORMED_TEST_PRODUCTS = [
    {
        "id": "p1", "name": "Test Phone", "category": "Smartphone", "brand": "BrandX",
        "price": 10000000, "currency": "IDR", "description": "A great phone.",
        "specifications": {
            "rating": 4.5, "sold": 500, "stock": 50, "condition": "Baru",
            "shop_location": "Indonesia", "shop_name": "BrandX Store",
            "storage": "128GB", "color": "Black"
        },
        "availability": "in_stock", "reviews_count": 100,
        "images": ["https://example.com/p1.jpg"], "url": "https://shopee.co.id/p1"
    },
    {
        "id": "p2", "name": "Test Laptop", "category": "Laptop", "brand": "BrandY",
        "price": 15000000, "currency": "IDR", "description": "Powerful laptop for work.",
        "specifications": {
            "rating": 4.8, "sold": 500, "stock": 30, "condition": "Baru",
            "shop_location": "Indonesia", "shop_name": "BrandY Store",
            "ram": "16GB", "processor": "Intel i7"
        },
        "availability": "in_stock", "reviews_count": 50,
        "images": ["https://example.com/p2.jpg"], "url": "https://shopee.co.id/p2"
    },
    {
        "id": "p3", "name": "Earbuds A", "category": "Audio", "brand": "BrandX",
        "price": 2000000, "currency": "IDR", "description": "Wireless earbuds with ANC.",
        "specifications": {
            "rating": 4.2, "sold": 500, "stock": 100, "condition": "Baru",
            "shop_location": "Indonesia", "shop_name": "BrandX Store",
            "battery": "24h"
        },
        "availability": "in_stock", "reviews_count": 200,
        "images": ["https://example.com/p3.jpg"], "url": "https://shopee.co.id/p3"
    },
    {
        "id": "p4", "name": "Smartwatch Z", "category": "Wearable", "brand": "BrandZ",
        "price": 5000000, "currency": "IDR", "description": "Fitness tracking smartwatch.",
        "specifications": {
            "rating": 4.0, "sold": 500, "stock": 20, "condition": "Baru",
            "shop_location": "Indonesia", "shop_name": "BrandZ Store",
            "display_size": "1.5 inch"
        },
        "availability": "out_of_stock", "reviews_count": 30,
        "images": ["https://example.com/p4.jpg"], "url": "https://shopee.co.id/p4"
    },
    {
        "id": "p5", "name": "Test Monitor", "category": "Monitor", "brand": "BrandY",
        "price": 3000000, "currency": "IDR", "description": "High refresh rate monitor.",
        "specifications": {
            "rating": 4.1, "sold": 500, "stock": 70, "condition": "Baru",
            "shop_location": "Indonesia", "shop_name": "BrandY Store",
            "size": "27 inch", "resolution": "QHD"
        },
        "availability": "in_stock", "reviews_count": 80,
        "images": ["https://example.com/p5.jpg"], "url": "https://shopee.co.id/p5"
    },
    {
        "id": "p6", "name": "Budget Phone", "category": "Smartphone", "brand": "BrandA",
        "price": 1500000, "currency": "IDR", "description": "Affordable smartphone.",
        "specifications": {
            "rating": 3.9, "sold": 500, "stock": 200, "condition": "Baru",
            "shop_location": "Indonesia", "shop_name": "BrandA Store",
        },
        "availability": "in_stock", "reviews_count": 150,
        "images": ["https://example.com/p6.jpg"], "url": "https://shopee.co.id/p6"
    },
    {
        "id": "p7", "name": "Premium Phone", "category": "Smartphone", "brand": "BrandX",
        "price": 25000000, "currency": "IDR", "description": "High-end smartphone.",
        "specifications": {
            "rating": 4.9, "sold": 500, "stock": 10, "condition": "Baru",
            "shop_location": "Indonesia", "shop_name": "BrandX Store",
        },
        "availability": "in_stock", "reviews_count": 500,
        "images": ["https://example.com/p7.jpg"], "url": "https://shopee.co.id/p7"
    }
]

# Fallback Products as defined in the source code for direct comparison
EXPECTED_FALLBACK_PRODUCTS = [
    # Include all 8 fallback products as per the source code
    {
        "id": "1", "name": "iPhone 15 Pro Max", "category": "Smartphone", "brand": "Apple",
        "price": 25000000, "currency": "IDR",
        "description": "iPhone 15 Pro Max dengan chip A17 Pro, kamera 48MP, dan layar 6.7 inch Super Retina XDR. Dilengkapi dengan titanium design dan performa gaming yang luar biasa.",
        "specifications": {
            "rating": 4.8, "sold": 1250, "stock": 50, "condition": "Baru",
            "shop_location": "Jakarta", "shop_name": "Apple Store Indonesia",
            "storage": "256GB", "color": "Titanium Natural", "warranty": "1 Tahun",
            "processor": "A17 Pro", "camera": "48MP Main + 12MP Ultra Wide + 12MP Telephoto",
            "display": "6.7 inch Super Retina XDR"
        },
        "images": ["https://example.com/iphone15.jpg"], "url": "https://shopee.co.id/iphone-15-pro-max"
    },
    {
        "id": "2", "name": "Samsung Galaxy S24 Ultra", "category": "Smartphone", "brand": "Samsung",
        "price": 22000000, "currency": "IDR",
        "description": "Samsung Galaxy S24 Ultra dengan S Pen, kamera 200MP, dan AI features canggih. Dilengkapi dengan Snapdragon 8 Gen 3 dan layar AMOLED 6.8 inch.",
        "specifications": {
            "rating": 4.7, "sold": 980, "stock": 35, "condition": "Baru",
            "shop_location": "Surabaya", "shop_name": "Samsung Store",
            "storage": "512GB", "color": "Titanium Gray", "warranty": "1 Tahun",
            "processor": "Snapdragon 8 Gen 3",
            "camera": "200MP Main + 12MP Ultra Wide + 50MP Telephoto + 10MP Telephoto",
            "display": "6.8 inch Dynamic AMOLED 2X"
        },
        "images": ["https://example.com/s24-ultra.jpg"], "url": "https://shopee.co.id/samsung-s24-ultra"
    },
    {
        "id": "3", "name": "MacBook Pro 14 inch M3", "category": "Laptop", "brand": "Apple",
        "price": 35000000, "currency": "IDR",
        "description": "MacBook Pro dengan chip M3, layar 14 inch Liquid Retina XDR, dan performa tinggi untuk profesional. Cocok untuk video editing, programming, dan gaming.",
        "specifications": {
            "rating": 4.9, "sold": 450, "stock": 25, "condition": "Baru",
            "shop_location": "Jakarta", "shop_name": "Apple Store Indonesia",
            "storage": "1TB", "color": "Space Gray", "warranty": "1 Tahun",
            "processor": "Apple M3", "ram": "16GB Unified Memory", "display": "14 inch Liquid Retina XDR"
        },
        "images": ["https://example.com/macbook-pro.jpg"], "url": "https://shopee.co.id/macbook-pro-m3"
    },
    {
        "id": "4", "name": "AirPods Pro 2nd Gen", "category": "Audio", "brand": "Apple",
        "price": 4500000, "currency": "IDR",
        "description": "AirPods Pro dengan Active Noise Cancellation dan Spatial Audio. Dilengkapi dengan chip H2 untuk performa audio yang lebih baik dan fitur Find My.",
        "specifications": {
            "rating": 4.6, "sold": 2100, "stock": 100, "condition": "Baru",
            "shop_location": "Bandung", "shop_name": "Apple Store Indonesia",
            "color": "White", "warranty": "1 Tahun", "battery": "6 jam dengan ANC, 30 jam dengan case",
            "features": "Active Noise Cancellation, Spatial Audio, Find My"
        },
        "images": ["https://example.com/airpods-pro.jpg"], "url": "https://shopee.co.id/airpods-pro-2"
    },
    {
        "id": "5", "name": "iPad Air 5th Gen", "category": "Tablet", "brand": "Apple",
        "price": 12000000, "currency": "IDR",
        "description": "iPad Air dengan chip M1, layar 10.9 inch Liquid Retina, dan Apple Pencil support. Cocok untuk kreativitas, note-taking, dan entertainment.",
        "specifications": {
            "rating": 4.5, "sold": 750, "stock": 40, "condition": "Baru",
            "shop_location": "Medan", "shop_name": "Apple Store Indonesia",
            "storage": "256GB", "color": "Blue", "warranty": "1 Tahun",
            "processor": "Apple M1", "display": "10.9 inch Liquid Retina", "features": "Apple Pencil support, Magic Keyboard support"
        },
        "images": ["https://example.com/ipad-air.jpg"], "url": "https://shopee.co.id/ipad-air-5"
    },
    {
        "id": "6", "name": "ASUS ROG Strix G15", "category": "Laptop", "brand": "ASUS",
        "price": 18000000, "currency": "IDR",
        "description": "Laptop gaming ASUS ROG Strix G15 dengan RTX 4060, AMD Ryzen 7, dan layar 15.6 inch 144Hz. Dilengkapi dengan RGB keyboard dan cooling system yang powerful.",
        "specifications": {
            "rating": 4.4, "sold": 320, "stock": 15, "condition": "Baru",
            "shop_location": "Jakarta", "shop_name": "ASUS Store",
            "storage": "512GB SSD", "color": "Black", "warranty": "2 Tahun",
            "processor": "AMD Ryzen 7 7735HS", "gpu": "NVIDIA RTX 4060 8GB", "ram": "16GB DDR5",
            "display": "15.6 inch FHD 144Hz"
        },
        "images": ["https://example.com/rog-strix.jpg"], "url": "https://shopee.co.id/asus-rog-strix-g15"
    },
    {
        "id": "7", "name": "Sony WH-1000XM5", "category": "Audio", "brand": "Sony",
        "price": 5500000, "currency": "IDR",
        "description": "Headphone wireless Sony WH-1000XM5 dengan noise cancellation terbaik di kelasnya. Dilengkapi dengan 30 jam battery life dan quick charge.",
        "specifications": {
            "rating": 4.8, "sold": 890, "stock": 30, "condition": "Baru",
            "shop_location": "Surabaya", "shop_name": "Sony Store",
            "color": "Black", "warranty": "1 Tahun", "battery": "30 jam dengan ANC",
            "features": "Industry-leading noise cancellation, Quick Charge, Multipoint connection"
        },
        "images": ["https://example.com/sony-wh1000xm5.jpg"], "url": "https://shopee.co.id/sony-wh1000xm5"
    },
    {
        "id": "8", "name": "Samsung Galaxy Tab S9", "category": "Tablet", "brand": "Samsung",
        "price": 15000000, "currency": "IDR",
        "description": "Samsung Galaxy Tab S9 dengan S Pen, layar AMOLED 11 inch, dan Snapdragon 8 Gen 2. Cocok untuk productivity dan entertainment.",
        "specifications": {
            "rating": 4.3, "sold": 280, "stock": 20, "condition": "Baru",
            "shop_location": "Bandung", "shop_name": "Samsung Store",
            "storage": "256GB", "color": "Graphite", "warranty": "1 Tahun",
            "processor": "Snapdragon 8 Gen 2", "display": "11 inch Dynamic AMOLED 2X",
            "features": "S Pen included, DeX mode, Multi-window"
        },
        "images": ["https://example.com/galaxy-tab-s9.jpg"], "url": "https://shopee.co.id/galaxy-tab-s9"
    }
]


# --- Fixtures ---

@pytest.fixture
def mock_local_product_service_file_structure(tmp_path):
    """
    Creates a dummy directory structure mirroring the app and data directories
    within tmp_path, and places a dummy local_product_service.py for __file__ patching.
    Returns the path to the data directory within this temp structure.
    """
    # Create app/services directory
    app_dir = tmp_path / "app"
    services_dir = app_dir / "services"
    services_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy local_product_service.py file
    dummy_service_file = services_dir / "local_product_service.py"
    # Write some minimal content to make it a valid Python file
    dummy_service_file.write_text("import logging\nfrom pathlib import Path\nclass LocalProductService: pass\n")

    # Create data directory at the same level as app
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)

    return dummy_service_file


@pytest.fixture
def mock_products_json_path(mock_local_product_service_file_structure):
    """
    Creates a temporary 'data/products.json' file with test data.
    Returns the path to the dummy file.
    """
    # The data directory is at mock_local_product_service_file_structure.parent.parent.parent / "data"
    # if mock_local_product_service_file_structure is Path(__file__) for the service.
    # The root is tmp_path. So data_dir is tmp_path / "data".
    json_file_path = mock_local_product_service_file_structure.parent.parent.parent / "data" / "products.json"
    json_file_path.write_text(json.dumps(TEST_PRODUCTS_RAW_JSON_CONTENT))
    return json_file_path


@pytest.fixture(autouse=True)
def mock_random_randint(mocker):
    """Mocks random.randint to return a fixed value for deterministic 'sold' counts."""
    mocker.patch('random.randint', return_value=500)


@pytest.fixture
def local_product_service_instance_with_mocked_load(mocker):
    """
    Provides an instance of LocalProductService with its _load_local_products
    method mocked to return a fixed, transformed dataset. This isolates tests
    from file I/O and data transformation specifics.
    """
    mocker.patch.object(LocalProductService, '_load_local_products', return_value=TRANSFORMED_TEST_PRODUCTS)
    return LocalProductService()


@pytest.fixture
def local_product_service_instance_with_real_load(mocker, mock_products_json_path, mock_local_product_service_file_structure):
    """
    Provides an instance of LocalProductService that attempts to load from a real
    (but temporary and controlled) file. This fixture is for testing _load_local_products itself.
    """
    # Patch __file__ global within the LocalProductService module to point to our dummy file
    mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))

    # Ensure Path.exists returns True for our mock products.json
    # We patch Path.exists globally or specifically for the path that LocalProductService tries to find.
    # The path will be based on mock_local_product_service_file_structure, so we need to match it.
    mock_full_path = mock_local_product_service_file_structure.parent.parent.parent / "data" / "products.json"
    mocker.patch.object(Path, 'exists', return_value=True) # Patching the method for any Path object
    
    # Mock open to return the content of our test JSON
    mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(TEST_PRODUCTS_RAW_JSON_CONTENT)))

    return LocalProductService()

# --- Tests for LocalProductService ---

class TestLocalProductServiceInitialization:
    """Tests for the __init__ method and overall product loading behavior."""

    def test_init_loads_products_successfully_from_file(self, local_product_service_instance_with_real_load, caplog):
        """
        Test that __init__ successfully loads products from a valid JSON file.
        Uses the fixture that simulates a real file system load.
        """
        service = local_product_service_instance_with_real_load
        assert len(service.products) == len(TRANSFORMED_TEST_PRODUCTS)
        assert service.products[0]["id"] == "p1"
        assert service.products[0]["specifications"]["sold"] == 500 # From mock_random_randint

        assert "Loaded 7 local products from JSON file" in caplog.text
        assert "Successfully loaded 7 products from JSON file using utf-8 encoding" in caplog.text


    def test_init_calls_fallback_if_file_not_found(self, mocker, caplog, mock_local_product_service_file_structure):
        """
        Test that __init__ uses fallback products if the JSON file is not found.
        This simulates Path.exists() returning False.
        """
        # Patch __file__ for Path() calculation
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=False)
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=EXPECTED_FALLBACK_PRODUCTS)

        service = LocalProductService()

        # Verify fallback was called and products are fallback ones
        assert service.products == EXPECTED_FALLBACK_PRODUCTS
        assert "Products JSON file not found at:" in caplog.text
        assert f"Loaded {len(EXPECTED_FALLBACK_PRODUCTS)} local products from JSON file" in caplog.text


    def test_init_calls_fallback_on_json_decode_error(self, mocker, caplog, mock_local_product_service_file_structure):
        """
        Test that __init__ uses fallback products if JSON decoding fails for all encodings.
        """
        # Patch __file__ for Path() calculation
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=True)
        # Mock open to return invalid JSON data
        mocker.patch('builtins.open', mocker.mock_open(read_data='invalid json'))
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=EXPECTED_FALLBACK_PRODUCTS)

        service = LocalProductService()

        assert service.products == EXPECTED_FALLBACK_PRODUCTS
        assert "Failed to load with utf-16-le encoding: " in caplog.text
        assert "Failed to load with utf-8 encoding: Expecting value" in caplog.text
        assert "All encoding attempts failed, using fallback products" in caplog.text
        assert f"Loaded {len(EXPECTED_FALLBACK_PRODUCTS)} local products from JSON file" in caplog.text


    def test_init_calls_fallback_on_unicode_decode_error(self, mocker, caplog, mock_local_product_service_file_structure):
        """
        Test that __init__ uses fallback products if Unicode decoding fails for all encodings.
        """
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=True)
        # Mock open's read method to raise UnicodeDecodeError for any encoding attempt
        mock_open_func = mocker.mock_open()
        mock_open_func.return_value.__enter__.return_value.read.side_effect = UnicodeDecodeError("utf-8", b'\xff', 0, 1, "test error")
        mocker.patch('builtins.open', mock_open_func)
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=EXPECTED_FALLBACK_PRODUCTS)

        service = LocalProductService()

        assert service.products == EXPECTED_FALLBACK_PRODUCTS
        assert "Failed to load with utf-16-le encoding: test error" in caplog.text
        assert "All encoding attempts failed, using fallback products" in caplog.text
        assert f"Loaded {len(EXPECTED_FALLBACK_PRODUCTS)} local products from JSON file" in caplog.text
        
    def test_init_calls_fallback_on_general_exception_during_load(self, mocker, caplog, mock_local_product_service_file_structure):
        """
        Test that __init__ uses fallback products if a general exception occurs during file loading.
        """
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        # Simulate an exception when trying to check file existence
        mocker.patch('pathlib.Path.exists', side_effect=Exception("Permission denied"))
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=EXPECTED_FALLBACK_PRODUCTS)

        service = LocalProductService()

        assert service.products == EXPECTED_FALLBACK_PRODUCTS
        assert "Error loading products from JSON file: Permission denied" in caplog.text
        assert f"Loaded {len(EXPECTED_FALLBACK_PRODUCTS)} local products from JSON file" in caplog.text


class TestLoadLocalProductsMethod:
    """Tests specifically for the _load_local_products method."""

    def test_load_local_products_success_utf8_bom(self, mocker, mock_products_json_path, mock_local_product_service_file_structure, caplog):
        """Test successful loading of UTF-8 JSON with BOM, ensuring BOM is stripped."""
        content_with_bom = '\ufeff' + json.dumps(TEST_PRODUCTS_RAW_JSON_CONTENT)
        
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('builtins.open', mocker.mock_open(read_data=content_with_bom))

        service = LocalProductService()
        # Call the method directly to test its specific behavior, not through __init__
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_TEST_PRODUCTS)
        assert products[0]['id'] == 'p1'
        assert products[0]['specifications']['sold'] == 500 # From fixture
        assert "Successfully loaded 7 products from JSON file using utf-8 encoding" in caplog.text

    def test_load_local_products_success_utf16_le(self, mocker, mock_products_json_path, mock_local_product_service_file_structure, caplog):
        """Test successful loading of UTF-16LE encoded JSON."""
        # Simulate UTF-16LE content by encoding and then decoding to string for mock_open
        utf16_le_content = json.dumps(TEST_PRODUCTS_RAW_JSON_CONTENT).encode('utf-16-le').decode('utf-16-le')
        
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=True)
        # Mock open to return data that would be successfully read as UTF-16LE
        mock_open_mock = mocker.mock_open()
        mock_open_mock.return_value.__enter__.return_value.read.return_value = utf16_le_content
        mocker.patch('builtins.open', mock_open_mock)

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == len(TRANSFORMED_TEST_PRODUCTS)
        assert products[0]['id'] == 'p1'
        assert "Successfully loaded 7 products from JSON file using utf-16-le encoding" in caplog.text

    def test_load_local_products_missing_products_key_in_json(self, mocker, mock_products_json_path, mock_local_product_service_file_structure, caplog):
        """
        Test _load_local_products when 'products' key is missing in JSON.
        It should return an empty list for products.
        """
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps({"other_data": "value"})))

        service = LocalProductService()
        products = service._load_local_products()
        
        assert products == []
        assert "Successfully loaded 0 products from JSON file using utf-8 encoding" in caplog.text

    def test_load_local_products_empty_products_list_in_json(self, mocker, mock_products_json_path, mock_local_product_service_file_structure, caplog):
        """
        Test _load_local_products when 'products' key is an empty list in JSON.
        """
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps({"products": []})))

        service = LocalProductService()
        products = service._load_local_products()
        
        assert products == []
        assert "Successfully loaded 0 products from JSON file using utf-8 encoding" in caplog.text
        
    def test_load_local_products_handles_missing_optional_product_keys(self, mocker, mock_products_json_path, mock_local_product_service_file_structure, caplog):
        """
        Test that missing optional keys in product dictionaries are handled gracefully with defaults
        during transformation.
        """
        minimal_product_json = {
            "products": [
                {"id": "mp1", "name": "Minimal Product"},
                {"id": "mp2", "price": 1000},
                {"name": "No ID Product"} # missing ID
            ]
        }
        
        mocker.patch('app.services.local_product_service.__file__', str(mock_local_product_service_file_structure))
        mocker.patch('pathlib.Path.exists', return_value=True)
        mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(minimal_product_json)))

        service = LocalProductService()
        products = service._load_local_products()
        
        assert len(products) == 3
        # Check defaults for mp1
        assert products[0]['id'] == 'mp1'
        assert products[0]['name'] == 'Minimal Product'
        assert products[0]['category'] == ''
        assert products[0]['price'] == 0
        assert products[0]['specifications']['rating'] == 0
        assert products[0]['specifications']['sold'] == 500
        assert products[0]['images'] == ['https://example.com/mp1.jpg']
        assert products[0]['url'] == 'https://shopee.co.id/mp1'
        
        # Check defaults for mp2
        assert products[1]['id'] == 'mp2'
        assert products[1]['price'] == 1000
        assert products[1]['name'] == ''
        
        # Check product with missing ID
        assert products[2]['id'] == '' # Default ID
        assert products[2]['name'] == 'No ID Product'
        assert products[2]['images'] == ['https://example.com/product.jpg'] # Default image
        assert products[2]['url'] == 'https://shopee.co.id/product' # Default URL
        
        assert "Successfully loaded 3 products from JSON file using utf-8 encoding" in caplog.text


class TestGetFallbackProducts:
    """Tests for the _get_fallback_products method."""

    def test_get_fallback_products_returns_expected_data(self, caplog):
        """Test that _get_fallback_products returns the predefined fallback data."""
        service = LocalProductService()
        # Directly call the method, as it doesn't depend on self.products loading
        products = service._get_fallback_products()
        
        assert isinstance(products, list)
        assert len(products) == len(EXPECTED_FALLBACK_PRODUCTS)
        assert products[0]['id'] == "1"
        assert products[0]['name'] == "iPhone 15 Pro Max"
        assert "Using fallback products due to JSON file loading error" in caplog.text


class TestSearchProducts:
    """Tests for the search_products method."""

    def test_search_products_by_name(self, local_product_service_instance_with_mocked_load):
        """Test searching products by name keyword."""
        results = local_product_service_instance_with_mocked_load.search_products("Test Phone")
        assert len(results) == 1
        assert results[0]['id'] == 'p1'

    def test_search_products_case_insensitive(self, local_product_service_instance_with_mocked_load):
        """Test case-insensitive search."""
        results = local_product_service_instance_with_mocked_load.search_products("test laptop")
        assert len(results) == 1
        assert results[0]['id'] == 'p2'

    def test_search_products_by_category(self, local_product_service_instance_with_mocked_load):
        """Test searching products by category keyword."""
        results = local_product_service_instance_with_mocked_load.search_products("Smartphone")
        assert len(results) == 3
        # Ensure correct items are found and order is stable based on the code's sorting logic
        # For 'Smartphone' keyword, all 3 get score 3 (category match).
        # Since no name/brand match, and no price filter, original order is maintained.
        assert [p['id'] for p in results] == ['p1', 'p6', 'p7']

    def test_search_products_by_description(self, local_product_service_instance_with_mocked_load):
        """Test searching products by description keyword."""
        results = local_product_service_instance_with_mocked_load.search_products("powerful laptop")
        assert len(results) == 1
        assert results[0]['id'] == 'p2'

    def test_search_products_by_brand_and_relevance(self, local_product_service_instance_with_mocked_load):
        """Test searching by brand and verify relevance sorting."""
        results = local_product_service_instance_with_mocked_load.search_products("BrandX")
        assert len(results) == 3
        # p1: 'Test Phone' (name 'Test Phone' matches 'phone' in "Test Phone") -> score 10 (name match), 5 (brandX match), 3 (category)
        # p3: 'Earbuds A' -> score 5 (brandX match)
        # p7: 'Premium Phone' -> score 5 (brandX match)
        # p1 will be first due to higher score. p3, p7 should follow in original order.
        assert [p['id'] for p in results] == ['p1', 'p3', 'p7']

    def test_search_products_no_match(self, local_product_service_instance_with_mocked_load):
        """Test searching with a keyword that yields no results."""
        results = local_product_service_instance_with_mocked_load.search_products("nonexistent product")
        assert len(results) == 0

    def test_search_products_limit(self, local_product_service_instance_with_mocked_load):
        """Test the limit parameter."""
        results = local_product_service_instance_with_mocked_load.search_products("phone", limit=2)
        assert len(results) == 2
        # 'Test Phone', 'Budget Phone', 'Premium Phone' all match "phone" in their names.
        # Original order is p1, p6, p7.
        assert [p['id'] for p in results] == ['p1', 'p6']


    def test_search_products_with_price_limit_from_keyword(self, local_product_service_instance_with_mocked_load):
        """Test searching with price limit extracted from keyword (e.g., "phone 3 juta")."""
        # keyword="phone 3 juta" -> max_price = 3,000,000. keyword_lower = "phone 3 juta"
        # Filtered products (by price first, then by text):
        # p1 (10M): Not <= 3M. Text "Test Phone", has "phone". Added.
        # p2 (15M): Not <= 3M. No "phone". Skipped.
        # p3 (2M): <= 3M. Added.
        # p4 (5M): Not <= 3M. No "phone". Skipped.
        # p5 (3M): <= 3M. Added.
        # p6 (1.5M): <= 3M. Added. Text "Budget Phone", has "phone".
        # p7 (25M): Not <= 3M. Text "Premium Phone", has "phone". Added.
        # products after initial filter: [p3, p5, p6] (price filter) + [p1, p7] (text filter)
        # Combined: [p3, p5, p6, p1, p7] (in iteration order, duplicates handled by set logic not implemented)
        # In reality, it will be added once.
        # filtered_products will contain: p3, p5, p6 (from price match) and p1, p7 (from text match).
        # p6 also matches text, but added once. So the set is {p1, p3, p5, p6, p7}
        #
        # Relevance scores with price consideration (max_price is present):
        # score += (10000000 - price) / 1000000
        # p6 (1.5M, Smartphone, "Budget Phone"): 10 (name) + 3 (category) + (10-1.5) = 21.5
        # p3 (2M, Audio): (10-2) = 8
        # p5 (3M, Monitor): (10-3) = 7
        # p1 (10M, Smartphone, "Test Phone"): 10 (name) + 3 (category) + (10-10) = 13
        # p7 (25M, Smartphone, "Premium Phone"): 10 (name) + 3 (category) + (10-25) = -2
        #
        # Sorted (desc): p6, p1, p3, p5, p7
        results = local_product_service_instance_with_mocked_load.search_products("phone 3 juta", limit=5)
        assert len(results) == 5
        assert [p['id'] for p in results] == ['p6', 'p1', 'p3', 'p5', 'p7']


    def test_search_products_with_budget_keyword(self, local_product_service_instance_with_mocked_load):
        """Test searching with a budget keyword (e.g., "smartphone murah")."""
        # "murah" sets max_price = 5,000,000.
        # Products <= 5M: p3 (2M), p4 (5M), p5 (3M), p6 (1.5M)
        # Products with "smartphone" in text: p1, p6, p7
        # Combined distinct set for scoring: {p1, p3, p4, p5, p6, p7}
        # Scores (with price factor for 'murah'):
        # p6 (1.5M, "Budget Phone", Smartphone): 10 (name) + 3 (category) + (10-1.5) = 21.5
        # p1 (10M, "Test Phone", Smartphone): 10 (name) + 3 (category) + (10-10) = 13
        # p7 (25M, "Premium Phone", Smartphone): 10 (name) + 3 (category) + (10-25) = -2
        # p3 (2M, Audio): (10-2) = 8
        # p5 (3M, Monitor): (10-3) = 7
        # p4 (5M, Wearable): (10-5) = 5
        # Sorted (desc): p6, p1, p3, p5, p4, p7
        results = local_product_service_instance_with_mocked_load.search_products("smartphone murah")
        assert len(results) == 6
        assert [p['id'] for p in results] == ['p6', 'p1', 'p3', 'p5', 'p4', 'p7']

    def test_search_products_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in search_products."""
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', side_effect=Exception("Database error"))
        results = local_product_service_instance_with_mocked_load.search_products("anything")
        assert results == []
        assert "Error searching products: Database error" in caplog.text


class TestExtractPriceFromKeyword:
    """Tests for the _extract_price_from_keyword method."""

    @pytest.mark.parametrize("keyword, expected_price", [
        ("iphone 10 juta", 10000000),
        ("laptop 500 ribu", 500000),
        ("harga rp 2500000", 2500000),
        ("tv 750000 rp", 750000),
        ("headphone 200k", 200000),
        ("monitor 1m", 1000000), # The pattern `(\d+)\s*m` captures '1' from '1m'
        ("macbook murah", 5000000), # Budget keyword
        ("budget gaming pc", 5000000), # Budget keyword
        ("hp hemat", 3000000), # Budget keyword
        ("smartphone terjangkau", 4000000), # Budget keyword
        ("tablet ekonomis", 2000000), # Budget keyword
        ("no price here", None),
        ("just text", None),
        ("", None),
        ("1000k", 1000000),
        ("rp10000", 10000),
        ("rp 5.000.000", None), # Current regexes might not handle dots/commas
        ("laptop 5jt", 5000000) # Test 'jt' abbreviation (not explicitly covered by patterns, should return None)
    ])
    def test_extract_price_from_keyword_valid_patterns(self, local_product_service_instance_with_mocked_load, keyword, expected_price):
        """Test various valid price extraction patterns."""
        price = local_product_service_instance_with_mocked_load._extract_price_from_keyword(keyword)
        assert price == expected_price

    def test_extract_price_from_keyword_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in _extract_price_from_keyword."""
        mocker.patch('re.search', side_effect=Exception("Regex processing error"))
        price = local_product_service_instance_with_mocked_load._extract_price_from_keyword("keyword with 1 juta")
        assert price is None
        assert "Error extracting price from keyword: Regex processing error" in caplog.text


class TestGetProductDetails:
    """Tests for the get_product_details method."""

    def test_get_product_details_existing_id(self, local_product_service_instance_with_mocked_load):
        """Test retrieving details for an existing product ID."""
        product = local_product_service_instance_with_mocked_load.get_product_details("p1")
        assert product is not None
        assert product['id'] == 'p1'
        assert product['name'] == 'Test Phone'

    def test_get_product_details_non_existing_id(self, local_product_service_instance_with_mocked_load):
        """Test retrieving details for a non-existing product ID."""
        product = local_product_service_instance_with_mocked_load.get_product_details("nonexistent")
        assert product is None

    def test_get_product_details_empty_id(self, local_product_service_instance_with_mocked_load):
        """Test retrieving details for an empty product ID."""
        product = local_product_service_instance_with_mocked_load.get_product_details("")
        assert product is None

    def test_get_product_details_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in get_product_details."""
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', side_effect=Exception("Data access error"))
        product = local_product_service_instance_with_mocked_load.get_product_details("p1")
        assert product is None
        assert "Error getting product details: Data access error" in caplog.text


class TestGetCategories:
    """Tests for the get_categories method."""

    def test_get_categories_returns_unique_sorted_categories(self, local_product_service_instance_with_mocked_load):
        """Test that get_categories returns unique, sorted category names."""
        categories = local_product_service_instance_with_mocked_load.get_categories()
        expected_categories = sorted(['Smartphone', 'Laptop', 'Audio', 'Wearable', 'Monitor'])
        assert categories == expected_categories

    def test_get_categories_handles_missing_category_key(self, mocker, local_product_service_instance_with_mocked_load):
        """Test that get_categories handles products with missing 'category' key."""
        mock_products_with_missing_category = TRANSFORMED_TEST_PRODUCTS + [{"id": "no_cat", "name": "No Category Product"}]
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', mock_products_with_missing_category)
        categories = local_product_service_instance_with_mocked_load.get_categories()
        expected_categories = sorted(['Smartphone', 'Laptop', 'Audio', 'Wearable', 'Monitor', '']) # '' for missing category
        assert categories == expected_categories


class TestGetBrands:
    """Tests for the get_brands method."""

    def test_get_brands_returns_unique_sorted_brands(self, local_product_service_instance_with_mocked_load):
        """Test that get_brands returns unique, sorted brand names."""
        brands = local_product_service_instance_with_mocked_load.get_brands()
        expected_brands = sorted(['BrandX', 'BrandY', 'BrandA', 'BrandZ'])
        assert brands == expected_brands

    def test_get_brands_handles_missing_brand_key(self, mocker, local_product_service_instance_with_mocked_load):
        """Test that get_brands handles products with missing 'brand' key."""
        mock_products_with_missing_brand = TRANSFORMED_TEST_PRODUCTS + [{"id": "no_brand", "name": "No Brand Product"}]
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', mock_products_with_missing_brand)
        brands = local_product_service_instance_with_mocked_load.get_brands()
        expected_brands = sorted(['BrandX', 'BrandY', 'BrandA', 'BrandZ', '']) # '' for missing brand
        assert brands == expected_brands


class TestGetProductsByCategory:
    """Tests for the get_products_by_category method."""

    def test_get_products_by_category_existing(self, local_product_service_instance_with_mocked_load):
        """Test retrieving products for an existing category."""
        products = local_product_service_instance_with_mocked_load.get_products_by_category("Smartphone")
        assert len(products) == 3
        assert {p['id'] for p in products} == {'p1', 'p6', 'p7'}

    def test_get_products_by_category_case_insensitive(self, local_product_service_instance_with_mocked_load):
        """Test case-insensitive category search."""
        products = local_product_service_instance_with_mocked_load.get_products_by_category("smartphone")
        assert len(products) == 3
        assert {p['id'] for p in products} == {'p1', 'p6', 'p7'}

    def test_get_products_by_category_non_existing(self, local_product_service_instance_with_mocked_load):
        """Test retrieving products for a non-existing category."""
        products = local_product_service_instance_with_mocked_load.get_products_by_category("Gaming PC")
        assert products == []

    def test_get_products_by_category_empty_string(self, local_product_service_instance_with_mocked_load):
        """Test retrieving products for an empty category string (should return nothing if all have categories)."""
        products = local_product_service_instance_with_mocked_load.get_products_by_category("")
        assert products == [] # In TRANSFORMED_TEST_PRODUCTS, all products have a non-empty category

    def test_get_products_by_category_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in get_products_by_category."""
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', side_effect=Exception("Data error"))
        products = local_product_service_instance_with_mocked_load.get_products_by_category("Smartphone")
        assert products == []
        assert "Error getting products by category: Data error" in caplog.text


class TestGetProductsByBrand:
    """Tests for the get_products_by_brand method."""

    def test_get_products_by_brand_existing(self, local_product_service_instance_with_mocked_load):
        """Test retrieving products for an existing brand."""
        products = local_product_service_instance_with_mocked_load.get_products_by_brand("BrandX")
        assert len(products) == 3
        assert {p['id'] for p in products} == {'p1', 'p3', 'p7'}

    def test_get_products_by_brand_case_insensitive(self, local_product_service_instance_with_mocked_load):
        """Test case-insensitive brand search."""
        products = local_product_service_instance_with_mocked_load.get_products_by_brand("brandx")
        assert len(products) == 3
        assert {p['id'] for p in products} == {'p1', 'p3', 'p7'}

    def test_get_products_by_brand_non_existing(self, local_product_service_instance_with_mocked_load):
        """Test retrieving products for a non-existing brand."""
        products = local_product_service_instance_with_mocked_load.get_products_by_brand("NonExistentBrand")
        assert products == []

    def test_get_products_by_brand_empty_string(self, local_product_service_instance_with_mocked_load):
        """Test retrieving products for an empty brand string (should return nothing if all have brands)."""
        products = local_product_service_instance_with_mocked_load.get_products_by_brand("")
        assert products == [] # In TRANSFORMED_TEST_PRODUCTS, all products have a non-empty brand

    def test_get_products_by_brand_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in get_products_by_brand."""
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', side_effect=Exception("Data error"))
        products = local_product_service_instance_with_mocked_load.get_products_by_brand("BrandX")
        assert products == []
        assert "Error getting products by brand: Data error" in caplog.text


class TestGetTopRatedProducts:
    """Tests for the get_top_rated_products method."""

    def test_get_top_rated_products_default_limit(self, local_product_service_instance_with_mocked_load):
        """Test retrieving top-rated products with default limit."""
        # p7 (4.9), p2 (4.8), p1 (4.5), p3 (4.2), p5 (4.1), p4 (4.0), p6 (3.9)
        products = local_product_service_instance_with_mocked_load.get_top_rated_products() # default limit=5
        assert len(products) == 5
        assert [p['id'] for p in products] == ['p7', 'p2', 'p1', 'p3', 'p5']

    def test_get_top_rated_products_custom_limit(self, local_product_service_instance_with_mocked_load):
        """Test retrieving top-rated products with a custom limit."""
        products = local_product_service_instance_with_mocked_load.get_top_rated_products(limit=2)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p7', 'p2']

    def test_get_top_rated_products_limit_greater_than_available(self, local_product_service_instance_with_mocked_load):
        """Test retrieving top-rated products with a limit greater than available products."""
        products = local_product_service_instance_with_mocked_load.get_top_rated_products(limit=10)
        assert len(products) == len(TRANSFORMED_TEST_PRODUCTS)
        assert [p['id'] for p in products] == ['p7', 'p2', 'p1', 'p3', 'p5', 'p4', 'p6']

    def test_get_top_rated_products_handles_missing_rating(self, mocker, local_product_service_instance_with_mocked_load):
        """Test that get_top_rated_products handles products missing 'rating' key."""
        products_with_missing_rating = [
            {"id": "high_rating", "specifications": {"rating": 5.0}},
            {"id": "no_rating", "specifications": {}}, # Missing rating (defaults to 0)
            {"id": "low_rating", "specifications": {"rating": 1.0}},
            {"id": "no_specs", "name": "No Specs Product"} # Missing specifications key entirely (defaults rating to 0)
        ]
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', products_with_missing_rating)
        products = local_product_service_instance_with_mocked_load.get_top_rated_products(limit=3)
        # Expected order: high_rating (5.0), low_rating (1.0), then no_rating/no_specs (both 0.0, stable sort)
        assert [p['id'] for p in products] == ['high_rating', 'low_rating', 'no_rating']

    def test_get_top_rated_products_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in get_top_rated_products."""
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', side_effect=Exception("Sort error"))
        products = local_product_service_instance_with_mocked_load.get_top_rated_products()
        assert products == []
        assert "Error getting top rated products: Sort error" in caplog.text


class TestGetBestSellingProducts:
    """Tests for the get_best_selling_products method."""

    def test_get_best_selling_products_default_limit(self, local_product_service_instance_with_mocked_load, caplog):
        """Test retrieving best-selling products with default limit."""
        # All products have sold: 500 due to mock_random_randint fixture.
        # So order should be stable based on original list order of TRANSFORMED_TEST_PRODUCTS.
        products = local_product_service_instance_with_mocked_load.get_best_selling_products() # default limit=5
        assert len(products) == 5
        assert [p['id'] for p in products] == ['p1', 'p2', 'p3', 'p4', 'p5']
        assert "Getting best selling products, limit: 5" in caplog.text
        assert "Returning 5 best selling products" in caplog.text

    def test_get_best_selling_products_custom_limit(self, local_product_service_instance_with_mocked_load, caplog):
        """Test retrieving best-selling products with a custom limit."""
        products = local_product_service_instance_with_mocked_load.get_best_selling_products(limit=2)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p1', 'p2']
        assert "Getting best selling products, limit: 2" in caplog.text
        assert "Returning 2 best selling products" in caplog.text

    def test_get_best_selling_products_limit_greater_than_available(self, local_product_service_instance_with_mocked_load):
        """Test retrieving best-selling products with a limit greater than available products."""
        products = local_product_service_instance_with_mocked_load.get_best_selling_products(limit=10)
        assert len(products) == len(TRANSFORMED_TEST_PRODUCTS)
        assert [p['id'] for p in products] == ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']

    def test_get_best_selling_products_handles_missing_sold(self, mocker, local_product_service_instance_with_mocked_load):
        """Test that get_best_selling_products handles products missing 'sold' key."""
        products_with_missing_sold = [
            {"id": "high_sold", "specifications": {"sold": 1000}},
            {"id": "no_sold", "specifications": {}}, # Missing sold (defaults to 0)
            {"id": "low_sold", "specifications": {"sold": 100}},
            {"id": "no_specs", "name": "No Specs Product"} # Missing specifications key entirely (defaults sold to 0)
        ]
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', products_with_missing_sold)
        products = local_product_service_instance_with_mocked_load.get_best_selling_products(limit=3)
        # Expected order: high_sold (1000), low_sold (100), no_sold (0), no_specs (0)
        assert [p['id'] for p in products] == ['high_sold', 'low_sold', 'no_sold']

    def test_get_best_selling_products_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in get_best_selling_products."""
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', side_effect=Exception("Sort error"))
        products = local_product_service_instance_with_mocked_load.get_best_selling_products()
        assert products == []
        assert "Error getting best selling products: Sort error" in caplog.text


class TestGetProducts:
    """Tests for the get_products method."""

    def test_get_products_default_limit(self, local_product_service_instance_with_mocked_load, caplog):
        """Test retrieving all products with default limit."""
        products = local_product_service_instance_with_mocked_load.get_products() # default limit=10
        assert len(products) == len(TRANSFORMED_TEST_PRODUCTS)
        assert [p['id'] for p in products] == ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']
        assert "Getting all products, limit: 10" in caplog.text

    def test_get_products_custom_limit(self, local_product_service_instance_with_mocked_load, caplog):
        """Test retrieving products with a custom limit."""
        products = local_product_service_instance_with_mocked_load.get_products(limit=3)
        assert len(products) == 3
        assert [p['id'] for p in products] == ['p1', 'p2', 'p3']
        assert "Getting all products, limit: 3" in caplog.text

    def test_get_products_limit_greater_than_available(self, local_product_service_instance_with_mocked_load):
        """Test retrieving products with a limit greater than available products."""
        products = local_product_service_instance_with_mocked_load.get_products(limit=100)
        assert len(products) == len(TRANSFORMED_TEST_PRODUCTS)

    def test_get_products_error_handling(self, local_product_service_instance_with_mocked_load, mocker, caplog):
        """Test error handling in get_products."""
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', side_effect=Exception("Access error"))
        products = local_product_service_instance_with_mocked_load.get_products()
        assert products == []
        assert "Error getting products: Access error" in caplog.text


class TestSmartSearchProducts:
    """Tests for the smart_search_products method, including its complex fallback logic."""

    # Scenario 1: User asks for "terbaik" (best) generally
    def test_smart_search_best_general(self, local_product_service_instance_with_mocked_load):
        """Test smart search for general 'best' products (top rated overall)."""
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="produk terbaik", limit=2)
        # Should return p7 (4.9), p2 (4.8) as top 2 rated
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p7', 'p2']
        assert message == "Berikut produk terbaik berdasarkan rating:"

    # Scenario 2: User asks for "terbaik" in a specific category
    def test_smart_search_best_in_category_found(self, local_product_service_instance_with_mocked_load):
        """Test smart search for 'best' products in an existing category."""
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="smartphone terbaik", category="Smartphone", limit=2)
        # Smartphones in order of rating: p7 (4.9), p1 (4.5), p6 (3.9)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p7', 'p1']
        assert message == "Berikut Smartphone terbaik berdasarkan rating:"

    def test_smart_search_best_in_category_not_found_fallback_general(self, local_product_service_instance_with_mocked_load):
        """Test smart search for 'best' in non-existent category, fallback to general best."""
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="gadget terbaik", category="NonExistentCategory", limit=2)
        # Should fallback to general best: p7 (4.9), p2 (4.8)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p7', 'p2']
        assert message == "Tidak ada produk kategori NonExistentCategory, berikut produk terbaik secara umum:"

    # Scenario 3: All criteria met (keyword, category, max_price)
    def test_smart_search_all_criteria_met(self, local_product_service_instance_with_mocked_load):
        """Test smart search where keyword, category, and max_price all match."""
        # Products that are "phone", "Smartphone", and <= 10,000,000:
        # p1 (Test Phone, 10M, Smartphone) - matches all
        # p6 (Budget Phone, 1.5M, Smartphone) - matches all
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="phone", category="Smartphone", max_price=10000000, limit=5)
        assert len(products) == 2
        # Order is based on original list for exact matches in the main filter
        assert [p['id'] for p in products] == ['p1', 'p6']
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    # Scenario 4: No exact match, fallback to same category (without price/keyword filtering)
    def test_smart_search_no_exact_match_fallback_category(self, local_product_service_instance_with_mocked_load):
        """
        Test smart search fallback to products in the same category if no exact match
        for the given keyword/price filters.
        """
        # "xyz" is a non-matching keyword, max_price is too low for any product.
        # Fallback to products in "Smartphone" category, sorted by price (ascending) as per code.
        # Smartphones: p6 (1.5M), p1 (10M), p7 (25M)
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="xyz", category="Smartphone", max_price=100000, limit=2)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p6', 'p1']
        assert message == "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."

    # Scenario 5: No category match, fallback to products within budget
    def test_smart_search_no_category_fallback_budget(self, local_product_service_instance_with_mocked_load):
        """
        Test smart search fallback to products within budget if no specific category match
        or full criteria match.
        """
        # "nonexistent" is a non-matching keyword, "NonExistentCategory" is a non-existent category.
        # max_price = 5,000,000.
        # Products <= 5M: p3 (2M), p4 (5M), p5 (3M), p6 (1.5M)
        # Order is based on original list order for the filtered set.
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="nonexistent", category="NonExistentCategory", max_price=5000000, limit=3)
        assert len(products) == 3
        # Expected: p3, p4, p5 (first three from the list of products <=5M as per original TRANSFORMED_TEST_PRODUCTS order)
        assert [p['id'] for p in products] == ['p3', 'p4', 'p5']
        assert message == "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda."

    # Scenario 6: No match at all, fallback to best-selling/popular products
    def test_smart_search_no_match_fallback_popular(self, local_product_service_instance_with_mocked_load):
        """Test smart search fallback to best-selling products if no other match."""
        # No keyword match, no category, no price filter that yields results.
        # Falls back to popular products (sorted by 'sold' count).
        # Since 'sold' is mocked to 500 for all, original order is maintained for 'best-selling'.
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="really unique xyz product", category="FakeCat", max_price=100, limit=2)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p1', 'p2']
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_only_category_provided(self, local_product_service_instance_with_mocked_load):
        """Test smart search with only category provided, no keyword or price."""
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(category="Laptop", limit=1)
        assert len(products) == 1
        assert products[0]['id'] == 'p2'
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_only_max_price_provided(self, local_product_service_instance_with_mocked_load):
        """Test smart search with only max_price provided, no keyword or category."""
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(max_price=3000000, limit=2)
        # Products <= 3M: p3 (2M), p5 (3M), p6 (1.5M).
        # In this specific case, the `results` list (from general filter) will contain these products in their original order.
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p3', 'p5']
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."

    def test_smart_search_no_parameters(self, local_product_service_instance_with_mocked_load):
        """Test smart search with no parameters (should fallback to popular products)."""
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(limit=2)
        assert len(products) == 2
        assert [p['id'] for p in products] == ['p1', 'p2'] # Based on default sold 500
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_with_empty_products_list(self, local_product_service_instance_with_mocked_load, mocker):
        """
        Test smart search when the internal products list is empty.
        Should return an empty list and the popular fallback message.
        """
        mocker.patch.object(local_product_service_instance_with_mocked_load, 'products', [])
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="any", category="any", max_price=1000)
        assert products == []
        assert message == "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler."

    def test_smart_search_specific_keyword_no_other_filter(self, local_product_service_instance_with_mocked_load):
        """Test smart search with just a keyword, no category or price."""
        products, message = local_product_service_instance_with_mocked_load.smart_search_products(keyword="phone", limit=3)
        # Products with "phone" in name: p1, p6, p7.
        # Order is based on original list (no other filtering or specific sorting criteria met).
        assert len(products) == 3
        assert [p['id'] for p in products] == ['p1', 'p6', 'p7']
        assert message == "Berikut produk yang sesuai dengan kriteria Anda."