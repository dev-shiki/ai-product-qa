import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Mock get_settings to provide a dummy API key
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key"

    # Mock the genai.Client instance and its methods
    mock_genai_client_instance = MagicMock()
    # Configure the return value for generate_content to simulate AI response
    mock_genai_client_instance.models.generate_content.return_value.text = "This is a mocked AI response for the given context."

    # Mock ProductDataService as well, as AIService.__init__ initializes it,
    # even though generate_response does not directly use it.
    mock_product_data_service_instance = MagicMock()

    # Use patch to replace the actual dependencies with our mocks during the test execution
    with patch('app.utils.config.get_settings', return_value=mock_settings), \
         patch('google.genai.Client', return_value=mock_genai_client_instance), \
         patch('app.services.ai_service.ProductDataService', return_value=mock_product_data_service_instance):
        
        # Import AIService after patching, ensuring it uses the mocks
        from app.services.ai_service import AIService
        ai_service = AIService()

        # Define a simple context for the test
        sample_context = "Tell me about the importance of product reviews."

        # Call the generate_response function
        response = ai_service.generate_response(sample_context)

        # Assert that the response matches our mocked AI response
        assert response == "This is a mocked AI response for the given context."

        # Assert that the AI model was called with the correct prompt and parameters
        expected_prompt_prefix = "You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n"
        expected_prompt_suffix = "\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."
        expected_full_prompt = f"{expected_prompt_prefix}{sample_context}{expected_prompt_suffix}"

        mock_genai_client_instance.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash",
            contents=expected_full_prompt
        )
