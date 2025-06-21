import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import AIService

@pytest.mark.asyncio
@patch("app.services.ai_service.get_settings")
@patch("app.services.ai_service.genai.Client")
@patch("app.services.ai_service.ProductDataService")
async def test_get_response(mock_product_service, mock_client, mock_settings):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_client.return_value.models.generate_content.return_value.text = "AI answer"
    mock_product_service.return_value.search_products = AsyncMock(return_value=[{"name": "Produk A", "price": 10000, "brand": "BrandX", "category": "Elektronik", "specifications": {"rating": 5}, "description": "desc"}])
    
    # Import after mocking
    ai = AIService()
    result = await ai.get_response("Apa laptop terbaik?")
    assert "AI answer" in result

@pytest.mark.skipif('google' not in globals(), reason="google.genai not available")
@patch("app.services.ai_service.get_settings")
@patch("app.services.ai_service.genai.Client")
@patch("app.services.ai_service.ProductDataService")
def test_generate_response(mock_product_service, mock_client, mock_settings):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_client.return_value.models.generate_content.return_value.text = "AI answer"
    
    # Import after mocking
    ai = AIService()
    result = ai.generate_response("context")
    assert result == "AI answer"

@pytest.mark.asyncio
async def test_get_response():
    service = AIService()
    with patch('app.services.ai_service.genai') as mock_genai:
        mock_model = AsyncMock()
        mock_model.generate_content.return_value.text = "Test response"
        mock_genai.GenerativeModel.return_value = mock_model
        
        response = await service.get_response("Test question")
        assert response == "Test response"

@pytest.mark.asyncio
async def test_get_response_with_error():
    service = AIService()
    with patch('app.services.ai_service.genai') as mock_genai:
        mock_model = AsyncMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        
        response = await service.get_response("Test question")
        assert "Maaf, saya tidak dapat memproses pertanyaan Anda saat ini" in response

@pytest.mark.asyncio
async def test_get_response_with_empty_question():
    service = AIService()
    response = await service.get_response("")
    assert "Pertanyaan tidak boleh kosong" in response

@pytest.mark.asyncio
async def test_get_response_with_long_question():
    service = AIService()
    long_question = "A" * 1000
    response = await service.get_response(long_question)
    assert "Pertanyaan terlalu panjang" in response

@pytest.mark.asyncio
async def test_get_response_with_special_characters():
    service = AIService()
    with patch('app.services.ai_service.genai') as mock_genai:
        mock_model = AsyncMock()
        mock_model.generate_content.return_value.text = "Response with special chars"
        mock_genai.GenerativeModel.return_value = mock_model
        
        response = await service.get_response("Test question with @#$%^&*()")
        assert response == "Response with special chars" 