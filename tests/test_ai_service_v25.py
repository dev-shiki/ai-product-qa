import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    """
    Test basic functionality of the generate_response method,
    ensuring it correctly forms the prompt and interacts with the AI client.
    """
    # Mock get_settings to prevent actual config loading and dependency on GOOGLE_API_KEY
    mock_settings = mocker.Mock()
    mock_settings.GOOGLE_API_KEY = "mock_api_key"
    mocker.patch('app.services.ai_service.get_settings', return_value=mock_settings)

    # Mock the genai.Client and its methods
    mock_client_instance = mocker.Mock()
    mock_ai_response = mocker.Mock()
    mock_ai_response.text = "This is a simulated AI response based on your product inquiry."
    mock_client_instance.models.generate_content.return_value = mock_ai_response
    mocker.patch('app.services.ai_service.genai.Client', return_value=mock_client_instance)

    # Import AIService after mocks are set up, so its __init__ uses the mocks
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a sample context for the test
    test_context = "User is looking for a gaming laptop under 15 million rupiah."

    # Call the function under test
    response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify that genai.Client was instantiated (implicitly by AIService init)
    # 2. Verify that generate_content was called exactly once
    mock_client_instance.models.generate_content.assert_called_once()

    # 3. Verify the arguments passed to generate_content
    # It should be called with model="gemini-2.0-flash" and a prompt containing the context.
    args, kwargs = mock_client_instance.models.generate_content.call_args
    assert kwargs['model'] == "gemini-2.0-flash"
    
    # Check if the generated prompt contains the test_context and adheres to the structure
    expected_prompt_structure_start = "You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n"
    expected_prompt_structure_end = "\n\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."
    
    assert kwargs['contents'].startswith(expected_prompt_structure_start)
    assert test_context in kwargs['contents']
    assert kwargs['contents'].endswith(expected_prompt_structure_end)

    # 4. Verify that the returned response is the mocked AI response
    assert response == mock_ai_response.text
