import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Mock get_settings to avoid actual config loading
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.GOOGLE_API_KEY = "dummy_api_key"
        mock_get_settings.return_value = mock_settings

        # Mock google.genai.Client and its methods
        with patch('google.genai.Client') as MockGenaiClient:
            # Mock the instance of the client created by AIService
            mock_genai_instance = MockGenaiClient.return_value
            
            # Mock the return value of models.generate_content
            mock_generate_content_result = MagicMock()
            mock_generate_content_result.text = "Ini adalah respons AI yang di-mock."
            mock_genai_instance.models.generate_content.return_value = mock_generate_content_result

            # Instantiate AIService, which will use the patched dependencies
            ai_service = AIService()

            # Define a simple context for the test
            test_context = "Pengguna bertanya tentang produk laptop."

            # Call the function under test
            response = ai_service.generate_response(test_context)

            # Assertions
            assert isinstance(response, str)
            assert response == "Ini adalah respons AI yang di-mock."
            
            # Verify that genai.Client was instantiated correctly
            MockGenaiClient.assert_called_once_with(api_key="dummy_api_key")
            
            # Verify that generate_content was called
            mock_genai_instance.models.generate_content.assert_called_once()
            
            # Extract arguments passed to generate_content
            args, kwargs = mock_genai_instance.models.generate_content.call_args
            
            # Verify the model used
            assert kwargs['model'] == "gemini-2.0-flash"
            
            # Verify the contents (prompt) contain the expected parts
            assert "You are a helpful product assistant." in kwargs['contents']
            assert test_context in kwargs['contents']
            assert "Please provide a clear and concise answer" in kwargs['contents']
