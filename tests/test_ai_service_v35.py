import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock settings and product service for AIService initialization
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy-api-key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Mock the genai client and its methods
    mock_ai_response_text = "Ini adalah respons AI yang di-mock dari generate_response."
    
    # Create a mock for the object returned by client.models.generate_content
    mock_gemini_response = mocker.MagicMock()
    mock_gemini_response.text = mock_ai_response_text

    # Create a mock for client.models.generate_content method
    mock_generate_content = mocker.MagicMock(return_value=mock_gemini_response)
    
    # Create a mock for client.models
    mock_models = mocker.MagicMock()
    mock_models.generate_content = mock_generate_content
    
    # Create a mock for genai.Client instance
    mock_genai_client = mocker.MagicMock()
    mock_genai_client.models = mock_models
    
    # Patch the genai.Client constructor
    mocker.patch('google.genai.Client', return_value=mock_genai_client)

    # Import the AIService after all necessary patches are in place
    from app.services.ai_service import AIService

    # Instantiate AIService
    ai_service = AIService()

    # Define a test context
    test_context = "Saya mencari rekomendasi smartphone yang bagus untuk fotografi."

    # Expected prompt based on the generate_response function's logic
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Call the function under test
    response = ai_service.generate_response(test_context)

    # Assertions
    assert response == mock_ai_response_text, "The response text should match the mocked AI response."
    
    # Assert that generate_content was called exactly once with the correct arguments
    mock_generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
