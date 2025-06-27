import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(monkeypatch, mocker):
    # Mock app.utils.config.get_settings to avoid actual config loading
    class MockSettings:
        GOOGLE_API_KEY = "dummy_api_key_for_test"
    
    monkeypatch.setattr("app.utils.config.get_settings", lambda: MockSettings())

    # Mock app.services.product_data_service.ProductDataService
    # AIService initializes this, but generate_response doesn't use it directly.
    # mocker.patch is a clean way to mock the class.
    mocker.patch("app.services.product_data_service.ProductDataService")

    # Mock google.genai.Client and its nested methods
    # Create a mock response object with a .text attribute
    mock_gemini_response = mocker.MagicMock()
    mock_gemini_response.text = "Mocked AI response from Gemini 2.0 Flash."

    # Create a mock for the generate_content method
    mock_generate_content = mocker.MagicMock(return_value=mock_gemini_response)

    # Create a mock for the .models attribute, which contains generate_content
    mock_models_attr = mocker.MagicMock()
    mock_models_attr.generate_content = mock_generate_content

    # Create a mock for the genai.Client instance
    mock_client_instance = mocker.MagicMock()
    mock_client_instance.models = mock_models_attr
    
    # Patch the genai.Client class itself so that when AIService initializes it,
    # it gets our mock instance.
    mocker.patch("google.genai.Client", return_value=mock_client_instance)

    # Import the service class *after* its dependencies have been mocked.
    # This ensures that when AIService is initialized, it uses the mocked components.
    from app.services.ai_service import AIService

    # Initialize the AIService
    ai_service = AIService()

    # Define a simple context for the function under test
    test_context = "Saya ingin tahu lebih banyak tentang laptop gaming."

    # Call the generate_response function
    response = ai_service.generate_response(test_context)

    # Assert that the response matches our mocked text
    assert response == "Mocked AI response from Gemini 2.0 Flash."

    # Assert that the generate_content method was called with the correct arguments
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n{test_context}\n\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    
    mock_generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
