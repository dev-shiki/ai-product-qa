import pytest
from app.services.ai_service import generate_response

from unittest.mock import MagicMock, patch
from app.services.ai_service import AIService

def test_generate_response_basic():
    # Define mock data for the test
    mock_context_input = "User is looking for recommendations for a gaming laptop under 15 million IDR."
    mock_ai_response_text = "Based on your interest in gaming laptops, I recommend considering models like the Asus ROG Strix G15 or Lenovo Legion 5. They offer strong performance for gaming within your budget."

    # 1. Mock the return value chain of genai.Client().models.generate_content().text
    # The innermost part: the response object from generate_content, which has a '.text' attribute
    mock_genai_response_object = MagicMock()
    mock_genai_response_object.text = mock_ai_response_text

    # The next level: the generate_content method, which returns the above object
    mock_generate_content_method = MagicMock(return_value=mock_genai_response_object)

    # The 'models' attribute of the client, which contains the 'generate_content' method
    mock_models_attribute = MagicMock()
    mock_models_attribute.generate_content = mock_generate_content_method

    # The genai.Client instance, which has the 'models' attribute
    mock_genai_client_instance = MagicMock()
    mock_genai_client_instance.models = mock_models_attribute

    # Use patch as context managers for dependencies
    # Patch `genai.Client` where it's imported in `ai_service.py`
    with patch('app.services.ai_service.genai.Client', return_value=mock_genai_client_instance) as mock_genai_client_cls:
        # Patch `get_settings` as it's called during AIService initialization
        with patch('app.services.ai_service.get_settings') as mock_get_settings:
            mock_settings_instance = MagicMock()
            mock_settings_instance.GOOGLE_API_KEY = "dummy_api_key_for_test"
            mock_get_settings.return_value = mock_settings_instance

            # Patch `ProductDataService` as it's instantiated during AIService initialization
            with patch('app.services.ai_service.ProductDataService') as mock_product_data_service_cls:
                # 2. Instantiate AIService (its __init__ uses the patched dependencies)
                ai_service = AIService()

                # 3. Call the target function: generate_response
                actual_response = ai_service.generate_response(mock_context_input)

                # 4. Assertions
                # Check that genai.Client was initialized correctly
                mock_genai_client_cls.assert_called_once_with(api_key="dummy_api_key_for_test")
                
                # Construct the exact expected prompt that generate_response sends to the AI model
                expected_prompt = (
                    "You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n"
                    f"{mock_context_input}\n\n"
                    "Please provide a clear and concise answer that helps the user understand the products and make an informed decision."
                )

                # Check that generate_content was called with the correct model and prompt
                mock_generate_content_method.assert_called_once_with(
                    model="gemini-2.0-flash",
                    contents=expected_prompt
                )
                
                # Check that the function returned the mocked AI response
                assert actual_response == mock_ai_response_text
