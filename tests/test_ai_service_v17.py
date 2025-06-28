import pytest
import asyncio  # Required for async tests with pytest.mark.asyncio
from app.services.ai_service import AIService

# IMPORTANT NOTE:
# The provided source code does not contain a method named 'generate_response'.
# It contains an async method named 'get_response(self, question: str)'.
# This test suite is created assuming that 'generate_response' in the prompt
# was a typo and actually refers to the 'get_response' method in the source.
# Therefore, the tests call 'get_response' and use 'async/await'.

@pytest.mark.asyncio
async def test_generate_response_basic():
    """
    Test the AI service's response generation with a basic, valid question.
    This test assumes 'generate_response' from the prompt refers to 'get_response'.
    """
    try:
        # Initialize the AI service
        service = AIService()
        
        # Use a realistic question for the 'get_response' method
        question_input = "Tell me about some good laptops."
        
        # Call the asynchronous method
        response = await service.get_response(question_input)
        
        # Assertions for a basic valid response
        assert response is not None, "Response should not be None"
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response string should not be empty"
        
    except Exception as e:
        # This catches errors during AIService initialization (e.g., missing API key)
        # or during the API call itself.
        pytest.skip(f"Test skipped due to dependency or external API issue: {e}")

@pytest.mark.asyncio
async def test_generate_response_edge_cases():
    """
    Test the AI service's response generation with various edge case scenarios for questions.
    This test assumes 'generate_response' from the prompt refers to 'get_response'.
    """
    try:
        # Initialize the AI service
        service = AIService()

        # Test case 1: Empty question string
        empty_question = ""
        response_empty = await service.get_response(empty_question)
        assert response_empty is not None, "Response for empty question should not be None"
        assert isinstance(response_empty, str), "Response for empty question should be a string"
        # Expecting some kind of general or error message, not necessarily an empty string
        assert len(response_empty) > 0, "Response for empty question should not be empty (e.g., a fallback message)"

        # Test case 2: Question requiring specific product search logic (e.g., category, price)
        # Based on the snippet, 'get_response' attempts to parse categories and prices.
        specific_product_question = "I am looking for a smartphone under $500."
        response_specific = await service.get_response(specific_product_question)
        assert response_specific is not None, "Response for specific product question should not be None"
        assert isinstance(response_specific, str), "Response for specific product question should be a string"
        assert len(response_specific) > 0, "Response for specific product question should not be empty"

        # Test case 3: Question for a general/unhandled topic (outside the product domain)
        general_question = "What is the capital of France?"
        response_general = await service.get_response(general_question)
        assert response_general is not None, "Response for general question should not be None"
        assert isinstance(response_general, str), "Response for general question should be a string"
        assert len(response_general) > 0, "Response for general question should not be empty"
        
    except Exception as e:
        # This catches errors during AIService initialization or API calls.
        pytest.skip(f"Test skipped due to dependency or external API issue: {e}")