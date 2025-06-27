import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # We assume 'patch', 'MagicMock', and 'AIService' are available in the scope
    # due to an external setup or imports as per instruction "JANGAN menambahkan import statement".
    # For this test to run, typical setup would involve:
    # from unittest.mock import MagicMock, patch
    # from app.services.ai_service import AIService # The class containing the target method

    # Mock app.utils.config.get_settings to control API key during AIService initialization
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.GOOGLE_API_KEY = "mock_api_key_123"
        mock_get_settings.return_value = mock_settings

        # Mock google.genai.Client and its methods that generate_response will call
        with patch('google.genai.Client') as mock_genai_client:
            mock_client_instance = MagicMock()
            
            # Configure the return value for client.models.generate_content
            mock_gemini_response = MagicMock()
            mock_gemini_response.text = "Mocked AI response for your context."
            mock_client_instance.models.generate_content.return_value = mock_gemini_response
            
            mock_genai_client.return_value = mock_client_instance

            # Mock ProductDataService to prevent actual DB calls during AIService initialization
            # (generate_response doesn't use it, but AIService's __init__ does)
            with patch('app.services.product_data_service.ProductDataService'):
                # Instantiate AIService. AIService class is assumed to be accessible.
                service = AIService()

                # Define a simple context for the test
                test_context = "User is looking for a new smartphone with a good camera."

                # Call the generate_response function
                actual_response = service.generate_response(test_context)

                # Assertions
                # 1. Verify that generate_content was called
                mock_client_instance.models.generate_content.assert_called_once()
                
                # 2. Verify the arguments passed to generate_content
                expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
                
                mock_client_instance.models.generate_content.assert_called_with(
                    model="gemini-2.0-flash", # As specified in the source code for generate_response
                    contents=expected_prompt
                )
                
                # 3. Verify the returned value
                assert actual_response == "Mocked AI response for your context."
