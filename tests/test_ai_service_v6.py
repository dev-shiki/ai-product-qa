import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import logging

# Set up basic logging for tests to capture output
logging.basicConfig(level=logging.INFO)

# Fixture to mock external dependencies at the module level
# This is crucial for __init__ tests that happen upon class instantiation
@pytest.fixture(autouse=True)
def mock_dependencies():
    """
    Mocks external dependencies for AIService initialization.
    - app.utils.config.get_settings
    - google.genai.Client
    - app.services.product_data_service.ProductDataService
    """
    with patch('app.utils.config.get_settings') as mock_get_settings, \
         patch('google.genai.Client') as mock_genai_client_cls, \
         patch('app.services.product_data_service.ProductDataService') as mock_product_data_service_cls:
        
        # Configure get_settings mock
        mock_settings_instance = MagicMock()
        mock_settings_instance.GOOGLE_API_KEY = "test-api-key"
        mock_get_settings.return_value = mock_settings_instance

        # Configure genai.Client mock
        # We need a mock for client.models.generate_content
        mock_genai_client_instance = MagicMock()
        mock_genai_client_instance.models.generate_content = AsyncMock() # This needs to be AsyncMock for async methods
        mock_genai_client_cls.return_value = mock_genai_client_instance

        # Configure ProductDataService mock
        mock_product_data_service_instance = AsyncMock() # This needs to be AsyncMock for smart_search_products
        mock_product_data_service_instance.smart_search_products = AsyncMock()
        mock_product_data_service_cls.return_value = mock_product_data_service_instance

        yield mock_get_settings, mock_genai_client_cls, mock_genai_client_instance, \
              mock_product_data_service_cls, mock_product_data_service_instance


# Import AIService after initial mocks are set up for __init__ testing
from app.services.ai_service import AIService


@pytest.fixture
def ai_service_instance(mock_dependencies):
    """
    Fixture to provide an AIService instance with pre-configured mocked dependencies.
    Resets mocks for isolation between tests.
    """
    mock_get_settings, mock_genai_client_cls, mock_genai_client_instance, \
    mock_product_data_service_cls, mock_product_data_service_instance = mock_dependencies
    
    # Reset mocks before each test that uses this fixture to ensure test isolation
    mock_get_settings.reset_mock()
    mock_genai_client_cls.reset_mock()
    mock_genai_client_instance.models.generate_content.reset_mock()
    mock_product_data_service_cls.reset_mock()
    mock_product_data_service_instance.smart_search_products.reset_mock()

    # Re-configure mocks after reset for this specific instance if needed (important for return values)
    mock_settings_instance = MagicMock()
    mock_settings_instance.GOOGLE_API_KEY = "test-api-key"
    mock_get_settings.return_value = mock_settings_instance

    mock_genai_client_cls.return_value = mock_genai_client_instance
    mock_product_data_service_cls.return_value = mock_product_data_service_instance

    service = AIService()
    yield service, mock_genai_client_instance, mock_product_data_service_instance


@pytest.fixture
def mock_products():
    """Fixture to provide a list of mock product data for testing."""
    return [
        {
            "name": "Super Laptop X",
            "price": 15000000,
            "brand": "TechCorp",
            "category": "laptop",
            "specifications": {"rating": 4.5},
            "description": "A high-performance laptop for demanding users. Features a powerful processor and a stunning display. This description is long enough to be truncated by the AI service context building logic."
        },
        {
            "name": "Budget Smartphone Y",
            "price": 3000000,
            "brand": "PhoneCo",
            "category": "smartphone",
            "specifications": {"rating": 3.8},
            "description": "An affordable smartphone with essential features for everyday use. Great battery life."
        },
        {
            "name": "Gaming Headset Z",
            "price": 1200000,
            "brand": "AudioPro",
            "category": "headphone",
            "specifications": {"rating": 4.2},
            "description": "Immersive gaming experience with surround sound and comfortable earcups."
        }
    ]

# --- Tests for __init__ method ---

def test_ai_service_init_success(mock_dependencies):
    """
    Test that AIService initializes successfully when all dependencies
    (get_settings, genai.Client, ProductDataService) are available and configured.
    Verifies that the client and product_service attributes are correctly set.
    """
    mock_get_settings, mock_genai_client_cls, mock_genai_client_instance, \
    mock_product_data_service_cls, mock_product_data_service_instance = mock_dependencies
    
    service = AIService()
    
    mock_get_settings.assert_called_once()
    mock_genai_client_cls.assert_called_once_with(api_key="test-api-key")
    mock_product_data_service_cls.assert_called_once()
    
    assert service.client is mock_genai_client_instance
    assert service.product_service is mock_product_data_service_instance


def test_ai_service_init_failure_api_key_missing(mock_dependencies, caplog):
    """
    Test that AIService initialization fails if GOOGLE_API_KEY is not provided
    or genai.Client initialization fails, and logs the error.
    """
    mock_get_settings, mock_genai_client_cls, _, _, _ = mock_dependencies
    
    # Simulate an error during genai.Client initialization (e.g., due to a missing API key or invalid config)
    mock_genai_client_cls.side_effect = Exception("Google AI client initialization failed: API key invalid")
    
    with pytest.raises(Exception) as excinfo:
        AIService()
    
    assert "Google AI client initialization failed: API key invalid" in str(excinfo.value)
    
    # Check if the error was logged
    assert "Error initializing AI service: Google AI client initialization failed: API key invalid" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"

def test_ai_service_init_failure_product_service_init(mock_dependencies, caplog):
    """
    Test that AIService initialization fails if ProductDataService initialization fails.
    """
    mock_get_settings, mock_genai_client_cls, _, mock_product_data_service_cls, _ = mock_dependencies
    
    # Simulate an error during ProductDataService initialization
    mock_product_data_service_cls.side_effect = Exception("Product data service failed to init")
    
    with pytest.raises(Exception) as excinfo:
        AIService()
    
    assert "Product data service failed to init" in str(excinfo.value)
    
    # Check if the error was logged
    assert "Error initializing AI service: Product data service failed to init" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"


# --- Tests for get_response method ---

@pytest.mark.asyncio
async def test_get_response_success_with_products_context(ai_service_instance, mock_products):
    """
    Test get_response successfully generates an AI response when relevant products are found.
    Verifies that the product context is correctly built and passed to the AI model.
    """
    service, mock_genai_client, mock_product_service = ai_service_instance
    
    # Configure mock responses for product search and AI generation
    mock_product_service.smart_search_products.return_value = (mock_products, "Here are some relevant products.")
    mock_genai_client.models.generate_content.return_value.text = "AI response about the suggested products."

    question = "recommend a good laptop below 20 juta"
    response = await service.get_response(question)

    # Assert that smart_search_products was called with correct parameters
    mock_product_service.smart_search_products.assert_called_once_with(
        keyword=question, category="laptop", max_price=None, limit=5 # Price detection is handled separately, for '20 juta' should be None
    )

    # Assert on the prompt content passed to generate_content
    args, kwargs = mock_genai_client.models.generate_content.call_args
    prompt_arg = kwargs['contents']
    
    assert "Question: recommend a good laptop below 20 juta" in prompt_arg
    assert "Here are some relevant products." in prompt_arg
    assert "Relevant Products:" in prompt_arg
    assert "1. Super Laptop X" in prompt_arg
    assert "Price: Rp 15,000,000" in prompt_arg
    assert "Brand: TechCorp" in prompt_arg
    assert "Category: laptop" in prompt_arg
    assert "Rating: 4.5/5" in prompt_arg
    # Check for description truncation
    assert "A high-performance laptop for demanding users. Features a powerful processor and a stunning display..." in prompt_arg
    assert "2. Budget Smartphone Y" in prompt_arg
    assert "3. Gaming Headset Z" in prompt_arg
    assert "model='gemini-2.5-flash'" in str(mock_genai_client.models.generate_content.call_args) # Verify model used

    assert response == "AI response about the suggested products."


@pytest.mark.asyncio
async def test_get_response_success_no_products_found(ai_service_instance):
    """
    Test get_response successfully generates an AI response when no products are found.
    Verifies that the correct fallback context is built and passed to the AI model.
    """
    service, mock_genai_client, mock_product_service = ai_service_instance
    
    # Configure mock responses
    mock_product_service.smart_search_products.return_value = ([], "No specific products matched your criteria.")
    mock_genai_client.models.generate_content.return_value.text = "AI general recommendation for your query."

    question = "tell me about smart home devices"
    response = await service.get_response(question)

    mock_product_service.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )

    # Assert on the prompt content passed to generate_content
    args, kwargs = mock_genai_client.models.generate_content.call_args
    prompt_arg = kwargs['contents']
    
    assert "Question: tell me about smart home devices" in prompt_arg
    assert "No specific products matched your criteria." in prompt_arg
    assert "No specific products found, but I can provide general recommendations." in prompt_arg
    assert "Relevant Products:" not in prompt_arg # Should not be present if no products
    assert "model='gemini-2.5-flash'" in str(mock_genai_client.models.generate_content.call_args)

    assert response == "AI general recommendation for your query."


@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category", [
    ("what is a good laptop?", "laptop"),
    ("rekomendasi hp murah", "smartphone"),
    ("cari handphone", "smartphone"),
    ("tablet untuk anak", "tablet"),
    ("headset gaming", "headphone"),
    ("earphone bluetooth", "headphone"),
    ("camera dslr", "kamera"),
    ("speaker bass", "audio"),
    ("tv 4k", "tv"),
    ("drone fotografi", "drone"),
    ("jam tangan pintar", "jam"),
    ("unknown product type", None), # No category match
    ("cari computer buat kerja", "laptop"), # Synonym for laptop
])
async def test_get_response_category_detection(ai_service_instance, question, expected_category):
    """
    Test that get_response correctly extracts product categories from various questions.
    """
    service, mock_genai_client, mock_product_service = ai_service_instance
    
    mock_product_service.smart_search_products.return_value = ([], "Fallback")
    mock_genai_client.models.generate_content.return_value.text = "AI response"

    await service.get_response(question)

    mock_product_service.smart_search_products.assert_called_once()
    args, kwargs = mock_product_service.smart_search_products.call_args
    assert kwargs['category'] == expected_category


@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_max_price", [
    ("laptop 10 juta", 10000000),
    ("smartphone budget 5 juta", 5000000),
    ("cari hp murah", 5000000), # 'murah' keyword
    ("tablet dengan budget 20 juta", 20000000), # 'budget' keyword with explicit price
    ("harga dibawah 3 juta", 3000000), # Test for price with "juta"
    ("kamera bagus", None), # No price specified
    ("laptop 7 juta", 7000000),
    ("ponsel di bawah 1 juta", 1000000)
])
async def test_get_response_price_detection(ai_service_instance, question, expected_max_price):
    """
    Test that get_response correctly extracts max_price from questions.
    The current regex `(\d+)\s*juta` only captures integer values before "juta".
    """
    service, mock_genai_client, mock_product_service = ai_service_instance
    
    mock_product_service.smart_search_products.return_value = ([], "Fallback")
    mock_genai_client.models.generate_content.return_value.text = "AI response"

    await service.get_response(question)

    mock_product_service.smart_search_products.assert_called_once()
    args, kwargs = mock_product_service.smart_search_products.call_args
    assert kwargs['max_price'] == expected_max_price


@pytest.mark.asyncio
async def test_get_response_smart_search_products_exception(ai_service_instance, caplog):
    """
    Test get_response handles exceptions raised by smart_search_products gracefully.
    It should log the error and return the predefined fallback message.
    """
    service, mock_genai_client, mock_product_service = ai_service_instance
    
    mock_product_service.smart_search_products.side_effect = Exception("Product search service is down")
    
    question = "I need a new phone"
    response = await service.get_response(question)

    mock_product_service.smart_search_products.assert_called_once()
    mock_genai_client.models.generate_content.assert_not_called() # AI generation should not occur after search failure
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Product search service is down" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"


@pytest.mark.asyncio
async def test_get_response_generate_content_exception(ai_service_instance, caplog):
    """
    Test get_response handles exceptions raised by the AI client during content generation.
    It should log the error and return the predefined fallback message.
    """
    service, mock_genai_client, mock_product_service = ai_service_instance
    
    mock_product_service.smart_search_products.return_value = ([], "Successfully searched.")
    mock_genai_client.models.generate_content.side_effect = Exception("AI model connection error")
    
    question = "What is the best TV?"
    response = await service.get_response(question)

    mock_product_service.smart_search_products.assert_called_once()
    mock_genai_client.models.generate_content.assert_called_once()
    
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: AI model connection error" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"

@pytest.mark.asyncio
async def test_get_response_empty_question_string(ai_service_instance):
    """
    Test get_response with an empty question string.
    It should still attempt to search products (with no category/price) and generate a general AI response.
    """
    service, mock_genai_client, mock_product_service = ai_service_instance
    
    mock_product_service.smart_search_products.return_value = ([], "No query provided, providing general assistance.")
    mock_genai_client.models.generate_content.return_value.text = "I am here to help. How can I assist you today?"

    question = ""
    response = await service.get_response(question)

    mock_product_service.smart_search_products.assert_called_once_with(
        keyword="", category=None, max_price=None, limit=5
    )

    args, kwargs = mock_genai_client.models.generate_content.call_args
    prompt_arg = kwargs['contents']
    assert "Question: " in prompt_arg # Ensure the question part of the context is still present
    assert "No query provided, providing general assistance." in prompt_arg
    
    assert response == "I am here to help. How can I assist you today?"


# --- Tests for generate_response method (legacy method) ---

def test_generate_response_success(ai_service_instance):
    """
    Test generate_response successfully gets a response from the AI client.
    Verifies the prompt content and the model used.
    """
    service, mock_genai_client, _ = ai_service_instance
    
    mock_genai_client.models.generate_content.return_value.text = "Legacy AI response based on provided context."

    context = "This is a test context for the legacy generate_response method."
    response = service.generate_response(context)

    # Check that generate_content was called with the correct prompt and model
    args, kwargs = mock_genai_client.models.generate_content.call_args
    prompt_arg = kwargs['contents']

    assert "You are a helpful product assistant." in prompt_arg
    assert context in prompt_arg
    assert "Please provide a clear and concise answer that helps the user understand the products and make an informed decision." in prompt_arg
    assert "model='gemini-2.0-flash'" in str(mock_genai_client.models.generate_content.call_args) # Verify model used

    assert response == "Legacy AI response based on provided context."


def test_generate_response_exception(ai_service_instance, caplog):
    """
    Test generate_response raises an exception if the AI client call fails,
    and logs the error.
    """
    service, mock_genai_client, _ = ai_service_instance
    
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI model processing error")

    context = "Some context for an error scenario."
    with pytest.raises(Exception) as excinfo:
        service.generate_response(context)
    
    assert "Legacy AI model processing error" in str(excinfo.value)
    assert "Error generating AI response: Legacy AI model processing error" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"