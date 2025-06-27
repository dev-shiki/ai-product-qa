import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to prevent actual config loading and API key reliance
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "mock_api_key"
    mocker.patch('app.services.ai_service.get_settings', return_value=mock_settings)

    # Mock ProductDataService to prevent external dependencies during AIService init
    mocker.patch('app.services.ai_service.ProductDataService')

    # Mock the genai.Client and its methods
    mock_genai_client = mocker.MagicMock()
    # Configure the return value for the generate_content call chain
    mock_genai_client.models.generate_content.return_value = mocker.MagicMock(text="Mocked AI response for context.")
    mocker.patch('app.services.ai_service.genai.Client', return_value=mock_genai_client)

    # Import the service *after* patching to ensure the patches apply correctly
    from app.services.ai_service import AIService

    # Instantiate the service, which will use our mocked dependencies
    ai_service = AIService()

    # Define a simple context string to pass to the function
    test_context = "User is asking about recommended smartphones. Product X: 128GB, good camera. Product Y: 256GB, long battery life."

    # Call the function under test
    response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Check if the response is a string
    assert isinstance(response, str)
    
    # 2. Check if the mocked response text is contained in the actual response
    assert "Mocked AI response for context." in response

    # 3. Verify that genai.Client.models.generate_content was called exactly once
    mock_genai_client.models.generate_content.assert_called_once()

    # 4. Verify the arguments passed to generate_content
    call_args, call_kwargs = mock_genai_client.models.generate_content.call_args
    assert call_kwargs['model'] == "gemini-2.0-flash"
    
    # Check parts of the constructed prompt
    generated_prompt = call_kwargs['contents']
    assert "You are a helpful product assistant." in generated_prompt
    assert test_context in generated_prompt
    assert "Please provide a clear and concise answer" in generated_prompt
