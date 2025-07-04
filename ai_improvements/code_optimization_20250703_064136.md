# Code Optimization

**File**: `./tests/test_ai_service.py`  
**Time**: 06:41:36  
**Type**: code_optimization

## Improvement

**Improvement:**

Instantiate `AIService` **outside** the test functions and reuse it.

**Explanation:**

The current code instantiates `service = AIService()` at the beginning of each test function.  This means a new `AIService` object (presumably including potentially expensive initializations of the `client`) is created for every single test.  We can avoid this unnecessary overhead by creating one instance of `AIService` at the module level (outside the test functions) and reusing that same instance in all of the tests. This will reduce execution time and resource consumption, especially if `AIService` initialization is heavy.
```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import AIService

service = AIService()  # Instantiate outside the test functions

@pytest.mark.asyncio
async def test_get_response():
    # service = AIService()  # Removed
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response

        response = await service.get_response("Test question")
        assert response == "Test response"

@pytest.mark.asyncio
async def test_get_response_with_error():
    # service = AIService() # Removed
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_generate.side_effect = Exception("API Error")

        response = await service.get_response("Test question")
        assert "Maaf, saya sedang mengalami kesulitan" in response

@pytest.mark.asyncio
async def test_get_response_with_empty_question():
    # service = AIService() # Removed
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Pertanyaan tidak boleh kosong"
        mock_generate.return_value = mock_response

        response = await service.get_response("")
        assert "Pertanyaan tidak boleh kosong" in response

@pytest.mark.asyncio
async def test_get_response_with_long_question():
    # service = AIService() # Removed
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Pertanyaan terlalu panjang"
        mock_generate.return_value = mock_response

        long_question = "A" * 1000
        response = await service.get_response(long_question)
        assert "Pertanyaan terlalu panjang" in response

@pytest.mark.asyncio
async def test_get_response_with_special_characters():
    # service = AIService() # Removed
    ...

```

This optimization is particularly relevant because `AIService` likely initializes a client object (connecting to an AI service), which could be slow. Reusing the same instance avoids repeatedly establishing this connection. It maintains test isolation because of the `patch` operation that happens within each test.

---
*Generated by Smart AI Bot*
