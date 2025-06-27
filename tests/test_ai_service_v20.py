import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to prevent actual config loading and API key access during AIService initialization
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock ProductDataService.__init__ as it's called in AIService.__init__
    # This ensures AIService can be initialized without real product data service dependencies.
    mocker.patch('app.services.product_data_service.ProductDataService.__init__', return_value=None)

    # Mock the genai.Client instance and its generate_content method
    mock_genai_client_instance = mocker.MagicMock()
    
    # Configure the return value for generate_content
    mock_ai_response = mocker.MagicMock()
    mock_ai_response.text = "This is a simulated AI response based on your test context."
    mock_genai_client_instance.models.generate_content.return_value = mock_ai_response

    # Patch the genai.Client constructor so that when AIService initializes,
    # it gets our mock client instance instead of a real one.
    mocker.patch('google.genai.Client', return_value=mock_genai_client_instance)

    # Assuming AIService class is available in the test scope (e.g., imported by the test file)
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "The user is asking about the best laptops for gaming under $1500."

    # Call the target function
    actual_response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify the return type
    assert isinstance(actual_response, str)
    # 2. Verify the content of the response matches our mock
    assert actual_response == mock_ai_response.text

    # 3. Verify that the mocked generate_content method was called exactly once
    mock_genai_client_instance.models.generate_content.assert_called_once()

    # 4. Verify the arguments passed to generate_content
    call_args, call_kwargs = mock_genai_client_instance.models.generate_content.call_args
    
    # Check the model used
    assert call_kwargs['model'] == "gemini-2.0-flash"

    # Check the prompt content structure and if the context was included
    expected_prompt_start = "You are a helpful product assistant. Based on the following context, provide a helpful and informative response:"
    expected_prompt_end = "Please provide a clear and concise answer that helps the user understand the products and make an informed decision."
    
    generated_prompt = call_kwargs['contents']
    assert expected_prompt_start in generated_prompt
    assert test_context in generated_prompt
    assert expected_prompt_end in generated_prompt
    # Ensure the context is correctly embedded between the standard parts
    assert generated_prompt.index(expected_prompt_start) < generated_prompt.index(test_context)
    assert generated_prompt.index(test_context) < generated_prompt.index(expected_prompt_end)
