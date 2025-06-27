import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import logging

# Import the actual classes to be mocked for spec checking
from app.utils.config import Settings
from app.services.product_data_service import ProductDataService


@pytest.fixture
def mock_settings(mocker):
    """Mocks get_settings to return a Settings object with a dummy API key."""
    mock_settings_obj = MagicMock(spec=Settings)
    mock_settings_obj.GOOGLE_API_KEY = "dummy_api_key_123"
    mocker.patch("app.utils.config.get_settings", return_value=mock_settings_obj)
    return mock_settings_obj

@pytest.fixture
def mock_genai_client(mocker):
    """
    Mocks google.genai.Client and its models.generate_content method.
    The models.generate_content method is an AsyncMock.
    """
    # Create a mock for the client instance itself
    mock_client_instance = MagicMock()
    
    # Mock the 'models' attribute, which in turn has 'generate_content'
    mock_client_instance.models = MagicMock()
    mock_client_instance.models.generate_content = AsyncMock()
    
    # Patch the google.genai.Client class to return our mock instance
    mocker.patch("google.genai.Client", return_value=mock_client_instance)
    return mock_client_instance

@pytest.fixture
def mock_product_data_service(mocker):
    """
    Mocks ProductDataService and its smart_search_products method.
    The smart_search_products method is an AsyncMock.
    """
    mock_service_instance = MagicMock(spec=ProductDataService)
    mock_service_instance.smart_search_products = AsyncMock()
    mocker.patch("app.services.product_data_service.ProductDataService", return_value=mock_service_instance)
    return mock_service_instance

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_data_service):
    """Fixture to create an AIService instance with all necessary mocks."""
    # Importing AIService here to ensure mocks are set up before import,
    # in case __init__ is called on import (which it isn't, but good practice).
    from app.services.ai_service import AIService
    return AIService()

# Adjust logging level for tests to capture INFO messages
@pytest.fixture(autouse=True)
def set_logging_level(caplog):
    caplog.set_level(logging.INFO)

# --- Tests for AIService.__init__ ---

@pytest.mark.asyncio
async def test_ai_service_init_success(ai_service_instance, mock_settings, mock_genai_client, mock_product_data_service, caplog):
    """
    Test successful initialization of AIService.
    Verifies that all internal components (settings, genai client, product service) are
    initialized correctly and info logs are recorded.
    """
    mock_settings.assert_called_once()
    mock_genai_client.assert_called_once_with(api_key="dummy_api_key_123")
    mock_product_data_service.assert_called_once() # Checks if ProductDataService() was called

    assert ai_service_instance.client == mock_genai_client
    assert ai_service_instance.product_service == mock_product_data_service

    assert "Successfully initialized AI service with Google AI client" in caplog.text
    assert caplog.records[0].levelname == "INFO"

@pytest.mark.asyncio
async def test_ai_service_init_get_settings_failure(mocker, caplog):
    """
    Test AIService initialization when app.utils.config.get_settings fails.
    Verifies that an exception is raised and an error log is recorded.
    """
    mocker.patch("app.utils.config.get_settings", side_effect=Exception("Test config error"))
    # Ensure other components are not initialized if settings fail
    mocker.patch("google.genai.Client")
    mocker.patch("app.services.product_data_service.ProductDataService")

    from app.services.ai_service import AIService # Import here to ensure mocks are active

    with pytest.raises(Exception, match="Test config error"):
        AIService()

    assert "Error initializing AI service: Test config error" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"

@pytest.mark.asyncio
async def test_ai_service_init_genai_client_failure(mocker, mock_settings, caplog):
    """
    Test AIService initialization when google.genai.Client fails during instantiation.
    Verifies that an exception is raised and an error log is recorded.
    """
    mocker.patch("google.genai.Client", side_effect=Exception("GenAI client init error"))
    mocker.patch("app.services.product_data_service.ProductDataService")

    from app.services.ai_service import AIService # Import here to ensure mocks are active

    with pytest.raises(Exception, match="GenAI client init error"):
        AIService()

    assert "Error initializing AI service: GenAI client init error" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"

# --- Tests for AIService.get_response ---

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question, expected_category, expected_max_price",
    [
        ("rekomendasi laptop", "laptop", None),
        ("cari smartphone gaming", "smartphone", None),
        ("tablet murah", "tablet", 5000000),
        ("headphone harga 2 juta", "headphone", 2000000),
        ("kamera dibawah 15 juta", "kamera", 15000000),
        ("speaker bluetooth", "audio", None),
        ("tv terbaik", "tv", None),
        ("drone dengan budget 3 juta", "drone", 3000000),
        ("smartwatch", "jam", None),
        ("laptop budget 8 juta", "laptop", 8000000),
        ("hp 5 juta", "smartphone", 5000000),
        ("berapa harga kamera yang bagus di bawah 10 juta?", "kamera", 10000000),
        ("ponsel yang bagus dan murah", "smartphone", 5000000), # Test 'murah' with category
        ("saya tidak tahu mau beli apa", None, None), # General question, no specific match
        ("cari produk", None, None), # Short, generic question
        ("", None, None), # Empty question
        ("laptop budget 10 jt", "laptop", 10000000) # Test 'jt' abbreviation
    ]
)
async def test_get_response_question_parsing_and_service_call(
    ai_service_instance, mock_product_data_service, mock_genai_client, caplog,
    question, expected_category, expected_max_price
):
    """
    Test that get_response correctly parses category and max_price from questions
    and passes them to product_service.smart_search_products.
    Verifies the correct arguments are passed and basic success flow.
    """
    mock_product_data_service.smart_search_products.return_value = ([], "Default fallback message.")
    mock_genai_client.models.generate_content.return_value.text = "Mock AI response for " + question

    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword=question,
        category=expected_category,
        max_price=expected_max_price,
        limit=5
    )
    assert f"Getting AI response for question: {question}" in caplog.text
    assert "Successfully generated AI response" in caplog.text
    assert response == "Mock AI response for " + question


@pytest.mark.asyncio
async def test_get_response_no_products_found_context(
    ai_service_instance, mock_product_data_service, mock_genai_client
):
    """
    Test get_response when smart_search_products returns no products,
    ensuring the context built for the AI model is correct.
    """
    mock_product_data_service.smart_search_products.return_value = (
        [],
        "No specific products found for your query. Consider broadening your search."
    )
    mock_genai_client.models.generate_content.return_value.text = "AI general recommendation."

    question = "recommend something random"
    await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once()
    mock_genai_client.models.generate_content.assert_called_once()

    # Verify prompt content passed to generate_content
    args, _ = mock_genai_client.models.generate_content.call_args
    prompt = args[0].get('contents')
    assert f"Question: {question}" in prompt
    assert "No specific products found for your query. Consider broadening your search." in prompt
    assert "No specific products found, but I can provide general recommendations." in prompt
    assert "Relevant Products:" not in prompt # Should not be present if no products


@pytest.mark.asyncio
async def test_get_response_with_products_found_context(
    ai_service_instance, mock_product_data_service, mock_genai_client
):
    """
    Test get_response when smart_search_products returns relevant products,
    ensuring the context built for the AI model correctly includes product details.
    Also tests price formatting and description truncation.
    """
    mock_products = [
        {
            "name": "Laptop A Super X",
            "price": 10500000,
            "brand": "BrandX",
            "category": "laptop",
            "specifications": {"rating": 4.5},
            "description": "Powerful laptop for gaming and work. It features the latest processor and a high-resolution display, perfect for professionals and gamers alike. Very durable and stylish."
        },
        {
            "name": "Smartphone B Pro",
            "price": 5250000,
            "brand": "BrandY",
            "category": "smartphone",
            "specifications": {"rating": 4.0},
            "description": "Compact phone with great camera. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        }
    ]
    mock_product_data_service.smart_search_products.return_value = (
        mock_products,
        "Here are some relevant products based on your query."
    )
    mock_genai_client.models.generate_content.return_value.text = "AI response with product details."

    question = "recommend a laptop and smartphone for me"
    response = await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once()
    mock_genai_client.models.generate_content.assert_called_once()

    # Verify prompt content passed to generate_content
    args, _ = mock_genai_client.models.generate_content.call_args
    prompt = args[0].get('contents')
    
    assert f"Question: {question}" in prompt
    assert "Here are some relevant products based on your query." in prompt
    assert "Relevant Products:\n" in prompt
    
    # Check product 1 details
    assert "1. Laptop A Super X\n" in prompt
    assert "   Price: Rp 10,500,000\n" in prompt
    assert "   Brand: BrandX\n" in prompt
    assert "   Category: laptop\n" in prompt
    assert "   Rating: 4.5/5\n" in prompt
    assert "   Description: Powerful laptop for gaming and work. It features the latest processor and a high-resolution display, perfect for professionals and gamers alike. Very durable and stylish...\n\n" in prompt
    
    # Check product 2 details, including description truncation
    assert "2. Smartphone B Pro\n" in prompt
    assert "   Price: Rp 5,250,000\n" in prompt
    assert "   Brand: BrandY\n" in prompt
    assert "   Category: smartphone\n" in prompt
    assert "   Rating: 4.0/5\n" in prompt
    # Check that the description is truncated to 200 characters followed by "..."
    # A bit tricky to verify exact length due to potential whitespace, but checking the content is key.
    expected_desc_truncated = "Compact phone with great camera. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."[:200]
    assert f"   Description: {expected_desc_truncated}...\n\n" in prompt
    
    assert response == "AI response with product details."


@pytest.mark.asyncio
async def test_get_response_product_data_missing_keys_default_values(
    ai_service_instance, mock_product_data_service, mock_genai_client
):
    """
    Test get_response when product data returned from product_service.smart_search_products
    has missing keys, ensuring default values ('Unknown', 0, 'No description') are used.
    """
    mock_products = [
        {
            "name": "Product X",
            "price": 1000,
            # Missing brand, category, specifications, description intentionally
        },
        {
            "name": "Product Y",
            "brand": "KnownBrand",
            # Missing price, category, specifications, description
        }
    ]
    mock_product_data_service.smart_search_products.return_value = (mock_products, "Fallback message.")
    mock_genai_client.models.generate_content.return_value.text = "AI response."

    question = "test missing keys"
    await ai_service_instance.get_response(question)

    args, _ = mock_genai_client.models.generate_content.call_args
    prompt = args[0].get('contents')

    # Verify defaults for Product X
    assert "1. Product X\n" in prompt
    assert "   Price: Rp 1,000\n" in prompt
    assert "   Brand: Unknown\n" in prompt
    assert "   Category: Unknown\n" in prompt
    assert "   Rating: 0/5\n" in prompt
    assert "   Description: No description...\n\n" in prompt

    # Verify defaults for Product Y
    assert "2. Product Y\n" in prompt
    assert "   Price: Rp 0\n" in prompt # Default for missing price
    assert "   Brand: KnownBrand\n" in prompt
    assert "   Category: Unknown\n" in prompt
    assert "   Rating: 0/5\n" in prompt
    assert "   Description: No description...\n\n" in prompt


@pytest.mark.asyncio
async def test_get_response_ai_generation_failure(ai_service_instance, mock_genai_client, caplog):
    """
    Test get_response when self.client.models.generate_content raises an exception.
    Verifies that a user-friendly error message is returned and an error log is recorded.
    """
    mock_genai_client.models.generate_content.side_effect = Exception("Internal AI API error occurred")
    
    # Ensure product service returns successfully so the error comes from AI client
    ai_service_instance.product_service.smart_search_products.return_value = ([], "Default fallback.")

    question = "some question for AI failure"
    response = await ai_service_instance.get_response(question)

    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Internal AI API error occurred" in caplog.text
    assert caplog.records[-1].levelname == "ERROR" # Check the last log is the error


@pytest.mark.asyncio
async def test_get_response_product_service_failure(ai_service_instance, mock_product_data_service, caplog):
    """
    Test get_response when smart_search_products raises an exception.
    Verifies that the entire get_response method catches this and returns the
    user-friendly error message, and an error log is recorded.
    """
    mock_product_data_service.smart_search_products.side_effect = Exception("Product data service internal error")
    mock_genai_client = ai_service_instance.client # Get the actual mock client from the instance

    question = "some question for product service failure"
    response = await ai_service_instance.get_response(question)

    # The outer try-except in get_response catches *any* exception, including from product_service
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Product data service internal error" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"
    mock_genai_client.models.generate_content.assert_not_called() # AI client should not be called if product service fails

# --- Tests for AIService.generate_response (legacy method) ---

@pytest.mark.asyncio
async def test_generate_response_success(ai_service_instance, mock_genai_client, caplog):
    """
    Test successful generation of AI response using the legacy 'generate_response' method.
    Verifies that the correct model and prompt are used and info logs are recorded.
    """
    mock_genai_client.models.generate_content.return_value.text = "Legacy AI response successfully generated."
    context_text = "This is some context provided for the legacy method to process."

    response = ai_service_instance.generate_response(context_text) # Note: this is a synchronous method

    mock_genai_client.models.generate_content.assert_called_once()
    args, _ = mock_genai_client.models.generate_content.call_args
    prompt_arg = args[0] # This is expected to be a dictionary-like object with 'model' and 'contents'

    assert prompt_arg['model'] == "gemini-2.0-flash" # Verify the specific model used for legacy method
    assert prompt_arg['contents'] == f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context_text}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    
    assert response == "Legacy AI response successfully generated."
    assert "Generating AI response" in caplog.text
    assert "Successfully generated AI response" in caplog.text
    # Check that info logs are present before the last log (which might be from fixture teardown)
    assert any("Generating AI response" in r.message for r in caplog.records)
    assert any("Successfully generated AI response" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_generate_response_failure(ai_service_instance, mock_genai_client, caplog):
    """
    Test generate_response when self.client.models.generate_content raises an exception.
    Verifies that the exception is re-raised and an error log is recorded.
    """
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI generation failed")
    context_text = "Some context for a failing call."

    with pytest.raises(Exception, match="Legacy AI generation failed"):
        ai_service_instance.generate_response(context_text)

    assert "Error generating AI response: Legacy AI generation failed" in caplog.text
    assert caplog.records[-1].levelname == "ERROR"
    mock_genai_client.models.generate_content.assert_called_once()