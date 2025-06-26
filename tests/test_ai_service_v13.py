import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
import re

# Import the service under test
from app.services.ai_service import AIService

# --- Fixtures ---

@pytest.fixture
def mock_get_settings(mocker):
    """Mocks app.utils.config.get_settings to return a mock Settings object."""
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "test_api_key_123"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
    return mock_settings

@pytest.fixture
def mock_genai_client(mocker):
    """
    Mocks google.genai.Client and its models.generate_content method.
    The mock client will have a .models attribute, which has a .generate_content method,
    which returns an object with a .text attribute.
    """
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "Mocked AI response from GenAI"
    mocker.patch('google.genai.Client', return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_product_data_service(mocker):
    """
    Mocks ProductDataService and its smart_search_products method.
    smart_search_products is an async method, so it needs to be an AsyncMock.
    """
    mock_service_instance = AsyncMock()
    # Default return value for smart_search_products for basic cases
    mock_service_instance.smart_search_products.return_value = ([], "No specific products found.")
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_service_instance)
    return mock_service_instance

@pytest.fixture
def ai_service_instance(mock_get_settings, mock_genai_client, mock_product_data_service):
    """Provides an initialized AIService instance for tests."""
    return AIService()

@pytest.fixture(autouse=True)
def cap_logs(caplog):
    """Captures logs for verification and sets minimum level to INFO."""
    caplog.set_level(logging.INFO)
    yield


# --- Tests for AIService.__init__ ---

def test_ai_service_init_success(mock_get_settings, mock_genai_client, mock_product_data_service, caplog):
    """
    Test successful initialization of AIService.
    Verifies that client and product_service are set and info log is recorded.
    """
    service = AIService()
    assert service.client == mock_genai_client
    assert service.product_service == mock_product_data_service
    mock_get_settings.assert_called_once()
    mock_genai_client.assert_called_once_with(api_key="test_api_key_123")
    mock_product_data_service.assert_called_once() # Checks ProductDataService() was called
    assert "Successfully initialized AI service with Google AI client" in caplog.text

def test_ai_service_init_failure_get_settings(mocker, caplog):
    """
    Test AIService initialization failure when get_settings raises an exception.
    Verifies error logging and exception re-raising.
    """
    mocker.patch('app.utils.config.get_settings', side_effect=ValueError("Settings loading failed"))
    
    with pytest.raises(ValueError, match="Settings loading failed"):
        AIService()
    assert "Error initializing AI service: Settings loading failed" in caplog.text
    assert "ERROR" in caplog.text # Ensure it's logged as an error

def test_ai_service_init_failure_genai_client(mock_get_settings, mocker, caplog):
    """
    Test AIService initialization failure when genai.Client raises an exception.
    Verifies error logging and exception re-raising.
    """
    mocker.patch('google.genai.Client', side_effect=Exception("Google AI Client instantiation error"))
    
    with pytest.raises(Exception, match="Google AI Client instantiation error"):
        AIService()
    assert "Error initializing AI service: Google AI Client instantiation error" in caplog.text
    assert "ERROR" in caplog.text # Ensure it's logged as an error


# --- Tests for AIService.get_response ---

@pytest.mark.asyncio
async def test_get_response_success_with_products(
    ai_service_instance, mock_product_data_service, mock_genai_client, caplog
):
    """
    Test get_response when product search returns relevant products.
    Verifies correct context building, AI content generation, and info logging.
    """
    question = "Cari laptop gaming dengan budget 15 juta"
    
    mock_products = [
        {'name': 'Gaming Laptop X', 'price': 14500000, 'brand': 'Brand A', 'category': 'laptop', 'specifications': {'rating': 4.5}, 'description': 'Powerful gaming laptop with RTX 3080 and a fast SSD. Ideal for demanding games and creative tasks. Long battery life and sleek design.'},
        {'name': 'Gaming Laptop Y', 'price': 13000000, 'brand': 'Brand B', 'category': 'laptop', 'specifications': {'rating': 4.2}, 'description': 'Affordable gaming laptop with good performance. Suitable for casual gamers and everyday use.'}
    ]
    mock_fallback_message = "Found some great gaming laptops for you!"
    mock_product_data_service.smart_search_products.return_value = (mock_products, mock_fallback_message)
    
    expected_ai_response = "Here are some gaming laptops based on your budget: Gaming Laptop X and Gaming Laptop Y..."
    mock_genai_client.models.generate_content.return_value.text = expected_ai_response

    response = await ai_service_instance.get_response(question)

    assert response == expected_ai_response
    assert f"Getting AI response for question: {question}" in caplog.text
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category='laptop', max_price=15000000, limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()
    
    # Verify prompt content
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']
    assert "gemini-2.5-flash" == call_args[0]['model'] # Ensure correct model is used
    assert f"Question: {question}" in prompt
    assert f"{mock_fallback_message}" in prompt
    assert "Relevant Products:\n" in prompt
    assert "1. Gaming Laptop X" in prompt
    assert "   Price: Rp 14,500,000" in prompt
    assert "   Brand: Brand A" in prompt
    assert "   Category: laptop" in prompt
    assert "   Rating: 4.5/5" in prompt
    assert "   Description: Powerful gaming laptop with RTX 3080 and a fast SSD. Ideal for demanding games and creative tasks. Long battery life and sleek design."[:200] + "..." in prompt
    assert "2. Gaming Laptop Y" in prompt
    assert "   Price: Rp 13,000,000" in prompt
    assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
async def test_get_response_success_no_products(
    ai_service_instance, mock_product_data_service, mock_genai_client, caplog
):
    """
    Test get_response when product search returns no relevant products.
    Verifies correct context building for no products and AI content generation.
    """
    question = "Can you recommend a flying car from 2050?" # Unlikely to find products
    
    mock_product_data_service.smart_search_products.return_value = ([], "I couldn't find any flying cars, but I can help with other products.")
    
    expected_ai_response = "Sorry, I cannot find any flying cars, but I can suggest some futuristic gadgets."
    mock_genai_client.models.generate_content.return_value.text = expected_ai_response

    response = await ai_service_instance.get_response(question)

    assert response == expected_ai_response
    assert f"Getting AI response for question: {question}" in caplog.text
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()
    
    # Verify prompt content
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']
    assert f"Question: {question}" in prompt
    assert "No specific products found, but I can provide general recommendations." in prompt
    assert "Successfully generated AI response" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    ("rekomendasi laptop", "laptop", None),
    ("smartphone budget 5 juta", "smartphone", 5000000),
    ("hp murah", "smartphone", 5000000), # Test 'hp' keyword for smartphone
    ("headphone murah", "headphone", 5000000),
    ("cari tablet 2 juta", "tablet", 2000000),
    ("kamera bagus dibawah 10 juta", "kamera", 10000000),
    ("tv LED", "tv", None),
    ("saya mau beli handphone", "smartphone", None),
    ("berapa harga smartwatch", "jam", None),
    ("drone untuk pemula", "drone", None),
    ("speaker aktif", "audio", None),
    ("saya mencari notebook", "laptop", None),
    ("rekomendasi komputer", "laptop", None),
    ("phone terbaik", "smartphone", None),
    ("earphone nirkabel", "headphone", None),
    ("headset gaming", "headphone", None),
    ("ipad pro", "tablet", None),
    ("audio system", "audio", None),
    ("fotografi untuk pemula", "kamera", None),
    ("sound system", "audio", None),
    ("televisi pintar", "tv", None),
    ("quadcopter dji", "drone", None),
    ("watch series", "jam", None),
    ("ponsel terbaru", "smartphone", None),
    ("telepon rumah", "smartphone", None), # 'telepon' maps to smartphone
    ("barang apa saja di bawah 3 juta", None, 3000000), # Price without explicit category
    ("budget sekitar 7 juta", None, 7000000), # 'budget' keyword with explicit amount
    ("saya mau yang murah", None, 5000000), # Only 'murah' keyword
    ("apakah ada produk baru", None, None), # No category or price keywords
    ("tidak ada kategori spesifik atau harga", None, None), # No category or price keywords
    ("berapa harga laptop 10 juta", "laptop", 10000000), # Explicit category and price
    ("harga hp 1.5 juta", "smartphone", 1500000) # Price with decimal implied, should still catch integer part
])
async def test_get_response_category_and_price_detection(
    ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_category, expected_max_price
):
    """
    Test various question inputs for correct category and max_price extraction.
    This covers the regex and keyword matching logic.
    """
    mock_product_data_service.smart_search_products.return_value = ([], "Mocked fallback")
    mock_genai_client.models.generate_content.return_value.text = "Mocked AI response"

    await ai_service_instance.get_response(question)
    
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category=expected_category, max_price=expected_max_price, limit=5
    )


@pytest.mark.asyncio
async def test_get_response_product_details_in_context_full(
    ai_service_instance, mock_product_data_service, mock_genai_client
):
    """
    Test that all relevant product details are correctly formatted into the AI context
    when all product fields are present and description is long.
    """
    question = "Laptop gaming murah"
    long_description = "A high-performance laptop for professionals and gamers. Features a fast processor, ample RAM, and a dedicated graphics card. Designed for efficiency and power. Excellent battery life for on-the-go productivity. Sleek design and durable build quality. Comes with pre-installed Windows 11. This is a very long description to test truncation."
    mock_products = [
        {
            'name': 'SuperBook Pro',
            'price': 12345678,
            'brand': 'TechGenius',
            'category': 'laptop',
            'specifications': {'rating': 4.8},
            'description': long_description
        }
    ]
    mock_fallback_message = "Here's a top pick for your budget!"
    mock_product_data_service.smart_search_products.return_value = (mock_products, mock_fallback_message)
    mock_genai_client.models.generate_content.return_value.text = "AI response about SuperBook Pro."

    await ai_service_instance.get_response(question)
    
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']

    assert "Relevant Products:\n" in prompt
    assert "1. SuperBook Pro" in prompt
    assert "   Price: Rp 12,345,678" in prompt
    assert "   Brand: TechGenius" in prompt
    assert "   Category: laptop" in prompt
    assert "   Rating: 4.8/5" in prompt
    # Check for description truncation and '...'
    assert prompt.count(long_description[:200] + "...") == 1


@pytest.mark.asyncio
async def test_get_response_product_details_in_context_missing_keys(
    ai_service_instance, mock_product_data_service, mock_genai_client
):
    """
    Test that product details are correctly formatted into the AI context
    when some product fields are missing or rating is not available.
    """
    question = "Simple gadget"
    short_description = "This is a simple device." # Shorter than 200 chars
    mock_products = [
        {
            'name': 'Basic Gadget',
            # Missing 'price', 'brand', 'category'
            'specifications': {}, # No 'rating'
            'description': short_description
        },
        {
            'name': 'Another Gadget',
            'price': None, # Price is None
            'brand': None, # Brand is None
            'category': 'Unknown Category',
            'specifications': {'rating': None}, # Rating is None
            'description': None # Description is None
        }
    ]
    mock_fallback_message = "Some general gadgets for you."
    mock_product_data_service.smart_search_products.return_value = (mock_products, mock_fallback_message)
    mock_genai_client.models.generate_content.return_value.text = "AI response."

    await ai_service_instance.get_response(question)
    
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']

    # Test Basic Gadget (missing keys)
    assert "1. Basic Gadget" in prompt
    assert "   Price: Rp 0" in prompt
    assert "   Brand: Unknown" in prompt
    assert "   Category: Unknown" in prompt
    assert "   Rating: 0/5" in prompt
    assert f"   Description: {short_description}..." in prompt # Shorter descriptions also get '...'

    # Test Another Gadget (None values)
    assert "2. Another Gadget" in prompt
    assert "   Price: Rp 0" in prompt
    assert "   Brand: Unknown" in prompt
    assert "   Category: Unknown Category" in prompt
    assert "   Rating: 0/5" in prompt
    assert "   Description: No description..." in prompt


@pytest.mark.asyncio
async def test_get_response_error_product_search_failure(
    ai_service_instance, mock_product_data_service, caplog
):
    """
    Test get_response when smart_search_products raises an exception.
    Verifies error logging and returns the fallback error message.
    """
    mock_product_data_service.smart_search_products.side_effect = Exception("Product search API failed unexpectedly")
    
    response = await ai_service_instance.get_response("test question")
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Product search API failed unexpectedly" in caplog.text
    assert "ERROR" in caplog.text # Ensure it's logged as an error

@pytest.mark.asyncio
async def test_get_response_error_genai_failure(
    ai_service_instance, mock_product_data_service, mock_genai_client, caplog
):
    """
    Test get_response when generate_content raises an exception.
    Verifies error logging and returns the fallback error message.
    """
    mock_genai_client.models.generate_content.side_effect = Exception("Google AI API communication error")
    
    response = await ai_service_instance.get_response("test question")
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Google AI API communication error" in caplog.text
    assert "ERROR" in caplog.text # Ensure it's logged as an error

@pytest.mark.asyncio
async def test_get_response_empty_question(
    ai_service_instance, mock_product_data_service, mock_genai_client, caplog
):
    """
    Test get_response with an empty question string.
    Ensures graceful handling (no crash) and correct behavior (no category/price, generic search).
    """
    question = ""
    mock_product_data_service.smart_search_products.return_value = ([], "No query, no specific results.")
    mock_genai_client.models.generate_content.return_value.text = "Generic AI response for empty query."

    response = await ai_service_instance.get_response(question)
    
    assert response == "Generic AI response for empty query."
    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    # Check that the prompt contains the empty question
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']
    assert f"Question: {question}" in prompt # Should still include the empty question string
    assert "Successfully generated AI response" in caplog.text


# --- Tests for AIService.generate_response --- (Legacy method)

def test_generate_response_success(ai_service_instance, mock_genai_client, caplog):
    """
    Test successful generation of AI response using the legacy method.
    Verifies correct prompt building, AI content generation, and info logging.
    """
    context = "User is asking about general product categories, specifically 'electronics'."
    expected_ai_response = "Here are some general electronics recommendations."
    mock_genai_client.models.generate_content.return_value.text = expected_ai_response

    response = ai_service_instance.generate_response(context)

    assert response == expected_ai_response
    assert "Generating AI response" in caplog.text
    mock_genai_client.models.generate_content.assert_called_once()
    
    # Verify prompt content for legacy method
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']
    expected_prompt_structure = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    assert prompt == expected_prompt_structure
    assert call_args[0]['model'] == "gemini-2.0-flash" # Ensure correct legacy model is used
    assert "Successfully generated AI response" in caplog.text


def test_generate_response_error_genai_failure(ai_service_instance, mock_genai_client, caplog):
    """
    Test generate_response when generate_content raises an exception.
    Verifies error logging and exception re-raising, as per the method's behavior.
    """
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI service internal error")
    context = "Some context for legacy call"
    
    with pytest.raises(Exception, match="Legacy AI service internal error"):
        ai_service_instance.generate_response(context)
        
    assert "Error generating AI response: Legacy AI service internal error" in caplog.text
    assert "ERROR" in caplog.text # Ensure it's logged as an error