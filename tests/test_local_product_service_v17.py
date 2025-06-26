import pytest
import json
import logging
from unittest.mock import mock_open, patch
from pathlib import Path
import random

# Import the class under test
from app.services.local_product_service import LocalProductService

# --- Fixtures ---

@pytest.fixture
def mock_products_data():
    """Sample raw product data as it would appear in products.json."""
    return {
        "products": [
            {
                "id": "prod1",
                "name": "Smartphone A",
                "category": "Electronics",
                "brand": "BrandX",
                "price": 10000000,
                "currency": "IDR",
                "description": "A great smartphone.",
                "specifications": {"rating": 4.5, "stock_count": 50},
                "availability": "in_stock",
                "reviews_count": 100,
            },
            {
                "id": "prod2",
                "name": "Laptop B",
                "category": "Electronics",
                "brand": "BrandY",
                "price": 15000000,
                "currency": "IDR",
                "description": "Powerful laptop for professionals.",
                "specifications": {"rating": 4.8, "stock_count": 30},
                "availability": "in_stock",
                "reviews_count": 150,
            },
            {
                "id": "prod3",
                "name": "Headphones C",
                "category": "Audio",
                "brand": "BrandX",
                "price": 2000000,
                "currency": "IDR",
                "description": "Noise cancelling headphones.",
                "specifications": {"rating": 4.0, "stock_count": 100},
                "availability": "in_stock",
                "reviews_count": 50,
            },
            {
                "id": "prod4",
                "name": "Smartwatch D",
                "category": "Wearables",
                "brand": "BrandZ",
                "price": 3000000,
                "currency": "IDR",
                "description": "Feature-rich smartwatch.",
                "specifications": {"rating": 4.2, "stock_count": 20},
                "availability": "in_stock",
                "reviews_count": 70,
            },
            {
                "id": "prod5",
                "name": "Smartphone E (Murah)",
                "category": "Electronics",
                "brand": "BrandW",
                "price": 1500000,
                "currency": "IDR",
                "description": "Affordable smartphone.",
                "specifications": {"rating": 3.9, "stock_count": 200},
                "availability": "in_stock",
                "reviews_count": 200,
            },
            # Products for specific edge cases or sold count testing
            {
                "id": "prod6",
                "name": "Product without category",
                "brand": "NoBrand",
                "price": 100000,
                "specifications": {"rating": 0, "stock_count": 10, "sold": 75}, # Explicit sold
                "reviews_count": 0,
            },
            {
                "id": "prod7",
                "name": "Product with no specs or rating or brand or category",
                "price": 50000,
            },
            {
                "id": "prod8",
                "name": "Product for Sold Testing - High Sold",
                "category": "Audio",
                "brand": "BrandX",
                "price": 1000000,
                "specifications": {"rating": 4.1, "sold": 500},
            },
            {
                "id": "prod9",
                "name": "Another Product for Sold Testing - Highest Sold",
                "category": "Audio",
                "brand": "BrandY",
                "price": 1200000,
                "specifications": {"rating": 4.3, "sold": 1500},
            },
        ]
    }

@pytest.fixture
def mock_transformed_products(mock_products_data):
    """
    Returns the expected structure of products after transformation by _load_local_products.
    Ensures a consistent 'sold' value (100) for products where not explicitly defined in raw data.
    """
    transformed = []
    for product in mock_products_data['products']:
        # Ensure sold count is predictable. Use explicit sold, else default 100 (matching random.randint mock)
        sold_count = product.get('specifications', {}).get('sold', 100)
        
        transformed_product = {
            "id": product.get('id', ''),
            "name": product.get('name', ''),
            "category": product.get('category', ''),
            "brand": product.get('brand', ''),
            "price": product.get('price', 0),
            "currency": product.get('currency', 'IDR'),
            "description": product.get('description', ''),
            "specifications": {
                "rating": product.get('specifications', {}).get('rating', 0),
                "sold": sold_count,
                "stock": product.get('specifications', {}).get('stock_count', 0),
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
def mock_local_product_service(mocker, mock_transformed_products):
    """
    Provides a LocalProductService instance where _load_local_products is mocked
    to return a predefined set of transformed products.
    Also mocks random.randint for consistent 'sold' values.
    """
    mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_transformed_products)
    mocker.patch("random.randint", return_value=100) # Ensures consistent 'sold' values for new instances
    service = LocalProductService()
    return service

@pytest.fixture
def mock_local_product_service_empty(mocker):
    """
    Provides a LocalProductService instance with an empty product list.
    """
    mocker.patch.object(LocalProductService, '_load_local_products', return_value=[])
    mocker.patch("random.randint", return_value=100)
    service = LocalProductService()
    return service

@pytest.fixture
def setup_mock_product_file(mocker, tmp_path):
    """
    Fixture to mock `Path(__file__).parent.parent.parent` to `tmp_path`,
    so that `LocalProductService._load_local_products` looks for `products.json`
    within `tmp_path/data/`.
    Yields the actual `Path` object for the temporary `products.json` file.
    """
    # Create the expected temporary directory structure
    temp_root_dir = tmp_path
    temp_data_dir = temp_root_dir / "data"
    temp_data_dir.mkdir(exist_ok=True)
    temp_json_path = temp_data_dir / "products.json"

    # Mock the Path class constructor to control the `current_dir` resolution
    # This mock ensures that `Path(__file__).parent.parent.parent` resolves to `temp_root_dir`
    mock_path_class = mocker.patch('app.services.local_product_service.Path', autospec=True)
    
    # Configure the mocked Path(__file__) object chain
    mock_file_path_obj = mocker.MagicMock(spec=Path) # Represents Path(__file__)
    mock_file_path_obj.parent.parent.parent.return_value = temp_root_dir # Represents `current_dir`

    # Set `side_effect` for the mocked Path constructor
    # If `Path(__file__)` is called, return our mock chain. Otherwise, use real Path for other operations (like in tests)
    mock_path_class.side_effect = lambda path_str: mock_file_path_obj if path_str == __file__ else Path(path_str)

    yield temp_json_path # Yield the actual Path object for the temporary file

# --- Test Cases ---

class TestLocalProductService:

    def test_init_success(self, mocker, mock_transformed_products, caplog):
        """Test __init__ successfully loads products."""
        with caplog.at_level(logging.INFO):
            mocker.patch.object(LocalProductService, '_load_local_products', return_value=mock_transformed_products)
            mocker.patch("random.randint", return_value=100) # Ensure random.randint is mocked for init
            service = LocalProductService()
            assert service.products == mock_transformed_products
            assert f"Loaded {len(mock_transformed_products)} local products from JSON file" in caplog.text

    def test_init_load_error_falls_back(self, mocker, caplog):
        """Test __init__ falls back to default products if _load_local_products fails."""
        with caplog.at_level(logging.ERROR):
            mocker.patch.object(LocalProductService, '_load_local_products', side_effect=Exception("Simulated load error"))
            mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback_prod"}])
            mocker.patch("random.randint", return_value=100) # Ensure random.randint is mocked for init
            service = LocalProductService()
            assert service.products == [{"id": "fallback_prod"}]
            assert "Simulated load error" in caplog.text
            assert "Loaded 1 local products from JSON file" in caplog.text # Log from __init__

    # --- Test _load_local_products ---

    def test_load_local_products_success_utf8(self, mocker, mock_products_data, mock_transformed_products, caplog, setup_mock_product_file):
        """Test _load_local_products loads a valid JSON file with utf-8 encoding."""
        # Arrange
        temp_json_path = setup_mock_product_file
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            json.dump(mock_products_data, f)

        mocker.patch('random.randint', return_value=100) # Consistent 'sold' value

        # Act
        service = LocalProductService() # This will call _load_local_products internally
        products = service.products

        # Assert
        assert products is not None
        assert len(products) == len(mock_products_data['products'])
        # Verify transformation (checking a few keys from first product)
        assert products[0]['id'] == 'prod1'
        assert products[0]['specifications']['rating'] == 4.5
        assert 'sold' in products[0]['specifications']
        assert products[0]['specifications']['sold'] == 100 # From mocked random.randint
        assert products[0]['images'] == [f"https://example.com/prod1.jpg"]
        assert products[0]['url'] == f"https://shopee.co.id/prod1"
        with caplog.at_level(logging.INFO):
            # Re-initialize to trigger logging specific to _load_local_products
            LocalProductService()
            assert f"Successfully loaded {len(mock_transformed_products)} products from JSON file using utf-8 encoding" in caplog.text

    def test_load_local_products_file_not_found(self, mocker, caplog, setup_mock_product_file):
        """Test _load_local_products when JSON file does not exist."""
        # The file is not created by setup_mock_product_file, so Path.exists() will be naturally False
        temp_json_path = setup_mock_product_file # This ensures the mock Path setup is active
        
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback"}])
        mocker.patch("random.randint", return_value=100)

        with caplog.at_level(logging.ERROR):
            service = LocalProductService()
            products = service.products
            assert products == [{"id": "fallback"}]
            assert "Products JSON file not found" in caplog.text
            assert "Using fallback products" in caplog.text # Log from _get_fallback_products

    @pytest.mark.parametrize("encoding, bom", [
        ('utf-16-le', b'\xff\xfe'),
        ('utf-16', b'\xff\xfe'),
        ('utf-8-sig', b'\xef\xbb\xbf'),
    ])
    def test_load_local_products_different_encodings_and_bom(self, mocker, mock_products_data, mock_transformed_products, encoding, bom, caplog, setup_mock_product_file):
        """Test _load_local_products handles different encodings and BOM."""
        temp_json_path = setup_mock_product_file
        json_content = json.dumps(mock_products_data, ensure_ascii=False)
        
        with open(temp_json_path, 'wb') as f: # Write as bytes to include BOM
            f.write(bom + json_content.encode(encoding))

        mocker.patch('random.randint', return_value=100) # Consistent 'sold' value

        service = LocalProductService()
        products = service.products

        assert products is not None
        assert len(products) == len(mock_transformed_products)
        assert products[0]['id'] == 'prod1'
        with caplog.at_level(logging.INFO):
            # Re-initialize to capture the specific success log
            LocalProductService()
            assert f"Successfully loaded {len(mock_transformed_products)} products from JSON file using {encoding} encoding" in caplog.text

    def test_load_local_products_malformed_json(self, mocker, caplog, setup_mock_product_file):
        """Test _load_local_products handles malformed JSON."""
        temp_json_path = setup_mock_product_file
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            f.write("{invalid json]") # Malformed JSON

        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback"}])
        mocker.patch("random.randint", return_value=100)

        with caplog.at_level(logging.WARNING):
            service = LocalProductService()
            products = service.products
            assert products == [{"id": "fallback"}]
            assert "Failed to load with utf-16-le encoding" in caplog.text
            assert "Failed to load with utf-8 encoding" in caplog.text # utf-8 is also tried
            assert "All encoding attempts failed, using fallback products" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_load_local_products_empty_json_file(self, mocker, caplog, setup_mock_product_file):
        """Test _load_local_products handles an empty JSON file."""
        temp_json_path = setup_mock_product_file
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            f.write("") # Empty file

        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback"}])
        mocker.patch("random.randint", return_value=100)

        with caplog.at_level(logging.WARNING):
            service = LocalProductService()
            products = service.products
            assert products == [{"id": "fallback"}]
            assert "Failed to load with utf-16-le encoding" in caplog.text
            assert "All encoding attempts failed, using fallback products" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

    def test_load_local_products_json_missing_products_key(self, mocker, caplog, setup_mock_product_file):
        """Test _load_local_products when 'products' key is missing in JSON."""
        temp_json_path = setup_mock_product_file
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            json.dump({"other_key": []}, f) # Missing 'products' key

        mocker.patch('random.randint', return_value=100)

        with caplog.at_level(logging.INFO):
            service = LocalProductService()
            products = service.products
            assert products == [] # Should return an empty list of products
            assert "Successfully loaded 0 products from JSON file using utf-8 encoding" in caplog.text

    def test_load_local_products_general_exception(self, mocker, caplog, setup_mock_product_file):
        """Test _load_local_products handles a general exception during file operations."""
        # Simulate an exception when trying to open the file
        mocker.patch('builtins.open', side_effect=IOError("Permission denied"))
        mocker.patch.object(LocalProductService, '_get_fallback_products', return_value=[{"id": "fallback"}])
        mocker.patch("random.randint", return_value=100)

        with caplog.at_level(logging.ERROR):
            service = LocalProductService()
            products = service.products
            assert products == [{"id": "fallback"}]
            assert "Error loading products from JSON file: Permission denied" in caplog.text
            assert "Using fallback products due to JSON file loading error" in caplog.text

    # --- Test _get_fallback_products ---
    def test_get_fallback_products(self, caplog):
        """Test _get_fallback_products returns a non-empty list of dicts."""
        # Initialize LocalProductService to have access to its methods
        service = LocalProductService() 
        # To isolate _get_fallback_products, we can temporarily clear products if needed,
        # but for simple return value check, direct call is fine.
        
        with caplog.at_level(logging.WARNING):
            fallback_products = service._get_fallback_products()
            assert isinstance(fallback_products, list)
            assert len(fallback_products) > 0
            assert all(isinstance(p, dict) for p in fallback_products)
            assert "Using fallback products due to JSON file loading error" in caplog.text

    # --- Test search_products ---
    def test_search_products_by_name(self, mock_local_product_service):
        """Test searching products by name."""
        results = mock_local_product_service.search_products("smartphone A")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'
        assert "Smartphone A" in results[0]['name']

    def test_search_products_case_insensitive(self, mock_local_product_service):
        """Test searching products case-insensitively."""
        results = mock_local_product_service.search_products("smartphone a")
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'

    def test_search_products_by_category(self, mock_local_product_service):
        """Test searching products by category."""
        results = mock_local_product_service.search_products("Audio")
        assert len(results) == 2 # Headphones C, Product for Sold Testing
        assert any(p['id'] == 'prod3' for p in results)
        assert any(p['id'] == 'prod8' for p in results)

    def test_search_products_by_brand(self, mock_local_product_service):
        """Test searching products by brand."""
        results = mock_local_product_service.search_products("BrandX")
        assert len(results) == 2
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod3' for p in results)

    def test_search_products_by_description(self, mock_local_product_service):
        """Test searching products by description."""
        results = mock_local_product_service.search_products("powerful laptop")
        assert len(results) == 1
        assert results[0]['id'] == 'prod2'

    def test_search_products_by_specifications_content(self, mock_local_product_service):
        """Test searching products by specifications content (e.g., specific stock count)."""
        # Note: specifications are converted to string for search
        results = mock_local_product_service.search_products("stock_count': 50")
        assert len(results) >= 1
        assert any(p['id'] == 'prod1' for p in results) # Smartphone A has stock_count 50

    def test_search_products_no_match(self, mock_local_product_service):
        """Test searching with no matching products."""
        results = mock_local_product_service.search_products("nonexistent_product")
        assert len(results) == 0

    def test_search_products_empty_keyword_returns_all(self, mock_local_product_service, mock_transformed_products):
        """Test searching with an empty keyword returns all products up to limit."""
        results = mock_local_product_service.search_products("", limit=100)
        assert len(results) == len(mock_transformed_products) # Should return all available mocked products

    def test_search_products_limit(self, mock_local_product_service):
        """Test the limit parameter for search_products."""
        results = mock_local_product_service.search_products("Smartphone", limit=1)
        assert len(results) == 1
        # Due to relevance sorting (name match), 'Smartphone A' should be first.
        assert results[0]['id'] == 'prod1'

    def test_search_products_with_price_keyword_juta(self, mock_local_product_service):
        """Test searching with a 'juta' price keyword."""
        results = mock_local_product_service.search_products("smartphone 12 juta")
        # prod1 (10jt), prod5 (1.5jt) should match the 'smartphone' keyword and price <= 12jt
        assert len(results) == 2
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod5' for p in results)
        # Check sorting by price for budget search (lower price preferred)
        assert results[0]['price'] == 1500000 # Prod5
        assert results[1]['price'] == 10000000 # Prod1

    def test_search_products_with_price_keyword_ribu(self, mock_local_product_service):
        """Test searching with a 'ribu' price keyword."""
        results = mock_local_product_service.search_products("barang 500 ribu")
        # '500 ribu' -> 500000. prod6 (100rb), prod7 (50rb) should match price
        # Sorted by price, lowest first for budget.
        assert len(results) == 2
        assert results[0]['id'] == 'prod7' # 50,000
        assert results[1]['id'] == 'prod6' # 100,000

    def test_search_products_with_budget_keyword_and_match(self, mock_local_product_service):
        """Test searching with a 'budget' keyword, and an actual product match."""
        results = mock_local_product_service.search_products("smartphone murah")
        # 'murah' -> 5,000,000. prod5 (1.5jt) is only smartphone below 5M.
        # Prod3 (2jt), Prod4 (3jt) also match price constraint.
        assert len(results) == 3 
        assert any(p['id'] == 'prod5' for p in results)
        assert any(p['id'] == 'prod3' for p in results)
        assert any(p['id'] == 'prod4' for p in results)
        # Prod5 (1.5jt) should be highest score due to exact match + low price preference
        assert results[0]['id'] == 'prod5'

    def test_search_products_relevance_sorting_exact_name_match(self, mock_local_product_service):
        """Test relevance sorting prioritizes exact name matches."""
        # 'BrandX' is in name of prod1 (Smartphone A, BrandX) and brand of prod3 (Headphones C, BrandX)
        results = mock_local_product_service.search_products("BrandX")
        # Prod1 should be first because 'BrandX' is in its name.
        assert results[0]['id'] == 'prod1'
        assert results[1]['id'] == 'prod3'

    def test_search_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test search_products error handling."""
        mocker.patch.object(mock_local_product_service, '_extract_price_from_keyword', side_effect=Exception("Price extract error"))
        with caplog.at_level(logging.ERROR):
            results = mock_local_product_service.search_products("test")
            assert results == []
            assert "Error searching products: Price extract error" in caplog.text


    # --- Test _extract_price_from_keyword ---
    @pytest.mark.parametrize("keyword, expected_price", [
        ("smartphone 5 juta", 5000000),
        ("laptop 10juta", 10000000),
        ("hp 2jt", 2000000),
        ("earphone 500 ribu", 500000),
        ("charger 20rb", 20000),
        ("rp 150000", 150000),
        ("120000 rp", 120000),
        ("monitor 3.5 juta", None), # Should not match floating point
        ("mouse 10k", 10000),
        ("tv 2m", 2000000),
        ("kamera murah", 5000000),
        ("aksesoris budget", 5000000),
        ("printer hemat", 3000000),
        ("router terjangkau", 4000000),
        ("speaker ekonomis", 2000000),
        ("headset", None), # No price keyword
        ("iphone 12345678", None), # Just numbers without price unit
        ("", None), # Empty keyword
        (" ", None) # Whitespace keyword
    ])
    def test_extract_price_from_keyword_valid_patterns(self, mock_local_product_service, keyword, expected_price):
        """Test _extract_price_from_keyword with various valid price patterns."""
        price = mock_local_product_service._extract_price_from_keyword(keyword)
        assert price == expected_price

    def test_extract_price_from_keyword_no_match(self, mock_local_product_service):
        """Test _extract_price_from_keyword when no price pattern matches."""
        price = mock_local_product_service._extract_price_from_keyword("some random text")
        assert price is None

    def test_extract_price_from_keyword_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test _extract_price_from_keyword error handling."""
        mocker.patch('re.search', side_effect=Exception("Simulated regex error"))
        with caplog.at_level(logging.ERROR):
            price = mock_local_product_service._extract_price_from_keyword("10 juta")
            assert price is None
            assert "Error extracting price from keyword: Simulated regex error" in caplog.text


    # --- Test get_product_details ---
    def test_get_product_details_existing_id(self, mock_local_product_service):
        """Test getting details for an existing product ID."""
        product = mock_local_product_service.get_product_details("prod1")
        assert product is not None
        assert product['id'] == 'prod1'
        assert product['name'] == 'Smartphone A'

    def test_get_product_details_non_existing_id(self, mock_local_product_service):
        """Test getting details for a non-existing product ID."""
        product = mock_local_product_service.get_product_details("nonexistent_id")
        assert product is None

    def test_get_product_details_empty_id(self, mock_local_product_service):
        """Test getting details for an empty product ID."""
        product = mock_local_product_service.get_product_details("")
        assert product is None

    def test_get_product_details_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test get_product_details error handling."""
        # Temporarily break product iteration by making `self.products` raise an error
        mocker.patch.object(mock_local_product_service, 'products', new_callable=mocker.PropertyMock, side_effect=Exception("Product list error"))
        with caplog.at_level(logging.ERROR):
            product = mock_local_product_service.get_product_details("prod1")
            assert product is None
            assert "Error getting product details: Product list error" in caplog.text

    # --- Test get_categories ---
    def test_get_categories(self, mock_local_product_service):
        """Test getting unique sorted categories."""
        categories = mock_local_product_service.get_categories()
        # 'Electronics', 'Audio', 'Wearables', '' (for prod6, prod7 which lack explicit categories)
        expected_categories = sorted(['Electronics', 'Audio', 'Wearables', ''])
        assert categories == expected_categories

    def test_get_categories_no_products(self, mock_local_product_service_empty):
        """Test getting categories when there are no products."""
        categories = mock_local_product_service_empty.get_categories()
        assert categories == []

    # --- Test get_brands ---
    def test_get_brands(self, mock_local_product_service):
        """Test getting unique sorted brands."""
        brands = mock_local_product_service.get_brands()
        # 'BrandX', 'BrandY', 'BrandZ', 'BrandW', 'NoBrand', '' (for prod7 which lacks explicit brand)
        expected_brands = sorted(['BrandX', 'BrandY', 'BrandZ', 'BrandW', 'NoBrand', ''])
        assert brands == expected_brands

    def test_get_brands_no_products(self, mock_local_product_service_empty):
        """Test getting brands when there are no products."""
        brands = mock_local_product_service_empty.get_brands()
        assert brands == []

    # --- Test get_products_by_category ---
    def test_get_products_by_category_existing(self, mock_local_product_service):
        """Test getting products by an existing category."""
        products = mock_local_product_service.get_products_by_category("electronics")
        assert len(products) == 3
        assert all('electronics' in p['category'].lower() for p in products)
        assert any(p['id'] == 'prod1' for p in products)
        assert any(p['id'] == 'prod2' for p in products)
        assert any(p['id'] == 'prod5' for p in products)

    def test_get_products_by_category_non_existing(self, mock_local_product_service):
        """Test getting products by a non-existing category."""
        products = mock_local_product_service.get_products_by_category("nonexistent")
        assert len(products) == 0

    def test_get_products_by_category_empty_string(self, mock_local_product_service):
        """Test getting products by an empty category string (should match products with no category explicitly set)."""
        products = mock_local_product_service.get_products_by_category("")
        assert len(products) == 2 # prod6, prod7
        assert any(p['id'] == 'prod6' for p in products)
        assert any(p['id'] == 'prod7' for p in products)

    def test_get_products_by_category_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test get_products_by_category error handling."""
        mocker.patch.object(mock_local_product_service, 'products', new_callable=mocker.PropertyMock, side_effect=Exception("Product list error"))
        with caplog.at_level(logging.ERROR):
            products = mock_local_product_service.get_products_by_category("Electronics")
            assert products == []
            assert "Error getting products by category: Product list error" in caplog.text

    # --- Test get_products_by_brand ---
    def test_get_products_by_brand_existing(self, mock_local_product_service):
        """Test getting products by an existing brand."""
        products = mock_local_product_service.get_products_by_brand("brandx")
        assert len(products) == 2
        assert all('brandx' in p['brand'].lower() for p in products)
        assert any(p['id'] == 'prod1' for p in products)
        assert any(p['id'] == 'prod3' for p in products)

    def test_get_products_by_brand_non_existing(self, mock_local_product_service):
        """Test getting products by a non-existing brand."""
        products = mock_local_product_service.get_products_by_brand("nonexistent")
        assert len(products) == 0

    def test_get_products_by_brand_empty_string(self, mock_local_product_service):
        """Test getting products by an empty brand string (should match products with no brand explicitly set)."""
        products = mock_local_product_service.get_products_by_brand("")
        assert len(products) == 1 # prod7 has no brand (empty string)
        assert any(p['id'] == 'prod7' for p in products)

    def test_get_products_by_brand_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test get_products_by_brand error handling."""
        mocker.patch.object(mock_local_product_service, 'products', new_callable=mocker.PropertyMock, side_effect=Exception("Product list error"))
        with caplog.at_level(logging.ERROR):
            products = mock_local_product_service.get_products_by_brand("BrandX")
            assert products == []
            assert "Error getting products by brand: Product list error" in caplog.text

    # --- Test get_top_rated_products ---
    def test_get_top_rated_products(self, mock_local_product_service):
        """Test getting top rated products."""
        # mock_transformed_products ratings: prod2(4.8), prod1(4.5), prod4(4.2), prod8(4.1), prod3(4.0), prod5(3.9), prod6(0), prod7(0)
        # Expected order (by rating then original order for tie-breaking by Python's stable sort):
        # prod2, prod1, prod4, prod8, prod3
        top_products = mock_local_product_service.get_top_rated_products(limit=5)
        assert len(top_products) == 5
        assert top_products[0]['id'] == 'prod2'
        assert top_products[1]['id'] == 'prod1'
        assert top_products[2]['id'] == 'prod4'
        assert top_products[3]['id'] == 'prod8'
        assert top_products[4]['id'] == 'prod3'

    def test_get_top_rated_products_limit_exceeds_total(self, mock_local_product_service, mock_transformed_products):
        """Test getting top rated products with limit greater than total products."""
        top_products = mock_local_product_service.get_top_rated_products(limit=100)
        assert len(top_products) == len(mock_transformed_products)

    def test_get_top_rated_products_no_products(self, mock_local_product_service_empty):
        """Test getting top rated products when there are no products."""
        top_products = mock_local_product_service_empty.get_top_rated_products(limit=5)
        assert len(top_products) == 0

    def test_get_top_rated_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test get_top_rated_products error handling."""
        mocker.patch.object(mock_local_product_service, 'products', new_callable=mocker.PropertyMock, side_effect=Exception("Product list error"))
        with caplog.at_level(logging.ERROR):
            top_products = mock_local_product_service.get_top_rated_products()
            assert top_products == []
            assert "Error getting top rated products: Product list error" in caplog.text

    # --- Test get_best_selling_products ---
    def test_get_best_selling_products(self, mock_local_product_service, caplog):
        """Test getting best selling products."""
        # mock_transformed_products 'sold' values:
        # prod9: 1500, prod8: 500, prod6: 75
        # All others: 100 (from random.randint mock in mock_transformed_products fixture itself)
        # Expected order by sold: prod9 (1500), prod8 (500), (then any of the products with sold=100), prod6 (75)
        best_selling = mock_local_product_service.get_best_selling_products(limit=5)
        assert len(best_selling) == 5
        assert best_selling[0]['id'] == 'prod9'
        assert best_selling[1]['id'] == 'prod8'
        # Check that the remaining three are products with 100 sold
        assert best_selling[2]['specifications']['sold'] == 100
        assert best_selling[3]['specifications']['sold'] == 100
        assert best_selling[4]['specifications']['sold'] == 100
        assert best_selling[0]['specifications']['sold'] == 1500
        assert best_selling[1]['specifications']['sold'] == 500
        with caplog.at_level(logging.INFO):
            mock_local_product_service.get_best_selling_products(limit=5)
            assert "Getting best selling products, limit: 5" in caplog.text
            assert "Returning 5 best selling products" in caplog.text


    def test_get_best_selling_products_limit_exceeds_total(self, mock_local_product_service, mock_transformed_products):
        """Test getting best selling products with limit greater than total products."""
        best_selling = mock_local_product_service.get_best_selling_products(limit=100)
        assert len(best_selling) == len(mock_transformed_products)

    def test_get_best_selling_products_no_products(self, mock_local_product_service_empty):
        """Test getting best selling products when there are no products."""
        best_selling = mock_local_product_service_empty.get_best_selling_products(limit=5)
        assert len(best_selling) == 0

    def test_get_best_selling_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test get_best_selling_products error handling."""
        mocker.patch.object(mock_local_product_service, 'products', new_callable=mocker.PropertyMock, side_effect=Exception("Product list error"))
        with caplog.at_level(logging.ERROR):
            best_selling = mock_local_product_service.get_best_selling_products()
            assert best_selling == []
            assert "Error getting best selling products: Product list error" in caplog.text


    # --- Test get_products ---
    def test_get_products(self, mock_local_product_service, mock_transformed_products, caplog):
        """Test getting all products with a limit."""
        products = mock_local_product_service.get_products(limit=2)
        assert len(products) == 2
        assert products == mock_transformed_products[:2]
        with caplog.at_level(logging.INFO):
            mock_local_product_service.get_products(limit=2)
            assert "Getting all products, limit: 2" in caplog.text

    def test_get_products_limit_exceeds_total(self, mock_local_product_service, mock_transformed_products):
        """Test getting all products when limit exceeds total."""
        products = mock_local_product_service.get_products(limit=100)
        assert len(products) == len(mock_transformed_products)
        assert products == mock_transformed_products

    def test_get_products_no_products(self, mock_local_product_service_empty):
        """Test getting all products when there are no products."""
        products = mock_local_product_service_empty.get_products(limit=5)
        assert len(products) == 0

    def test_get_products_error_handling(self, mock_local_product_service, mocker, caplog):
        """Test get_products error handling."""
        mocker.patch.object(mock_local_product_service, 'products', new_callable=mocker.PropertyMock, side_effect=Exception("Product list error"))
        with caplog.at_level(logging.ERROR):
            products = mock_local_product_service.get_products()
            assert products == []
            assert "Error getting products: Product list error" in caplog.text

    # --- Test smart_search_products ---
    def test_smart_search_products_best_no_category(self, mock_local_product_service):
        """Test smart_search for 'terbaik' without specific category."""
        # Expected: top rated products (prod2, prod1, prod4, prod8, prod3)
        results, message = mock_local_product_service.smart_search_products(keyword="produk terbaik", limit=3)
        assert len(results) == 3
        assert results[0]['id'] == 'prod2' # Rating 4.8
        assert results[1]['id'] == 'prod1' # Rating 4.5
        assert "Berikut produk terbaik berdasarkan rating" in message

    def test_smart_search_products_best_with_existing_category(self, mock_local_product_service):
        """Test smart_search for 'terbaik' with an existing category."""
        # Electronics: prod2(4.8), prod1(4.5), prod5(3.9)
        results, message = mock_local_product_service.smart_search_products(keyword="terbaik", category="Electronics", limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'prod2'
        assert results[1]['id'] == 'prod1'
        assert "Berikut Electronics terbaik berdasarkan rating:" in message

    def test_smart_search_products_best_with_non_existing_category_fallback(self, mock_local_product_service):
        """Test smart_search for 'terbaik' with non-existing category, falling back to general best."""
        # Expected: fallback to general top rated
        results, message = mock_local_product_service.smart_search_products(keyword="terbaik", category="Furniture", limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'prod2'
        assert results[1]['id'] == 'prod1'
        assert "Tidak ada produk kategori Furniture, berikut produk terbaik secara umum:" in message

    def test_smart_search_products_exact_match_all_criteria(self, mock_local_product_service):
        """Test smart_search with exact match on keyword, category, and max_price."""
        # prod1: Smartphone A, Electronics, 10M
        results, message = mock_local_product_service.smart_search_products(
            keyword="Smartphone A", category="Electronics", max_price=10000000, limit=1
        )
        assert len(results) == 1
        assert results[0]['id'] == 'prod1'
        assert "Berikut produk yang sesuai dengan kriteria Anda." in message

    def test_smart_search_products_no_exact_match_fallback_category(self, mock_local_product_service):
        """Test smart_search fallback to category match only (no keyword/price match)."""
        # Keyword "XYZ" doesn't match, but category "Electronics" exists. Max_price too low for most electronics.
        # This should trigger fallback 4: "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut."
        results, message = mock_local_product_service.smart_search_products(
            keyword="NonExistentProduct", category="Electronics", max_price=100, limit=2
        )
        assert len(results) == 3 # All electronics products
        assert results[0]['id'] == 'prod5' # Cheapest electronics (1.5M)
        assert "Tidak ada produk di bawah budget, berikut produk termurah di kategori tersebut." in message
        assert results[0]['price'] == 1500000

    def test_smart_search_products_no_exact_match_fallback_price(self, mock_local_product_service):
        """Test smart_search fallback to price match only (no keyword/category match)."""
        # Keyword "XYZ" and category "ABC" don't match, but max_price=2M matches prod3 (2M), prod5 (1.5M), prod6 (0.1M), prod7 (0.05M)
        results, message = mock_local_product_service.smart_search_products(
            keyword="Random", category="NonCategory", max_price=2000000, limit=4
        )
        assert len(results) == 4
        assert any(p['id'] == 'prod3' for p in results)
        assert any(p['id'] == 'prod5' for p in results)
        assert any(p['id'] == 'prod6' for p in results)
        assert any(p['id'] == 'prod7' for p in results)
        assert "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda." in message

    def test_smart_search_products_no_match_fallback_popular(self, mock_local_product_service):
        """Test smart_search fallback to popular products when no criteria match."""
        results, message = mock_local_product_service.smart_search_products(
            keyword="CompletelyUnique", category="DoesNotExist", max_price=10, limit=2
        )
        assert len(results) == 2
        assert results[0]['id'] == 'prod9' # Best selling (1500)
        assert results[1]['id'] == 'prod8' # Next best selling (500)
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message

    def test_smart_search_products_empty_inputs(self, mock_local_product_service):
        """Test smart_search with all empty inputs."""
        # Should return popular products by default (as nothing else is specified)
        results, message = mock_local_product_service.smart_search_products(limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'prod9'
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message

    def test_smart_search_products_no_products_available(self, mock_local_product_service_empty):
        """Test smart_search when no products are loaded at all."""
        results, message = mock_local_product_service_empty.smart_search_products(keyword="test", limit=2)
        assert len(results) == 0
        # The message is generated even if results are empty, which aligns with the code.
        assert "Tidak ada produk yang sesuai, berikut rekomendasi produk terpopuler." in message

    def test_smart_search_products_combined_keyword_category(self, mock_local_product_service):
        """Test smart_search with combined keyword and category."""
        # Search for "phone" in "Electronics"
        results, message = mock_local_product_service.smart_search_products(keyword="phone", category="Electronics", limit=10)
        assert len(results) == 2 # Smartphone A, Smartphone E
        assert any(p['id'] == 'prod1' for p in results)
        assert any(p['id'] == 'prod5' for p in results)
        assert "Berikut produk yang sesuai dengan kriteria Anda." in message

    def test_smart_search_products_combined_keyword_price_no_match_then_fallback(self, mock_local_product_service):
        """Test smart_search with combined keyword and price where initial match fails, then falls back to price."""
        # Search for "laptop" under 2M. Laptop B is 15M, so no exact match for "laptop" under 2M.
        # Fallback chain:
        # 1-3. No exact match.
        # 4. No category provided.
        # 5. Max_price provided, filter by price. (prod3, prod5, prod6, prod7 are all <= 2M)
        results, message = mock_local_product_service.smart_search_products(keyword="laptop", max_price=2000000, limit=4)
        assert len(results) == 4
        # Should contain products under 2M. Order by original order from the mock list.
        assert results[0]['id'] == 'prod3' # Headphones C (2M)
        assert results[1]['id'] == 'prod5' # Smartphone E (1.5M)
        assert results[2]['id'] == 'prod6' # Product without category (0.1M)
        assert results[3]['id'] == 'prod7' # Product with no specs (0.05M)
        assert "Tidak ada produk di kategori tersebut, berikut produk lain yang sesuai budget Anda." in message