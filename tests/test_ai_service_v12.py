import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.ai_service import AIService
from app.utils.config import Settings
import logging
import re

# Define a fixture for settings
@pytest.fixture
def mock_settings():
    """Mocks the Settings object with a test API key."""
    settings = MagicMock(spec=Settings)
    settings.GOOGLE_API_KEY = "test_google_api_key_123"
    return settings

# Define a fixture for a mock genai client
@pytest.fixture
def mock_genai_client(mocker):
    """Mocks the google.genai.Client and its methods."""
    mock_client = mocker.MagicMock()
    # Mock models.generate_content for async methods
    mock_client.models.generate_content = mocker.AsyncMock()
    return mock_client

# Define a fixture for a mock product data service
@pytest.fixture
def mock_product_data_service(mocker):
    """Mocks the ProductDataService and its smart_search_products method."""
    mock_service = mocker.MagicMock()
    mock_service.smart_search_products = mocker.AsyncMock()
    return mock_service

# Fixture to create AIService instance with mocked dependencies
@pytest.fixture
def ai_service_instance(mocker, mock_settings, mock_genai_client, mock_product_data_service):
    """
    Provides an AIService instance with its dependencies mocked.
    This ensures that external services are not called during tests.
    """
    # Patch get_settings to return our mock settings
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
    # Patch genai.Client to return our mock client
    mocker.patch('google.genai.Client', return_value=mock_genai_client)
    # Patch ProductDataService to return our mock service
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_product_data_service)
    
    # Instantiate the service after patching dependencies
    service = AIService()
    return service

# Sample product data for mocking
@pytest.fixture
def sample_products():
    """Provides a list of sample product data for testing."""
    return [
        {
            "id": "1",
            "name": "Laptop Premium X",
            "price": 18500000,
            "brand": "TechBrand",
            "category": "laptop",
            "specifications": {"rating": 4.7, "processor": "Intel i7", "ram": "16GB", "storage": "512GB SSD"},
            "description": "A powerful and sleek laptop designed for professionals. Features a high-resolution display, long battery life, and excellent performance for demanding tasks. Ideal for graphic design, video editing, and advanced computing. Comes with a backlit keyboard and fingerprint sensor for security."
        },
        {
            "id": "2",
            "name": "Smartphone Elite",
            "price": 9250000,
            "brand": "MobileCorp",
            "category": "smartphone",
            "specifications": {"rating": 4.5, "camera": "108MP", "screen_size": "6.7 inch"},
            "description": "Capture stunning photos and videos with this smartphone's advanced camera system. Enjoy a vibrant AMOLED display and lightning-fast performance for gaming and multitasking. Durable design and all-day battery life make it perfect for on-the-go users."
        },
        {
            "id": "3",
            "name": "Noise-Cancelling Headphones Z",
            "price": 2800000,
            "brand": "AudioPro",
            "category": "headphone",
            "specifications": {"rating": 4.9, "connectivity": "Bluetooth 5.0"},
            "description": "Immersive audio experience with industry-leading noise cancellation. Comfortable over-ear design and long-lasting battery for extended listening sessions. Perfect for travel, work, and pure enjoyment of music. Comes with a compact carrying case."
        }
    ]

class TestAIService:

    # --- Test AIService.__init__ ---
    def test_init_success(self, mocker, mock_settings, mock_genai_client, mock_product_data_service, caplog):
        """
        Test successful initialization of AIService.
        Verifies that dependencies are correctly mocked and logger info message is emitted.
        """
        caplog.set_level(logging.INFO)
        
        # Patch the actual classes/functions that are instantiated/called in __init__
        mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
        mock_genai_client_constructor = mocker.patch('google.genai.Client', return_value=mock_genai_client)
        mock_product_data_service_constructor = mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_product_data_service)

        service = AIService()

        # Assertions
        mock_settings.GOOGLE_API_KEY # Ensure it was accessed
        mock_genai_client_constructor.assert_called_once_with(api_key="test_google_api_key_123")
        mock_product_data_service_constructor.assert_called_once()
        assert service.client == mock_genai_client
        assert service.product_service == mock_product_data_service
        assert "Successfully initialized AI service with Google AI client" in caplog.text

    def test_init_failure_get_settings(self, mocker, caplog):
        """
        Test initialization failure when get_settings raises an exception.
        Verifies that an error is logged and the exception is re-raised.
        """
        caplog.set_level(logging.ERROR)
        
        mocker.patch('app.utils.config.get_settings', side_effect=Exception("Failed to load settings"))
        
        with pytest.raises(Exception, match="Failed to load settings"):
            AIService()
        
        assert "Error initializing AI service: Failed to load settings" in caplog.text

    def test_init_failure_genai_client_creation(self, mocker, mock_settings, caplog):
        """
        Test initialization failure when google.genai.Client construction fails.
        Verifies that an error is logged and the exception is re-raised.
        """
        caplog.set_level(logging.ERROR)

        mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
        mocker.patch('google.genai.Client', side_effect=Exception("GenAI client init error"))
        
        with pytest.raises(Exception, match="GenAI client init error"):
            AIService()
        
        assert "Error initializing AI service: GenAI client init error" in caplog.text

    # --- Test AIService.get_response ---
    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_category, expected_max_price, search_products_return", [
        # No category/price detection, no products
        ("Tell me about tech gadgets.", None, None, ([], "No specific product information available for this query.")),
        # Category detection, no price, products found
        ("I need a new laptop.", "laptop", None, ([], "No specific product information available for this query.")), # To test when product search returns nothing
        ("What's a good notebook?", "laptop", None, ([], "No specific product information available for this query.")),
        ("Recommendations for a smartphone.", "smartphone", None, ([], "No specific product information available for this query.")),
        ("Best hp for photos?", "smartphone", None, ([], "No specific product information available for this query.")),
        ("Looking for a tablet.", "tablet", None, ([], "No specific product information available for this query.")),
        ("Headphones for travel.", "headphone", None, ([], "No specific product information available for this query.")),
        ("Show me some cameras.", "kamera", None, ([], "No specific product information available for this query.")),
        ("Good audio system.", "audio", None, ([], "No specific product information available for this query.")),
        ("Buying a TV.", "tv", None, ([], "No specific product information available for this query.")),
        ("Any drones?", "drone", None, ([], "No specific product information available for this query.")),
        ("Smartwatch suggestions.", "jam", None, ([], "No specific product information available for this query.")),
        # Price detection, no category
        ("What's a product around 5 juta?", None, 5000000, ([], "No specific product information available for this query.")),
        ("Something cheap, budget friendly.", None, 5000000, ([], "No specific product information available for this query.")), # 'budget' keyword
        ("Murah products?", None, 5000000, ([], "No specific product information available for this query.")), # 'murah' keyword
        ("Expensive item around 20 juta?", None, 20000000, ([], "No specific product information available for this query.")),
        # Both category and price detection
        ("A good laptop under 10 juta.", "laptop", 10000000, ([], "No specific product information available for this query.")),
        ("Budget smartphone recommendations.", "smartphone", 5000000, ([], "No specific product information available for this query.")),
        ("Drone below 2 juta.", "drone", 2000000, ([], "No specific product information available for this query.")),
        # Edge cases for questions
        ("What is the capital of France?", None, None, ([], "I can only provide product recommendations. Please ask about products.")), # Irrelevant
        ("", None, None, ([], "Please provide a question about products.")), # Empty question
    ])
    async def test_get_response_question_parsing_and_no_products(
        self, ai_service_instance, mock_genai_client, mock_product_data_service, caplog, 
        question, expected_category, expected_max_price, search_products_return
    ):
        """
        Test get_response with various questions to ensure correct category/price parsing.
        This set of tests assumes `smart_search_products` returns no products,
        to focus on parsing and fallback prompt generation.
        """
        caplog.set_level(logging.INFO)
        
        mock_product_data_service.smart_search_products.return_value = search_products_return
        mock_genai_client.models.generate_content.return_value.text = "AI response based on general query."

        response = await ai_service_instance.get_response(question)

        # Assert smart_search_products was called with correct parameters
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=expected_category, max_price=expected_max_price, limit=5
        )

        # Assert generate_content was called
        mock_genai_client.models.generate_content.assert_called_once()
        
        # Check prompt content (partial check for context building when no products)
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = args[0]['contents']
        
        assert f"Question: {question}" in prompt
        assert search_products_return[1] in prompt # Fallback message should be in prompt
        assert "No specific products found" in prompt # Generic "no products" message
        assert "Relevant Products:" not in prompt # Should not be present if no products
        assert response == "AI response based on general query."
        assert f"Getting AI response for question: {question}" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_with_products_found(
        self, ai_service_instance, mock_genai_client, mock_product_data_service, sample_products, caplog
    ):
        """
        Test get_response when smart_search_products returns actual products.
        Verifies correct context building, including product details and truncation.
        """
        caplog.set_level(logging.INFO)
        question = "What are the best laptops and smartphones?"
        
        mock_product_data_service.smart_search_products.return_value = (
            [sample_products[0], sample_products[1]], # Laptop and Smartphone
            "Found some relevant products for you."
        )
        mock_genai_client.models.generate_content.return_value.text = "Here are some great devices based on your query."

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        mock_genai_client.models.generate_content.assert_called_once()
        
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = args[0]['contents']
        
        assert "Relevant Products:" in prompt
        
        # Verify first product details in prompt
        prod1 = sample_products[0]
        assert f"1. {prod1['name']}" in prompt
        assert f"   Price: Rp {prod1['price']:,.0f}" in prompt
        assert f"   Brand: {prod1['brand']}" in prompt
        assert f"   Category: {prod1['category']}" in prompt
        assert f"   Rating: {prod1['specifications']['rating']}/5" in prompt
        # Check description truncation
        expected_desc_truncated = prod1['description'][:200] + "..."
        assert f"   Description: {expected_desc_truncated}" in prompt

        # Verify second product details in prompt
        prod2 = sample_products[1]
        assert f"2. {prod2['name']}" in prompt
        assert f"   Price: Rp {prod2['price']:,.0f}" in prompt
        assert f"   Brand: {prod2['brand']}" in prompt
        assert f"   Category: {prod2['category']}" in prompt
        assert f"   Rating: {prod2['specifications']['rating']}/5" in prompt
        expected_desc_truncated = prod2['description'][:200] + "..."
        assert f"   Description: {expected_desc_truncated}" in prompt

        assert response == "Here are some great devices based on your query."
        assert "Successfully generated AI response" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_product_data_defaults(
        self, ai_service_instance, mock_genai_client, mock_product_data_service, caplog
    ):
        """
        Test get_response when products have missing or default values for some fields.
        Ensures graceful handling and default displays.
        """
        caplog.set_level(logging.INFO)
        question = "Products with incomplete data"
        
        mock_products_incomplete = [
            {
                "name": "Minimal Gadget",
                "brand": "MinBrand",
                "category": "misc"
                # Missing price, specifications, description
            },
            {
                "name": "Zero-Value Gadget",
                "price": 0,
                "brand": "ZeroBrand",
                "category": "test",
                "specifications": {"rating": 0}, # Explicitly zero rating
                "description": "" # Empty description
            }
        ]
        mock_product_data_service.smart_search_products.return_value = (
            mock_products_incomplete, 
            "Found some items with partial info."
        )
        mock_genai_client.models.generate_content.return_value.text = "AI response about partial data."

        await ai_service_instance.get_response(question)

        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = args[0]['contents']
        
        # Verify handling of missing/default values for Minimal Gadget
        assert "1. Minimal Gadget" in prompt
        assert "Price: Rp 0" in prompt  # Default price
        assert "Rating: 0/5" in prompt  # Default rating
        assert "Description: No description..." in prompt # Default description

        # Verify handling of missing/default values for Zero-Value Gadget
        assert "2. Zero-Value Gadget" in prompt
        assert "Price: Rp 0" in prompt
        assert "Rating: 0/5" in prompt
        assert "Description: No description..." in prompt

    @pytest.mark.asyncio
    async def test_get_response_product_service_raises_exception(self, ai_service_instance, mock_product_data_service, caplog):
        """
        Test error handling in get_response when ProductDataService raises an exception.
        Verifies that an error message is logged and a user-friendly fallback is returned.
        """
        caplog.set_level(logging.ERROR)
        question = "Question that causes product service error."

        mock_product_data_service.smart_search_products.side_effect = Exception("Product search API failed")

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once()
        # genai.Client.models.generate_content should NOT be called if smart_search_products fails
        assert not ai_service_instance.client.models.generate_content.called
        
        assert "Error generating AI response: Product search API failed" in caplog.text
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    @pytest.mark.asyncio
    async def test_get_response_genai_client_raises_exception(self, ai_service_instance, mock_genai_client, mock_product_data_service, caplog):
        """
        Test error handling in get_response when genai.Client raises an exception.
        Verifies that an error message is logged and a user-friendly fallback is returned.
        """
        caplog.set_level(logging.ERROR)
        question = "Question that causes AI generation error."

        mock_product_data_service.smart_search_products.return_value = (
            [], 
            "No products found."
        )
        mock_genai_client.models.generate_content.side_effect = Exception("GenAI API call failed")

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once()
        mock_genai_client.models.generate_content.assert_called_once()
        
        assert "Error generating AI response: GenAI API call failed" in caplog.text
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    # --- Test AIService.generate_response (Legacy method) ---
    def test_generate_response_success(self, ai_service_instance, mock_genai_client, caplog):
        """
        Test successful generation of AI response using the legacy method (`generate_response`).
        Verifies correct model, prompt, and return value.
        """
        caplog.set_level(logging.INFO)
        context = "This is a custom context for the legacy AI, detailing a product."
        expected_response_text = "Legacy AI has successfully responded based on the provided context."
        
        mock_genai_client.models.generate_content.return_value.text = expected_response_text

        response = ai_service_instance.generate_response(context)

        # Assert generate_content was called with correct model and contents
        expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

        mock_genai_client.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash",
            contents=expected_prompt
        )
        assert response == expected_response_text
        assert "Generating AI response" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    def test_generate_response_failure(self, ai_service_instance, mock_genai_client, caplog):
        """
        Test failure in generating AI response using the legacy method (`generate_response`).
        Verifies that an error is logged and the exception is re-raised.
        """
        caplog.set_level(logging.ERROR)
        context = "Context for an AI error scenario."
        
        mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI generation failed")

        with pytest.raises(Exception, match="Legacy AI generation failed"):
            ai_service_instance.generate_response(context)
        
        mock_genai_client.models.generate_content.assert_called_once()
        assert "Error generating AI response: Legacy AI generation failed" in caplog.text