import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging
import asyncio # Required for running async tests with pytest-asyncio

# Import the class to be tested
from app.services.ai_service import AIService

# --- Fixtures ---

@pytest.fixture(autouse=True)
def mock_settings():
    """Mocks get_settings to return a dummy API key."""
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings_instance = MagicMock()
        mock_settings_instance.GOOGLE_API_KEY = "test_api_key"
        mock_get_settings.return_value = mock_settings_instance
        yield mock_get_settings

@pytest.fixture
def mock_genai_client_class():
    """Mocks google.genai.Client class and its instance methods."""
    with patch('google.genai.Client') as mock_client_cls:
        # Mock the instance returned by genai.Client()
        mock_client_instance = MagicMock()
        # Mock models.generate_content as an AsyncMock
        mock_client_instance.models.generate_content = AsyncMock()
        mock_client_cls.return_value = mock_client_instance
        yield mock_client_cls # Yield the class mock to check constructor calls

@pytest.fixture
def mock_product_data_service_class():
    """Mocks ProductDataService class and its instance methods."""
    with patch('app.services.product_data_service.ProductDataService') as mock_service_cls:
        # Mock the instance returned by ProductDataService()
        mock_service_instance = MagicMock()
        # Mock smart_search_products as an AsyncMock
        mock_service_instance.smart_search_products = AsyncMock()
        mock_service_cls.return_value = mock_service_instance
        yield mock_service_cls # Yield the class mock to check constructor calls

@pytest.fixture
def ai_service_instance(mock_genai_client_class, mock_product_data_service_class):
    """Provides an AIService instance with mocked dependencies."""
    return AIService()

@pytest.fixture
def caplog_info(caplog):
    """Fixture to capture INFO level logs."""
    caplog.set_level(logging.INFO)
    return caplog

@pytest.fixture
def caplog_error(caplog):
    """Fixture to capture ERROR level logs."""
    caplog.set_level(logging.ERROR)
    return caplog

# --- Test Cases for __init__ ---

class TestAIServiceInit:
    def test_init_success(self, mock_settings, mock_genai_client_class, mock_product_data_service_class, caplog_info):
        """Test successful initialization of AIService."""
        service = AIService()
        
        mock_settings.assert_called_once()
        mock_genai_client_class.assert_called_once_with(api_key="test_api_key")
        mock_product_data_service_class.assert_called_once()
        
        assert "Successfully initialized AI service with Google AI client" in caplog_info.text
        assert service.client == mock_genai_client_class.return_value
        assert service.product_service == mock_product_data_service_class.return_value

    def test_init_failure_get_settings(self, mock_settings, caplog_error):
        """Test initialization failure when get_settings raises an exception."""
        mock_settings.side_effect = Exception("Settings error")
        with pytest.raises(Exception, match="Settings error"):
            AIService()
        assert "Error initializing AI service: Settings error" in caplog_error.text
        mock_settings.assert_called_once()

    def test_init_failure_genai_client(self, mock_settings, mock_genai_client_class, caplog_error):
        """Test initialization failure when genai.Client raises an exception."""
        mock_genai_client_class.side_effect = Exception("GenAI client error")
        with pytest.raises(Exception, match="GenAI client error"):
            AIService()
        assert "Error initializing AI service: GenAI client error" in caplog_error.text
        mock_settings.assert_called_once()
        mock_genai_client_class.assert_called_once_with(api_key="test_api_key")

    def test_init_failure_product_data_service(self, mock_settings, mock_genai_client_class, mock_product_data_service_class, caplog_error):
        """Test initialization failure when ProductDataService raises an exception."""
        mock_product_data_service_class.side_effect = Exception("Product service error")
        with pytest.raises(Exception, match="Product service error"):
            AIService()
        assert "Error initializing AI service: Product service error" in caplog_error.text
        mock_settings.assert_called_once()
        mock_genai_client_class.assert_called_once_with(api_key="test_api_key")
        mock_product_data_service_class.assert_called_once()

# --- Test Cases for get_response ---

class TestAIServiceGetResponse:
    # Sample product data for mocking
    SAMPLE_PRODUCTS = [
        {
            'name': 'Laptop Super X',
            'price': 15000000,
            'brand': 'BrandA',
            'category': 'laptop',
            'specifications': {'rating': 4.5},
            'description': 'Description of Laptop Super X, a powerful device for gaming and work and productivity. It has a great screen and long battery life. This description is long enough to be truncated.'
        },
        {
            'name': 'Smartphone Z9',
            'price': 8000000,
            'brand': 'BrandB',
            'category': 'smartphone',
            'specifications': {'rating': 4.0},
            'description': 'The latest smartphone with amazing camera features and long battery life.'
        }
    ]

    async def test_get_response_success_with_products(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, caplog_info):
        """Test get_response with product context and successful AI generation."""
        question = "Cari laptop gaming dengan budget 15 juta"
        expected_ai_response = "Here are some recommendations based on your query."

        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = (self.SAMPLE_PRODUCTS, "Found some relevant items.")
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        response = await ai_service_instance.get_response(question)

        mock_product_service_instance.smart_search_products.assert_awaited_once_with(
            keyword=question, category='laptop', max_price=15000000, limit=5
        )
        
        args, kwargs = mock_genai_client_instance.models.generate_content.call_args
        prompt = kwargs['contents'] if 'contents' in kwargs else args[0]
        
        assert "Question: Cari laptop gaming dengan budget 15 juta" in prompt
        assert "Found some relevant items." in prompt
        assert "Relevant Products:\n" in prompt
        assert "1. Laptop Super X" in prompt
        assert "Price: Rp 15,000,000" in prompt
        assert "Brand: BrandA" in prompt
        assert "Category: laptop" in prompt
        assert "Rating: 4.5/5" in prompt
        assert self.SAMPLE_PRODUCTS[0]['description'][:200] in prompt # Check truncated description
        assert "..." in prompt # Verify truncation indicator
        
        # Product 2 is a smartphone, but included in the mock return value,
        # so it should also appear in the prompt to reflect the current implementation's behavior.
        assert "2. Smartphone Z9" in prompt
        assert "Price: Rp 8,000,000" in prompt
        assert "Brand: BrandB" in prompt
        assert "Category: smartphone" in prompt
        assert "Rating: 4.0/5" in prompt
        assert self.SAMPLE_PRODUCTS[1]['description'][:200] in prompt

        mock_genai_client_instance.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents=prompt
        )
        assert response == expected_ai_response
        assert f"Getting AI response for question: {question}" in caplog_info.text
        assert "Successfully generated AI response" in caplog_info.text

    async def test_get_response_success_no_products(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, caplog_info):
        """Test get_response when no products are found."""
        question = "Apa rekomendasi umum untuk perlengkapan rumah tangga?"
        expected_ai_response = "I can provide general recommendations for home appliances."

        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = ([], "No specific items found for your query.")
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        response = await ai_service_instance.get_response(question)

        mock_product_service_instance.smart_search_products.assert_awaited_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )

        args, kwargs = mock_genai_client_instance.models.generate_content.call_args
        prompt = kwargs['contents'] if 'contents' in kwargs else args[0]
        
        assert "Question: Apa rekomendasi umum untuk perlengkapan rumah tangga?" in prompt
        assert "No specific items found for your query." in prompt
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt 

        mock_genai_client_instance.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents=prompt
        )
        assert response == expected_ai_response
        assert f"Getting AI response for question: {question}" in caplog_info.text

    async def test_get_response_empty_products_empty_fallback(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class):
        """Test get_response when products and fallback message are empty."""
        question = "Empty search"
        expected_ai_response = "AI response for empty search."

        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = ([], "") # Empty fallback
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        response = await ai_service_instance.get_response(question)

        args, kwargs = mock_genai_client_instance.models.generate_content.call_args
        prompt = kwargs['contents'] if 'contents' in kwargs else args[0]
        
        assert "Question: Empty search" in prompt
        assert "\n\n\n\n" in prompt # Two empty lines for empty fallback message
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt 
        assert response == expected_ai_response


    @pytest.mark.parametrize("question, expected_category, expected_max_price", [
        ("Cari laptop murah", "laptop", 5000000),
        ("Handphone 5 juta", "smartphone", 5000000), # "5 juta" matches price pattern
        ("Mau cari tablet bagus", "tablet", None),
        ("Headphone budget 2 juta", "headphone", 2000000),
        ("Ada kamera di bawah 10 juta?", "kamera", 10000000),
        ("Speaker bluetooth", "audio", None),
        ("TV 7 juta", "tv", 7000000),
        ("Drone yang bagus", "drone", None),
        ("Smartwatch murah", "jam", 5000000), # "murah" maps to 5M
        ("Produk umum lainnya", None, None), # No category, no price
        ("Smartphone untuk 12 juta", "smartphone", 12000000),
        ("Berapa harga hp", "smartphone", None),
        ("laptop acer", "laptop", None),
        ("Saya punya budget 3 juta untuk hp", "smartphone", 3000000),
        ("Mencari notebook dibawah 7 juta", "laptop", 7000000),
        ("Headset gaming", "headphone", None),
        ("500ribu", None, None), # Should not match "juta" or "budget/murah"
        ("Produk bagus dan murah", None, 5000000),
        ("Apa rekomendasi untuk menonton TV", "tv", None),
        ("Tablet harga 4 juta", "tablet", 4000000),
        ("Komputer desktop", "laptop", None), # "komputer" maps to laptop
        ("iPhone terbaru", "smartphone", None), # iPhone implies smartphone
        ("ponsel android", "smartphone", None),
        ("iPad Pro", "tablet", None),
        ("earphone bluetooth", "headphone", None),
        ("kamera mirrorless", "kamera", None),
        ("sound system", "audio", None),
        ("televisi pintar", "tv", None),
        ("quadcopter mini", "drone", None),
        ("jam tangan pintar", "jam", None),
        ("Laptop 20 juta", "laptop", 20000000),
        ("Budget 1 juta", None, 1000000) # Price parsing works for standalone budget
    ])
    async def test_get_response_question_parsing(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, question, expected_category, expected_max_price):
        """Test various question parsing scenarios for category and max_price."""
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = ([], "No products.")
        mock_genai_client_instance.models.generate_content.return_value.text = "Dummy AI response."

        await ai_service_instance.get_response(question)

        mock_product_service_instance.smart_search_products.assert_awaited_once_with(
            keyword=question, category=expected_category, max_price=expected_max_price, limit=5
        )

    async def test_get_response_failure_smart_search_products(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, caplog_error):
        """Test get_response when smart_search_products raises an exception."""
        question = "Test question"
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.side_effect = Exception("Search error")
        
        response = await ai_service_instance.get_response(question)

        mock_product_service_instance.smart_search_products.assert_awaited_once()
        mock_genai_client_instance.models.generate_content.assert_not_called() # Should not call AI if search fails
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        assert "Error generating AI response: Search error" in caplog_error.text

    async def test_get_response_failure_generate_content(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, caplog_error):
        """Test get_response when generate_content raises an exception."""
        question = "Test question"
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = (self.SAMPLE_PRODUCTS, "Found some relevant items.")
        mock_genai_client_instance.models.generate_content.side_effect = Exception("GenAI error")

        response = await ai_service_instance.get_response(question)

        mock_product_service_instance.smart_search_products.assert_awaited_once()
        mock_genai_client_instance.models.generate_content.assert_called_once()
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        assert "Error generating AI response: GenAI error" in caplog_error.text

    async def test_get_response_product_missing_optional_keys(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class):
        """Test get_response handles products with missing description and rating."""
        question = "Product with missing info"
        product_no_desc_rating = [{
            'name': 'Simple Product',
            'price': 1000000,
            'brand': 'BasicCo',
            'category': 'misc',
            'specifications': {} # Missing rating, but key 'specifications' exists
            # Missing 'description'
        }]
        expected_ai_response = "Response for product with missing info."
        
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = (product_no_desc_rating, "Minimal info product.")
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        response = await ai_service_instance.get_response(question)

        args, kwargs = mock_genai_client_instance.models.generate_content.call_args
        prompt = kwargs['contents'] if 'contents' in kwargs else args[0]
        
        assert "Description: No description..." in prompt # Uses default 'No description'
        assert "Rating: 0/5" in prompt # Uses default 0
        assert response == expected_ai_response

    async def test_get_response_short_description(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class):
        """Test get_response handles products with short description (less than 200 chars)."""
        question = "Product with short description"
        product_short_desc = [{
            'name': 'Short Desc Product',
            'price': 500000,
            'brand': 'TinyCo',
            'category': 'gadget',
            'specifications': {'rating': 3.0},
            'description': 'This is a very short description.'
        }]
        expected_ai_response = "Response for short description product."

        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = (product_short_desc, "Short description product.")
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        response = await ai_service_instance.get_response(question)

        args, kwargs = mock_genai_client_instance.models.generate_content.call_args
        prompt = kwargs['contents'] if 'contents' in kwargs else args[0]
        
        # Check that the description is exactly as provided, followed by "..."
        assert "Description: This is a very short description...." in prompt
        assert response == expected_ai_response

    async def test_get_response_unknown_category_and_no_price(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class):
        """Test get_response with a question that yields no category or price detection."""
        question = "Tell me about cars"
        expected_ai_response = "I cannot help with cars."
        
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_genai_client_instance = mock_genai_client_class.return_value

        mock_product_service_instance.smart_search_products.return_value = ([], "No products related to cars.")
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        response = await ai_service_instance.get_response(question)

        mock_product_service_instance.smart_search_products.assert_awaited_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        assert response == expected_ai_response


# --- Test Cases for generate_response (Legacy Method) ---

class TestAIServiceGenerateResponse:
    def test_generate_response_success(self, ai_service_instance, mock_genai_client_class, caplog_info):
        """Test successful generation of AI response using the legacy method."""
        context = "This is a test context for legacy generation."
        expected_ai_response = "This is the AI's response from legacy method."
        
        mock_genai_client_instance = mock_genai_client_class.return_value
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        response = ai_service_instance.generate_response(context)

        # Verify prompt content
        args, kwargs = mock_genai_client_instance.models.generate_content.call_args
        prompt = kwargs['contents'] if 'contents' in kwargs else args[0]
        
        assert f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision.""" == prompt

        mock_genai_client_instance.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash",
            contents=prompt
        )
        assert response == expected_ai_response
        assert "Generating AI response" in caplog_info.text
        assert "Successfully generated AI response" in caplog_info.text

    def test_generate_response_failure(self, ai_service_instance, mock_genai_client_class, caplog_error):
        """Test failure in generate_response when genai.Client raises an exception."""
        context = "Error context"
        mock_genai_client_instance = mock_genai_client_class.return_value
        mock_genai_client_instance.models.generate_content.side_effect = Exception("GenAI legacy error")

        with pytest.raises(Exception, match="GenAI legacy error"):
            ai_service_instance.generate_response(context)

        mock_genai_client_instance.models.generate_content.assert_called_once()
        assert "Error generating AI response: GenAI legacy error" in caplog_error.text