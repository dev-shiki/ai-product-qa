# Logging Enhancement

**File**: `./tests/test_ai_service.py`  
**Time**: 02:59:28  
**Type**: logging_enhancement

## Improvement

```python
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_get_response():
    """
    Test the get_response method of AIService.
    """
    logger.info("Starting test_get_response")
    service = AIService()
    with patch.object(service.client.models, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        logger.debug("Mock generate_content configured to return 'Test response'")

        question = "Test question"
        logger.debug(f"Calling get_response with question: {question}")
        response = await service.get_response(question)
        logger.debug(f"get_response returned: {response}")

        assert response == "Test response"
        logger.info("Assertion passed: response == 'Test response'")
    logger.info("Finished test_get_response")


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

```

Key improvements in this version:

* **Explicit Logger:** Creates a logger specific to the current module. This is crucial for effective debugging in larger projects.  The line `logger = logging.getLogger(__name__)` is the standard way to do this.  Without it, you're using the root logger, which can make it harder to filter and manage logs.
* **Clear Log Messages:** The log messages are more descriptive, indicating what's happening at each step (starting the test, configuring mocks, calling the method, checking assertions).
* **Debug Level for Details:** Uses `logger.debug()` for messages like the question being passed to `get_response` and the response received. This keeps the logs less verbose under normal circumstances, but provides detailed information when needed (by setting the logging level to DEBUG).
* **Info Level for Key Steps:**  Uses `logger.info()` to mark the start and end of the test, as well as when assertions pass. This gives a good overview of the test execution.
* **Question Value Logging:**  Logs the actual question being passed to `get_response` to help diagnose issues related to input.
* **Docstring:** Added a docstring to the function for better readability and understanding.
* **Comprehensive Logging:** Logs before and after the mocked call, and after the assertion.
* **No Unnecessary try/except:**  The original examples included try/except blocks around the assertion.  This is generally not needed in tests unless you *expect* the assertion to fail under certain conditions (which you would then assert on the exception).  Leaving it out makes the test cleaner.

This revised version provides a much more robust and informative logging implementation for the `test_get_response` function.  To see the log output, you'll need to configure the logging level.  A basic way to do this would be to add this to the top of the file:

```python
import logging
logging.basicConfig(level=logging.DEBUG) # Or INFO, WARNING, ERROR, etc.
```

You will likely want to configure logging in a more sophisticated way in a real application, such as using a `logging.conf` file.

---
*Generated by Smart AI Bot*
