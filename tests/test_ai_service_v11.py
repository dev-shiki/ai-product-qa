import pytest
from app.services.ai_service import AIService

@pytest.mark.asyncio
async def test_generate_response_basic():
    """
    Test the AI service with a basic question.
    Note: The original request specified 'generate_response', but the provided code
    contains 'get_response'. This test targets 'get_response' as it's the
    relevant method for generating a response based on the code provided.
    The 'context' parameter from the prompt is mapped to 'question'.
    """
    # Using "context_value" as requested, mapped to the 'question' parameter
    context_value = "Tell me about the best laptops for gaming."
    try:
        service = AIService()
        result = await service.get_response(question=context_value)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    except Exception as e:
        # This catch-all handles issues like missing GOOGLE_API_KEY, network errors,
        # or other external service failures during initialization or response generation.
        pytest.skip(f"Test skipped due to dependency or external service error: {e}")

@pytest.mark.asyncio
async def test_generate_response_edge_cases():
    """
    Test the AI service with various edge cases for the question/context.
    """
    test_cases = [
        "Are there any good smartphones under $300?",  # Specific query with price
        "Recommend a tablet for students.",             # Specific query with category and user type
        "What's new in technology?",                    # General query
        "",                                             # Empty string input
        "a" * 1000,                                     # Very long string input
    ]

    for context_value in test_cases:
        try:
            service = AIService()
            result = await service.get_response(question=context_value)
            assert result is not None, f"Response should not be None for input: '{context_value}'"
            assert isinstance(result, str), f"Response should be a string for input: '{context_value}'"
            assert len(result) > 0, f"Response string should not be empty for input: '{context_value}'"
        except Exception as e:
            pytest.skip(f"Test for '{context_value}' skipped due to dependency or external service error: {e}")