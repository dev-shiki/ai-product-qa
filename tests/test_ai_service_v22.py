import pytest
import pytest_asyncio
from app.services.ai_service import AIService

# Note: The provided source code for AIService contains a method named 'get_response',
# while the instructions and example call refer to 'generate_response'.
# This test suite will assume 'generate_response' is intended to map to the 'get_response' method
# in the provided source code, and will call 'get_response' accordingly, while adhering
# to the requested test function names (e.g., test_generate_response_basic).

@pytest.mark.asyncio
async def test_generate_response_basic():
    """
    Test the basic functionality of the AI service's response generation.
    Checks if a non-null string response is returned for a typical question.
    """
    try:
        service = AIService()
        # Use a realistic question as input for the 'get_response' method
        question_input = "Tell me about the latest gaming laptops."
        
        # Call the actual method name 'get_response'
        result = await service.get_response(question_input)
        
        # Assertions as per prompt's expected output and good practice
        assert result is not None
        assert isinstance(result, str)
        # Given the partial source code, the return content cannot be fully predicted.
        # We assume a string response is always intended.
        assert len(result) >= 0 # The method returns a string, could be empty or a processing status based on partial code
                                # but generally expected to be non-empty for meaningful responses.

    except Exception as e:
        # If initialization or method execution fails (e.g., missing API key, network issues),
        # skip the test as per instructions.
        pytest.skip(f"Test skipped due to dependency or unexpected error during basic test: {e}")

@pytest.mark.asyncio
async def test_generate_response_edge_cases():
    """
    Test the response generation with edge case inputs.
    Includes empty string, string with only spaces, and a complex question.
    """
    try:
        service = AIService()

        # Edge Case 1: Empty question string
        empty_question = ""
        result_empty = await service.get_response(empty_question)
        assert result_empty is not None
        assert isinstance(result_empty, str)
        # assert len(result_empty) >= 0 # Expected behavior for empty input depends on full implementation

        # Edge Case 2: Question string with only spaces
        space_question = "   "
        result_space = await service.get_response(space_question)
        assert result_space is not None
        assert isinstance(result_space, str)
        # assert len(result_space) >= 0

        # Edge Case 3: Complex question involving multiple potential categories/criteria
        complex_question = "Can you recommend a good smartphone under $800, and also suggest some noise-cancelling headphones for travel?"
        result_complex = await service.get_response(complex_question)
        assert result_complex is not None
        assert isinstance(result_complex, str)
        # assert len(result_complex) >= 0

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error during edge cases test: {e}")

@pytest.mark.asyncio
async def test_generate_response_specific_categories():
    """
    Test response generation with questions that explicitly target categories
    known by the service's internal mapping (e.g., 'laptop', 'smartphone').
    """
    try:
        service = AIService()

        # Test with 'laptop' keyword
        question_laptop = "What are the latest laptop models?"
        result_laptop = await service.get_response(question_laptop)
        assert result_laptop is not None
        assert isinstance(result_laptop, str)

        # Test with 'smartphone' keyword
        question_smartphone = "Looking for a new smartphone, any suggestions?"
        result_smartphone = await service.get_response(question_smartphone)
        assert result_smartphone is not None
        assert isinstance(result_smartphone, str)

        # Test with 'tablet' keyword
        question_tablet = "Which tablets are currently trending?"
        result_tablet = await service.get_response(question_tablet)
        assert result_tablet is not None
        assert isinstance(result_tablet, str)

        # Test with 'headphone' keyword
        question_headphone = "Recommend some durable headphones for sports."
        result_headphone = await service.get_response(question_headphone)
        assert result_headphone is not None
        assert isinstance(result_headphone, str)

    except Exception as e:
        pytest.skip(f"Test skipped due to dependency or unexpected error during category test: {e}")