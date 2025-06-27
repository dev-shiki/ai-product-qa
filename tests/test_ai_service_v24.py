import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock the external dependencies needed by AIService.__init__
    mocker.patch('app.services.ai_service.get_settings')
    mocker.patch('app.services.ai_service.ProductDataService')

    # Mock the Google AI client and its generate_content method
    mock_ai_response = mocker.Mock()
    mock_ai_response.text = "Ini adalah respons AI tiruan untuk pengujian."
    
    mock_generate_content = mocker.Mock(return_value=mock_ai_response)
    
    # Patch genai.Client so that when AIService initializes, it uses our mock
    # We'll then set the mock's 'models.generate_content' to our specific mock
    mock_genai_client_instance = mocker.Mock()
    mock_genai_client_instance.models.generate_content = mock_generate_content
    mocker.patch('app.services.ai_service.genai.Client', return_value=mock_genai_client_instance)

    # Import AIService after patching, so its __init__ uses the mocks
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define the test context
    test_context = "Pertanyaan pengguna tentang rekomendasi produk secara umum."

    # Call the function under test
    response = ai_service.generate_response(test_context)

    # Construct the expected prompt that generate_response would send
    expected_prompt_start = "You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n"
    expected_prompt_end = "\n\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."
    expected_prompt = f"{expected_prompt_start}{test_context}{expected_prompt_end}"

    # Assertions
    # 1. Verify that generate_content was called exactly once
    mock_generate_content.assert_called_once()
    
    # 2. Verify that generate_content was called with the correct model and prompt
    mock_generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
    
    # 3. Verify that the function returned the text from our mock AI response
    assert response == "Ini adalah respons AI tiruan untuk pengujian."
