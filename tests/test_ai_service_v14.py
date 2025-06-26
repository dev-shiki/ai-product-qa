import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import logging
import sys
import os

# Adjust sys.path to allow imports from the 'app' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.services.ai_service import AIService

# --- Fixtures ---

@pytest.fixture
def mock_settings():
    """Mocks the get_settings function to return a dummy API key."""
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings_instance = MagicMock()
        mock_settings_instance.GOOGLE_API_KEY = "test_api_key"
        mock_get_settings.return_value = mock_settings_instance
        yield mock_get_settings

@pytest.fixture
def mock_genai_client():
    """Mocks the google.genai.Client and its models.generate_content method."""
    with patch('google.genai.Client') as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content = MagicMock()
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def mock_product_service():
    """Mocks the ProductDataService and its smart_search_products method."""
    with patch('app.services.product_data_service.ProductDataService') as mock_product_service_class:
        mock_service_instance = AsyncMock() # smart_search_products is an async method
        mock_product_service_class.return_value = mock_service_instance
        yield mock_service_instance

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_service):
    """Provides an initialized AIService instance with mocked dependencies."""
    return AIService()

@pytest.fixture
def caplog_info(caplog):
    """Sets caplog level to INFO for easier assertion."""
    caplog.set_level(logging.INFO)
    return caplog

@pytest.fixture
def sample_products():
    """Provides a sample list of product dictionaries."""
    return [
        {
            "name": "Product A Laptop",
            "price": 10000000,
            "brand": "Brand X",
            "category": "laptop",
            "specifications": {"rating": 4.5, "processor": "i7"},
            "description": "This is a great product A with many features. It's designed for high performance and durability, suitable for professional use and casual tasks. It has a long battery life and a stunning display. This description is long to test truncation."
        },
        {
            "name": "Product B Smartphone",
            "price": 5000000,
            "brand": "Brand Y",
            "category": "smartphone",
            "specifications": {"rating": 3.8, "camera": "12MP"},
            "description": "Product B is a budget-friendly smartphone. It offers decent performance for everyday use, good camera quality in well-lit conditions, and a compact design, making it easy to carry around. This description is also long to test truncation."
        }
    ]

# --- Test AIService.__init__ ---

def test_ai_service_init_success(mock_settings, mock_genai_client, mock_product_service, caplog_info):
    """
    Test successful initialization of AIService.
    Verifies that dependencies are called and attributes are set.
    """
    service = AIService()
    mock_settings.assert_called_once()
    mock_genai_client.assert_called_once_with(api_key="test_api_key")
    mock_product_service.assert_called_once()
    assert service.client == mock_genai_client.return_value
    assert service.product_service == mock_product_service.return_value
    assert "Successfully initialized AI service with Google AI client" in caplog_info.text

def test_ai_service_init_failure_get_settings(mock_settings, caplog):
    """
    Test initialization failure when get_settings raises an exception.
    Ensures an exception is re-raised and error is logged.
    """
    mock_settings.side_effect = Exception("Config error")
    with pytest.raises(Exception, match="Config error"):
        AIService()
    mock_settings.assert_called_once()
    assert "Error initializing AI service: Config error" in caplog.text

def test_ai_service_init_failure_genai_client(mock_settings, mock_genai_client, caplog):
    """
    Test initialization failure when genai.Client raises an exception.
    Ensures an exception is re-raised and error is logged.
    """
    mock_genai_client.side_effect = Exception("API client error")
    with pytest.raises(Exception, match="API client error"):
        AIService()
    mock_settings.assert_called_once()
    mock_genai_client.assert_called_once()
    assert "Error initializing AI service: API client error" in caplog.text

# --- Test AIService.get_response ---

@pytest.mark.asyncio
async def test_get_response_success_with_products(ai_service_instance, mock_product_service, mock_genai_client, sample_products, caplog_info):
    """
    Test get_response when products are found and AI generates a successful response.
    Verifies product search, context building, and AI call.
    """
    question = "Recommend a laptop under 15 juta"
    fallback_msg = "Here are some general recommendations related to your query."
    mock_product_service.smart_search_products.return_value = (sample_products, fallback_msg)
    mock_genai_client.models.generate_content.return_value.text = "AI response about products."

    response = await ai_service_instance.get_response(question)

    mock_product_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category="laptop", max_price=15000000, limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()
    
    # Assertions on prompt content (partial check for key elements)
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args.kwargs['model'] == "gemini-2.5-flash"
    prompt = call_args.kwargs['contents']
    assert f"Question: {question}" in prompt
    assert fallback_msg in prompt
    assert "Relevant Products:\n" in prompt
    
    # Check for specific product details and truncation
    assert "1. Product A Laptop" in prompt
    assert "Price: Rp 10,000,000" in prompt
    assert "Brand: Brand X" in prompt
    assert "Category: laptop" in prompt
    assert "Rating: 4.5/5" in prompt
    assert "This is a great product A with many features. It's designed for high performance and durability, suitable for professional use and casual tasks. It has a long battery life and a stunning display..." in prompt
    assert len(prompt.split("This description is long to test truncation.")[0]) > 200 # check that it's truncated at 200 chars and ... added

    assert "2. Product B Smartphone" in prompt
    assert "Price: Rp 5,000,000" in prompt
    assert "Brand: Brand Y" in prompt
    assert "Category: smartphone" in prompt
    assert "Rating: 3.8/5" in prompt
    assert "Product B is a budget-friendly smartphone. It offers decent performance for everyday use, good camera quality in well-lit conditions, and a compact design, making it easy to carry around..." in prompt
    
    assert response == "AI response about products."
    assert f"Getting AI response for question: {question}" in caplog_info.text
    assert "Successfully generated AI response" in caplog_info.text

@pytest.mark.asyncio
async def test_get_response_success_no_products(ai_service_instance, mock_product_service, mock_genai_client, caplog_info):
    """
    Test get_response when no products are found but AI still generates a response.
    """
    question = "Tell me about cars"
    fallback_msg = "No specific product recommendations for cars were found."
    mock_product_service.smart_search_products.return_value = ([], fallback_msg)
    mock_genai_client.models.generate_content.return_value.text = "General AI response about cars."

    response = await ai_service_instance.get_response(question)

    mock_product_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()
    
    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']
    assert f"Question: {question}" in prompt
    assert fallback_msg in prompt
    assert "No specific products found, but I can provide general recommendations." in prompt
    assert "Relevant Products:" not in prompt # Make sure it's not included
    
    assert response == "General AI response about cars."
    assert f"Getting AI response for question: {question}" in caplog_info.text
    assert "Successfully generated AI response" in caplog_info.text

@pytest.mark.asyncio
async def test_get_response_fallback_message_only(ai_service_instance, mock_product_service, mock_genai_client, caplog_info):
    """
    Test get_response when product service returns no products and an empty fallback message.
    """
    question = "General query"
    mock_product_service.smart_search_products.return_value = ([], "")
    mock_genai_client.models.generate_content.return_value.text = "General AI response."

    response = await ai_service_instance.get_response(question)

    mock_product_service.smart_search_products.assert_awaited_once()
    mock_genai_client.models.generate_content.assert_called_once()
    
    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']
    assert f"Question: {question}" in prompt
    assert "\n\n\n" in prompt # Placeholder for empty fallback + newlines
    assert "No specific products found, but I can provide general recommendations." in prompt
    
    assert response == "General AI response."

@pytest.mark.asyncio
async def test_get_response_failure_product_search(ai_service_instance, mock_product_service, caplog):
    """
    Test get_response when product search fails.
    Ensures a fallback message is returned and error is logged.
    """
    question = "What is the best phone?"
    mock_product_service.smart_search_products.side_effect = Exception("Product DB error")

    response = await ai_service_instance.get_response(question)

    mock_product_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category="smartphone", max_price=None, limit=5
    )
    
    # The AI generation part should not be called if product search fails
    ai_service_instance.client.models.generate_content.assert_not_called()
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Product DB error" in caplog.text

@pytest.mark.asyncio
async def test_get_response_failure_ai_generation(ai_service_instance, mock_product_service, mock_genai_client, caplog):
    """
    Test get_response when AI content generation fails.
    Ensures a fallback message is returned and error is logged.
    """
    question = "Show me new laptops."
    mock_product_service.smart_search_products.return_value = ([], "No specific products.")
    mock_genai_client.models.generate_content.side_effect = Exception("AI API error")

    response = await ai_service_instance.get_response(question)

    mock_product_service.smart_search_products.assert_awaited_once()
    mock_genai_client.models.generate_content.assert_called_once()
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: AI API error" in caplog.text

# --- Test Input Parsing in get_response ---

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category", [
    ("what is a good laptop", "laptop"),
    ("recommend a notebook for work", "laptop"),
    ("harga komputer terbaru", "laptop"),
    ("hp terbaik", "smartphone"),
    ("cari handphone murah", "smartphone"),
    ("telepon pintar", "smartphone"),
    ("tablet untuk belajar", "tablet"),
    ("ipad pro", "tablet"),
    ("headphone bluetooth", "headphone"),
    ("earphone gaming", "headphone"),
    ("headset murah", "headphone"),
    ("camera dslr", "kamera"),
    ("fotografi keren", "kamera"),
    ("speaker aktif", "audio"),
    ("sound system", "audio"),
    ("tv pintar", "tv"),
    ("televisi 4k", "tv"),
    ("drone untuk pemula", "drone"),
    ("jam tangan pintar", "jam"),
    ("smartwatch olahraga", "jam"),
    ("what should I buy?", None), # No category
    ("tell me about apple products", None), # Not a direct category keyword
    ("cari laptop dan smartphone", "laptop"), # First match wins
    ("laptop murah", "laptop"),
])
async def test_get_response_category_detection(ai_service_instance, mock_product_service, mock_genai_client, question, expected_category):
    """
    Test the category detection logic within get_response.
    """
    mock_product_service.smart_search_products.return_value = ([], "")
    mock_genai_client.models.generate_content.return_value.text = "AI response."

    await ai_service_instance.get_response(question)
    
    mock_product_service.smart_search_products.assert_awaited_once()
    call_args = mock_product_service.smart_search_products.call_args
    assert call_args.kwargs['category'] == expected_category

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_max_price", [
    ("laptop 10 juta", 10000000),
    ("smartphone budget 5 juta", 5000000),
    ("cari laptop harga 7.5 juta", 7500000), # Non-integer juta (should be handled by int())
    ("headphone murah", 5000000), # Budget/murah keyword
    ("saya ada budget 2 juta untuk tablet", 2000000),
    ("saya ingin yang murah", 5000000),
    ("recommend a product", None), # No price keyword
    ("laptop 1000", None), # Not 'juta'
    ("harga 3 juta an", 3000000), # With ' an' suffix
    ("di bawah 5 juta", 5000000), # Only price, no category
    ("budget sekitar 4 juta", 4000000),
    ("laptop 15 Juta", 15000000), # Mixed case
])
async def test_get_response_price_detection(ai_service_instance, mock_product_service, mock_genai_client, question, expected_max_price):
    """
    Test the max_price detection logic within get_response.
    """
    mock_product_service.smart_search_products.return_value = ([], "")
    mock_genai_client.models.generate_content.return_value.text = "AI response."

    await ai_service_instance.get_response(question)
    
    mock_product_service.smart_search_products.assert_awaited_once()
    call_args = mock_product_service.smart_search_products.call_args
    assert call_args.kwargs['max_price'] == expected_max_price

@pytest.mark.asyncio
async def test_get_response_product_description_truncation(ai_service_instance, mock_product_service, mock_genai_client):
    """
    Test that product descriptions in the context are truncated to 200 characters and append '...'.
    """
    long_description = "A" * 250
    products_with_long_desc = [{
        "name": "Long Desc Product",
        "price": 1000,
        "brand": "Test",
        "category": "Test",
        "specifications": {"rating": 5},
        "description": long_description
    }]
    mock_product_service.smart_search_products.return_value = (products_with_long_desc, "")
    mock_genai_client.models.generate_content.return_value.text = "AI response."

    await ai_service_instance.get_response("test")
    
    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']
    
    expected_truncated_desc = long_description[:200] + "..."
    assert expected_truncated_desc in prompt
    assert long_description[200:] not in prompt # Ensure the rest is not there

@pytest.mark.asyncio
async def test_get_response_empty_product_details(ai_service_instance, mock_product_service, mock_genai_client):
    """
    Test that product details use default values if missing from the product dict.
    """
    product_missing_details = [{
        "name": "Missing Data Product",
        "price": None, # Missing price
        "brand": None, # Missing brand
        "category": None, # Missing category
        "specifications": {}, # Missing rating
        "description": None # Missing description
    }]
    mock_product_service.smart_search_products.return_value = (product_missing_details, "")
    mock_genai_client.models.generate_content.return_value.text = "AI response."

    await ai_service_instance.get_response("test")
    
    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']

    assert "Name: Missing Data Product" in prompt
    assert "Price: Rp 0" in prompt
    assert "Brand: Unknown" in prompt
    assert "Category: Unknown" in prompt
    assert "Rating: 0/5" in prompt
    assert "Description: No description" in prompt

@pytest.mark.asyncio
async def test_get_response_product_details_partially_missing(ai_service_instance, mock_product_service, mock_genai_client):
    """
    Test that product details use default values for specific missing keys, but present values for others.
    """
    product_partially_missing_details = [{
        "name": "Partial Data Product",
        "price": 12345,
        "brand": "Known Brand",
        "category": None, # Missing category
        "specifications": {"rating": None}, # Rating is None
        "description": "Some description here"
    }]
    mock_product_service.smart_search_products.return_value = (product_partially_missing_details, "")
    mock_genai_client.models.generate_content.return_value.text = "AI response."

    await ai_service_instance.get_response("test")
    
    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs['contents']

    assert "Name: Partial Data Product" in prompt
    assert "Price: Rp 12,345" in prompt
    assert "Brand: Known Brand" in prompt
    assert "Category: Unknown" in prompt
    assert "Rating: 0/5" in prompt # None rating defaults to 0
    assert "Description: Some description here" in prompt


# --- Test AIService.generate_response (Legacy) ---

def test_generate_response_success(ai_service_instance, mock_genai_client, caplog_info):
    """
    Test successful generation using the legacy generate_response method.
    """
    context = "This is a test context for legacy AI. It contains information about products."
    mock_genai_client.models.generate_content.return_value.text = "Legacy AI generated text based on context."

    response = ai_service_instance.generate_response(context)

    mock_genai_client.models.generate_content.assert_called_once()
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args.kwargs['model'] == "gemini-2.0-flash"
    assert call_args.kwargs['contents'] == f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    assert response == "Legacy AI generated text based on context."
    assert "Generating AI response" in caplog_info.text
    assert "Successfully generated AI response" in caplog_info.text

def test_generate_response_failure(ai_service_instance, mock_genai_client, caplog):
    """
    Test generation failure in the legacy generate_response method.
    Ensures an exception is re-raised and error is logged.
    """
    context = "This is a failing context."
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI error")

    with pytest.raises(Exception, match="Legacy AI error"):
        ai_service_instance.generate_response(context)
    
    mock_genai_client.models.generate_content.assert_called_once()
    assert "Error generating AI response: Legacy AI error" in caplog.text

def test_generate_response_empty_context(ai_service_instance, mock_genai_client, caplog_info):
    """
    Test generate_response with an empty context string.
    """
    context = ""
    mock_genai_client.models.generate_content.return_value.text = "AI response for empty context."

    response = ai_service_instance.generate_response(context)

    mock_genai_client.models.generate_content.assert_called_once()
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args.kwargs['contents'] == f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

\n
Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    assert response == "AI response for empty context."
    assert "Generating AI response" in caplog_info.text