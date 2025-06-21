from app.services.external_product_service import ExternalProductService
import pytest
from unittest.mock import patch, MagicMock

def test_external_product_service_init():
    service = ExternalProductService()
    assert service is not None

def test_external_product_service_methods():
    service = ExternalProductService()
    # Test all public methods with dummy args
    assert hasattr(service, "get_products")
    assert hasattr(service, "get_categories")
    assert hasattr(service, "search_products")
    assert hasattr(service, "get_top_rated_products")
    assert hasattr(service, "get_best_selling_products")

@patch('app.services.external_product_service.requests.Session')
def test_search_products_fakestoreapi_success(mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": 1,
            "title": "Test Product",
            "category": "electronics",
            "price": 10.0,
            "description": "Test description",
            "rating": {"rate": 4.5},
            "image": "test.jpg"
        }
    ]
    mock_response.raise_for_status.return_value = None
    mock_session.return_value.get.return_value = mock_response
    
    service = ExternalProductService()
    result = service.search_products_fakestoreapi("test", 5)
    
    assert len(result) > 0
    assert result[0]["name"] == "Test Product"

@patch('app.services.external_product_service.requests.Session')
def test_search_products_fakestoreapi_error(mock_session):
    mock_session.return_value.get.side_effect = Exception("Network error")
    
    service = ExternalProductService()
    result = service.search_products_fakestoreapi("test", 5)
    
    assert result == []

def test_search_products_fallback():
    service = ExternalProductService()
    result = service.search_products("test", 5, "fallback")
    
    assert len(result) > 0
    assert "iPhone 15 Pro Max" in [p["name"] for p in result]

@patch('app.services.external_product_service.requests.Session')
def test_get_product_details_success(mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": 1,
        "title": "Test Product",
        "category": "electronics",
        "price": 10.0,
        "description": "Test description",
        "rating": {"rate": 4.5},
        "image": "test.jpg"
    }
    mock_response.raise_for_status.return_value = None
    mock_session.return_value.get.return_value = mock_response
    
    service = ExternalProductService()
    result = service.get_product_details("1", "fakestoreapi")
    
    assert result is not None
    assert result["name"] == "Test Product"

def test_get_product_details_fallback():
    service = ExternalProductService()
    result = service.get_product_details("fallback_1", "fakestoreapi")
    
    assert result is not None
    assert result["name"] == "iPhone 15 Pro Max"

def test_get_product_details_not_found():
    service = ExternalProductService()
    result = service.get_product_details("nonexistent", "fakestoreapi")
    
    assert result is None

@patch('app.services.external_product_service.requests.Session')
def test_get_categories_success(mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"category": "electronics"},
        {"category": "clothing"},
        {"category": "electronics"}
    ]
    mock_response.raise_for_status.return_value = None
    mock_session.return_value.get.return_value = mock_response
    
    service = ExternalProductService()
    result = service.get_categories()
    
    assert len(result) > 0
    # Check that categories are extracted correctly
    assert any("electronics" in str(cat) for cat in result)

@patch('app.services.external_product_service.requests.Session')
def test_get_categories_error(mock_session):
    mock_session.return_value.get.side_effect = Exception("Network error")
    
    service = ExternalProductService()
    result = service.get_categories()
    
    # Should return fallback categories
    assert len(result) > 0
    assert "electronics" in result

@patch('app.services.external_product_service.requests.Session')
def test_get_brands_success(mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"category": "electronics"},
        {"category": "clothing"}
    ]
    mock_response.raise_for_status.return_value = None
    mock_session.return_value.get.return_value = mock_response
    
    service = ExternalProductService()
    result = service.get_brands()
    
    assert len(result) > 0
    assert "electronics" in result
    assert "clothing" in result

@patch('app.services.external_product_service.requests.Session')
def test_get_brands_error(mock_session):
    mock_session.return_value.get.side_effect = Exception("Network error")
    
    service = ExternalProductService()
    result = service.get_brands()
    
    assert result == ["Unknown"]

def test_get_products():
    service = ExternalProductService()
    result = service.get_products(5)
    
    assert len(result) > 0

def test_get_top_rated_products():
    service = ExternalProductService()
    result = service.get_top_rated_products(3)
    
    assert len(result) > 0

def test_get_best_selling_products():
    service = ExternalProductService()
    result = service.get_best_selling_products(3)
    
    assert len(result) > 0

@patch('app.services.external_product_service.requests.Session')
def test_test_connection_success(mock_session):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_session.return_value.get.return_value = mock_response
    
    service = ExternalProductService()
    result = service.test_connection()
    
    assert result == True

@patch('app.services.external_product_service.requests.Session')
def test_test_connection_failure(mock_session):
    mock_session.return_value.get.side_effect = Exception("Network error")
    
    service = ExternalProductService()
    result = service.test_connection()
    
    assert result == False 