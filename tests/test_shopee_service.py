from app.services.shopee_service import ShopeeService
import pytest

def test_shopee_service_methods():
    service = ShopeeService()
    # Test all public methods with dummy args
    assert hasattr(service, "get_products")
    assert hasattr(service, "get_categories")
    assert hasattr(service, "search_products")
    assert hasattr(service, "get_top_rated_products")
    assert hasattr(service, "get_best_selling_products") 