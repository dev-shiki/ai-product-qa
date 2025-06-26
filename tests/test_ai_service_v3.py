import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import logging

# Import the service directly assuming app is in the Python path
# For local development/testing, you might need to adjust sys.path or use poetry/venv properly configured.
from app.services.ai_service import AIService

# Fixture for a mocked settings object
@pytest.fixture
def mock_settings():
    """Mocks the get_settings function to return a settings object with an API key."""
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings_obj = MagicMock()
        mock_settings_obj.GOOGLE_API_KEY = "test_google_api_key"
        mock_get_settings.return_value = mock_settings_obj
        yield mock_get_settings

# Fixture for a mocked Google GenAI client
@pytest.fixture
def mock_genai_client():
    """Mocks the google.genai.Client and its methods."""
    with patch('google.genai.Client') as MockClient:
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        
        # Mock generate_content method for the models object
        # It needs to return an object with a .text attribute
        mock_client_instance.models.generate_content.return_value = MagicMock(text="Mocked AI response")
        yield MockClient

# Fixture for a mocked ProductDataService
@pytest.fixture
def mock_product_service():
    """Mocks the ProductDataService and its smart_search_products method."""
    with patch('app.services.product_data_service.ProductDataService') as MockProductDataService:
        mock_service_instance = AsyncMock() # Use AsyncMock for async methods
        MockProductDataService.return_value = mock_service_instance
        
        # Default mock return for smart_search_products
        # It should return a tuple: (list of products, fallback message string)
        mock_service_instance.smart_search_products.return_value = ([], "Default fallback message.")
        yield MockProductDataService

# Test cases for AIService initialization
class TestAIServiceInit:
    def test_init_success(self, mock_settings, mock_genai_client, mock_product_service, caplog):
        """
        Test successful initialization of AIService.
        Verifies that settings, genai.Client, and ProductDataService are called correctly
        and info logs are emitted.
        """
        caplog.set_level(logging.INFO)
        service = AIService()
        
        mock_settings.assert_called_once()
        mock_genai_client.assert_called_once_with(api_key="test_google_api_key")
        mock_product_service.assert_called_once()
        
        assert isinstance(service.client, MagicMock)
        assert isinstance(service.product_service, AsyncMock) # Should be AsyncMock from patch
        assert "Successfully initialized AI service with Google AI client" in caplog.text

    def test_init_failure_get_settings(self, mock_settings, caplog):
        """
        Test initialization failure when get_settings raises an exception.
        Verifies that an exception is raised and error logs are emitted.
        """
        mock_settings.side_effect = Exception("Failed to load settings")
        caplog.set_level(logging.ERROR)
        
        with pytest.raises(Exception, match="Failed to load settings"):
            AIService()
        
        assert "Error initializing AI service: Failed to load settings" in caplog.text

    def test_init_failure_genai_client(self, mock_settings, mock_genai_client, caplog):
        """
        Test initialization failure when genai.Client raises an exception.
        Verifies that an exception is raised and error logs are emitted.
        """
        mock_genai_client.side_effect = Exception("GenAI client error")
        caplog.set_level(logging.ERROR)
        
        with pytest.raises(Exception, match="GenAI client error"):
            AIService()
        
        assert "Error initializing AI service: GenAI client error" in caplog.text

# Test cases for get_response method
class TestAIServiceGetResponse:
    @pytest.fixture(autouse=True)
    def setup(self, mock_settings, mock_genai_client, mock_product_service):
        """
        Setup for all get_response tests. Initializes AIService with mocked dependencies.
        `autouse=True` means this fixture runs before every test in this class.
        """
        self.service = AIService()
        self.mock_genai_client_instance = mock_genai_client.return_value
        self.mock_product_service_instance = mock_product_service.return_value

    @pytest.mark.asyncio
    async def test_get_response_success_no_products(self, caplog):
        """
        Test get_response with a general question where no specific products are found.
        Verifies logging, calls to product service and genai client, and prompt content.
        """
        caplog.set_level(logging.INFO)
        question = "What is the best way to choose a gadget in general?"
        
        self.mock_product_service_instance.smart_search_products.return_value = (
            [], 
            "No specific products found for your general query."
        )
        self.mock_genai_client_instance.models.generate_content.return_value = MagicMock(text="General advice on gadgets.")

        response = await self.service.get_response(question)
        
        self.mock_product_service_instance.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        
        assert "General advice on gadgets." == response
        assert f"Getting AI response for question: {question}" in caplog.text
        assert "Successfully generated AI response" in caplog.text
        
        # Verify prompt content
        args, _ = self.mock_genai_client_instance.models.generate_content.call_args
        prompt = args[0]
        assert "You are a helpful product assistant." in prompt
        assert f"Question: {question}" in prompt
        assert "No specific products found for your general query." in prompt
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt # Ensure no product context is included

    @pytest.mark.asyncio
    async def test_get_response_success_with_products(self, caplog):
        """
        Test get_response with a specific question where relevant products are found.
        Verifies logging, calls to product service and genai client, and prompt content
        including product details.
        """
        caplog.set_level(logging.INFO)
        question = "Rekomendasi laptop gaming budget 15 juta?"
        
        mock_products = [
            {
                'name': 'Gaming Laptop X', 'price': 14500000, 'brand': 'Brand A',
                'category': 'laptop', 'specifications': {'rating': 4.5},
                'description': 'Powerful gaming laptop with latest GPU and CPU, great for high-end gaming and productivity tasks.'
            },
            {
                'name': 'Gaming Laptop Y', 'price': 13000000, 'brand': 'Brand B',
                'category': 'laptop', 'specifications': {'rating': 4.0},
                'description': 'Affordable gaming laptop for casual gamers, featuring a balanced performance and good battery life.'
            }
        ]
        
        self.mock_product_service_instance.smart_search_products.return_value = (
            mock_products, 
            "Based on your query, here are some gaming laptops."
        )
        self.mock_genai_client_instance.models.generate_content.return_value = MagicMock(text="Here are some laptops for you.")

        response = await self.service.get_response(question)
        
        self.mock_product_service_instance.smart_search_products.assert_called_once_with(
            keyword=question, category="laptop", max_price=15000000, limit=5
        )
        
        assert "Here are some laptops for you." == response
        assert "Successfully generated AI response" in caplog.text
        
        # Verify prompt content including formatted product details
        args, _ = self.mock_genai_client_instance.models.generate_content.call_args
        prompt = args[0]
        assert "You are a helpful product assistant." in prompt
        assert f"Question: {question}" in prompt
        assert "Based on your query, here are some gaming laptops." in prompt
        assert "Relevant Products:\n" in prompt
        assert "1. Gaming Laptop X" in prompt
        assert "Price: Rp 14,500,000" in prompt
        assert "Brand: Brand A" in prompt
        assert "Category: laptop" in prompt
        assert "Rating: 4.5/5" in prompt
        assert "Description: Powerful gaming laptop with latest GPU and CPU, great for high-end gaming and productivity tasks..." in prompt # Check slicing and ellipsis
        assert "2. Gaming Laptop Y" in prompt

    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_category, expected_max_price", [
        ("Cari handphone Samsung", "smartphone", None),
        ("Rekomendasi tablet murah", "tablet", 5000000), # 'murah' -> 5 juta
        ("Headphone gaming budget 2 juta", "headphone", 2000000),
        ("Kamera DSLR terbaik", "kamera", None),
        ("Smartwatch terbaik", "jam", None),
        ("Laptop untuk kerja", "laptop", None),
        ("TV 55 inch", "tv", None),
        ("Drone dengan kamera", "drone", None),
        ("Speaker bluetooth budget 5 juta", "audio", 5000000),
        ("Ponsel di bawah 3 juta", "smartphone", 3000000), # Test 'juta' price detection
        ("Saya punya budget 4 juta untuk hp", "smartphone", 4000000), # Test 'budget' with 'juta'
        ("Cari komputer gaming", "laptop", None), # Test another keyword for laptop
        ("Apa ada notebook 10 juta?", "laptop", 10000000),
        ("handphone harga 1 juta", "smartphone", 1000000),
        ("Telepon pintar baru", "smartphone", None), # Another synonym for smartphone
        ("headset gaming", "headphone", None), # Another synonym for headphone
        ("cari audio system", "audio", None), # Another synonym for audio
        ("fotografi gear", "kamera", None), # Another synonym for kamera
        ("jam tangan", "jam", None), # Another synonym for jam
        ("Tidak ada kata kunci", None, None), # No category, no price
        ("Budget 10 juta saja", None, 10000000), # Price only
        ("murah banget", None, 5000000) # Only 'murah'
    ])
    async def test_get_response_question_parsing(self, question, expected_category, expected_max_price):
        """
        Test various question inputs for correct category and max_price extraction logic.
        Verifies that smart_search_products is called with the correctly parsed arguments.
        """
        self.mock_genai_client_instance.models.generate_content.return_value = MagicMock(text="Test response")
        
        await self.service.get_response(question)
        
        self.mock_product_service_instance.smart_search_products.assert_called_once_with(
            keyword=question, category=expected_category, max_price=expected_max_price, limit=5
        )

    @pytest.mark.asyncio
    async def test_get_response_product_service_failure(self, caplog):
        """
        Test get_response when smart_search_products raises an exception.
        Verifies error logging and the fallback message is returned without calling GenAI.
        """
        caplog.set_level(logging.ERROR)
        question = "Any product?"
        
        self.mock_product_service_instance.smart_search_products.side_effect = Exception("Product service down")
        
        response = await self.service.get_response(question)
        
        assert "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti." == response
        assert "Error generating AI response: Product service down" in caplog.text
        # Ensure genai client was NOT called if product service failed
        self.mock_genai_client_instance.models.generate_content.assert_not_called()
        self.mock_product_service_instance.smart_search_products.assert_called_once() # Still called

    @pytest.mark.asyncio
    async def test_get_response_genai_client_failure(self, caplog):
        """
        Test get_response when genai.Client.models.generate_content raises an exception.
        Verifies error logging and the fallback message is returned.
        """
        caplog.set_level(logging.ERROR)
        question = "Suggest a product."
        
        self.mock_product_service_instance.smart_search_products.return_value = ([], "No products.")
        self.mock_genai_client_instance.models.generate_content.side_effect = Exception("GenAI API error")
        
        response = await self.service.get_response(question)
        
        assert "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti." == response
        assert "Error generating AI response: GenAI API error" in caplog.text
        self.mock_product_service_instance.smart_search_products.assert_called_once() # Should still be called
        self.mock_genai_client_instance.models.generate_content.assert_called_once() # Should be called before it fails

# Test cases for generate_response method (legacy/direct context method)
class TestAIServiceGenerateResponse:
    @pytest.fixture(autouse=True)
    def setup(self, mock_settings, mock_genai_client, mock_product_service):
        """
        Setup for all generate_response tests. Initializes AIService with mocked dependencies.
        `autouse=True` means this fixture runs before every test in this class.
        """
        self.service = AIService()
        self.mock_genai_client_instance = mock_genai_client.return_value

    def test_generate_response_success(self, caplog):
        """
        Test successful generation of AI response using the direct context method.
        Verifies logging, calls to genai client, and prompt content.
        """
        caplog.set_level(logging.INFO)
        context = "User is asking about laptops suitable for students in college."
        
        self.mock_genai_client_instance.models.generate_content.return_value = MagicMock(text="Student laptop recommendations.")
        
        response = self.service.generate_response(context)
        
        self.mock_genai_client_instance.models.generate_content.assert_called_once()
        
        assert "Student laptop recommendations." == response
        assert "Generating AI response" in caplog.text
        assert "Successfully generated AI response" in caplog.text
        
        # Verify prompt content and model used
        args, kwargs = self.mock_genai_client_instance.models.generate_content.call_args
        prompt = args[0]
        assert "You are a helpful product assistant." in prompt
        assert context in prompt
        assert "Please provide a clear and concise answer" in prompt
        assert kwargs['model'] == "gemini-2.0-flash" # Ensure the correct model is used

    def test_generate_response_failure(self, caplog):
        """
        Test generation failure when genai.Client.models.generate_content raises an exception
        in the direct context method.
        Verifies error logging and that the exception is re-raised.
        """
        caplog.set_level(logging.ERROR)
        context = "Some context for failure."
        
        self.mock_genai_client_instance.models.generate_content.side_effect = Exception("GenAI API error (legacy)")
        
        with pytest.raises(Exception, match="GenAI API error (legacy)"):
            self.service.generate_response(context)
        
        assert "Error generating AI response: GenAI API error (legacy)" in caplog.text
        self.mock_genai_client_instance.models.generate_content.assert_called_once()