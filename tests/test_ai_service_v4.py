import pytest
from unittest.mock import Mock, AsyncMock
import logging
import re

# Import the service under test
from app.services.ai_service import AIService
# We need to mock app.utils.config.get_settings, so importing Settings for type hinting on mock
from app.utils.config import Settings 

# Use pytest_asyncio for async tests
pytest_plugins = ('pytest_asyncio',)

# --- Fixtures ---

@pytest.fixture
def mock_settings():
    """Fixture to provide a mock Settings object."""
    settings = Mock(spec=Settings)
    settings.GOOGLE_API_KEY = "mock-api-key-123"
    return settings

@pytest.fixture
def mock_genai_client(mocker):
    """Mocks google.genai.Client and its models.generate_content method."""
    mock_client_instance = Mock()
    mock_client_instance.models.generate_content.return_value.text = "Mocked AI Response Text"
    mocker.patch('google.genai.Client', return_value=mock_client_instance)
    return mock_client_instance

@pytest.fixture
def mock_product_service(mocker):
    """Mocks ProductDataService and its smart_search_products method."""
    mock_service_instance = AsyncMock()  # Use AsyncMock because smart_search_products is async
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_service_instance)
    return mock_service_instance

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_service, mocker):
    """Fixture to provide an initialized AIService instance with all dependencies mocked."""
    # Ensure get_settings returns our mock_settings
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
    
    # Initialize the service
    service = AIService()
    return service

@pytest.fixture
def caplog_info_error(caplog):
    """Fixture to capture log messages at INFO and ERROR levels."""
    caplog.set_level(logging.INFO)
    return caplog

# --- Tests for __init__ ---

def test_ai_service_init_success(ai_service_instance, mock_settings, mock_genai_client, mock_product_service, caplog_info_error):
    """Test successful initialization of AIService."""
    assert isinstance(ai_service_instance, AIService)
    mock_genai_client.assert_called_once_with(api_key="mock-api-key-123")
    assert "Successfully initialized AI service with Google AI client" in caplog_info_error.text
    # Verify that ProductDataService was instantiated
    assert isinstance(ai_service_instance.product_service, AsyncMock)


def test_ai_service_init_failure_get_settings(mocker, caplog_info_error):
    """Test AIService initialization failure when get_settings raises an error."""
    mocker.patch('app.utils.config.get_settings', side_effect=Exception("Mock config error"))
    with pytest.raises(Exception, match="Mock config error"):
        AIService()
    assert "Error initializing AI service: Mock config error" in caplog_info_error.text


def test_ai_service_init_failure_genai_client(mocker, mock_settings, caplog_info_error):
    """Test AIService initialization failure when google.genai.Client raises an error."""
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
    mocker.patch('google.genai.Client', side_effect=Exception("Mock GenAI client error"))
    with pytest.raises(Exception, match="Mock GenAI client error"):
        AIService()
    assert "Error initializing AI service: Mock GenAI client error" in caplog_info_error.text


# --- Tests for get_response (async method) ---

@pytest.mark.asyncio
async def test_get_response_basic_question_no_products(ai_service_instance, mock_product_service, mock_genai_client, caplog_info_error):
    """Test get_response with a basic question and no products found."""
    mock_product_service.smart_search_products.return_value = ([], "No specific products found for your query.")
    
    question = "What is the best product?"
    expected_response_text = "Mocked AI Response Text"
    
    response = await ai_service_instance.get_response(question)
    
    assert response == expected_response_text
    
    mock_product_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    
    # Verify prompt content sent to the AI client
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args is not None
    prompt = call_args.kwargs['contents']
    assert f"Question: {question}" in prompt
    assert "No specific products found for your query." in prompt
    assert "No specific products found, but I can provide general recommendations." in prompt
    assert "Relevant Products:" not in prompt  # Ensure this part is not included
    assert "Successfully generated AI response" in caplog_info_error.text
    assert f"Getting AI response for question: {question}" in caplog_info_error.text


@pytest.mark.asyncio
async def test_get_response_with_products_and_fallback(ai_service_instance, mock_product_service, mock_genai_client, caplog_info_error):
    """Test get_response with products found and a fallback message."""
    mock_products = [
        {"name": "Laptop X", "price": 15000000, "brand": "BrandA", "category": "laptop", "specifications": {"rating": 4.5}, "description": "Powerful laptop for gaming and work."},
        {"name": "Laptop Y", "price": 12000000, "brand": "BrandB", "category": "laptop", "specifications": {"rating": 4.0}, "description": "Lightweight and portable laptop for everyday use."}
    ]
    fallback_msg = "Here are some laptops that match your criteria."
    mock_product_service.smart_search_products.return_value = (mock_products, fallback_msg)

    question = "Recommend a good laptop for under 20 juta"
    expected_response_text = "Mocked AI Response Text"
    
    response = await ai_service_instance.get_response(question)
    
    assert response == expected_response_text
    
    mock_product_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category="laptop", max_price=20000000, limit=5
    )
    
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args is not None
    prompt = call_args.kwargs['contents']
    assert f"Question: {question}" in prompt
    assert fallback_msg in prompt
    assert "Relevant Products:" in prompt
    assert "1. Laptop X" in prompt
    assert "Price: Rp 15,000,000" in prompt
    assert "Brand: BrandA" in prompt
    assert "Category: laptop" in prompt
    assert "Rating: 4.5/5" in prompt
    assert "Description: Powerful laptop for gaming and work..." in prompt[:200]
    assert "2. Laptop Y" in prompt
    assert "Price: Rp 12,000,000" in prompt
    assert "Brand: BrandB" in prompt
    assert "Category: laptop" in prompt
    assert "Rating: 4.0/5" in prompt
    assert "Description: Lightweight and portable laptop for everyday use..." in prompt[:200]
    assert "No specific products found, but I can provide general recommendations." not in prompt


@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    ("carikan hp bagus", "smartphone", None),
    ("smartphone budget 3 juta", "smartphone", 3000000),
    ("laptop 5 juta", "laptop", 5000000),
    ("headphone murah", "headphone", 5000000),  # Test 'murah' for default budget
    ("kamera pro dibawah 10 juta", "kamera", 10000000),
    ("tablet untuk anak", "tablet", None),
    ("rekomendasi tv", "tv", None),
    ("drone harga 2 juta", "drone", 2000000),
    ("smartwatch", "jam", None),
    ("komputer gaming", "laptop", None),  # 'komputer' maps to 'laptop'
    ("ponsel murah", "smartphone", 5000000),  # 'ponsel' maps to 'smartphone' and 'murah'
    ("audio system", "audio", None),
    ("handphone 7 juta", "smartphone", 7000000),
    ("telepon", "smartphone", None),
    ("ipad", "tablet", None),
    ("earphone", "headphone", None),
    ("headset", "headphone", None),
    ("fotografi", "kamera", None),
    ("speaker", "audio", None),
    ("televisi", "tv", None),
    ("quadcopter", "drone", None),
    ("watch", "jam", None),
    ("apa saja produk Anda?", None, None),  # No category, no price
    ("produk dibawah 2 juta", None, 2000000),  # Price only
    ("budget 5 juta", None, 5000000),  # Price only (budget keyword)
    ("harga hp 4.5 juta", "smartphone", None), # Decimal price not matched by regex
    ("handphone 5 juta rupiah", "smartphone", 5000000), # Test 'rupiah' suffix
    ("ada laptop 15juta?", "laptop", 15000000), # Test 'juta' without space
    ("saya mau beli tablet", "tablet", None),
])
async def test_get_response_category_and_price_detection(ai_service_instance, mock_product_service, mock_genai_client, question, expected_category, expected_max_price):
    """Test various question inputs for correct category and max_price detection."""
    mock_product_service.smart_search_products.return_value = ([], "No products found.")
    
    await ai_service_instance.get_response(question)
    
    mock_product_service.smart_search_products.assert_awaited_once()
    call_args = mock_product_service.smart_search_products.call_args.kwargs
    assert call_args['category'] == expected_category
    assert call_args['max_price'] == expected_max_price


@pytest.mark.asyncio
async def test_get_response_product_data_missing_fields(ai_service_instance, mock_product_service, mock_genai_client):
    """Test get_response when product data is missing some fields, verifying default values."""
    mock_products = [
        {"name": "Product A", "price": 1000000},  # Missing brand, category, specs, description
        {"name": "Product B", "brand": "BrandX", "description": "Just a product that is quite long so it should be truncated for the description field content in the prompt, let's make it more than 200 characters to ensure truncation works as expected by python slicing and adding ellipses at the end." * 5}  # Missing price, category, specs
    ]
    mock_product_service.smart_search_products.return_value = (mock_products, "Some products found.")

    question = "Show me something"
    await ai_service_instance.get_response(question)

    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']
    
    # Verify default values are used for missing fields and description truncation
    assert "1. Product A" in prompt
    assert "Price: Rp 1,000,000" in prompt
    assert "Brand: Unknown" in prompt
    assert "Category: Unknown" in prompt
    assert "Rating: 0/5" in prompt
    assert "Description: No description..." in prompt

    assert "2. Product B" in prompt
    assert "Price: Rp 0" in prompt  # Default price
    assert "Brand: BrandX" in prompt
    assert "Category: Unknown" in prompt
    assert "Rating: 0/5" in prompt
    assert "Description: Just a product that is quite long so it should be truncated for the description field content in the prompt, let's make it more than 200 characters to ensure truncation works as expected by python slicing and adding ellipses at the end..." in prompt


@pytest.mark.asyncio
async def test_get_response_empty_question(ai_service_instance, mock_product_service, mock_genai_client, caplog_info_error):
    """Test get_response with an empty question string."""
    mock_product_service.smart_search_products.return_value = ([], "No search criteria provided.")
    question = ""
    response = await ai_service_instance.get_response(question)
    
    assert response == "Mocked AI Response Text"
    mock_product_service.smart_search_products.assert_awaited_once_with(
        keyword="", category=None, max_price=None, limit=5
    )
    
    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']
    assert "Question: \n\nNo search criteria provided.\n\nNo specific products found, but I can provide general recommendations." in prompt
    assert "Getting AI response for question: " in caplog_info_error.text


@pytest.mark.asyncio
async def test_get_response_empty_fallback_message_no_products(ai_service_instance, mock_product_service, mock_genai_client):
    """Test get_response when smart_search_products returns an empty fallback message and no products."""
    mock_products = []
    fallback_msg = ""  # Empty string
    mock_product_service.smart_search_products.return_value = (mock_products, fallback_msg)

    question = "Test question"
    await ai_service_instance.get_response(question)

    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']
    # Verify the exact prompt structure with empty fallback and no products
    expected_prompt_snippet = f"Question: {question}\n\n\n\nNo specific products found, but I can provide general recommendations."
    assert expected_prompt_snippet in prompt


@pytest.mark.asyncio
async def test_get_response_smart_search_products_raises_exception(ai_service_instance, mock_product_service, caplog_info_error):
    """Test get_response error handling when smart_search_products raises an exception."""
    mock_product_service.smart_search_products.side_effect = Exception("Product search failed mock")
    
    question = "Any product?"
    response = await ai_service_instance.get_response(question)
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Product search failed mock" in caplog_info_error.text


@pytest.mark.asyncio
async def test_get_response_genai_client_raises_exception(ai_service_instance, mock_product_service, mock_genai_client, caplog_info_error):
    """Test get_response error handling when genai.Client.models.generate_content raises an exception."""
    mock_product_service.smart_search_products.return_value = ([], "No products found.")
    mock_genai_client.models.generate_content.side_effect = Exception("GenAI API error mock")
    
    question = "Ask something to AI"
    response = await ai_service_instance.get_response(question)
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: GenAI API error mock" in caplog_info_error.text


# --- Tests for generate_response (sync, legacy method) ---

def test_generate_response_success(ai_service_instance, mock_genai_client, caplog_info_error):
    """Test successful generation of AI response using the legacy method."""
    context = "This is a test context about products and their features."
    expected_response_text = "Mocked AI Response Text"
    
    response = ai_service_instance.generate_response(context)
    
    assert response == expected_response_text
    
    mock_genai_client.models.generate_content.assert_called_once()
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args is not None
    assert call_args.kwargs['model'] == "gemini-2.0-flash"
    prompt = call_args.kwargs['contents']
    assert f"Based on the following context, provide a helpful and informative response:\n\n{context}" in prompt
    assert "Successfully generated AI response" in caplog_info_error.text
    assert "Generating AI response" in caplog_info_error.text

def test_generate_response_genai_client_raises_exception(ai_service_instance, mock_genai_client, caplog_info_error):
    """Test generate_response error handling when genai.Client.models.generate_content raises an exception."""
    mock_genai_client.models.generate_content.side_effect = Exception("GenAI API error for legacy mock")
    
    context = "Some context for legacy call"
    with pytest.raises(Exception, match="GenAI API error for legacy mock"):
        ai_service_instance.generate_response(context)
    
    assert "Error generating AI response: GenAI API error for legacy mock" in caplog_info_error.text