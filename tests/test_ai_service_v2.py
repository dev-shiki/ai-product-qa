import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
import os

# --- Mocks for external dependencies ---

# Mock the Settings object used by get_settings
class MockSettings:
    def __init__(self, api_key="test_api_key_123"):
        self.GOOGLE_API_KEY = api_key

@pytest.fixture(autouse=True)
def mock_get_settings(mocker):
    """
    Fixture to mock app.utils.config.get_settings globally for tests.
    Ensures a consistent Settings object is returned.
    """
    mock_settings_instance = MockSettings()
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings_instance)
    return mock_settings_instance

@pytest.fixture
def mock_genai_client(mocker):
    """
    Fixture to mock google.genai.Client and its methods.
    It simulates the behavior of the Google AI client for content generation.
    """
    mock_client = MagicMock()
    # Configure the return value chain for generate_content
    mock_client.models.generate_content.return_value.text = "Mocked AI response from Gemini"
    mocker.patch('google.genai.Client', return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_product_data_service(mocker):
    """
    Fixture to mock app.services.product_data_service.ProductDataService.
    It simulates the async smart_search_products method.
    """
    mock_service_instance = AsyncMock()
    # Default return value for smart_search_products
    mock_service_instance.smart_search_products.return_value = ([], "No specific products found.")
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_service_instance)
    return mock_service_instance

@pytest.fixture
def ai_service_instance(mock_genai_client, mock_product_data_service):
    """
    Fixture to provide an initialized AIService instance for tests.
    Ensures AIService is imported after its dependencies are mocked.
    """
    # Import AIService here to ensure that mocks are active when AIService is instantiated
    from app.services.ai_service import AIService
    return AIService()

# --- Test cases for AIService.__init__ ---

class TestAIServiceInit:
    """Tests for the initialization of the AIService class."""

    def test_init_success(self, mock_get_settings, mock_genai_client, mock_product_data_service, caplog):
        """
        Test successful initialization of AIService.
        Verifies that client and product_service are correctly set and logs are as expected.
        """
        caplog.set_level(logging.INFO)
        # Import AIService again within the test to ensure its __init__ is run with active mocks
        from app.services.ai_service import AIService
        service = AIService()

        assert service.client is mock_genai_client
        assert service.product_service is mock_product_data_service
        
        mock_get_settings.assert_called_once()
        mock_genai_client.assert_called_once_with(api_key=mock_get_settings.GOOGLE_API_KEY)
        mock_product_data_service.assert_called_once() # Checks if ProductDataService() was called

        assert "Successfully initialized AI service with Google AI client" in caplog.text

    def test_init_get_settings_failure(self, mocker, caplog):
        """
        Test initialization failure when app.utils.config.get_settings raises an exception.
        Ensures an error is logged and the exception is re-raised.
        """
        caplog.set_level(logging.ERROR)
        # Patch get_settings to raise an exception
        mocker.patch('app.utils.config.get_settings', side_effect=Exception("Settings load error"))

        from app.services.ai_service import AIService
        with pytest.raises(Exception, match="Settings load error"):
            AIService()

        assert "Error initializing AI service: Settings load error" in caplog.text

    def test_init_genai_client_failure(self, mocker, mock_get_settings, caplog):
        """
        Test initialization failure when google.genai.Client raises an exception during instantiation.
        Ensures an error is logged and the exception is re-raised.
        """
        caplog.set_level(logging.ERROR)
        # Patch genai.Client to raise an exception upon instantiation
        mocker.patch('google.genai.Client', side_effect=Exception("GenAI client init error"))

        from app.services.ai_service import AIService
        with pytest.raises(Exception, match="GenAI client init error"):
            AIService()

        assert "Error initializing AI service: GenAI client init error" in caplog.text

# --- Test cases for AIService.get_response (async method) ---

@pytest.mark.asyncio
class TestAIServiceGetResponse:
    """Tests for the asynchronous get_response method."""

    async def test_get_response_basic_question_no_match(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """
        Test get_response with a basic question that doesn't trigger category or price detection.
        Verifies correct calls to product service and genai client, and proper context building.
        """
        caplog.set_level(logging.INFO)
        question = "What is the best product for general use?"
        
        expected_products = []
        expected_fallback = "I couldn't find specific products for your query, but can offer general guidance."
        mock_product_data_service.smart_search_products.return_value = (expected_products, expected_fallback)

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        
        mock_genai_client.models.generate_content.assert_called_once()
        args, kwargs = mock_genai_client.models.generate_content.call_args
        
        # Verify prompt content and model
        prompt_content = kwargs['contents']
        assert kwargs['model'] == "gemini-2.5-flash"
        assert f"Question: {question}" in prompt_content
        assert f"{expected_fallback}" in prompt_content
        assert "No specific products found, but I can provide general recommendations." in prompt_content
        assert "Relevant Products:" not in prompt_content # Ensure no products section
        
        assert response == "Mocked AI response from Gemini"
        assert f"Getting AI response for question: {question}" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    @pytest.mark.parametrize("question, expected_category", [
        ("Cari laptop gaming", "laptop"),
        ("Rekomendasi HP terbaru", "smartphone"),
        ("Tablet yang bagus apa ya?", "tablet"),
        ("Headphone wireless terbaik", "headphone"),
        ("Kamera DSLR murah", "kamera"),
        ("Speaker bluetooth", "audio"),
        ("TV 4K", "tv"),
        ("Drone yang stabil", "drone"),
        ("Jam tangan pintar", "jam"),
        # Case insensitivity and alternative keywords
        ("notebook gaming", "laptop"),
        ("TELEPON SELULER", "smartphone"),
        ("earphone murah", "headphone"),
        ("smartwatch keren", "jam"),
        ("ipad pro", "tablet"),
        ("komputer kantor", "laptop"),
        ("Fotografi perjalanan", "kamera"),
        ("sound system", "audio"),
    ])
    async def test_get_response_category_detection(self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_category):
        """
        Test get_response to ensure correct category detection from various keywords and cases.
        """
        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=expected_category, max_price=None, limit=5
        )
        # Reset mock for next parameter if this was not a new instance per param
        mock_product_data_service.smart_search_products.reset_mock()
        mock_genai_client.models.generate_content.reset_mock()


    @pytest.mark.parametrize("question, expected_max_price", [
        ("Laptop budget 10 juta", 10000000),
        ("HP di bawah 5 juta", 5000000), # Detects "5 juta" specifically
        ("TV murah", 5000000), # Detects 'murah' -> 5 juta default
        ("Smartphone murah", 5000000), # Detects 'murah' -> 5 juta default
        ("Saya punya budget 2 juta untuk tablet", 2000000),
        ("Harga max 7 juta", 7000000),
    ])
    async def test_get_response_price_detection(self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_max_price):
        """
        Test get_response to ensure correct price detection from various keywords and formats.
        """
        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=expected_max_price, limit=5
        )
        mock_product_data_service.smart_search_products.reset_mock()
        mock_genai_client.models.generate_content.reset_mock()

    async def test_get_response_category_and_price_detection(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """
        Test get_response with a question containing both category and price keywords.
        """
        question = "Cari laptop gaming budget 15 juta"
        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category="laptop", max_price=15000000, limit=5
        )

    async def test_get_response_with_products_found(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """
        Test get_response when smart_search_products returns relevant products.
        Verifies that product details are correctly formatted and included in the AI prompt context.
        """
        question = "Tell me about high-end laptops."
        products = [
            {
                "name": "Laptop Alpha",
                "price": 12500000,
                "brand": "BrandX",
                "category": "laptop",
                "specifications": {"rating": 4.5},
                "description": "Powerful laptop with 16GB RAM and 512GB SSD for gaming and productivity. It has a great screen and long battery life. This is a very long description that needs to be truncated to fit the context limit."
            },
            {
                "name": "Laptop Beta",
                "price": 8000000,
                "brand": "BrandY",
                "category": "laptop",
                "specifications": {"rating": 3.8},
                "description": "Affordable laptop for everyday use with basic features."
            }
        ]
        fallback_message = "Here are some top-rated laptops that might interest you."
        mock_product_data_service.smart_search_products.return_value = (products, fallback_message)

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once()
        
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt_content = kwargs['contents']
        
        assert "Relevant Products:" in prompt_content
        assert f"Question: {question}" in prompt_content
        assert f"{fallback_message}" in prompt_content

        # Verify details of Laptop Alpha
        assert "1. Laptop Alpha" in prompt_content
        assert "Price: Rp 12,500,000" in prompt_content
        assert "Brand: BrandX" in prompt_content
        assert "Category: laptop" in prompt_content
        assert "Rating: 4.5/5" in prompt_content
        # Check description truncation
        assert "Description: Powerful laptop with 16GB RAM and 512GB SSD for gaming and productivity. It has a great screen and long battery life. This is a very long description that needs to be truncated to fit the con..." in prompt_content 

        # Verify details of Laptop Beta
        assert "2. Laptop Beta" in prompt_content
        assert "Price: Rp 8,000,000" in prompt_content
        assert "Brand: BrandY" in prompt_content
        assert "Category: laptop" in prompt_content
        assert "Rating: 3.8/5" in prompt_content
        assert "Description: Affordable laptop for everyday use with basic features..." in prompt_content # Ends with "..."

        assert response == "Mocked AI response from Gemini"

    async def test_get_response_with_no_products_found_but_fallback_message(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """
        Test get_response when smart_search_products returns no products but provides a fallback message.
        Ensures the context correctly reflects the lack of products and includes the fallback.
        """
        question = "Unusual product query that won't find products"
        products = []
        fallback_message = "I couldn't find exact matches for your specific query, but I can suggest related categories."
        mock_product_data_service.smart_search_products.return_value = (products, fallback_message)

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once()
        
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt_content = kwargs['contents']
        
        assert f"Question: {question}" in prompt_content
        assert f"{fallback_message}" in prompt_content
        assert "No specific products found, but I can provide general recommendations." in prompt_content
        assert "Relevant Products:" not in prompt_content # Explicitly check no products section
        assert response == "Mocked AI response from Gemini"

    async def test_get_response_product_data_service_raises_exception(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """
        Test get_response when smart_search_products raises an exception.
        Ensures an error is logged and the correct fallback message is returned.
        """
        caplog.set_level(logging.ERROR)
        question = "Question causing product service error"
        mock_product_data_service.smart_search_products.side_effect = Exception("Product search service down")

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once()
        mock_genai_client.models.generate_content.assert_not_called() # AI generation should not be attempted

        assert "Error generating AI response: Product search service down" in caplog.text
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    async def test_get_response_genai_client_raises_exception(self, ai_service_instance, mock_genai_client, caplog):
        """
        Test get_response when google.genai.Client.models.generate_content raises an exception.
        Ensures an error is logged and the correct fallback message is returned.
        """
        caplog.set_level(logging.ERROR)
        question = "Question causing AI generation error"
        mock_genai_client.models.generate_content.side_effect = Exception("AI generation failed unexpectedly")

        response = await ai_service_instance.get_response(question)

        mock_genai_client.models.generate_content.assert_called_once() # Should be called before it errors
        assert "Error generating AI response: AI generation failed unexpectedly" in caplog.text
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

# --- Test cases for AIService.generate_response (legacy method) ---

class TestAIServiceGenerateResponse:
    """Tests for the synchronous generate_response (legacy) method."""

    def test_generate_response_success(self, ai_service_instance, mock_genai_client, caplog):
        """
        Test successful generation of AI response using the legacy method.
        Verifies correct call to genai client with specific model and prompt.
        """
        caplog.set_level(logging.INFO)
        context = "This is some test context for the legacy AI response generation."
        response = ai_service_instance.generate_response(context)

        mock_genai_client.models.generate_content.assert_called_once()
        args, kwargs = mock_genai_client.models.generate_content.call_args
        
        # Verify model and prompt content
        assert kwargs['model'] == "gemini-2.0-flash"
        assert context in kwargs['contents']
        assert "You are a helpful product assistant." in kwargs['contents']
        assert response == "Mocked AI response from Gemini"
        assert "Generating AI response" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    def test_generate_response_genai_client_raises_exception(self, ai_service_instance, mock_genai_client, caplog):
        """
        Test generate_response when google.genai.Client.models.generate_content raises an exception.
        Ensures an error is logged and the exception is re-raised.
        """
        caplog.set_level(logging.ERROR)
        context = "Error context for legacy method"
        mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI generation error")

        with pytest.raises(Exception, match="Legacy AI generation error"):
            ai_service_instance.generate_response(context)

        mock_genai_client.models.generate_content.assert_called_once() # Should be called before it errors
        assert "Error generating AI response: Legacy AI generation error" in caplog.text