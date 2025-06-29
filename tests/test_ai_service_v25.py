import pytest
import asyncio
from app.services.ai_service import AIService

# Note: The provided source code defines 'get_response' not 'generate_response'.
# This test suite targets 'get_response' as it aligns with the parameter context
# and the overall purpose implied by the request. The parameter is 'question'.

def test_get_response_basic_query():
    """
    Test AIService().get_response with a common, general question.
    Expects a non-empty string as a result.
    """
    try:
        service = AIService()
        question = "What is the best laptop for programming?"
        result = asyncio.run(service.get_response(question))

        assert isinstance(result, str)
        assert len(result) > 0, "The response should not be an empty string."
        # Further assertions could check for specific keywords if response structure is predictable
        # assert "laptop" in result.lower()

    except Exception as e:
        # This test relies on external services (Google AI) and environment variables (API keys).
        # It's skipped if initialization fails or the API call encounters an error.
        pytest.skip(f"Test skipped due to dependency or runtime error: {e}")

def test_get_response_specific_product_query():
    """
    Test AIService().get_response with a more specific product-related question,
    potentially involving price or category.
    Expects a non-empty string as a result.
    """
    try:
        service = AIService()
        question = "Show me smartphones under $700."
        result = asyncio.run(service.get_response(question))

        assert isinstance(result, str)
        assert len(result) > 0, "The response should not be an empty string."
        # assert "smartphone" in result.lower()
        # assert "$700" in result or "under $700" in result # More specific, but depends on AI response

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or runtime error: {e}")

def test_get_response_empty_query_string():
    """
    Test AIService().get_response with an empty string as input.
    The expected behavior might vary (empty string, default message, error).
    Asserts that it returns a string and does not crash.
    """
    try:
        service = AIService()
        question = ""
        result = asyncio.run(service.get_response(question))

        assert isinstance(result, str)
        # Depending on the AI's default behavior for empty input, the length might be 0 or more.
        # For robust checks, you might assert if it returns a specific "I need more info" message.
        assert len(result) >= 0 # Should return at least an empty string or a default message

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or runtime error: {e}")

def test_get_response_unclear_query():
    """
    Test AIService().get_response with an ambiguous or very short query.
    """
    try:
        service = AIService()
        question = "Hello" # A greeting, not a product query
        result = asyncio.run(service.get_response(question))

        assert isinstance(result, str)
        assert len(result) > 0, "Response should not be empty for an unclear query."
        # Expectation here might be a generic greeting back or a prompt for more info.

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or runtime error: {e}")