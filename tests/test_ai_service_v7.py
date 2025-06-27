import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Simple test for generate_response
    # This test mocks the external dependencies (Google AI client, config settings, product service)
    # to ensure the function's logic is tested in isolation.
    from unittest.mock import MagicMock, patch
    from app.services.ai_service import AIService

    # Mock get_settings to provide a dummy API key
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings_instance = MagicMock()
        mock_settings_instance.GOOGLE_API_KEY = "dummy_api_key_for_test"
        mock_get_settings.return_value = mock_settings_instance

        # Mock ProductDataService as it's initialized in AIService's constructor
        with patch('app.services.ai_service.ProductDataService') as mock_product_data_service_class:
            mock_product_data_service_instance = MagicMock()
            mock_product_data_service_class.return_value = mock_product_data_service_instance

            # Mock genai.Client and its internal methods
            with patch('google.genai.Client') as mock_genai_client_class:
                mock_client_instance = MagicMock()
                mock_genai_client_class.return_value = mock_client_instance

                # Configure the mock for the generate_content method
                mock_ai_response = MagicMock()
                mock_ai_response.text = "This is a test AI response based on your context."
                mock_client_instance.models.generate_content.return_value = mock_ai_response

                # Instantiate AIService - its __init__ will use the mocked dependencies
                ai_service = AIService()

                # Define the test context string
                test_context = "The user is looking for a good smartphone recommendation."

                # Construct the expected prompt based on the function's logic
                expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

                # Call the function under test
                actual_response = ai_service.generate_response(test_context)

                # Assertions:

                # 1. Verify that generate_content was called exactly once with the correct arguments
                mock_client_instance.models.generate_content.assert_called_once_with(
                    model="gemini-2.0-flash",
                    contents=expected_prompt
                )

                # 2. Verify that the function returned the expected mocked response text
                assert actual_response == mock_ai_response.text
