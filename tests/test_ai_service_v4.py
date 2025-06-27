import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Mock the external dependencies that AIService's __init__ relies on.
    # We assume 'MagicMock' and 'patch' from 'unittest.mock' are already imported
    # in the test file where this function will reside.
    # We also assume 'AIService' from 'app.services.ai_service' is imported.
    with patch('app.services.ai_service.genai.Client') as mock_genai_client, \
         patch('app.services.ai_service.ProductDataService'), \
         patch('app.services.ai_service.get_settings'):
        
        # Configure the mock AI client instance that `genai.Client()` would return.
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        # Configure the return value for the `generate_content` call.
        mock_generate_content_response = MagicMock()
        mock_generate_content_response.text = "Mocked AI response: This is a helpful answer based on your context."
        mock_client_instance.models.generate_content.return_value = mock_generate_content_response

        # Instantiate AIService. Its __init__ will use our patched components.
        # Assuming AIService class is available in scope (e.g., imported at the top of the test file).
        ai_service_instance = AIService()

        # Define a simple test context.
        test_context = "User is asking about a high-performance laptop for gaming."

        # Call the target function.
        actual_response = ai_service_instance.generate_response(test_context)

        # Assertions.
        assert actual_response == "Mocked AI response: This is a helpful answer based on your context."

        # Verify that `generate_content` was called with the correct arguments and prompt structure.
        expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
        
        mock_client_instance.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash", # Ensure the correct model name is used.
            contents=expected_prompt
        )
