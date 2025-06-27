import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import logging

from app.services.ai_service import AIService
from app.utils.config import get_settings
from app.services.product_data_service import ProductDataService
from google import genai

@pytest.fixture
def mock_get_settings(mocker):
    """Mocks app.utils.config.get_settings to return a dummy API key."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.GOOGLE_API_KEY = "dummy_api_key_123"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings_obj)
    return mock_settings_obj

@pytest.fixture
def mock_genai_client(mocker):
    """Mocks google.genai.Client and its models.generate_content method."""
    mock_client_instance = MagicMock()
    
    # Mock the models.generate_content method which should return an object with a .text attribute
    mock_response_obj = MagicMock()
    mock_response_obj.text = "AI generated response."
    mock_client_instance.models.generate_content.return_value = mock_response_obj
    
    # Patch the Client constructor itself to return our mock instance
    mocker.patch('google.genai.Client', return_value=mock_client_instance)
    
    return mock_client_instance

@pytest.fixture
def mock_product_data_service(mocker):
    """Mocks app.services.product_data_service.ProductDataService and its smart_search_products method."""
    mock_service_instance = MagicMock(spec=ProductDataService)
    # smart_search_products is async, so use AsyncMock
    mock_service_instance.smart_search_products = AsyncMock()
    
    # Patch the ProductDataService constructor to return our mock instance
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_service_instance)
    return mock_service_instance

@pytest.fixture
def ai_service_instance(mock_get_settings, mock_genai_client, mock_product_data_service):
    """Provides an AIService instance with all dependencies mocked."""
    # The mocks for get_settings, genai.Client, and ProductDataService constructors
    # are already applied by their respective fixtures before AIService is instantiated.
    service = AIService()
    return service

@pytest.fixture
def mock_logger(mocker):
    """Mocks the logger used in AIService."""
    # Patch the logger instance returned by logging.getLogger
    mock_log = mocker.patch('app.services.ai_service.logger')
    return mock_log

# Helper for creating mock product data
def create_mock_product(name, price, brand, category, rating, description):
    return {
        'name': name,
        'price': price,
        'brand': brand,
        'category': category,
        'specifications': {'rating': rating},
        'description': description
    }

# --- Test cases for __init__ ---

def test_ai_service_init_success(ai_service_instance, mock_get_settings, mock_genai_client, mock_product_data_service, mock_logger):
    """Test successful initialization of AIService."""
    # Assert that get_settings was called
    mock_get_settings.assert_called_once()
    
    # Assert that genai.Client constructor was called with the API key
    genai.Client.assert_called_once_with(api_key="dummy_api_key_123")
    assert ai_service_instance.client == mock_genai_client # Check it's the mock instance
    
    # Assert that ProductDataService constructor was called
    ProductDataService.assert_called_once()
    assert ai_service_instance.product_service == mock_product_data_service # Check it's the mock instance

    # Check logger info call
    mock_logger.info.assert_called_with("Successfully initialized AI service with Google AI client")
    mock_logger.error.assert_not_called()

def test_ai_service_init_failure_get_settings(mocker, mock_logger):
    """Test initialization failure when get_settings raises an exception."""
    mocker.patch('app.utils.config.get_settings', side_effect=ValueError("Settings error"))
    with pytest.raises(ValueError, match="Settings error"):
        AIService()
    mock_logger.error.assert_called_once_with("Error initializing AI service: Settings error")
    mock_logger.info.assert_not_called()

def test_ai_service_init_failure_genai_client(mocker, mock_get_settings, mock_logger):
    """Test initialization failure when genai.Client raises an exception."""
    mocker.patch('google.genai.Client', side_effect=ConnectionRefusedError("API connection error"))
    with pytest.raises(ConnectionRefusedError, match="API connection error"):
        AIService()
    # Check that get_settings was called before the client failed
    mock_get_settings.assert_called_once()
    mock_logger.error.assert_called_once_with("Error initializing AI service: API connection error")
    mock_logger.info.assert_not_called()

# --- Test cases for get_response ---

@pytest.mark.asyncio
async def test_get_response_no_category_no_price(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger):
    """Test get_response with a general question, no specific category or price."""
    question = "What are some good electronics?"
    mock_product_data_service.smart_search_products.return_value = (
        [], "No specific products found for your query. Here are some general recommendations."
    )
    mock_genai_client.models.generate_content.return_value.text = "AI's general response."

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    # Check the prompt content passed to the AI model
    generated_prompt = mock_genai_client.models.generate_content.call_args[1]['contents']
    assert "No specific products found, but I can provide general recommendations." in generated_prompt
    assert response == "AI's general response."
    mock_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category", [
    ("recommend a laptop", "laptop"),
    ("looking for a new hp", "smartphone"),
    ("best headphones for gaming", "headphone"),
    ("I need a kamera for photography", "kamera"),
    ("smartwatch recommendations", "jam"),
    ("audio system for my home", "audio"),
    ("what tv should I buy", "tv"),
    ("drone recommendations", "drone"),
    ("mencari komputer baru", "laptop"),
    ("handphone murah", "smartphone"),
    ("saya ingin beli tablet", "tablet"),
    ("headset gaming", "headphone"),
    ("kamera digital", "kamera"),
    ("speaker aktif", "audio"),
    ("televisi pintar", "tv"),
    ("quadcopter terbaik", "drone"),
    ("jam tangan pintar", "jam"),
])
async def test_get_response_category_extraction(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger, question, expected_category):
    """Test get_response with various category extractions."""
    mock_product_data_service.smart_search_products.return_value = (
        [], "No products found for this category."
    )
    mock_genai_client.models.generate_content.return_value.text = f"AI response for {expected_category}."

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=expected_category, max_price=None, limit=5
    )
    assert response == f"AI response for {expected_category}."
    mock_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_max_price", [
    ("laptop under 10 juta", 10_000_000),
    ("smartphone with budget 5 juta", 5_000_000),
    ("cheap headphones", 5_000_000), # default budget for 'budget' or 'murah'
    ("monitor murah", 5_000_000), # default budget
    ("anything below 2 juta", 2_000_000),
    ("budget 7 juta", 7_000_000),
])
async def test_get_response_price_extraction(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger, question, expected_max_price):
    """Test get_response with various price extractions."""
    mock_product_data_service.smart_search_products.return_value = (
        [], "No products found for this price range."
    )
    mock_genai_client.models.generate_content.return_value.text = f"AI response for {expected_max_price}."

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=None, max_price=expected_max_price, limit=5
    )
    assert response == f"AI response for {expected_max_price}."
    mock_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    ("I need a tablet with a budget of 3 juta", "tablet", 3_000_000),
    ("recommend a cheap laptop", "laptop", 5_000_000),
    ("hp under 7 juta", "smartphone", 7_000_000),
    ("camera 15 juta", "kamera", 15_000_000),
    ("headphone murah", "headphone", 5_000_000),
])
async def test_get_response_category_and_price_extraction(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger, question, expected_category, expected_max_price):
    """Test get_response with both category and price extraction."""
    mock_product_data_service.smart_search_products.return_value = (
        [], "No products found for this category and price."
    )
    mock_genai_client.models.generate_content.return_value.text = "AI response with both."

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=expected_category, max_price=expected_max_price, limit=5
    )
    assert response == "AI response with both."
    mock_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
async def test_get_response_with_found_products(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger):
    """Test get_response when smart_search_products returns relevant products."""
    question = "Looking for a good laptop"
    
    products_data = [
        create_mock_product("Gaming Laptop X", 15_000_000, "BrandA", "laptop", 4.5, "Powerful gaming laptop with high-end specs and amazing performance for all your gaming needs. This description is intentionally long to test truncation functionality up to 200 characters."),
        create_mock_product("Work Laptop Y", 8_000_000, "BrandB", "laptop", 4.0, "Slim and lightweight laptop for productivity, perfect for professionals on the go. It has a great battery life and a stunning display."),
    ]
    fallback_msg = "Here are some laptops that might fit your needs."
    
    mock_product_data_service.smart_search_products.return_value = (products_data, fallback_msg)
    mock_genai_client.models.generate_content.return_value.text = "AI response with product details."

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once()
    
    # Check context in the prompt
    generated_prompt = mock_genai_client.models.generate_content.call_args[1]['contents']
    assert f"Question: {question}" in generated_prompt
    assert fallback_msg in generated_prompt
    assert "Relevant Products:\n" in generated_prompt
    
    assert "1. Gaming Laptop X" in generated_prompt
    assert "Price: Rp 15,000,000" in generated_prompt
    assert "Brand: BrandA" in generated_prompt
    assert "Category: laptop" in generated_prompt
    assert "Rating: 4.5/5" in generated_prompt
    # Check description truncation (first 200 chars + "...")
    expected_desc1_truncated = products_data[0]['description'][:200] + "..."
    assert f"Description: {expected_desc1_truncated}" in generated_prompt
    
    assert "2. Work Laptop Y" in generated_prompt
    assert "Price: Rp 8,000,000" in generated_prompt
    assert "Brand: BrandB" in generated_prompt
    assert "Category: laptop" in generated_prompt
    assert "Rating: 4.0/5" in generated_prompt
    expected_desc2_truncated = products_data[1]['description'][:200] + "..."
    assert f"Description: {expected_desc2_truncated}" in generated_prompt

    assert response == "AI response with product details."
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
async def test_get_response_with_no_products_found(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger):
    """Test get_response when smart_search_products returns no products."""
    question = "Do you have flying cars?"
    fallback_msg = "Sorry, we don't have flying cars."
    
    mock_product_data_service.smart_search_products.return_value = ([], fallback_msg)
    mock_genai_client.models.generate_content.return_value.text = "AI says no flying cars."

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once()
    
    generated_prompt = mock_genai_client.models.generate_content.call_args[1]['contents']
    assert fallback_msg in generated_prompt
    assert "No specific products found, but I can provide general recommendations." in generated_prompt
    assert "Relevant Products:" not in generated_prompt # Ensure this section is absent
    assert response == "AI says no flying cars."
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
async def test_get_response_product_data_missing_keys(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger):
    """Test get_response gracefully handles missing keys in product data."""
    question = "Show me some gadgets"
    products_data = [
        {'name': 'Gadget A', 'price': 1000000}, # Missing brand, category, rating, description
        {'name': 'Gadget B', 'brand': 'XYZ', 'description': 'Just a gadget with a very long description that needs to be truncated to fit into the context limit provided to the AI model. This is an important test case to ensure robustness.'}, # Missing price, category, rating
        {'name': 'Gadget C', 'specifications': {'rating': 3.5}} # Missing price, brand, category, description
    ]
    fallback_msg = "Here are some gadgets."
    
    mock_product_data_service.smart_search_products.return_value = (products_data, fallback_msg)
    mock_genai_client.models.generate_content.return_value.text = "AI response with incomplete product details."

    response = await ai_service_instance.get_response(question)

    generated_prompt = mock_genai_client.models.generate_content.call_args[1]['contents']
    assert "1. Gadget A" in generated_prompt
    assert "Price: Rp 1,000,000" in generated_prompt
    assert "Brand: Unknown" in generated_prompt
    assert "Category: Unknown" in generated_prompt
    assert "Rating: 0/5" in generated_prompt
    assert "Description: No description..." in generated_prompt
    
    assert "2. Gadget B" in generated_prompt
    assert "Price: Rp 0" in generated_prompt
    assert "Brand: XYZ" in generated_prompt
    assert "Category: Unknown" in generated_prompt
    assert "Rating: 0/5" in generated_prompt
    expected_desc_b_truncated = products_data[1]['description'][:200] + "..."
    assert f"Description: {expected_desc_b_truncated}" in generated_prompt

    assert "3. Gadget C" in generated_prompt
    assert "Price: Rp 0" in generated_prompt
    assert "Brand: Unknown" in generated_prompt
    assert "Category: Unknown" in generated_prompt
    assert "Rating: 3.5/5" in generated_prompt
    assert "Description: No description..." in generated_prompt
    
    assert response == "AI response with incomplete product details."
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
async def test_get_response_empty_question(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger):
    """Test get_response with an empty question string."""
    question = ""
    mock_product_data_service.smart_search_products.return_value = ([], "Please provide a question.")
    mock_genai_client.models.generate_content.return_value.text = "AI's general response for empty question."

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    assert response == "AI's general response for empty question."
    mock_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio
async def test_get_response_product_service_exception(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger):
    """Test get_response handles exception from product_service."""
    question = "Any products?"
    mock_product_data_service.smart_search_products.side_effect = Exception("Product service error")

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_awaited_once()
    # Ensure genai.Client.models.generate_content was NOT called as exception happened before that.
    mock_genai_client.models.generate_content.assert_not_called()
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    mock_logger.error.assert_called_once_with("Error generating AI response: Product service error")
    mock_logger.info.assert_called_once_with(f"Getting AI response for question: {question}") # Still logs the start

@pytest.mark.asyncio
async def test_get_response_genai_client_exception(ai_service_instance, mock_product_data_service, mock_genai_client, mock_logger):
    """Test get_response handles exception from genai client."""
    question = "Hello AI"
    mock_product_data_service.smart_search_products.return_value = ([], "No products.")
    mock_genai_client.models.generate_content.side_effect = Exception("AI API error")

    response = await ai_service_instance.get_response(question)

    mock_genai_client.models.generate_content.assert_called_once()
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    mock_logger.error.assert_called_once_with("Error generating AI response: AI API error")
    mock_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_logger.info.assert_any_call("Successfully generated AI response") # This line is not reached on error

# --- Test cases for generate_response (legacy) ---

def test_generate_response_success(ai_service_instance, mock_genai_client, mock_logger):
    """Test generate_response with successful AI generation."""
    context = "This is a test context for the legacy method."
    mock_genai_client.models.generate_content.return_value.text = "Legacy AI response successfully generated."

    response = ai_service_instance.generate_response(context)

    # Check that generate_content was called with the correct model and prompt
    mock_genai_client.models.generate_content.assert_called_once()
    # Access arguments passed to the mocked method
    call_kwargs = mock_genai_client.models.generate_content.call_args[1]
    assert call_kwargs['model'] == "gemini-2.0-flash" # Model name
    assert "You are a helpful product assistant." in call_kwargs['contents'] # Prompt content
    assert context in call_kwargs['contents'] # Context in prompt

    assert response == "Legacy AI response successfully generated."
    mock_logger.info.assert_called_once_with("Generating AI response")
    mock_logger.info.assert_any_call("Successfully generated AI response")
    mock_logger.error.assert_not_called()

def test_generate_response_genai_client_exception(ai_service_instance, mock_genai_client, mock_logger):
    """Test generate_response handles exception from genai client."""
    context = "Error context for legacy method."
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI API error")

    with pytest.raises(Exception, match="Legacy AI API error"):
        ai_service_instance.generate_response(context)

    mock_genai_client.models.generate_content.assert_called_once()
    mock_logger.error.assert_called_once_with("Error generating AI response: Legacy AI API error")
    mock_logger.info.assert_called_once_with("Generating AI response")