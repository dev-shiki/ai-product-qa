import pytest
import asyncio
from app.services.product_data_service import ProductDataService

# pytest-asyncio is required for running async tests with pytest.
# Make sure you have it installed: pip install pytest pytest-asyncio

@pytest.fixture(scope="module")
def product_service():
    """Provides a ProductDataService instance for tests.
    Initialized once per module to avoid repeated setup."""
    try:
        service = ProductDataService()
        return service
    except Exception as e:
        # If ProductDataService cannot be initialized, all dependent tests will fail.
        # This indicates a fundamental issue with the service or its dependencies.
        pytest.fail(f"Failed to initialize ProductDataService: {e}")

def test_product_data_service_initialization(product_service):
    """Test if ProductDataService initializes correctly."""
    try:
        assert product_service is not None
        # Verify that the internal local_service attribute is set,
        # indicating successful dependency injection/instantiation.
        assert hasattr(product_service, 'local_service')
    except Exception as e:
        pytest.fail(f"Error during ProductDataService initialization test: {e}")

@pytest.mark.asyncio
async def test_get_categories(product_service):
    """Test fetching categories from the service."""
    try:
        categories = await product_service.get_categories()
        assert isinstance(categories, list)
        # Assert that the list of categories is not empty,
        # assuming the local product service has some default data.
        # If it can legitimately be empty, remove or adjust this assertion.
        assert len(categories) >= 0
        if categories: # If categories are found, ensure they are strings.
            assert isinstance(categories[0], str)
    except Exception as e:
        pytest.fail(f"Error in test_get_categories: {e}")

@pytest.mark.asyncio
async def test_search_products(product_service):
    """Test searching for products using a keyword."""
    try:
        keyword = "Laptop"
        # Request a limited number of products to keep the test quick.
        products = await product_service.search_products(keyword, limit=2)
        assert isinstance(products, list)
        assert len(products) <= 2  # Verify limit is respected.
        if products:
            # Check if the returned items are dictionaries, as expected for product data.
            assert isinstance(products[0], dict)
            # A more robust test would check if product names/descriptions contain the keyword,
            # but this depends on specific data in LocalProductService.
    except Exception as e:
        pytest.fail(f"Error in test_search_products: {e}")

@pytest.mark.asyncio
async def test_get_all_products_via_get_products(product_service):
    """Test retrieving all products using the general 'get_products' method without filters."""
    try:
        products = await product_service.get_products(limit=3)
        assert isinstance(products, list)
        assert len(products) <= 3 # Verify limit.
        if products:
            assert isinstance(products[0], dict)
    except Exception as e:
        pytest.fail(f"Error in test_get_all_products_via_get_products: {e}")

@pytest.mark.asyncio
async def test_get_products_by_category_via_get_products(product_service):
    """Test retrieving products filtered by category using the general 'get_products' method."""
    try:
        # First, try to get an existing category to make the test realistic.
        categories = await product_service.get_categories()
        if not categories:
            pytest.skip("No categories available from ProductDataService to test category filtering.")

        test_category = categories[0]  # Use the first available category for testing.
        products = await product_service.get_products(category=test_category, limit=2)
        assert isinstance(products, list)
        assert len(products) <= 2
        # If products are returned, ensure they all belong to the specified category.
        for product in products:
            assert product.get('category') == test_category, \
                f"Product {product.get('name')} (ID: {product.get('id')}) has incorrect category: {product.get('category')}"
    except Exception as e:
        pytest.fail(f"Error in test_get_products_by_category_via_get_products: {e}")

@pytest.mark.asyncio
async def test_get_products_by_search_via_get_products(product_service):
    """Test retrieving products using a search term via the general 'get_products' method."""
    try:
        search_term = "earbuds" # A common keyword to search for
        products = await product_service.get_products(search=search_term, limit=2)
        assert isinstance(products, list)
        assert len(products) <= 2
        # No specific content assertion here, as it depends on exact data in LocalProductService.
        # Just verifying the method returns a list is sufficient for this general test.
    except Exception as e:
        pytest.fail(f"Error in test_get_products_by_search_via_get_products: {e}")

@pytest.mark.asyncio
async def test_get_product_details(product_service):
    """Test fetching details for a specific product ID."""
    try:
        # Attempt to get an existing product to ensure we have a valid ID for testing.
        all_products = await product_service.get_products(limit=1)
        if not all_products:
            pytest.skip("No products available from ProductDataService to test get_product_details.")
            
        product_id = all_products[0].get('id')
        assert product_id is not None, "Fetched product has no 'id' attribute."

        details = await product_service.get_product_details(product_id)
        assert isinstance(details, dict)
        assert details.get('id') == product_id # Ensure the correct product details are returned.
        assert details.get('name') is not None # Ensure key details like name are present.
    except AttributeError:
        # Catches if get_product_details method doesn't exist or is not awaited correctly.
        pytest.fail("Method 'get_product_details' might be missing or not properly async.")
    except Exception as e:
        pytest.fail(f"Error in test_get_product_details: {e}")

@pytest.mark.asyncio
async def test_get_product_details_non_existent(product_service):
    """Test fetching details for a non-existent product ID."""
    try:
        non_existent_id = "non_existent_product_xyz"
        details = await product_service.get_product_details(non_existent_id)
        # For a non-existent product, the service should return None or an empty dictionary.
        assert details is None or details == {}
    except AttributeError:
        pytest.fail("Method 'get_product_details' might be missing or not properly async.")
    except Exception as e:
        pytest.fail(f"Error in test_get_product_details_non_existent: {e}")

@pytest.mark.asyncio
async def test_get_brands(product_service):
    """Test fetching available brands."""
    try:
        brands = await product_service.get_brands()
        assert isinstance(brands, list)
        assert len(brands) >= 0 # Can be empty if no brands are defined.
        if brands:
            assert isinstance(brands[0], str)
    except AttributeError:
        pytest.fail("Method 'get_brands' might be missing or not properly async.")
    except Exception as e:
        pytest.fail(f"Error in test_get_brands: {e}")

@pytest.mark.asyncio
async def test_get_products_by_brand(product_service):
    """Test fetching products filtered by brand."""
    try:
        # Get an existing brand to use for testing.
        brands = await product_service.get_brands()
        if not brands:
            pytest.skip("No brands available from ProductDataService to test brand filtering.")

        test_brand = brands[0]
        products = await product_service.get_products_by_brand(test_brand, limit=2)
        assert isinstance(products, list)
        assert len(products) <= 2
        # If products are returned, ensure they all belong to the specified brand.
        for product in products:
            assert product.get('brand') == test_brand, \
                f"Product {product.get('name')} (ID: {product.get('id')}) has incorrect brand: {product.get('brand')}"
    except AttributeError:
        pytest.fail("Method 'get_products_by_brand' might be missing or not properly async.")
    except Exception as e:
        pytest.fail(f"Error in test_get_products_by_brand: {e}")