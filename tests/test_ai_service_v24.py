import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch

# Configure logging for tests to capture output if needed, or disable
# caplog fixture will capture logs, so no global disabling is strictly necessary.
# logging.getLogger().setLevel(logging.INFO) 
# logging.getLogger('app.services.ai_service').setLevel(logging.DEBUG)


# Import the class to be tested
from app.services.ai_service import AIService

# --- Fixtures ---

@pytest.fixture
def mock_get_settings():
    """Mock for app.utils.config.get_settings"""
    with patch('app.utils.config.get_settings') as mock:
        # Ensure the mock returns an object with a GOOGLE_API_KEY attribute
        mock_settings = MagicMock(GOOGLE_API_KEY="test_api_key")
        mock.return_value = mock_settings
        yield mock

@pytest.fixture
def mock_genai_client():
    """Mock for google.genai.Client and its methods"""
    with patch('google.genai.Client') as mock_client_class:
        mock_instance = MagicMock()
        # Mock the models attribute and its generate_content method
        mock_instance.models.generate_content = MagicMock()
        mock_client_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_product_data_service():
    """Mock for app.services.product_data_service.ProductDataService"""
    with patch('app.services.product_data_service.ProductDataService') as mock_service_class:
        # The instance returned by ProductDataService() needs to be an AsyncMock
        # because its smart_search_products method is an async function.
        mock_instance = AsyncMock() 
        mock_instance.smart_search_products = AsyncMock() # Ensure this is also an AsyncMock
        mock_service_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def ai_service_instance(mock_get_settings, mock_genai_client, mock_product_data_service):
    """Fixture to provide a properly initialized AIService instance."""
    return AIService()

# --- Tests for AIService.__init__ ---

def test_aiservice_init_success(mock_get_settings, mock_genai_client, mock_product_data_service, caplog):
    """Test successful initialization of AIService."""
    with caplog.at_level(logging.INFO):
        service = AIService()
    
    mock_get_settings.assert_called_once()
    mock_genai_client.assert_called_once_with(api_key="test_api_key")
    mock_product_data_service.assert_called_once()
    assert isinstance(service.client, MagicMock)
    assert isinstance(service.product_service, AsyncMock) # Ensure it's the mocked instance
    assert "Successfully initialized AI service with Google AI client" in caplog.text

def test_aiservice_init_get_settings_error(mock_get_settings, caplog):
    """Test initialization when get_settings raises an error."""
    mock_get_settings.side_effect = ValueError("Settings API key missing")
    
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="Settings API key missing"):
            AIService()
    assert "Error initializing AI service: Settings API key missing" in caplog.text

def test_aiservice_init_genai_client_error(mock_get_settings, mock_genai_client, caplog):
    """Test initialization when genai.Client raises an error."""
    mock_genai_client.side_effect = Exception("GenAI client failed to initialize")
    
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="GenAI client failed to initialize"):
            AIService()
    assert "Error initializing AI service: GenAI client failed to initialize" in caplog.text

# --- Tests for AIService.get_response ---

@pytest.mark.asyncio
async def test_get_response_success_with_products(ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response with successful product search and AI generation, 
    including detailed context building and description truncation.
    """
    question = "Cari laptop gaming dengan budget 15 juta dan performa bagus"
    
    # A description longer than 200 characters to test truncation
    long_description = (
        "This is a very long and detailed description for a powerful gaming laptop. "
        "It covers all the essential aspects, including its cutting-edge processor, "
        "high-end dedicated GPU, ample RAM, fast SSD storage, vibrant display, "
        "and advanced cooling system. Users will find it incredibly useful for making "
        "an informed decision about their next purchase, ensuring they get the best "
        "value and performance for their gaming needs. This part should be truncated."
    )
    
    mock_products = [
        {
            'name': 'Ultimate Gaming Laptop', 
            'price': 14500000, 
            'brand': 'BrandX', 
            'category': 'laptop', 
            'specifications': {'rating': 4.8}, 
            'description': long_description
        },
        {
            'name': 'Pro Gamer Notebook', 
            'price': 13000000, 
            'brand': 'BrandY', 
            'category': 'laptop', 
            'specifications': {'rating': 4.5}, 
            'description': 'Compact and powerful gaming laptop.'
        }
    ]
    
    mock_product_data_service.smart_search_products.return_value = (mock_products, "Here are some top-tier gaming laptops matching your criteria.")
    
    # Simulate the genai response object with a .text attribute
    mock_genai_client.models.generate_content.return_value = MagicMock(text="Here are some great gaming laptops for you: Ultimate Gaming Laptop and Pro Gamer Notebook.")

    with caplog.at_level(logging.INFO):
        response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category='laptop', max_price=15000000, limit=5
    )
    
    # Assert genai client was called with the correct prompt
    args, kwargs = mock_genai_client.models.generate_content.call_args
    prompt = kwargs['contents']
    
    assert "You are a helpful product assistant." in prompt
    assert f"Question: {question}" in prompt
    assert "Here are some top-tier gaming laptops matching your criteria." in prompt
    assert "Relevant Products:\n" in prompt
    assert "1. Ultimate Gaming Laptop" in prompt
    assert "Price: Rp 14,500,000" in prompt
    assert "Brand: BrandX" in prompt
    assert "Category: laptop" in prompt
    assert "Rating: 4.8/5" in prompt
    
    # Verify description truncation
    expected_truncated_desc = long_description[:200] + "..."
    assert f"Description: {expected_truncated_desc}\n" in prompt 
    
    assert "2. Pro Gamer Notebook" in prompt
    assert "No specific products found" not in prompt # Should not be present if products are found
    assert kwargs['model'] == "gemini-2.5-flash"
    
    assert response == "Here are some great gaming laptops for you: Ultimate Gaming Laptop and Pro Gamer Notebook."
    assert f"Getting AI response for question: {question}" in caplog.text
    assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
async def test_get_response_success_no_products(ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
    """Test get_response when no products are found for the query."""
    question = "Cari produk sangat langka yang tidak mungkin ada"
    
    mock_product_data_service.smart_search_products.return_value = ([], "No products found for your specific query. Please try a different keyword or category.")
    mock_genai_client.models.generate_content.return_value = MagicMock(text="I couldn't find any specific products, but I can offer general advice or help you search for something else.")

    with caplog.at_level(logging.INFO):
        response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    
    args, kwargs = mock_genai_client.models.generate_content.call_args
    prompt = kwargs['contents']
    assert f"Question: {question}" in prompt
    assert "No products found for your specific query. Please try a different keyword or category." in prompt
    assert "Relevant Products:" not in prompt # Should not be present
    assert "No specific products found, but I can provide general recommendations." in prompt # This fallback message is hardcoded in the service
    assert kwargs['model'] == "gemini-2.5-flash"
    
    assert response == "I couldn't find any specific products, but I can offer general advice or help you search for something else."
    assert f"Getting AI response for question: {question}" in caplog.text
    assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    ("cari laptop terbaru", "laptop", None),
    ("smartphone budget 5 juta", "smartphone", 5000000),
    ("headphone murah", "headphone", 5000000), # "murah" maps to 5jt
    ("tablet di bawah 10 juta", "tablet", 10000000),
    ("kamera profesional", "kamera", None),
    ("beli tv", "tv", None),
    ("jam tangan pintar terbaik", "jam", None),
    ("drone untuk pemula 2 juta", "drone", 2000000),
    ("earphone gaming", "headphone", None),
    ("komputer desktop", "laptop", None), # 'komputer' maps to laptop
    ("hp harga 3 juta", "smartphone", 3000000),
    ("ponsel paling murah", "smartphone", 5000000), # 'murah' maps to 5jt
    ("speaker aktif", "audio", None), # 'audio' keyword covers speaker
    ("televisi 7 juta", "tv", 7000000),
    ("ipad 8 juta", "tablet", 8000000), # 'ipad' maps to tablet
    ("audio system", "audio", None),
    ("smartwatch", "jam", None),
    ("saya mau beli sesuatu", None, None), # No category/price detected
    ("Monitor gaming harga 1 juta", None, 1000000), # 'monitor' not in category_mapping, but price is detected
    ("apa rekomendasi sepatu lari?", None, None), # Completely outside product categories
])
async def test_get_response_category_price_detection(ai_service_instance, mock_product_data_service, mock_genai_client,
                                                     question, expected_category, expected_max_price):
    """Test that category and max_price are correctly extracted from various question patterns."""
    mock_product_data_service.smart_search_products.return_value = ([], "Search performed.")
    mock_genai_client.models.generate_content.return_value = MagicMock(text="AI response placeholder.")

    await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category=expected_category, max_price=expected_max_price, limit=5
    )

@pytest.mark.asyncio
async def test_get_response_product_service_exception(ai_service_instance, mock_product_data_service, caplog):
    """Test get_response when smart_search_products raises an exception."""
    question = "cari laptop"
    mock_product_data_service.smart_search_products.side_effect = Exception("Database connection error")

    with caplog.at_level(logging.ERROR):
        response = await ai_service_instance.get_response(question)
    
    assert "Error generating AI response: Database connection error" in caplog.text
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

@pytest.mark.asyncio
async def test_get_response_genai_api_exception(ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
    """Test get_response when genai.Client.models.generate_content raises an exception."""
    question = "test question for API error"
    mock_product_data_service.smart_search_products.return_value = ([], "No products.")
    mock_genai_client.models.generate_content.side_effect = Exception("Google AI API rate limit exceeded")

    with caplog.at_level(logging.ERROR):
        response = await ai_service_instance.get_response(question)
    
    assert "Error generating AI response: Google AI API rate limit exceeded" in caplog.text
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

# --- Tests for AIService.generate_response (legacy method) ---

def test_generate_response_success(ai_service_instance, mock_genai_client, caplog):
    """Test successful generation of response using the legacy generate_response method."""
    context = "This is a detailed context about specific product features for user. The user is looking for a budget smartphone."
    mock_genai_client.models.generate_content.return_value = MagicMock(text="AI response based on the provided context.")

    with caplog.at_level(logging.INFO):
        response = ai_service_instance.generate_response(context)

    # Verify the genai client was called with the correct model and prompt
    mock_genai_client.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    )
    assert response == "AI response based on the provided context."
    assert "Generating AI response" in caplog.text
    assert "Successfully generated AI response" in caplog.text

def test_generate_response_genai_api_exception(ai_service_instance, mock_genai_client, caplog):
    """Test generate_response when genai.Client.models.generate_content raises an exception."""
    context = "Error context for legacy method."
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy API call failed")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Legacy API call failed"):
            ai_service_instance.generate_response(context)
    
    assert "Error generating AI response: Legacy API call failed" in caplog.text