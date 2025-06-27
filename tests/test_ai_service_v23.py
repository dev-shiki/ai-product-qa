import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import logging

# Import the class to be tested
from app.services.ai_service import AIService

# Fixture for mock settings
@pytest.fixture
def mock_settings():
    """Mocks get_settings to provide a dummy API key."""
    with patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings_instance = MagicMock()
        mock_settings_instance.GOOGLE_API_KEY = "test_api_key_123"
        mock_get_settings.return_value = mock_settings_instance
        yield mock_get_settings

# Fixture for mock genai.Client class
@pytest.fixture
def mock_genai_client_class():
    """Mocks google.genai.Client class and sets up its return value (mocked instance)."""
    with patch('google.genai.Client') as mock_class:
        mock_instance = MagicMock()
        mock_instance.models.generate_content = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_class # Yield the mocked class, so we can assert on its call

# Fixture for mock genai.Client instance
@pytest.fixture
def mock_genai_client_instance(mock_genai_client_class):
    """Provides the mocked instance of genai.Client that AIService will use."""
    return mock_genai_client_class.return_value

# Fixture for mock ProductDataService class
@pytest.fixture
def mock_product_service_class():
    """Mocks ProductDataService class and sets up its return value (mocked instance)."""
    with patch('app.services.product_data_service.ProductDataService') as mock_class:
        mock_instance = MagicMock()
        mock_instance.smart_search_products = AsyncMock()
        mock_class.return_value = mock_instance
        yield mock_class # Yield the mocked class

# Fixture for mock ProductDataService instance
@pytest.fixture
def mock_product_service_instance(mock_product_service_class):
    """Provides the mocked instance of ProductDataService that AIService will use."""
    return mock_product_service_class.return_value

# Fixture for AIService instance
@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client_class, mock_product_service_class):
    """Provides an initialized AIService instance for tests.
    It relies on the class mocks being set up, which in turn provide the instances."""
    return AIService()

@pytest.mark.asyncio
class TestAIService:
    """
    Comprehensive test suite for the AIService class.
    Aims for high test coverage of all methods, success and error paths,
    and specific logic like category/price extraction.
    """

    # --- Test __init__ method ---

    async def test_init_success(self, mock_settings, mock_genai_client_class, mock_product_service_class, caplog):
        """
        Tests successful initialization of AIService.
        Verifies that client and product_service are correctly set and an info log is recorded.
        """
        with caplog.at_level(logging.INFO):
            service = AIService()
            # Assert that the client and product service instances are the ones returned by their mocked classes
            assert service.client is mock_genai_client_class.return_value
            assert service.product_service is mock_product_service_class.return_value
            mock_settings.assert_called_once()
            mock_genai_client_class.assert_called_once_with(api_key="test_api_key_123")
            mock_product_service_class.assert_called_once() # Assert ProductDataService() was called
            assert "Successfully initialized AI service with Google AI client" in caplog.text

    async def test_init_no_api_key_exception(self, mock_settings, caplog):
        """
        Tests initialization failure when GOOGLE_API_KEY is missing or None.
        Ensures an exception is raised and an error log is captured.
        """
        mock_settings.return_value.GOOGLE_API_KEY = None # Simulate missing API key
        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception) as excinfo:
                AIService()
            assert "Error initializing AI service" in str(excinfo.value)
            assert "Error initializing AI service" in caplog.text

    async def test_init_genai_client_exception(self, mock_settings, caplog):
        """
        Tests initialization failure when google.genai.Client instantiation raises an exception.
        Ensures the specific exception is re-raised and an error log is captured.
        """
        # Patch genai.Client to raise an error during its instantiation
        with patch('google.genai.Client', side_effect=ValueError("Client init failed")):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(ValueError) as excinfo:
                    AIService()
                assert "Client init failed" in str(excinfo.value)
                assert "Error initializing AI service: Client init failed" in caplog.text

    async def test_init_product_service_exception(self, mock_settings, caplog):
        """
        Tests initialization failure when ProductDataService instantiation raises an exception.
        Ensures the specific exception is re-raised and an error log is captured.
        """
        # Patch ProductDataService to raise an error during its instantiation
        with patch('app.services.product_data_service.ProductDataService', side_effect=RuntimeError("Product service creation failed")):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(RuntimeError) as excinfo:
                    AIService()
                assert "Product service creation failed" in str(excinfo.value)
                assert "Error initializing AI service: Product service creation failed" in caplog.text

    # --- Test get_response method ---

    @pytest.mark.parametrize(
        "question, expected_category, expected_max_price",
        [
            ("Saya butuh laptop untuk kerja, budget 10 juta", "laptop", 10000000),
            ("Cari smartphone murah", "smartphone", 5000000), # "murah" keyword
            ("Headphone bluetooth terbaik", "headphone", None),
            ("Ada kamera buat vlogging?", "kamera", None),
            ("Tablet yang bagus untuk edukasi", "tablet", None),
            ("Cari hp harga di bawah 2 juta", "smartphone", 2000000), # Test price with "di bawah" context
            ("Speaker portable", "audio", None),
            ("Televisi 4K", "tv", None),
            ("Drone dengan kamera bagus", "drone", None),
            ("Smartwatch paling baru", "jam", None),
            ("produk", None, None), # No category, no price
            ("Laptop gaming 15 juta", "laptop", 15000000),
            ("notebook harga 7 juta", "laptop", 7000000), # "notebook" keyword
            ("saya mau handphone", "smartphone", None), # "handphone" keyword
            ("mencari ponsel murah", "smartphone", 5000000), # "ponsel" keyword and "murah"
            ("earphone wireless", "headphone", None), # "earphone" keyword
            ("kamera dslr", "kamera", None),
            ("televisi pintar", "tv", None),
            ("jam tangan pintar", "jam", None),
            ("Saya mau komputer yang murah", "laptop", 5000000), # "komputer" keyword and "murah"
            ("Tablet 3 juta", "tablet", 3000000),
            ("Berapa harga laptop 5 juta?", "laptop", 5000000),
            ("Berapa budget untuk HP sekitar 4 juta?", "smartphone", 4000000),
            ("Ada rekomendasi audio murah?", "audio", 5000000),
            ("TV 2 juta-an", "tv", 2000000), # Test different "juta" phrasing
            ("Mencari iphone budget", "smartphone", 5000000), # Test "iphone" for smartphone category, and "budget"
            ("hp 6 juta", "smartphone", 6000000), # Simple "hp" and "juta"
            ("Cari komputer gaming", "laptop", None), # Specific test for 'komputer' keyword without price
            ("tablet for kids", "tablet", None), # 'tablet' keyword in English
            ("ponsel harga murah", "smartphone", 5000000), # Combination of keywords and price type
            ("Saya mau beli headphone dibawah 1 juta", "headphone", 1000000),
        ]
    )
    async def test_get_response_category_price_extraction(self, ai_service_instance, mock_product_service_instance, mock_genai_client_instance, question, expected_category, expected_max_price):
        """
        Tests the category and max_price extraction logic within get_response for various inputs.
        Verifies smart_search_products is called with the correct extracted parameters.
        """
        # Set up default mock returns for smart_search_products and generate_content
        mock_product_service_instance.smart_search_products.return_value = ([], "Fallback message for extraction test")
        mock_genai_client_instance.models.generate_content.return_value.text = "AI response"

        await ai_service_instance.get_response(question)

        # Assert smart_search_products was called with the expected category and max_price
        mock_product_service_instance.smart_search_products.assert_awaited_once_with(
            keyword=question,
            category=expected_category,
            max_price=expected_max_price,
            limit=5
        )
        mock_genai_client_instance.models.generate_content.assert_called_once() # Ensure AI call is made after extraction


    async def test_get_response_success_with_products(self, ai_service_instance, mock_product_service_instance, mock_genai_client_instance, caplog):
        """
        Tests successful AI response generation when relevant products are found.
        Verifies the prompt content includes product details and the final AI response.
        """
        mock_products = [
            {"name": "Laptop Pro X", "price": 15000000, "brand": "TechCorp", "category": "laptop", "specifications": {"rating": 4.5}, "description": "Powerful laptop for professionals. Features high performance CPU and GPU, 16GB RAM, 512GB SSD and a 15-inch display. Ideal for coding and gaming."},
            {"name": "Smartphone Elite", "price": 8000000, "brand": "MobileCo", "category": "smartphone", "specifications": {"rating": 4.2}, "description": "Sleek and fast smartphone with amazing camera, long battery life, and a vibrant OLED screen."}
        ]
        fallback_msg = "Here are some relevant products based on your query."
        expected_ai_response = "Here is the AI's helpful response about these great products."

        mock_product_service_instance.smart_search_products.return_value = (mock_products, fallback_msg)
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response("Cari laptop dan smartphone")

            assert response == expected_ai_response
            # Assert smart_search_products was called with expected category and other params
            mock_product_service_instance.smart_search_products.assert_awaited_once_with(
                keyword="Cari laptop dan smartphone", category="laptop", max_price=None, limit=5
            )
            mock_genai_client_instance.models.generate_content.assert_called_once()
            assert "Getting AI response for question: Cari laptop dan smartphone" in caplog.text
            assert "Successfully generated AI response" in caplog.text

            # Verify prompt content partially by checking if product details are included
            call_args = mock_genai_client_instance.models.generate_content.call_args[1]['contents']
            assert "Relevant Products:" in call_args
            assert f"Question: Cari laptop dan smartphone\n\n{fallback_msg}\n\n" in call_args
            assert "1. Laptop Pro X" in call_args
            assert "   Price: Rp 15,000,000" in call_args
            assert "   Brand: TechCorp" in call_args
            assert "   Category: laptop" in call_args
            assert "   Rating: 4.5/5" in call_args
            # Check description trimming (first 200 chars + "...")
            expected_desc1 = "   Description: Powerful laptop for professionals. Features high performance CPU and GPU, 16GB RAM, 512GB SSD and a 15-inch display. Ideal for coding and gaming..."
            assert expected_desc1 in call_args

            assert "2. Smartphone Elite" in call_args
            assert "   Price: Rp 8,000,000" in call_args
            assert "   Brand: MobileCo" in call_args
            assert "   Category: smartphone" in call_args
            assert "   Rating: 4.2/5" in call_args
            expected_desc2 = "   Description: Sleek and fast smartphone with amazing camera, long battery life, and a vibrant OLED screen..."
            assert expected_desc2 in call_args
            # Check the model used in the API call
            assert "model='gemini-2.5-flash'" in str(mock_genai_client_instance.models.generate_content.call_args)


    async def test_get_response_success_no_products(self, ai_service_instance, mock_product_service_instance, mock_genai_client_instance, caplog):
        """
        Tests successful AI response generation when no products are found by product_service.
        Verifies the prompt content reflects no products and the final AI response.
        """
        fallback_msg = "Tidak ada produk yang cocok dengan pencarian Anda, namun saya bisa memberikan informasi umum."
        expected_ai_response = "AI response based on general query as no specific products were found."

        mock_product_service_instance.smart_search_products.return_value = ([], fallback_msg) # Return empty products
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response("Cari sesuatu yang sangat spesifik dan aneh")

            assert response == expected_ai_response
            mock_product_service_instance.smart_search_products.assert_awaited_once()
            mock_genai_client_instance.models.generate_content.assert_called_once()
            
            # Verify prompt content
            call_args = mock_genai_client_instance.models.generate_content.call_args[1]['contents']
            assert "No specific products found, but I can provide general recommendations." in call_args
            assert fallback_msg in call_args
            assert "Relevant Products:" not in call_args # Ensure this section is absent

            assert "Successfully generated AI response" in caplog.text

    async def test_get_response_smart_search_products_exception(self, ai_service_instance, mock_product_service_instance, mock_genai_client_instance, caplog):
        """
        Tests get_response gracefully handles exceptions raised by smart_search_products.
        Ensures a user-friendly fallback message is returned and an error log is captured.
        """
        mock_product_service_instance.smart_search_products.side_effect = Exception("Product search API failed")

        with caplog.at_level(logging.ERROR):
            response = await ai_service_instance.get_response("any question")

            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
            mock_product_service_instance.smart_search_products.assert_awaited_once()
            mock_genai_client_instance.models.generate_content.assert_not_called() # AI generation should not be attempted
            assert "Error generating AI response: Product search API failed" in caplog.text

    async def test_get_response_generate_content_exception(self, ai_service_instance, mock_product_service_instance, mock_genai_client_instance, caplog):
        """
        Tests get_response gracefully handles exceptions raised by genai.models.generate_content.
        Ensures a user-friendly fallback message is returned and an error log is captured.
        """
        mock_product_service_instance.smart_search_products.return_value = ([], "Fallback message") # Simulate successful product search
        mock_genai_client_instance.models.generate_content.side_effect = Exception("AI model inference error")

        with caplog.at_level(logging.ERROR):
            response = await ai_service_instance.get_response("another question for AI")

            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
            mock_product_service_instance.smart_search_products.assert_awaited_once()
            mock_genai_client_instance.models.generate_content.assert_called_once()
            assert "Error generating AI response: AI model inference error" in caplog.text

    async def test_get_response_empty_question(self, ai_service_instance, mock_product_service_instance, mock_genai_client_instance, caplog):
        """
        Tests get_response behavior when an empty question string is provided.
        Ensures the process still attempts to get products and generate a response.
        """
        mock_product_service_instance.smart_search_products.return_value = ([], "General fallback for empty query")
        mock_genai_client_instance.models.generate_content.return_value.text = "AI response for empty question."

        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response("")

            assert response == "AI response for empty question."
            # Assert smart_search_products was called with an empty keyword and no category/price
            mock_product_service_instance.smart_search_products.assert_awaited_once_with(
                keyword="", category=None, max_price=None, limit=5
            )
            mock_genai_client_instance.models.generate_content.assert_called_once()
            assert "Getting AI response for question: " in caplog.text
            assert "Successfully generated AI response" in caplog.text

    # --- Test generate_response method (legacy) ---

    def test_generate_response_success(self, ai_service_instance, mock_genai_client_instance, caplog):
        """
        Tests successful generation of AI response using the legacy generate_response method.
        Verifies the prompt structure and the final AI response.
        """
        test_context = "This is a test context for the legacy method, with some specific details."
        expected_ai_response = "Legacy AI response based on the provided context."

        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        with caplog.at_level(logging.INFO):
            response = ai_service_instance.generate_response(test_context)

            assert response == expected_ai_response
            # Verify generate_content was called with the correct model and prompt content
            mock_genai_client_instance.models.generate_content.assert_called_once_with(
                model="gemini-2.0-flash", # Specific model for legacy method
                contents=f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
            )
            assert "Generating AI response" in caplog.text
            assert "Successfully generated AI response" in caplog.text


    def test_generate_response_exception(self, ai_service_instance, mock_genai_client_instance, caplog):
        """
        Tests generate_response re-raises exceptions from genai.models.generate_content.
        Ensures an error log is captured.
        """
        mock_genai_client_instance.models.generate_content.side_effect = ValueError("Legacy AI generation failed")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                ai_service_instance.generate_response("Some context for an error scenario")

            assert "Legacy AI generation failed" in str(excinfo.value)
            mock_genai_client_instance.models.generate_content.assert_called_once()
            assert "Error generating AI response: Legacy AI generation failed" in caplog.text