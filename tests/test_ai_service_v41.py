import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Mock external dependencies required by AIService's __init__ and generate_response method

    # Patch get_settings to return a mock settings object with a dummy API key
    with patch('app.services.ai_service.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.GOOGLE_API_KEY = "test_api_key"
        mock_get_settings.return_value = mock_settings

        # Patch genai.Client to control the behavior of the AI client
        with patch('app.services.ai_service.genai.Client') as mock_genai_client_class:
            # Create a mock instance for the client that AIService.__init__ will use
            mock_client_instance = MagicMock()
            mock_genai_client_class.return_value = mock_client_instance

            # Configure the mock client instance to return a specific value when generate_content is called
            mock_response_object = MagicMock()
            mock_response_object.text = "Mocked AI response for context."
            mock_client_instance.models.generate_content.return_value = mock_response_object

            # Patch ProductDataService as it's initialized in AIService.__init__ but not used by generate_response
            with patch('app.services.ai_service.ProductDataService'):
                # Instantiate AIService; its __init__ will use the mocked dependencies
                from app.services.ai_service import AIService
                ai_service = AIService()

                # Define a simple test context
                test_context = "What is the capital of France?"

                # Call the target function
                response = ai_service.generate_response(test_context)

                # Assert that the response matches the mocked return value
                assert response == "Mocked AI response for context."

                # Verify that generate_content was called with the correct arguments
                expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
                mock_client_instance.models.generate_content.assert_called_once_with(
                    model="gemini-2.0-flash",
                    contents=expected_prompt
                )
