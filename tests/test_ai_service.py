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