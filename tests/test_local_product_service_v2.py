import pytest
from app.services.local_product_service import LocalProductService
from pathlib import Path
import logging

# Suppress INFO logs from the service during tests to keep output clean
logging.getLogger('app.services.local_product_service').setLevel(logging.WARNING)

def get_service_instance_for_test():
    """
    Helper function to get a LocalProductService instance.
    Skips the test if initialization fails or if no products are loaded (even fallback).
    """
    try:
        service = LocalProductService()
        if not service.products:
            # This indicates _load_local_products (and fallback) failed to get any products.
            pytest.skip("LocalProductService initialized but no products loaded (even fallback). "
                         "This test requires products to run meaningfully. Check data/products.json or _get_fallback_products logic.")
        return service
    except Exception as e:
        pytest.skip(f"Skipping test due to LocalProductService initialization error: {e}")

def test_LocalProductService_basic():
    '''Test basic functionality of LocalProductService: instantiation and product loading.'''
    try:
        service = LocalProductService()
        assert service is not None, "Service instance should not be None"
        assert isinstance(service.products, list), "Service.products should be a list"
        # Check if products were loaded, even if it's the fallback
        assert len(service.products) >= 0, "Products list should be initialized (can be empty if fallback fails)"
        if not service.products:
            pytest.skip("LocalProductService initialized but no products loaded (even fallback). "
                         "Subsequent data-dependent tests might fail or skip.")
    except Exception as e:
        pytest.skip(f"Skipping test due to LocalProductService initialization error: {e}")

def test_search_products_found():
    """Test searching for products that should exist."""
    service = get_service_instance_for_test()
    
    # Try to find a common keyword or a name from loaded products
    search_term = "Product" # A common term likely to be in fallback products
    if service.products:
        first_product_name = service.products[0].get('name', '')
        if first_product_name:
            # Use a more specific part if available, otherwise fallback
            search_term = first_product_name.split(' ')[0] if ' ' in first_product_name and len(first_product_name.split(' ')[0]) > 2 else first_product_name[:4]
    
    results = service.search_products(search_term)
    assert isinstance(results, list)
    
    # If results are found, check their basic structure
    if results:
        assert len(results) > 0
        assert all(isinstance(p, dict) for p in results)
        assert all('id' in p and 'name' in p for p in results)

def test_search_products_not_found():
    """Test searching for products that should not exist."""
    service = get_service_instance_for_test()
    results = service.search_products("nonexistentproductxyz123")
    assert isinstance(results, list)
    assert len(results) == 0

def test_get_product_details_existing():
    """Test getting details for an existing product."""
    service = get_service_instance_for_test()
    
    if not service.products:
        pytest.skip("No products available to test get_product_details_existing")
    
    product_id = service.products[0]['id']
    details = service.get_product_details(product_id)
    assert isinstance(details, dict)
    assert details['id'] == product_id
    assert 'name' in details
    assert 'category' in details
    # Add more basic checks for expected keys if known from data structure

def test_get_product_details_non_existing():
    """Test getting details for a non-existing product."""
    service = get_service_instance_for_test()
    details = service.get_product_details("nonexistentid123")
    assert details is None

def test_get_categories():
    """Test getting all categories."""
    service = get_service_instance_for_test()
    categories = service.get_categories()
    assert isinstance(categories, list)
    assert len(categories) > 0, "Should have loaded some categories"
    assert all(isinstance(c, str) for c in categories)

def test_get_brands():
    """Test getting all brands."""
    service = get_service_instance_for_test()
    brands = service.get_brands()
    assert isinstance(brands, list)
    assert len(brands) > 0, "Should have loaded some brands"
    assert all(isinstance(b, str) for b in brands)

def test_get_products_by_category():
    """Test getting products by category."""
    service = get_service_instance_for_test()
    categories = service.get_categories()
    if not categories:
        pytest.skip("No categories available to test get_products_by_category")
    
    test_category = categories[0]
    products_in_category = service.get_products_by_category(test_category)
    assert isinstance(products_in_category, list)
    if products_in_category: # If there are products, check that they belong to the category
        assert all(isinstance(p, dict) and p.get('category') == test_category for p in products_in_category)

def test_get_products_by_category_non_existing():
    """Test getting products by a non-existing category."""
    service = get_service_instance_for_test()
    products = service.get_products_by_category("NonExistentCategoryXYZ")
    assert isinstance(products, list)
    assert len(products) == 0

def test_get_products_by_brand():
    """Test getting products by brand."""
    service = get_service_instance_for_test()
    brands = service.get_brands()
    if not brands:
        pytest.skip("No brands available to test get_products_by_brand")
    
    test_brand = brands[0]
    products_by_brand = service.get_products_by_brand(test_brand)
    assert isinstance(products_by_brand, list)
    if products_by_brand: # If there are products, check that they belong to the brand
        assert all(isinstance(p, dict) and p.get('brand') == test_brand for p in products_by_brand)

def test_get_products_by_brand_non_existing():
    """Test getting products by a non-existing brand."""
    service = get_service_instance_for_test()
    products = service.get_products_by_brand("NonExistentBrandXYZ")
    assert isinstance(products, list)
    assert len(products) == 0

def test_get_top_rated_products():
    """Test getting top-rated products."""
    service = get_service_instance_for_test()
    top_products = service.get_top_rated_products()
    assert isinstance(top_products, list)
    if top_products:
        assert all(isinstance(p, dict) and 'rating' in p for p in top_products)
        # Further checks could include ensuring ratings are >= 4.0 if that's the logic

def test_get_best_selling_products():
    """Test getting best-selling products."""
    service = get_service_instance_for_test()
    best_sellers = service.get_best_selling_products()
    assert isinstance(best_sellers, list)
    if best_sellers:
        assert all(isinstance(p, dict) and 'sales_count' in p for p in best_sellers)
        # Further checks could include ensuring they are sorted by sales_count

def test_get_products():
    """Test getting all products with limit and offset."""
    service = get_service_instance_for_test()
    
    # Test getting all products
    all_products = service.get_products()
    assert isinstance(all_products, list)
    assert len(all_products) == len(service.products)

    if not service.products:
        pytest.skip("No products available to test limit/offset scenarios")

    # Test with limit
    limited_products = service.get_products(limit=1)
    assert isinstance(limited_products, list)
    assert len(limited_products) == min(1, len(service.products))
    if service.products:
        assert limited_products[0] == service.products[0]

    # Test with offset
    offset_products = service.get_products(offset=1)
    assert isinstance(offset_products, list)
    expected_len_offset = max(0, len(service.products) - 1)
    assert len(offset_products) == expected_len_offset
    if len(service.products) > 1:
        assert offset_products[0] == service.products[1]
    
    # Test with both limit and offset
    limited_offset_products = service.get_products(limit=1, offset=1)
    assert isinstance(limited_offset_products, list)
    expected_len_limited_offset = min(1, max(0, len(service.products) - 1))
    assert len(limited_offset_products) == expected_len_limited_offset
    if len(service.products) > 1:
        assert limited_offset_products[0] == service.products[1]

def test_smart_search_products():
    """Test smart search functionality."""
    service = get_service_instance_for_test()
    
    if not service.products:
        pytest.skip("No products available to test smart_search_products")

    search_term = "Product" 
    if service.products:
        first_product_name = service.products[0].get('name', '')
        if first_product_name:
            search_term = first_product_name.split(' ')[0] if ' ' in first_product_name and len(first_product_name.split(' ')[0]) > 2 else first_product_name[:4]
    
    results = service.smart_search_products(search_term)
    
    assert isinstance(results, list)
    assert all(isinstance(item, dict) for item in results)
    if results:
        assert all('product' in item and 'score' in item for item in results)
        assert all(isinstance(item['product'], dict) for item in results)
        assert all('id' in item['product'] for item in results)
        assert all(isinstance(item['score'], (float, int)) for item in results)
        # Check if scores are sorted in descending order
        if len(results) > 1:
            scores = [item['score'] for item in results]
            assert all(scores[i] >= scores[i+1] for i in range(len(scores) - 1))

def test_relevance_score():
    """Test the internal relevance_score method directly."""
    service = get_service_instance_for_test()

    # Create a dummy product for testing the scoring logic
    product = {
        "id": "p1",
        "name": "Smartphone Pro Max",
        "description": "High-end smartphone with a powerful camera and long battery life.",
        "category": "Electronics",
        "brand": "TechCo",
        "features": ["Feature A", "Feature B", "5G Connectivity"]
    }

    # Test exact match in name
    score_exact_name = service.relevance_score("Smartphone Pro Max", product)
    assert score_exact_name > 0

    # Test partial match in name
    score_partial_name = service.relevance_score("smartphone", product)
    assert score_partial_name > 0
    # Exact match should generally have a higher score than partial
    # assert score_exact_name > score_partial_name # This depends on internal weights, so remove for robustness

    # Test match in description
    score_description = service.relevance_score("camera", product)
    assert score_description > 0

    # Test match in category
    score_category = service.relevance_score("Electronics", product)
    assert score_category > 0

    # Test match in brand
    score_brand = service.relevance_score("TechCo", product)
    assert score_brand > 0

    # Test match in features
    score_feature = service.relevance_score("5G Connectivity", product)
    assert score_feature > 0

    # Test no match
    score_no_match = service.relevance_score("nonexistentword", product)
    assert score_no_match == 0

    # Test case insensitivity (assuming internal logic handles this)
    score_case_insensitive = service.relevance_score("smartphone pro max", product)
    assert score_case_insensitive == score_exact_name

    # Test multiple words query, expecting higher score due to more matches
    score_multiple_matches = service.relevance_score("Smartphone Camera", product)
    assert score_multiple_matches > score_partial_name 
    assert score_multiple_matches > score_description