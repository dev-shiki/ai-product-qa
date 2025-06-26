import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.ai_service import AIService
from app.utils.config import Settings # Import Settings to properly type hint the mock

# Fixture to mock get_settings for all tests
@pytest.fixture
def mock_settings(mocker):
    """Mocks the get_settings function to return a predefined Settings object."""
    mock_settings_obj = MagicMock(spec=Settings)
    mock_settings_obj.GOOGLE_API_KEY = "test_api_key_123"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings_obj)
    return mock_settings_obj

# Fixture to mock google.genai.Client
@pytest.fixture
def mock_genai_client(mocker):
    """Mocks the google.genai.Client and its models.generate_content method."""
    # Mock the Client constructor
    mock_client_cls = mocker.patch('google.genai.Client')
    # Create a mock instance that will be returned when Client() is called
    mock_client_instance = MagicMock()
    mock_client_cls.return_value = mock_client_instance
    
    # Setup the chain for generate_content
    # The return value of generate_content needs a .text attribute
    mock_response_object = MagicMock()
    mock_response_object.text = "Mocked AI response content from Gemini"
    mock_client_instance.models.generate_content.return_value = mock_response_object
    
    return mock_client_instance

# Fixture to mock ProductDataService
@pytest.fixture
def mock_product_data_service(mocker):
    """Mocks the ProductDataService and its smart_search_products method."""
    # Mock the ProductDataService constructor
    mock_pds_cls = mocker.patch('app.services.product_data_service.ProductDataService')
    # Create a mock instance that will be returned when ProductDataService() is called
    mock_pds_instance = MagicMock()
    mock_pds_cls.return_value = mock_pds_instance
    
    # Setup the async method smart_search_products
    mock_pds_instance.smart_search_products = AsyncMock(return_value=(
        [], "No specific products found for your query. Here are some general recommendations."
    ))
    return mock_pds_instance

# AIService fixture that uses the above mocks
@pytest.fixture
def ai_service(mock_settings, mock_genai_client, mock_product_data_service):
    """Provides an initialized AIService instance with mocked dependencies."""
    # Ensure the AIService is initialized with the mocked dependencies
    service = AIService()
    return service

# --- Test AIService.__init__ ---

def test_aiservice_init_success(ai_service, mock_settings, mock_genai_client, mock_product_data_service, caplog):
    """
    Test successful initialization of AIService.
    Verifies that client and product_service are set correctly and info log is emitted.
    """
    with caplog.at_level(logging.INFO):
        # The ai_service fixture already initializes it, so just assert
        assert ai_service.client == mock_genai_client
        assert ai_service.product_service == mock_product_data_service
        assert "Successfully initialized AI service with Google AI client" in caplog.text

def test_aiservice_init_get_settings_failure(mocker, caplog):
    """
    Test AIService initialization failure when get_settings raises an exception.
    Verifies exception re-raise and error logging.
    """
    mocker.patch('app.utils.config.get_settings', side_effect=ValueError("Settings error occurred"))
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match="Settings error occurred"):
            AIService()
        assert "Error initializing AI service: Settings error occurred" in caplog.text

def test_aiservice_init_genai_client_failure(mock_settings, mocker, caplog):
    """
    Test AIService initialization failure when genai.Client construction raises an exception.
    Verifies exception re-raise and error logging.
    """
    mocker.patch('google.genai.Client', side_effect=Exception("Client init error"))
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Client init error"):
            AIService()
        assert "Error initializing AI service: Client init error" in caplog.text

def test_aiservice_init_product_data_service_failure(mock_settings, mock_genai_client, mocker, caplog):
    """
    Test AIService initialization failure when ProductDataService construction raises an exception.
    Verifies exception re-raise and error logging.
    """
    mocker.patch('app.services.product_data_service.ProductDataService', side_effect=Exception("PDS init error"))
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="PDS init error"):
            AIService()
        assert "Error initializing AI service: PDS init error" in caplog.text

# --- Test AIService.get_response ---

@pytest.mark.asyncio
async def test_get_response_basic_question_with_products(ai_service, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response with a basic question where product_service returns products.
    Verifies correct product context building, smart_search_products call, and AI response generation.
    """
    mock_products = [
        {
            'name': 'Laptop X Series',
            'price': 15000000,
            'brand': 'BrandL',
            'category': 'laptop',
            'specifications': {'rating': 4.7},
            'description': 'A powerful gaming laptop with high specs and impressive RGB lighting features.'
        },
        {
            'name': 'Smartphone Y Pro',
            'price': 8000000,
            'brand': 'BrandS',
            'category': 'smartphone',
            'specifications': {'rating': 4.2},
            'description': 'A versatile smartphone with a great camera, long battery life, and sleek design.'
        }
    ]
    mock_fallback_message = "Found some relevant products for your query."
    mock_product_data_service.smart_search_products.return_value = (mock_products, mock_fallback_message)
    
    question = "recommend me a good gadget"
    expected_ai_response = "Mocked AI response content from Gemini"

    with caplog.at_level(logging.INFO):
        response = await ai_service.get_response(question)

        assert response == expected_ai_response
        mock_product_data_service.smart_search_products.assert_awaited_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        
        # Verify prompt content
        mock_genai_client.models.generate_content.assert_called_once()
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = args[0]
        
        assert kwargs['model'] == "gemini-2.5-flash"
        assert "You are a helpful product assistant." in prompt
        assert f"Question: {question}" in prompt
        assert mock_fallback_message in prompt
        assert "Relevant Products:" in prompt
        assert "1. Laptop X Series" in prompt
        assert "Price: Rp 15,000,000" in prompt # Verifies price formatting
        assert "Brand: BrandL" in prompt
        assert "Category: laptop" in prompt
        assert "Rating: 4.7/5" in prompt
        assert "Description: A powerful gaming laptop with high specs and impressive RGB lighting features" in prompt # Check full description as it's short
        assert "2. Smartphone Y Pro" in prompt
        assert "Price: Rp 8,000,000" in prompt
        assert "Rating: 4.2/5" in prompt
        assert "Successfully generated AI response" in caplog.text
        assert f"Getting AI response for question: {question}" in caplog.text


@pytest.mark.asyncio
async def test_get_response_no_products_found(ai_service, mock_product_data_service, mock_genai_client, caplog):
    """
    Test get_response when product_service returns no products.
    Verifies that the "No specific products found" message is included in the prompt.
    """
    mock_product_data_service.smart_search_products.return_value = (
        [], "I couldn't find specific products matching your exact query. However, I can provide general information."
    )
    
    question = "tell me about smart homes in general"
    expected_ai_response = "Mocked AI response content from Gemini"

    with caplog.at_level(logging.INFO):
        response = await ai_service.get_response(question)

        assert response == expected_ai_response
        mock_product_data_service.smart_search_products.assert_awaited_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        
        mock_genai_client.models.generate_content.assert_called_once()
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = args[0]
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category", [
    ("saya mau beli laptop", "laptop"),
    ("cari notebook yang bagus", "laptop"),
    ("hp terbaru", "smartphone"),
    ("handphone murah", "smartphone"),
    ("ipad pro", "tablet"),
    ("headset gaming", "headphone"),
    ("kamera dslr", "kamera"),
    ("speaker bluetooth", "audio"),
    ("tv 4k", "tv"),
    ("drone dji", "drone"),
    ("smartwatch", "jam"),
    ("apakah ada telepon yang bagus?", "smartphone"),
    ("cari komputer", "laptop"),
    ("earphone nirkabel", "headphone"),
    ("fotografi untuk pemula", "kamera"),
    ("bagaimana kualitas sound di speaker ini?", "audio"),
    ("televisi terbaik", "tv"),
    ("quadcopter murah", "drone"),
    ("jam tangan pintar", "jam"),
])
async def test_get_response_category_detection(ai_service, mock_product_data_service, question, expected_category):
    """
    Test various category detections based on keywords in the question.
    Verifies that smart_search_products is called with the correct category.
    """
    await ai_service.get_response(question)
    mock_product_data_service.smart_search_products.assert_awaited_once()
    args, kwargs = mock_product_data_service.smart_search_products.call_args
    assert kwargs['category'] == expected_category

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_max_price", [
    ("laptop 10 juta", 10000000),
    ("smartphone budget 5 juta", 5000000),
    ("cari tablet dibawah 3 juta", 3000000),
    ("headphone 1 juta", 1000000),
    ("tv 25 juta rupiah", 25000000),
    ("berapa harga jam 20 juta?", 20000000),
])
async def test_get_response_price_detection_juta(ai_service, mock_product_data_service, question, expected_max_price):
    """
    Test price detection based on "juta" format in the question.
    Verifies that smart_search_products is called with the correct max_price.
    """
    await ai_service.get_response(question)
    mock_product_data_service.smart_search_products.assert_awaited_once()
    args, kwargs = mock_product_data_service.smart_search_products.call_args
    assert kwargs['max_price'] == expected_max_price

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_max_price", [
    ("cari smartphone murah", 5000000),
    ("laptop dengan budget terbatas", 5000000),
    ("rekomendasi tablet budget", 5000000),
    ("headphone murah tapi bagus", 5000000),
    ("kamera budget pelajar", 5000000),
])
async def test_get_response_price_detection_budget_murah(ai_service, mock_product_data_service, question, expected_max_price):
    """
    Test price detection based on "budget" or "murah" keywords in the question.
    Verifies that smart_search_products is called with the default max_price (5,000,000).
    """
    await ai_service.get_response(question)
    mock_product_data_service.smart_search_products.assert_awaited_once()
    args, kwargs = mock_product_data_service.smart_search_products.call_args
    assert kwargs['max_price'] == expected_max_price

@pytest.mark.asyncio
async def test_get_response_category_and_price_detection(ai_service, mock_product_data_service):
    """
    Test combined category and price detection in the question.
    Verifies both category and max_price are correctly extracted.
    """
    question = "cari laptop gaming 20 juta"
    await ai_service.get_response(question)
    mock_product_data_service.smart_search_products.assert_awaited_once()
    args, kwargs = mock_product_data_service.smart_search_products.call_args
    assert kwargs['category'] == 'laptop'
    assert kwargs['max_price'] == 20000000

@pytest.mark.asyncio
async def test_get_response_no_category_no_price(ai_service, mock_product_data_service):
    """
    Test get_response with a question that has neither category nor price keywords.
    Verifies smart_search_products is called with None for category and max_price.
    """
    question = "tell me something interesting"
    await ai_service.get_response(question)
    mock_product_data_service.smart_search_products.assert_awaited_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )

@pytest.mark.asyncio
async def test_get_response_empty_question(ai_service, mock_product_data_service):
    """
    Test get_response with an empty question string.
    Verifies smart_search_products is called with an empty keyword and no category/price.
    """
    question = ""
    await ai_service.get_response(question)
    mock_product_data_service.smart_search_products.assert_awaited_once_with(
        keyword="", category=None, max_price=None, limit=5
    )

@pytest.mark.asyncio
async def test_get_response_product_service_exception(ai_service, mock_product_data_service, caplog):
    """
    Test get_response when product_service.smart_search_products raises an exception.
    Verifies an error log is emitted and a user-friendly fallback message is returned.
    """
    mock_product_data_service.smart_search_products.side_effect = Exception("Product data service lookup failed")
    
    question = "any question"
    expected_error_message = "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    with caplog.at_level(logging.ERROR):
        response = await ai_service.get_response(question)
        assert response == expected_error_message
        assert "Error generating AI response: Product data service lookup failed" in caplog.text

@pytest.mark.asyncio
async def test_get_response_genai_exception(ai_service, mock_genai_client, caplog):
    """
    Test get_response when client.models.generate_content raises an exception.
    Verifies an error log is emitted and a user-friendly fallback message is returned.
    """
    mock_genai_client.models.generate_content.side_effect = Exception("GenAI API connection error")
    
    question = "any question"
    expected_error_message = "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    with caplog.at_level(logging.ERROR):
        response = await ai_service.get_response(question)
        assert response == expected_error_message
        assert "Error generating AI response: GenAI API connection error" in caplog.text

@pytest.mark.asyncio
async def test_get_response_product_description_truncation(ai_service, mock_product_data_service, mock_genai_client):
    """
    Test that long product descriptions are correctly truncated to 200 characters
    and appended with '...' in the generated prompt context.
    """
    long_description = "This is a very long product description that exceeds the 200 character limit. It contains many intricate details about the product's advanced features, numerous benefits, and comprehensive specifications. This extensive description is intentionally crafted to thoroughly test the truncation logic, ensuring that only the first 200 characters are included in the prompt, followed by an ellipsis, thereby maintaining prompt brevity."
    
    mock_products = [
        {
            'name': 'Test Product XL',
            'price': 1000000,
            'brand': 'TestBrand',
            'category': 'test',
            'specifications': {'rating': 5.0},
            'description': long_description
        }
    ]
    mock_product_data_service.smart_search_products.return_value = (mock_products, "Context message for truncation test.")

    await ai_service.get_response("test truncation of product description")

    mock_genai_client.models.generate_content.assert_called_once()
    args, _ = mock_genai_client.models.generate_content.call_args
    prompt = args[0]
    
    expected_truncated_desc = long_description[:200] + "..."
    assert f"Description: {expected_truncated_desc}" in prompt
    # Verify the exact length including "..."
    # Find the part of the prompt containing the description to assert its length
    desc_start = prompt.find("Description: ") + len("Description: ")
    desc_end = prompt.find("\n\n", desc_start)
    actual_desc_in_prompt = prompt[desc_start:desc_end]
    assert actual_desc_in_prompt == expected_truncated_desc
    assert len(actual_desc_in_prompt) == len(expected_truncated_desc)

# --- Test AIService.generate_response (legacy) ---

def test_generate_response_success(ai_service, mock_genai_client, caplog):
    """
    Test successful generation of AI response using the legacy `generate_response` method.
    Verifies correct model, prompt, and info logging.
    """
    context = "User is asking about general product recommendations based on broad categories."
    expected_ai_response = "Mocked AI response content from Gemini"

    with caplog.at_level(logging.INFO):
        response = ai_service.generate_response(context)

        assert response == expected_ai_response
        mock_genai_client.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash", # Note: Different model from get_response
            contents=f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
        )
        assert "Generating AI response" in caplog.text
        assert "Successfully generated AI response" in caplog.text

def test_generate_response_genai_exception(ai_service, mock_genai_client, caplog):
    """
    Test `generate_response` failure when client.models.generate_content raises an exception.
    Verifies an error log is emitted and the exception is re-raised.
    """
    mock_genai_client.models.generate_content.side_effect = Exception("GenAI API error (legacy call)")
    
    context = "some context for legacy method"

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="GenAI API error (legacy call)"):
            ai_service.generate_response(context)
        assert "Error generating AI response: GenAI API error (legacy call)" in caplog.text