import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import logging
import sys
import os

# Ensure the app root directory is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.services.ai_service import AIService
from app.services.product_data_service import ProductDataService


@pytest.fixture(autouse=True)
def mock_settings_for_init(mocker):
    """
    Mock app.utils.config.get_settings globally for all tests
    to ensure AIService initialization doesn't hit real config.
    """
    mock_settings_obj = mocker.MagicMock()
    mock_settings_obj.GOOGLE_API_KEY = "mock_api_key_123"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings_obj)
    return mock_settings_obj

@pytest.fixture
def mock_genai_client(mocker):
    """
    Mock google.genai.Client and its models.generate_content method.
    Based on the source code, generate_content is called without `await`,
    suggesting it's treated as a synchronous method in this context.
    """
    mock_client = mocker.MagicMock()
    # Mock generate_content as a synchronous method
    mock_client.models.generate_content = mocker.MagicMock()
    mocker.patch('google.genai.Client', return_value=mock_client)
    yield mock_client

@pytest.fixture
def mock_product_data_service(mocker):
    """
    Mock ProductDataService and its smart_search_products method as an AsyncMock,
    as it is awaited in AIService.get_response.
    """
    mock_service = mocker.MagicMock(spec=ProductDataService)
    mock_service.smart_search_products = mocker.AsyncMock(return_value=([], "No specific products found."))
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_service)
    yield mock_service

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """
    Configure logging to capture messages during tests and set the level.
    The caplog fixture from pytest automatically handles cleanup.
    """
    logger = logging.getLogger('app.services.ai_service')
    logger.setLevel(logging.INFO) # Set to INFO to capture both INFO and ERROR messages
    yield

class TestAIService:
    """
    Comprehensive test suite for the AIService class.
    """

    @pytest.mark.asyncio
    async def test_init_success(self, mock_genai_client, mock_product_data_service, caplog):
        """
        Test successful initialization of AIService.
        Verifies that client and product_service are correctly set up and an info log is recorded.
        """
        service = AIService()
        assert service.client is mock_genai_client
        assert service.product_service is mock_product_data_service
        assert "Successfully initialized AI service with Google AI client" in caplog.text

    @pytest.mark.asyncio
    async def test_init_raises_exception_on_settings_error(self, mocker, caplog):
        """
        Test that AIService initialization fails if get_settings raises an exception.
        Ensures the exception is propagated and an error log is recorded.
        """
        mocker.patch('app.utils.config.get_settings', side_effect=Exception("Settings load error"))
        with pytest.raises(Exception, match="Settings load error"):
            AIService()
        assert "Error initializing AI service: Settings load error" in caplog.text

    @pytest.mark.asyncio
    async def test_init_raises_exception_on_genai_client_error(self, mocker, caplog):
        """
        Test that AIService initialization fails if genai.Client constructor raises an exception.
        Ensures the exception is propagated and an error log is recorded.
        """
        mocker.patch('google.genai.Client', side_effect=Exception("GenAI client error"))
        with pytest.raises(Exception, match="GenAI client error"):
            AIService()
        assert "Error initializing AI service: GenAI client error" in caplog.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_category, expected_max_price, search_products_return_value, expected_ai_prompt_contains", [
        # Test case 1: Smartphone query with successful product find
        (
            "What's a good smartphone?",
            "smartphone",
            None,
            ([{'name': 'Phone A', 'price': 10000000, 'brand': 'Brand A', 'category': 'smartphone', 'specifications': {'rating': 4.5}, 'description': 'Description A long enough to be truncated.'}], "Here are some phones."),
            ["Question: What's a good smartphone?", "Here are some phones.", "Relevant Products:", "1. Phone A", "Price: Rp 10,000,000", "Brand: Brand A", "Category: smartphone", "Rating: 4.5/5", "Description: Description A long enough to be truncated..."]
        ),
        # Test case 2: Laptop query with budget and no products found
        (
            "Laptop di bawah 15 juta?",
            "laptop",
            15000000, # 15 million
            ([], "No specific laptops found within your budget."),
            ["Question: Laptop di bawah 15 juta?", "No specific laptops found within your budget.", "No specific products found, but I can provide general recommendations."]
        ),
        # Test case 3: Headphone query with "murah" budget and products found
        (
            "Headphone murah?",
            "headphone",
            5000000, # 5 million
            ([{'name': 'Budget Headphone X', 'price': 500000, 'brand': 'Brand X', 'category': 'headphone', 'specifications': {'rating': 4.0}, 'description': 'Desc X'}], "Found some budget headphones."),
            ["Question: Headphone murah?", "Found some budget headphones.", "1. Budget Headphone X"]
        ),
        # Test case 4: Camera query without price, products found
        (
            "Tell me about cameras?",
            "kamera",
            None,
            ([{'name': 'Camera P', 'price': 20000000, 'brand': 'Brand P', 'category': 'kamera', 'specifications': {'rating': 4.8}, 'description': 'Awesome camera for pros'}], "Here are some cameras."),
            ["Question: Tell me about cameras?", "Here are some cameras.", "1. Camera P"]
        ),
        # Test case 5: TV query, no products found
        (
            "Any good TVs around?",
            "tv",
            None,
            ([], "No TVs matched your query."),
            ["Question: Any good TVs around?", "No TVs matched your query.", "No specific products found, but I can provide general recommendations."]
        ),
        # Test case 6: General question without category or explicit price, products found
        (
            "General question without category or price.",
            None,
            None,
            ([{'name': 'Product Z', 'price': 1000000, 'brand': 'Brand Z', 'category': 'general', 'specifications': {'rating': 3.0}, 'description': 'General product description'}], "Here are some general products."),
            ["Question: General question without category or price.", "Here are some general products.", "1. Product Z"]
        ),
        # Test case 7: Budget without explicit category, no products found
        (
            "Question with 5 juta budget and no category",
            None,
            5000000, # 5 million
            ([], "No products found for your budget."),
            ["Question: Question with 5 juta budget and no category", "No products found for your budget.", "No specific products found, but I can provide general recommendations."]
        ),
        # Test case 8: Product with missing optional fields (ensure defaults are used in context)
        (
            "Product with missing fields",
            None,
            None,
            ([{'name': 'Incomplete Product'}], "Found one incomplete product."), # Missing price, brand, category, specifications, description
            ["Question: Product with missing fields", "Found one incomplete product.", "1. Incomplete Product", "Price: Rp 0", "Brand: Unknown", "Category: Unknown", "Rating: 0/5", "Description: No description..."]
        ),
        # Test case 9: Smartwatch with 'juta' budget
        (
            "Jam pintar 2 juta",
            "jam",
            2000000,
            ([{'name': 'Smartwatch A', 'price': 1800000, 'brand': 'Brand A', 'category': 'jam', 'specifications': {'rating': 4.2}, 'description': 'A great smartwatch.'}], "Found a smartwatch."),
            ["Question: Jam pintar 2 juta", "Found a smartwatch.", "1. Smartwatch A"]
        ),
        # Test case 10: Tablet query
        (
            "Looking for a new tablet",
            "tablet",
            None,
            ([{'name': 'Tablet X', 'price': 5500000, 'brand': 'Brand X', 'category': 'tablet', 'specifications': {'rating': 4.0}, 'description': 'Powerful tablet for work and play.'}], "Tablets available."),
            ["Question: Looking for a new tablet", "Tablets available.", "1. Tablet X"]
        ),
        # Test case 11: Audio system query
        (
            "I need an audio system",
            "audio",
            None,
            ([{'name': 'Audio System Y', 'price': 7000000, 'brand': 'Brand Y', 'category': 'audio', 'specifications': {'rating': 4.6}, 'description': 'High-end audio system.'}], "Audio systems found."),
            ["Question: I need an audio system", "Audio systems found.", "1. Audio System Y"]
        ),
        # Test case 12: Drone query
        (
            "Best drone recommendations?",
            "drone",
            None,
            ([{'name': 'Drone Z', 'price': 15000000, 'brand': 'Brand Z', 'category': 'drone', 'specifications': {'rating': 4.9}, 'description': 'Professional drone with 4K camera.'}], "Drones available."),
            ["Question: Best drone recommendations?", "Drones available.", "1. Drone Z"]
        ),
    ])
    async def test_get_response_success(self, mock_genai_client, mock_product_data_service, caplog,
                                      question, expected_category, expected_max_price, search_products_return_value, expected_ai_prompt_contains):
        """
        Test successful get_response with various question inputs and product search results.
        Covers question parsing, product service interaction, and AI prompt construction.
        """
        mock_product_data_service.smart_search_products.return_value = search_products_return_value
        
        mock_ai_response = MagicMock()
        mock_ai_response.text = f"Mocked AI response for: {question}"
        mock_genai_client.models.generate_content.return_value = mock_ai_response

        service = AIService()
        response = await service.get_response(question)

        # Assert smart_search_products was called with correctly parsed parameters
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=expected_category, max_price=expected_max_price, limit=5
        )

        # Assert genai_client.models.generate_content was called
        mock_genai_client.models.generate_content.assert_called_once()
        
        # Get the actual prompt passed to the AI model
        actual_prompt = mock_genai_client.models.generate_content.call_args[1]['contents']
        
        # Assert the prompt contains expected elements for context building
        for expected_str in expected_ai_prompt_contains:
            assert expected_str in actual_prompt

        assert "gemini-2.5-flash" == mock_genai_client.models.generate_content.call_args[1]['model']
        assert response == mock_ai_response.text
        assert f"Getting AI response for question: {question}" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_product_service_failure(self, mock_genai_client, mock_product_data_service, caplog):
        """
        Test get_response when smart_search_products raises an exception.
        Verifies that the method returns the fallback error message and logs the error.
        """
        mock_product_data_service.smart_search_products.side_effect = Exception("Product search service is down")
        
        service = AIService()
        response = await service.get_response("Any product?")

        mock_product_data_service.smart_search_products.assert_called_once()
        
        # If product search fails, the AI content generation should not be attempted
        mock_genai_client.models.generate_content.assert_not_called() 
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        assert "Error generating AI response: Product search service is down" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_genai_failure(self, mock_genai_client, mock_product_data_service, caplog):
        """
        Test get_response when genai.Client.models.generate_content raises an exception.
        Verifies that the method returns the fallback error message and logs the error.
        """
        # Product search succeeds, but AI generation fails
        mock_product_data_service.smart_search_products.return_value = ([{'name': 'Some Product'}], "Found a product.")
        mock_genai_client.models.generate_content.side_effect = Exception("GenAI service is unavailable")

        service = AIService()
        response = await service.get_response("Test question for AI failure")

        mock_product_data_service.smart_search_products.assert_called_once()
        mock_genai_client.models.generate_content.assert_called_once() # It should be called, then fail
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        assert "Error generating AI response: GenAI service is unavailable" in caplog.text

    def test_generate_response_success(self, mock_genai_client, caplog):
        """
        Test successful generate_response (legacy method).
        Verifies correct prompt construction, AI call, and return value.
        """
        context = "This is a test context for legacy AI generation."
        mock_ai_response = MagicMock()
        mock_ai_response.text = "Legacy AI response based on context."
        mock_genai_client.models.generate_content.return_value = mock_ai_response

        service = AIService()
        response = service.generate_response(context) # This method is not async

        mock_genai_client.models.generate_content.assert_called_once()
        
        actual_prompt = mock_genai_client.models.generate_content.call_args[1]['contents']
        assert "gemini-2.0-flash" == mock_genai_client.models.generate_content.call_args[1]['model']
        assert context in actual_prompt
        assert "You are a helpful product assistant." in actual_prompt
        assert "Please provide a clear and concise answer" in actual_prompt
        assert response == mock_ai_response.text
        assert "Generating AI response" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    def test_generate_response_genai_failure(self, mock_genai_client, caplog):
        """
        Test generate_response when genai.Client.models.generate_content raises an exception.
        Verifies that the exception is re-raised and an error log is recorded.
        """
        context = "Context causing an error in legacy method."
        mock_genai_client.models.generate_content.side_effect = Exception("GenAI legacy generation failed")

        service = AIService()
        with pytest.raises(Exception, match="GenAI legacy generation failed"):
            service.generate_response(context)

        mock_genai_client.models.generate_content.assert_called_once()
        assert "Error generating AI response: GenAI legacy generation failed" in caplog.text