import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock AIService's dependencies during initialization and method execution.
    
    # Mock app.utils.config.get_settings as it's called by AIService.__init__
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy-api-key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock app.services.product_data_service.ProductDataService init
    # Although generate_response doesn't directly use product_service,
    # AIService.__init__ does, so it needs to be mocked to avoid real dependency issues.
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Mock google.genai.Client and its methods to prevent actual API calls.
    # The target call is self.client.models.generate_content.
    mock_genai_client_instance = mocker.MagicMock()
    mock_genai_client_instance.models.generate_content.return_value.text = "Mocked AI response for the given context."
    mocker.patch('google.genai.Client', return_value=mock_genai_client_instance)

    # Instantiate AIService.
    # AIService is assumed to be imported at the top of the test file where this function resides.
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a simple test context to pass to the function.
    test_context = "This is a test context about product recommendations."

    # Call the function under test.
    response = ai_service.generate_response(test_context)

    # Assertions:

    # 1. Verify that the Google AI client's generate_content method was called exactly once.
    mock_genai_client_instance.models.generate_content.assert_called_once()

    # 2. Verify the arguments passed to generate_content.
    args, kwargs = mock_genai_client_instance.models.generate_content.call_args
    assert kwargs['model'] == "gemini-2.0-flash" # As defined in the source code.
    
    # Check if the prompt 'contents' include the provided test_context
    # and the fixed parts of the prompt structure.
    prompt_contents = kwargs['contents']
    assert test_context in prompt_contents
    assert "You are a helpful product assistant." in prompt_contents
    assert "Please provide a clear and concise answer" in prompt_contents

    # 3. Verify the returned response matches the mocked response.
    assert response == "Mocked AI response for the given context."
