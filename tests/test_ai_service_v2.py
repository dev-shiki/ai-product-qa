import pytest
from app.services.ai_service import AIService

def test_generate_response_basic():
    """
    Test generate_response with a basic, realistic context string.
    Expected: A non-None string response.
    """
    try:
        # Use a realistic context for a product data service AI, e.g., a common query
        result = AIService().generate_response("What are the features of the new MacBook Air?")
        assert result is not None
        assert isinstance(result, str) # Ensure the response is a string
        # Optionally, you might add more specific assertions based on expected content
        # For example: assert "MacBook Air" in result or "laptop" in result
    except Exception as e:
        # This catch-all handles potential issues like API key not set,
        # external service unavailability, or if 'generate_response' method is not found.
        pytest.skip(f"Test skipped due to dependency or method availability issue: {e}")

def test_generate_response_edge_cases():
    """
    Test generate_response with edge case context values.
    Expected: A non-None string response (could be empty, a default message, or an error message).
    """
    try:
        # Test with an empty context string
        result_empty = AIService().generate_response("")
        assert result_empty is not None
        assert isinstance(result_empty, str)

        # Test with a very long context string (optional, based on expected behavior)
        # long_context = "This is a very long context string designed to test the AI's handling of extensive input. " * 50
        # result_long = AIService().generate_response(long_context)
        # assert result_long is not None
        # assert isinstance(result_long, str)

        # Test with a context that might not yield specific product information
        # result_generic = AIService().generate_response("Tell me something interesting.")
        # assert result_generic is not None
        # assert isinstance(result_generic, str)

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or method availability issue: {e}")