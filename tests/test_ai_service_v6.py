import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Mock dependencies for AIService initialization and the method itself.
    # Assume 'patch' and 'MagicMock' are available from the test environment (e.g., unittest.mock).
    with patch('app.utils.config.get_settings') as mock_get_settings, \
         patch('google.genai.Client') as mock_genai_client, \
         patch('app.services.product_data_service.ProductDataService'): # Mock ProductDataService as it's used in __init__ but not directly by generate_response

        # Configure mock_get_settings for AIService.__init__ to avoid config errors.
        mock_settings_instance = MagicMock()
        mock_settings_instance.GOOGLE_API_KEY = "dummy_api_key"
        mock_get_settings.return_value = mock_settings_instance

        # Configure mock_genai_client for the generate_response method's call to the AI model.
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        # Set up the mock for the actual AI response generation.
        mock_generate_content_response = MagicMock()
        mock_generate_content_response.text = "This is a mocked AI response for the given context."
        mock_client_instance.models.generate_content.return_value = mock_generate_content_response

        # Import AIService after patching to ensure the patches are active when it's instantiated.
        # This import is usually at the top of a test file, but for the "only return function" constraint,
        # it's placed here assuming the overall test runner handles imports correctly or it's implicitly available.
        # For this specific context, let's assume AIService is already globally available or imported in the testing harness.
        # If not, the test would need 'from app.services.ai_service import AIService'
        from app.services.ai_service import AIService

        # Instantiate AIService. Its __init__ will use our mocks.
        ai_service = AIService()

        # Define a simple context for the test.
        test_context = "User is asking about recommended smartphones under 5 million."

        # Call the target function.
        response = ai_service.generate_response(context=test_context)

        # Assert the basic functionality: the response text matches the mocked return value.
        assert response == "This is a mocked AI response for the given context."

        # Verify that the underlying AI client method was called as expected.
        mock_client_instance.models.generate_content.assert_called_once()
        
        # Further verify the arguments passed to the AI model.
        call_kwargs = mock_client_instance.models.generate_content.call_args[1]
        
        assert call_kwargs['model'] == "gemini-2.0-flash"
        assert test_context in call_kwargs['contents']
        assert "You are a helpful product assistant." in call_kwargs['contents']
        assert "Please provide a clear and concise answer" in call_kwargs['contents']
