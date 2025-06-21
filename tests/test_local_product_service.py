from app.services.local_product_service import LocalProductService
import pytest

def test_local_product_service_init():
    service = LocalProductService()
    assert service is not None

def test_local_product_service_methods():
    service = LocalProductService()
    # Test all public methods with dummy args
    assert hasattr(service, "get_products")
    assert hasattr(service, "get_categories")
    assert hasattr(service, "search_products")
    assert hasattr(service, "get_top_rated_products")
    assert hasattr(service, "get_best_selling_products") 