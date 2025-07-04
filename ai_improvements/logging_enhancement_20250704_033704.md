# Logging Enhancement

**File**: `./tests/test_local_product_service.py`  
**Time**: 03:37:04  
**Type**: logging_enhancement

## Improvement

```python
from app.services.local_product_service import LocalProductService
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import logging

# Configure logging (adjust level and format as needed)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@pytest.fixture
def mock_json_data():
    """Mock JSON data for testing"""
    return {
        "products": [
            {
                "id": "P001",
                "name": "iPhone 15 Pro Max",
                "category": "smartphone",
                "brand": "Apple",
                "price": 21999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "48MP main, 12MP ultrawide, 12MP telephoto",
                    "battery": "4441 mAh",
                    "screen": "6.7 inch Super Retina XDR",
                    "processor": "A17 Pro chip"
                },
                "description": "iPhone 15 Pro Max dengan titanium design, kamera 48MP, dan performa terbaik",
                "availability": "in_stock",
                "stock_count": 25,
                "rating": 4.8,
                "reviews_count": 156
            },
            {
                "id": "P002",
                "name": "Samsung Galaxy S24 Ultra",
                "category": "smartphone",
                "brand": "Samsung",
                "price": 19999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "200MP main, 12MP ultrawide, 50MP telephoto, 10MP telephoto",
                    "battery": "5000 mAh",
                    "screen": "6.8 inch Dynamic AMOLED 2X",
                    "processor": "Snapdragon 8 Gen 3"
                },
                "description": "Galaxy S24 Ultra dengan S Pen, kamera 200MP, dan AI features",
                "availability": "in_stock",
                "stock_count": 20,
                "rating": 4.8,
                "reviews_count": 134
            },
            {
                "id": "P003",
                "name": "Google Pixel 8 Pro",
                "category": "smartphone",
                "brand": "Google",
                "price": 16999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "128GB, 256GB, 512GB",
                    "camera": "50MP main, 48MP ultrawide, 48MP telephoto",
                    "battery": "5050 mAh",
                    "screen": "6.7 inch LTPO OLED",
                    "processor": "Google Tensor G3"
                },
                "description": "Pixel 8 Pro dengan AI-powered features, kamera terbaik, dan desain yang unik",
                "availability": "in_stock",
                "stock_count": 15,
                "rating": 4.7,
                "reviews_count": 112
            },
            {
                "id": "P004",
                "name": "Xiaomi 14 Pro",
                "category": "smartphone",
                "brand": "Xiaomi",
                "price": 14999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB, 1TB",
                    "camera": "50MP main, 50MP ultrawide, 50MP telephoto",
                    "battery": "4880 mAh",
                    "screen": "6.73 inch AMOLED",
                    "processor": "Snapdragon 8 Gen 3"
                },
                "description": "Xiaomi 14 Pro dengan kamera Leica, pengisian daya cepat, dan performa tinggi",
                "availability": "out_of_stock",
                "stock_count": 0,
                "rating": 4.6,
                "reviews_count": 98
            },
            {
                "id": "P005",
                "name": "OnePlus 12",
                "category": "smartphone",
                "brand": "OnePlus",
                "price": 12999000,
                "currency": "IDR",
                "specifications": {
                    "storage": "256GB, 512GB",
                    "camera": "50MP main, 48MP ultrawide, 64MP telephoto",
                    "battery": "5400 mAh",
                    "screen": "6.82 inch LTPO AMOLED",
                    "processor": "Snapdragon 8 Gen 3"
                },
                "description": "OnePlus 12 dengan OxygenOS, pengisian daya super cepat, dan performa gaming",
                "availability": "in_stock",
                "stock_count": 10,
                "rating": 4.5,
                "reviews_count": 85
            }
        ]
    }


@pytest.fixture
def local_product_service(mock_json_data, tmp_path):
    """Fixture for LocalProductService with a temporary JSON file"""
    file_path = tmp_path / "products.json"
    with open(file_path, "w") as f:
        json.dump(mock_json_data, f)
    return LocalProductService(file_path)


def test_get_all_products(local_product_service):
    """Test getting all products"""
    products = local_product_service.get_all_products()
    assert len(products) == 5
    assert products[0]["id"] == "P001"

def test_get_product_by_id(local_product_service):
    """Test getting a product by ID"""
    product = local_product_service.get_product_by_id("P002")
    assert product["name"] == "Samsung Galaxy S24 Ultra"
    assert product["price"] == 19999000

def test_add_product(local_product_service):
    """Test adding a new product"""
    new_product = {
        "id": "P006",
        "name": "Sony Xperia 1 VI",
        "category": "smartphone",
        "brand": "Sony",
        "price": 15999000,
        "currency": "IDR",
        "specifications": {
            "storage": "256GB, 512GB",
            "camera": "48MP main, 12MP ultrawide, 12MP telephoto",
            "battery": "5000 mAh",
            "screen": "6.5 inch OLED",
            "processor": "Snapdragon 8 Gen 3"
        },
        "description": "Sony Xperia 1 VI dengan desain premium, kamera handal, dan audio berkualitas",
        "availability": "preorder",
        "stock_count": 5,
        "rating": 4.4,
        "reviews_count": 72
    }
    local_product_service.add_product(new_product)
    products = local_product_service.get_all_products()
    assert len(products) == 6
    assert products[-1]["name"] == "Sony Xperia 1 VI"


def test_update_product(local_product_service):
    """Test updating an existing product"""
    updated_product = {
        "id": "P003",
        "name": "Google Pixel 8 Pro (Updated)",
        "category": "smartphone",
        "brand": "Google",
        "price": 17999000,
        "currency": "IDR",
        "specifications": {
            "storage": "256GB, 512GB",
            "camera": "50MP main, 48MP ultrawide, 48MP telephoto",
            "battery": "5100 mAh",
            "screen": "6.7 inch LTPO OLED",
            "processor": "Google Tensor G3"
        },
        "description": "Pixel 8 Pro dengan AI-powered features, kamera terbaik, dan desain yang unik (Updated)",
        "availability": "in_stock",
        "stock_count": 18,
        "rating": 4.8,
        "reviews_count": 120
    }
    local_product_service.update_product("P003", updated_product)
    product = local_product_service.get_product_by_id("P003")
    assert product["name"] == "Google Pixel 8 Pro (Updated)"
    assert product["price"] == 17999000
    assert product["reviews_count"] == 120

def test_delete_product(local_product_service):
    """Test deleting a product"""
    local_product_service.delete_product("P004")
    products = local_product_service.get_all_products()
    assert len(products) == 4
    with pytest.raises(ValueError):
        local_product_service.get_product_by_id("P004")


def test_get_products_by_category(local_product_service):
    """Test getting products by category"""
    products = local_product_service.get_products_by_category("smartphone")
    assert len(products) == 5
    for product in products:
        assert product["category"] == "smartphone"


def test_get_products_by_brand(local_product_service):
    """Test getting products by brand"""
    products = local_product_service.get_products_by_brand("Samsung")
    assert len(products) == 1
    assert products[0]["name"] == "Samsung Galaxy S24 Ultra"

def test_get_products_by_availability(local_product_service):
    """Test getting products by availability"""
    in_stock_products = local_product_service.get_products_by_availability("in_stock")
    assert len(in_stock_products) == 4

    out_of_stock_products = local_product_service.get_products_by_availability("out_of_stock")
    assert len(out_of_stock_products) == 1
    assert out_of_stock_products[0]["name"] == "Xiaomi 14 Pro"


def test_get_products_by_price_range(local_product_service):
    """Test getting products by price range"""
    products = local_product_service.get_products_by_price_range(15000000, 20000000)
    assert len(products) == 3  # Samsung, Google, Xiaomi
    product_names = [product["name"] for product in products]
    assert "Samsung Galaxy S24 Ultra" in product_names
    assert "Google Pixel 8 Pro" in product_names
    assert "Xiaomi 14 Pro" in product_names

def test_search_products(local_product_service):
    """Test searching for products by keyword"""
    products = local_product_service.search_products("Pro")
    assert len(products) == 5
    product_names = [product["name"] for product in products]
    assert "iPhone 15 Pro Max" in product_names
    assert "Samsung Galaxy S24 Ultra" in product_names
    assert "Google Pixel 8 Pro" in product_names
    assert "Xiaomi 14 Pro" in product_names

def test_sort_products_by_price(local_product_service):
    """Test sorting products by price"""
    products = local_product_service.sort_products_by_price(ascending=True)
    assert products[0]["name"] == "OnePlus 12"
    assert products[-1]["name"] == "iPhone 15 Pro Max"

    products_desc = local_product_service.sort_products_by_price(ascending=False)
    assert products_desc[0]["name"] == "iPhone 15 Pro Max"
    assert products_desc[-1]["name"] == "OnePlus 12"


def test_sort_products_by_rating(local_product_service):
    """Test sorting products by rating"""
    products = local_product_service.sort_products_by_rating(ascending=True)
    assert products[0]["name"] == "OnePlus 12"
    assert products[-1]["name"] == "iPhone 15 Pro Max"

    products_desc = local_product_service.sort_products_by_rating(ascending=False)
    assert products_desc[0]["name"] == "iPhone 15 Pro Max"
    assert products_desc[-1]["name"] == "OnePlus 12"


def test_apply_discount(local_product_service):
    """Test applying a discount to all products"""
    discounted_products = local_product_service.apply_discount(10)
    for product in discounted_products:
        original_price = next(p["price"] for p in local_product_service.get_all_products() if p["id"] == product["id"])
        expected_discounted_price = original_price * 0.9  # 10% discount
        assert product["price"] == expected_discounted_price


def test_calculate_average_price(local_product_service):
    """Test calculating the average price of all products"""
    average_price = local_product_service.calculate_average_price()
    total_price = sum(product["price"] for product in local_product_service.get_all_products())
    expected_average_price = total_price / len(local_product_service.get_all_products())
    assert average_price == expected_average_price


def test_get_highest_rated_product(local_product_service):
    """Test getting the highest rated product"""
    highest_rated_product = local_product_service.get_highest_rated_product()
    assert highest_rated_product["name"] == "iPhone 15 Pro Max"

def test_get_most_reviewed_product(local_product_service):
    """Test getting the most reviewed product"""
    most_reviewed_product = local_product_service.get_most_reviewed_product()
    assert most_reviewed_product["name"] == "iPhone 15 Pro Max"

def test_get_products_with_low_stock(local_product_service):
    """Test getting products with stock count below a threshold"""
    low_stock_products = local_product_service.get_products_with_low_stock(15)
    assert len(low_stock_products) == 3
    product_names = [product["name"] for product in low_stock_products]
    assert "Google Pixel 8 Pro" in product_names
    assert "Xiaomi 14 Pro" in product_names
    assert "OnePlus 12" in product_names

def test_group_products_by_brand(local_product_service):
    """Test grouping products by brand"""
    grouped_products = local_product_service.group_products_by_brand()
    assert len(grouped_products) == 5
    assert "Apple" in grouped_products
    assert "Samsung" in grouped_products
    assert len(grouped_products["Apple"]) == 1
    assert grouped_products["Apple"][0]["name"] == "iPhone 15 Pro Max"

def test_get_total_stock_value(local_product_service):
    """Test calculating the total stock value of all products"""
    total_stock_value = local_product_service.get_total_stock_value()
    expected_total_stock_value = sum(product["price"] * product["stock_count"] for product in local_product_service.get_all_products())
    assert total_stock_value == expected_total_stock_value


def test_is_product_available(local_product_service):
    """Test checking if a product is available"""
    assert local_product_service.is_product_available("P001") == True
    assert local_product_service.is_product_available("P004") == False

def test_validate_product_data(local_product_service):
    """Test validating product data"""
    valid_product = {
        "id": "P007",
        "name": "New Product",
        "category": "electronics",
        "brand": "Generic",
        "price": 9999000,
        "currency": "IDR",
        "specifications": {},
        "description": "A new product",
        "availability": "in_stock",
        "stock_count": 10,
        "rating": 4.0,
        "reviews_count": 50
    }
    is_valid, errors = local_product_service.validate_product_data(valid_product)
    assert is_valid == True
    assert not errors

    invalid_product = {
        "id": "P008",
        "name": "Invalid Product",
        "category": "electronics",
        "brand": "Generic",
        "price": "invalid",  # Invalid price
        "currency": "IDR",
        "specifications": {},
        "description": "An invalid product",
        "availability": "in_stock",
        "stock_count": 10,
        "rating": 6.0,  # Invalid rating
        "reviews_count": 50
    }
    is_valid, errors = local_product_service.validate_product_data(invalid_product)
    assert is_valid == False
    assert errors

def test_calculate_total_revenue(local_product_service):
    """Test calculating the total revenue generated by all products"""
    # Assuming each product has been sold at least once (for simplicity)
    # In a real scenario, you would need to track sales data
    total_revenue = local_product_service.calculate_total_revenue()
    expected_total_revenue = sum(product["price"] * product["reviews_count"] for product in local_product_service.get_all_products())
    assert total_revenue == expected_total_revenue


def test_recommend_products(local_product_service):
    """Test recommending products based on a given product (simple example)"""
    # Assuming recommendations are based on category
    product_id = "P001"  # iPhone 15 Pro Max
    recommended_products = local_product_service.recommend_products(product_id)
    assert len(recommended_products) == 4  # Other smartphones
    for product in recommended_products:
        assert product["category"] == "smartphone"
        assert product["id"] != product_id


def test_update_stock_count(local_product_service):
    """Test updating the stock count of a product"""
    product_id = "P002"  # Samsung Galaxy S24 Ultra
    new_stock_count = 25
    local_product_service.update_stock_count(product_id, new_stock_count)
    product = local_product_service.get_product_by_id(product_id)
    assert product["stock_count"] == new_stock_count


def test_get_products_with_missing_fields(local_product_service):
    """Test identifying products with missing fields (for data quality checks)"""
    # Modify a product to have a missing field (e.g., remove description)
    products = local_product_service.get_all_products()
    products[0].pop("description")
    local_product_service.save_products(products)

    missing_field_products = local_product_service.get_products_with_missing_fields()
    assert len(missing_field_products) == 1
    assert missing_field_products[0]["id"] == "P001"
    assert "description" in missing_field_products[0]["missing_fields"]


def test_get_products_with_invalid_prices(local_product_service):
    """Test identifying products with invalid prices (e.g., negative or zero prices)"""
    # Modify a product to have an invalid price (e.g., set price to 0)
    products = local_product_service.get_all_products()
    products[0]["price"] = 0
    local_product_service.save_products(products)

    invalid_price_products = local_product_service.get_products_with_invalid_prices()
    assert len(invalid_price_products) == 1
    assert invalid_price_products[0]["id"] == "P001"
    assert invalid_price_products[0]["price"] == 0

def test_get_average_rating_by_category(local_product_service):
    """Test calculating the average rating for each product category"""
    average_ratings = local_product_service.get_average_rating_by_category()
    assert "smartphone" in average_ratings
    # Calculate expected average rating for smartphones
    smartphone_ratings = [product["rating"] for product in local_product_service.get_products_by_category("smartphone")]
    expected_average_rating = sum(smartphone_ratings) / len(smartphone_ratings)
    assert average_ratings["smartphone"] == expected_average_rating


def test_apply_bulk_discount(local_product_service):
    """Test applying a bulk discount to products based on certain criteria (e.g., brand)"""
    # Apply a 5% discount to all Samsung products
    brand = "Samsung"
    discount_percentage = 5
    local_product_service.apply_bulk_discount(brand, discount_percentage)

    # Verify that the discount was applied to Samsung products
    samsung_products = local_product_service.get_products_by_brand(brand)
    for product in samsung_products:
        original_price = next(p["price"] for p in local_product_service.get_all_products() if p["id"] == product["id"])
        expected_discounted_price = original_price * (1 - discount_percentage / 100)
        assert product["price"] == expected_discounted_price


def test_get_products_with_specifications(local_product_service):
    """Test filtering products based on specific specifications (e.g., camera resolution)"""
    # Get all products with a camera resolution greater than or equal to 50MP
    camera_resolution = "50MP"
    filtered_products = local_product_service.get_products_with_specifications(camera_resolution)

    # Verify that the filtered products meet the criteria
    for product in filtered_products:
        assert camera_resolution in product["specifications"]["camera"]

def test_get_products_with_partial_specifications(local_product_service):
    """Test getting products that contain specific substrings within their specifications."""
    search_term = "AMOLED"
    products = local_product_service.get_products_with_partial_specifications(search_term)
    assert len(products) > 0  # Assuming there are products with AMOLED in their specs.
    for product in products:
        found = False
        for key, value in product["specifications"].items():
            if search_term in value:
                found = True
                break
        assert found, f"Product {product['id']} should contain '{search_term}' in specifications."

def test_calculate_price_difference(local_product_service):
    """Test calculating the price difference between two products."""
    product1_id = "P001"
    product2_id = "P002"
    price_difference = local_product_service.calculate_price_difference(product1_id, product2_id)
    product1 = local_product_service.get_product_by_id(product1_id)
    product2 = local_product_service.get_product_by_id(product2_id)
    expected_price_difference = product1["price"] - product2["price"]
    assert price_difference == expected_price_difference


def test_get_common_specifications(local_product_service):
    """Test identifying common specifications among products within a specific category."""
    category = "smartphone"
    common_specs = local_product_service.get_common_specifications(category)
    # This test depends on the data.  For example, "storage" should be common.
    assert "storage" in common_specs  # Assuming all smartphones have storage as a specification.

def test_filter_products_by_multiple_criteria(local_product_service):
    """Test filtering products based on a combination of criteria."""
    # Filter for in-stock products with a price less than 18000000
    filters = {
        "availability": "in_stock",
        "max_price": 18000000
    }
    filtered_products = local_product_service.filter_products_by_multiple_criteria(filters)

    # Verify that the filtered products meet the criteria
    for product in filtered_products:
        assert product["availability"] == "in_stock"
        assert product["price"] < 18000000


def test_rank_products_by_popularity(local_product_service):
    """Test ranking products based on their popularity (e.g., review count)"""
    ranked_products = local_product_service.rank_products_by_popularity()
    # The most reviewed product should be the first
    assert ranked_products[0]["name"] == "iPhone 15 Pro Max"  # Assuming this has the highest reviews

def test_analyze_product_descriptions(local_product_service):
    """Test analyzing product descriptions to extract common keywords or features"""
    keywords = local_product_service.analyze_product_descriptions()
    # Assuming "kamera" (camera) is a common keyword in the descriptions
    assert "kamera" in keywords  # Depending on the data and analysis logic

def test_get_similar_products_by_specifications(local_product_service):
    """Test recommending similar products based on their specifications"""
    product_id = "P001"  # iPhone 15 Pro Max
    similar_products = local_product_service.get_similar_products_by_specifications(product_id)

    # Check if the returned products are similar (e.g., same category) and not the same as the input product
    for product in similar_products:
        assert product["category"] == "smartphone"
        assert product["id"] != product_id

def test_calculate_average_price_by_brand(local_product_service):
    """Test calculating the average price of products for each brand"""
    average_prices = local_product_service.calculate_average_price_by_brand()
    assert "Apple" in average_prices
    # Calculate expected average price for Apple products
    apple_products = local_product_service.get_products_by_brand("Apple")
    expected_average_price = sum(product["price"] for product in apple_products) / len(apple_products)
    assert average_prices["Apple"] == expected_average_price

def test_get_products_with_specific_storage(local_product_service):
    """Test getting products with a specific storage capacity."""
    storage_capacity = "256GB"
    products = local_product_service.get_products_with_specific_storage(storage_capacity)
    assert len(products) > 0
    for product in products:
        assert storage_capacity in product["specifications"]["storage"]

def test_update_product_availability(local_product_service):
    """Test updating the availability status of a product."""
    product_id = "P003"
    new_availability = "out_of_stock"
    local_product_service.update_product_availability(product_id, new_availability)
    product = local_product_service.get_product_by_id(product_id)
    assert product["availability"] == new_availability

def test_calculate_weighted_average_rating(local_product_service):
    """Test calculating a weighted average rating based on rating and review count."""
    weighted_average = local_product_service.calculate_weighted_average_rating()
    # This is a complex calculation, so we check only the type and non-negativity.
    assert isinstance(weighted_average, float)
    assert weighted_average >= 0  # Weighted average cannot be negative.

def test_get_products_with_long_descriptions(local_product_service):
    """Test getting products with descriptions longer than a specified length."""
    description_length = 100
    products = local_product_service.get_products_with_long_descriptions(description_length)
    assert len(products) > 0  # Assuming all descriptions are longer than 100 characters
    for product in products:
        assert len(product["description"]) > description_length

def test_validate_currency_consistency(local_product_service):
    """Test validating if all products use the same currency."""
    is_consistent = local_product_service.validate_currency_consistency()
    assert is_consistent  # All products use "IDR" in this data.

def test_group_products_by_price_range(local_product_service):
    """Test grouping products into predefined price ranges."""
    price_ranges = {
        "budget": (0, 15000000),
        "mid_range": (15000000, 20000000),
        "premium": (20000000, float('inf'))
    }
    grouped_products = local_product_service.group_products_by_price_range(price_ranges)

    # Verify the products are grouped correctly.
    assert "budget" in grouped_products
    assert "mid_range" in grouped_products
    assert "premium" in grouped_products

    for product in grouped_products["budget"]:
        assert product["price"] >= price_ranges["budget"][0] and product["price"] < price_ranges["budget"][1]

def test_get_products_with_similar_names(local_product_service):
    """Test finding products with similar names based on a given product name."""
    product_name = "Galaxy S24 Ultra"  # Example
    similar_products = local_product_service.get_products_with_similar_names(product_name)

    # Assuming similar products might have "Galaxy" or "S24" in their names
    for product in similar_products:
        assert "Galaxy" in product["name"] or "S24" in product["name"]

def test_filter_products_by_rating_range(local_product_service):
    """Test filtering products based on a specified rating range."""
    min_rating = 4.5
    max_rating = 4.8
    filtered_products = local_product_service.filter_products_by_rating_range(min_rating, max_rating)

    for product in filtered_products:
        assert min_rating <= product["rating"] <= max_rating

def test_calculate_average_stock_count(local_product_service):
    """Test calculating the average stock count of all products."""
    average_stock = local_product_service.calculate_average_stock_count()
    total_stock = sum(product["stock_count"] for product in local_product_service.get_all_products())
    expected_average_stock = total_stock / len(local_product_service.get_all_products())
    assert average_stock == expected_average_stock

def test_find_products_with_specific_keywords(local_product_service):
    """Test finding products whose descriptions contain specific keywords."""
    keywords = ["kamera", "terbaik"]
    products = local_product_service.find_products_with_specific_keywords(keywords)

    for product in products:
        description = product["description"].lower()  # Convert to lowercase for case-insensitive matching
        for keyword in keywords:
            assert keyword.lower() in description

def test_sort_products_by_name(local_product_service):
    """Test sorting products alphabetically by name."""
    ascending = True
    products = local_product_service.sort_products_by_name(ascending)
    sorted_names = [product["name"] for product in products]
    assert sorted_names == sorted(sorted_names)  # Check if the names are sorted alphabetically


def test_add_product(local_product_service):
    """Test adding a new product"""
    logging.info("Starting test_add_product")  # Log entry

    new_product = {
        "id": "P006",
        "name": "Sony Xperia 1 VI",
        "category": "smartphone",
        "brand": "Sony",
        "price": 15999000,
        "currency": "IDR",
        "specifications": {
            "storage": "256GB, 512GB",
            "camera": "48MP main, 12MP ultrawide, 12MP telephoto",
            "battery": "5000 mAh",
            "screen": "6.5 inch OLED",
            "processor": "Snapdragon 8 Gen 3"
        },
        "description": "Sony Xperia 1 VI dengan desain premium, kamera handal, dan audio berkualitas",
        "availability": "preorder",
        "stock_count": 5,
        "rating": 4.4,
        "reviews_count": 72
    }

    logging.debug(f"Adding product: {new_product}")  # Log the product being added

    local_product_service.add_product(new_product)
    products = local_product_service.get_all_products()

    logging.info(f"Number of products after adding: {len(products)}")  # Log the number of products

    assert len(products) == 6
    assert products[-1]["name"] == "Sony Xperia 1 VI"

    logging.info("Finished test_add_product successfully")  # Log exit

```

Key improvements and explanations:

* **Clear Logging Configuration

---
*Generated by Smart AI Bot*
