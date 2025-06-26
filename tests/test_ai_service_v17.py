import pytest
import logging
from unittest.mock import AsyncMock, MagicMock

# Import the class to be tested
from app.services.ai_service import AIService

# Import dependencies that need to be mocked
from app.utils.config import get_settings
from app.services.product_data_service import ProductDataService
from google import genai

# Setup logging for tests (optional, but good for debugging)
# logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_settings(mocker):
    """Fixture to mock get_settings and return a dummy API key."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.GOOGLE_API_KEY = "dummy_api_key"
    mocker.patch("app.utils.config.get_settings", return_value=mock_settings_obj)
    return mock_settings_obj

@pytest.fixture
def mock_genai_client(mocker):
    """Fixture to mock google.genai.Client and its methods."""
    mock_client_instance = MagicMock()
    # Mock models.generate_content for the client instance
    mock_client_instance.models.generate_content.return_value.text = "Mocked AI response"
    mocker.patch("google.genai.Client", return_value=mock_client_instance)
    return mock_client_instance

@pytest.fixture
def mock_product_data_service(mocker):
    """Fixture to mock ProductDataService and its methods."""
    mock_service_instance = AsyncMock()
    # Mock smart_search_products to return empty products by default
    mock_service_instance.smart_search_products.return_value = ([], "No specific products found.")
    mocker.patch("app.services.product_data_service.ProductDataService", return_value=mock_service_instance)
    return mock_service_instance

@pytest.fixture
def ai_service(mock_settings, mock_genai_client, mock_product_data_service):
    """Fixture to create an AIService instance with mocked dependencies."""
    return AIService()

# --- Test cases for AIService.__init__ ---

def test_ai_service_init_success(ai_service, mock_settings, mock_genai_client, mock_product_data_service, caplog):
    """
    Test that AIService initializes successfully, setting up client and product service.
    Verifies that get_settings, genai.Client, and ProductDataService are called.
    """
    caplog.set_level(logging.INFO)
    assert isinstance(ai_service, AIService)
    mock_settings.assert_called_once()
    mock_genai_client.assert_called_once_with(api_key="dummy_api_key")
    mock_product_data_service.assert_called_once()
    assert "Successfully initialized AI service" in caplog.text

def test_ai_service_init_get_settings_error(mocker, caplog):
    """
    Test that AIService initialization handles errors from get_settings.
    Ensures an exception is raised and an error log is recorded.
    """
    caplog.set_level(logging.ERROR)
    mocker.patch("app.utils.config.get_settings", side_effect=Exception("Settings error"))
    
    with pytest.raises(Exception, match="Settings error"):
        AIService()
    
    assert "Error initializing AI service: Settings error" in caplog.text

def test_ai_service_init_genai_client_error(mocker, mock_settings, caplog):
    """
    Test that AIService initialization handles errors from genai.Client.
    Ensures an exception is raised and an error log is recorded.
    """
    caplog.set_level(logging.ERROR)
    mocker.patch("google.genai.Client", side_effect=Exception("GenAI client error"))
    mocker.patch("app.services.product_data_service.ProductDataService") # Mock to prevent it from failing before client
    
    with pytest.raises(Exception, match="GenAI client error"):
        AIService()
    
    assert "Error initializing AI service: GenAI client error" in caplog.text

# --- Test cases for AIService.get_response ---

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    ("rekomendasi laptop gaming", "laptop", None),
    ("cari smartphone murah", "smartphone", 5000000),
    ("headphone under 2 juta", "headphone", 2000000),
    ("tablet untuk kerja", "tablet", None),
    ("kamera profesional", "kamera", None),
    ("speaker terbaik", "audio", None),
    ("drone budget 10 juta", "drone", 10000000),
    ("jam tangan smartwatch", "jam", None),
    ("apa rekomendasi tv", "tv", None),
    ("produk audio", "audio", None),
    ("coba cari notebook", "laptop", None),
    ("handphone 3 juta", "smartphone", 3000000),
    ("apa itu komputer", "laptop", None), # No price, generic category
    ("bagaimana cara memilih mouse", None, None), # No category, no price
    ("baju bagus", None, None), # Out of scope category
    ("budget 5 juta", None, 5000000), # No category, but budget present
    ("barang murah", None, 5000000), # No category, but budget present
    ("harga laptop 4.5 juta", "laptop", None), # Only 'juta' is parsed for now, no float
    ("saya mencari hp", "smartphone", None), # Simple category match
    ("laptop acer 7 juta", "laptop", 7000000), # Category and price
    ("rekomendasi terbaik", None, None), # Generic question
])
async def test_get_response_question_parsing(
    ai_service, mock_product_data_service, mock_genai_client,
    question, expected_category, expected_max_price
):
    """
    Test that get_response correctly extracts category and max_price from various questions.
    Verify that smart_search_products is called with the correct parameters.
    """
    mock_product_data_service.smart_search_products.return_value = ([], "Mocked fallback message.")
    
    await ai_service.get_response(question)
    
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, 
        category=expected_category, 
        max_price=expected_max_price, 
        limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_get_response_success_no_products(ai_service, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response when no relevant products are found.
    Verifies the prompt content and the returned AI response.
    """
    caplog.set_level(logging.INFO)
    mock_product_data_service.smart_search_products.return_value = ([], "No specific products found matching your criteria.")
    mock_genai_client.models.generate_content.return_value.text = "AI response about general recommendations."
    
    question = "rekomendasi laptop"
    response = await ai_service.get_response(question)
    
    assert response == "AI response about general recommendations."
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category="laptop", max_price=None, limit=5
    )
    
    # Check prompt content
    prompt_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = prompt_args[0].contents
    assert f"Question: {question}" in prompt
    assert "No specific products found matching your criteria." in prompt
    assert "No specific products found, but I can provide general recommendations." in prompt
    assert "Relevant Products:" not in prompt # Should not be present if no products
    assert "gemini-2.5-flash" == prompt_args[0].model
    assert "Successfully generated AI response" in caplog.text


@pytest.mark.asyncio
async def test_get_response_success_with_products(ai_service, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response when relevant products are found.
    Verifies the prompt content includes product details and the returned AI response.
    """
    caplog.set_level(logging.INFO)
    mock_products = [
        {
            "name": "Product A", "price": 10000000, "brand": "BrandX", "category": "laptop",
            "specifications": {"rating": 4.5}, "description": "This is a great product A."
        },
        {
            "name": "Product B", "price": 5000000, "brand": "BrandY", "category": "smartphone",
            "specifications": {"rating": 3.8}, "description": "Product B is affordable."
        }
    ]
    mock_product_data_service.smart_search_products.return_value = (mock_products, "Here are some relevant products.")
    mock_genai_client.models.generate_content.return_value.text = "AI response with product details."
    
    question = "cari laptop atau hp"
    response = await ai_service.get_response(question)
    
    assert response == "AI response with product details."
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    ) # Category will be None as question has both laptop and hp
    
    # Check prompt content
    prompt_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = prompt_args[0].contents
    assert f"Question: {question}" in prompt
    assert "Here are some relevant products." in prompt
    assert "Relevant Products:\n" in prompt
    assert "1. Product A\n   Price: Rp 10,000,000\n   Brand: BrandX\n   Category: laptop\n   Rating: 4.5/5\n   Description: This is a great product A..." in prompt
    assert "2. Product B\n   Price: Rp 5,000,000\n   Brand: BrandY\n   Category: smartphone\n   Rating: 3.8/5\n   Description: Product B is affordable..." in prompt
    assert "gemini-2.5-flash" == prompt_args[0].model
    assert "Successfully generated AI response" in caplog.text


@pytest.mark.asyncio
async def test_get_response_product_service_raises_exception(ai_service, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response when ProductDataService.smart_search_products raises an exception.
    Verifies that the correct fallback message is returned and an error log is recorded.
    """
    caplog.set_level(logging.ERROR)
    mock_product_data_service.smart_search_products.side_effect = Exception("Product search failed")
    
    question = "any question"
    response = await ai_service.get_response(question)
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    mock_product_data_service.smart_search_products.assert_called_once()
    mock_genai_client.models.generate_content.assert_not_called() # Should not call AI if product search fails
    assert "Error generating AI response: Product search failed" in caplog.text


@pytest.mark.asyncio
async def test_get_response_genai_client_raises_exception(ai_service, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response when the genai client's generate_content method raises an exception.
    Verifies that the correct fallback message is returned and an error log is recorded.
    """
    caplog.set_level(logging.ERROR)
    mock_product_data_service.smart_search_products.return_value = ([], "No products.")
    mock_genai_client.models.generate_content.side_effect = Exception("AI generation failed")
    
    question = "any question"
    response = await ai_service.get_response(question)
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    mock_product_data_service.smart_search_products.assert_called_once()
    mock_genai_client.models.generate_content.assert_called_once()
    assert "Error generating AI response: AI generation failed" in caplog.text

@pytest.mark.asyncio
async def test_get_response_empty_question(ai_service, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response with an empty question string.
    Ensures it still calls dependencies and produces a response.
    """
    caplog.set_level(logging.INFO)
    mock_product_data_service.smart_search_products.return_value = ([], "No products for empty query.")
    mock_genai_client.models.generate_content.return_value.text = "AI response for empty question."
    
    question = ""
    response = await ai_service.get_response(question)
    
    assert response == "AI response for empty question."
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword="", category=None, max_price=None, limit=5
    )
    prompt_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = prompt_args[0].contents
    assert "Question: \n\n" in prompt
    assert "No products for empty query." in prompt
    assert "Successfully generated AI response" in caplog.text

# --- Test cases for AIService.generate_response (legacy method) ---

def test_generate_response_success(ai_service, mock_genai_client, caplog):
    """
    Test generate_response (legacy method) for a successful AI response.
    Verifies the prompt content and the returned AI response.
    """
    caplog.set_level(logging.INFO)
    mock_genai_client.models.generate_content.return_value.text = "Legacy AI response."
    
    context = "This is a test context for the legacy method."
    response = ai_service.generate_response(context)
    
    assert response == "Legacy AI response."
    
    # Check prompt content and model
    prompt_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = prompt_args[0].contents
    assert context in prompt
    assert "You are a helpful product assistant." in prompt
    assert "gemini-2.0-flash" == prompt_args[0].model
    assert "Successfully generated AI response" in caplog.text


def test_generate_response_genai_client_raises_exception(ai_service, mock_genai_client, caplog):
    """
    Test generate_response (legacy method) when the genai client's generate_content method raises an exception.
    Verifies that the exception is re-raised and an error log is recorded.
    """
    caplog.set_level(logging.ERROR)
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI generation failed")
    
    context = "Some context"
    with pytest.raises(Exception, match="Legacy AI generation failed"):
        ai_service.generate_response(context)
    
    mock_genai_client.models.generate_content.assert_called_once()
    assert "Error generating AI response: Legacy AI generation failed" in caplog.text