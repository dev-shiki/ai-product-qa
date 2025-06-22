import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import AIService

@pytest.mark.asyncio
async def test_get_response():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("Test question")
        assert response == "Test response"

@pytest.mark.asyncio
async def test_get_response_with_error():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_generate.side_effect = Exception("API Error")
        
        response = await service.get_response("Test question")
        assert "Maaf, saya sedang mengalami kesulitan" in response

@pytest.mark.asyncio
async def test_get_response_with_empty_question():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Pertanyaan tidak boleh kosong"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("")
        assert "Pertanyaan tidak boleh kosong" in response

@pytest.mark.asyncio
async def test_get_response_with_long_question():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Pertanyaan terlalu panjang"
        mock_generate.return_value = mock_response
        
        long_question = "A" * 1000
        response = await service.get_response(long_question)
        assert "Pertanyaan terlalu panjang" in response

@pytest.mark.asyncio
async def test_get_response_with_special_characters():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Response with special chars"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("Test question with @#$%^&*()")
        assert response == "Response with special chars"

@pytest.mark.asyncio
async def test_get_response():
    with patch('app.services.ai_service.genai') as mock_genai:
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "AI answer"
        mock_model.generate_content.return_value = mock_response
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        # Import after mocking
        ai = AIService()
        result = await ai.get_response("Apa laptop terbaik?")
        assert result == "AI answer"

def test_generate_response():
    with patch('app.services.ai_service.genai') as mock_genai:
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "AI answer"
        mock_model.generate_content.return_value = mock_response
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        # Import after mocking
        ai = AIService()
        result = ai.generate_response("context")
        assert result == "AI answer"

@pytest.mark.asyncio
@patch('app.services.ai_service.genai.Client')
async def test_ai_service_init_error(mock_client):
    """Test AI service initialization error"""
    mock_client.side_effect = Exception("API Key Error")
    with pytest.raises(Exception):
        AIService()

@pytest.mark.asyncio
@patch('app.services.ai_service.genai.Client')
async def test_get_response_with_best_request(mock_client):
    """Test get_response with 'terbaik' keyword"""
    # Mock the client
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.text = "Berikut laptop terbaik berdasarkan rating"
    mock_client_instance.models.generate_content.return_value = mock_response
    
    # Mock product service
    with patch('app.services.ai_service.ProductDataService') as mock_product_service:
        mock_service_instance = MagicMock()
        mock_product_service.return_value = mock_service_instance
        mock_service_instance.smart_search_products = AsyncMock(return_value=(
            [{"name": "MacBook Pro", "price": 29999000, "brand": "Apple", "category": "laptop", "specifications": {"rating": 4.8}, "description": "Laptop terbaik"}],
            "Berikut laptop terbaik berdasarkan rating"
        ))
        
        ai_service = AIService()
        result = await ai_service.get_response("Saya ingin laptop terbaik")
        
        assert "laptop terbaik" in result.lower()
        mock_service_instance.smart_search_products.assert_called_once()

@pytest.mark.asyncio
@patch('app.services.ai_service.genai.Client')
async def test_get_response_with_budget_request(mock_client):
    """Test get_response with budget detection"""
    # Mock the client
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.text = "Berikut produk yang sesuai budget"
    mock_client_instance.models.generate_content.return_value = mock_response
    
    # Mock product service
    with patch('app.services.ai_service.ProductDataService') as mock_product_service:
        mock_service_instance = MagicMock()
        mock_product_service.return_value = mock_service_instance
        mock_service_instance.smart_search_products = AsyncMock(return_value=(
            [{"name": "iPhone 15", "price": 14999000, "brand": "Apple", "category": "smartphone", "specifications": {"rating": 4.6}, "description": "Smartphone murah"}],
            "Berikut produk yang sesuai budget"
        ))
        
        ai_service = AIService()
        result = await ai_service.get_response("Saya ingin smartphone budget 5 juta")
        
        assert "budget" in result.lower()
        mock_service_instance.smart_search_products.assert_called_once()

@pytest.mark.asyncio
@patch('app.services.ai_service.genai.Client')
async def test_get_response_ai_error(mock_client):
    """Test get_response when AI service fails"""
    # Mock the client
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Mock the response to raise an error
    mock_client_instance.models.generate_content.side_effect = Exception("AI Service Error")
    
    # Mock product service
    with patch('app.services.ai_service.ProductDataService') as mock_product_service:
        mock_service_instance = MagicMock()
        mock_product_service.return_value = mock_service_instance
        mock_service_instance.smart_search_products = AsyncMock(return_value=([], "No products found"))
        
        ai_service = AIService()
        result = await ai_service.get_response("Test question")
        
        assert "Maaf, saya sedang mengalami kesulitan" in result

@pytest.mark.asyncio
@patch('app.services.ai_service.genai.Client')
async def test_generate_response_legacy(mock_client):
    """Test legacy generate_response method"""
    # Mock the client
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.text = "Legacy response"
    mock_client_instance.models.generate_content.return_value = mock_response
    
    ai_service = AIService()
    result = ai_service.generate_response("Test context")
    
    assert result == "Legacy response"

@pytest.mark.asyncio
@patch('app.services.ai_service.genai.Client')
async def test_generate_response_legacy_error(mock_client):
    """Test legacy generate_response method with error"""
    # Mock the client
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Mock the response to raise an error
    mock_client_instance.models.generate_content.side_effect = Exception("Legacy AI Error")
    
    ai_service = AIService()
    with pytest.raises(Exception):
        ai_service.generate_response("Test context") 