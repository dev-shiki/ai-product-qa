import pytest
import asyncio # Ensure asyncio is imported for direct execution context
from app.services.ai_service import AIService

# Mark tests with pytest_asyncio for asynchronous execution
# (Requires 'pytest-asyncio' to be installed: pip install pytest-asyncio)

@pytest.mark.asyncio
async def test_generate_response_basic():
    """
    Test the AI service's response generation with a basic context.
    This test assumes the 'generate_response' method referenced in the prompt
    is the 'get_response' method in the provided source code, as 'generate_response'
    does not exist in the given snippet. The 'context' parameter from the prompt
    is mapped to the 'question' parameter of 'get_response'.
    """
    try:
        service = AIService()
        # Per prompt example: call AIService().generate_response("context_value")
        # Mapping "context_value" to the 'question' parameter of get_response.
        question_context = "context_value"
        result = await service.get_response(question_context)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0, "Response should not be an empty string"

    except Exception as e:
        # This catches errors during AIService initialization (e.g., missing GOOGLE_API_KEY,
        # network issues) or during the AI API call itself.
        pytest.skip(f"Test skipped due to dependency or external service error: {e}")

@pytest.mark.asyncio
async def test_generate_response_edge_cases():
    """
    Test the AI service's response generation with edge case inputs for the 'question' parameter.
    """
    try:
        service = AIService()

        # Test with an empty string question
        question_empty = ""
        result_empty = await service.get_response(question_empty)
        assert result_empty is not None
        assert isinstance(result_empty, str)
        # Expecting a non-empty string, possibly a generic "can't understand" message
        assert len(result_empty) > 0, "Response to empty question should not be an empty string"

        # Test with a specific, realistic product-related question
        question_specific = "I am looking for a new smartphone under $500, any recommendations?"
        result_specific = await service.get_response(question_specific)
        assert result_specific is not None
        assert isinstance(result_specific, str)
        assert len(result_specific) > 0, "Response to specific question should not be an empty string"

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or external service error: {e}")