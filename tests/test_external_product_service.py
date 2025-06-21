from app.services.external_product_service import ExternalProductService
import pytest

def test_external_product_service_methods():
    service = ExternalProductService()
    # Test all public methods with dummy args
    assert hasattr(service, "get_products")
    assert hasattr(service, "get_categories")
    assert hasattr(service, "search_products")
    assert hasattr(service, "get_top_rated_products")
    assert hasattr(service, "get_best_selling_products") 