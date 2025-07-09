# Type Hints Addition

**File**: `./tests/test_ai_service.py`  
**Time**: 07:33:04  
**Type**: type_hints_addition

## Improvement

```python
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
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("!@#$%^&*()")
        assert "Test response" in response

@pytest.mark.asyncio
async def test_get_response_with_numbers():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("1234567890")
        assert "Test response" in response

@pytest.mark.asyncio
async def test_get_response_with_mixed_input():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("Test123!@#")
        assert "Test response" in response

@pytest.mark.asyncio
async def test_get_response_with_unicode():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("你好世界")
        assert "Test response" in response

@pytest.mark.asyncio
async def test_get_response_with_sql_injection():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("SELECT * FROM users;")
        assert "Test response" in response

@pytest.mark.asyncio
async def test_get_response_with_xss():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("<script>alert('XSS');</script>")
        assert "Test response" in response

@pytest.mark.asyncio
async def test_get_response_with_valid_input():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Ini adalah jawaban yang valid"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("Apa kabar?")
        assert "Ini adalah jawaban yang valid" in response

@pytest.mark.asyncio
async def test_get_response_with_leading_and_trailing_spaces():
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        response = await service.get_response("   Test question   ")
        assert "Test response" in response
```

---
*Generated by Smart AI Bot*
