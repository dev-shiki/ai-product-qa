from app.models.product import Product, ProductSpecifications, ProductResponse

def test_product_specifications():
    spec = ProductSpecifications(rating=4.5, sold=100, stock=10, condition="Baru", shop_location="Jakarta", shop_name="Toko A", storage="128GB", color="Hitam", warranty="1 tahun")
    assert spec.rating == 4.5
    assert spec.sold == 100
    assert spec.shop_location == "Jakarta"
    assert spec.color == "Hitam"

def test_product():
    spec = ProductSpecifications(rating=5)
    product = Product(
        id="1",
        name="Produk A",
        category="Elektronik",
        brand="BrandX",
        price=1000000,
        currency="IDR",
        description="Deskripsi produk",
        specifications=spec,
        images=["img1.jpg"],
        url="http://produk.com/1"
    )
    assert product.id == "1"
    assert product.specifications.rating == 5
    assert product.images == ["img1.jpg"]

def test_product_response():
    resp = ProductResponse(
        id="1",
        name="Produk A",
        category="Elektronik",
        brand="BrandX",
        price=1000000,
        description="Deskripsi produk",
        specifications={"rating": 5},
        images=["img1.jpg"],
        url="http://produk.com/1"
    )
    assert resp.id == "1"
    assert resp.specifications["rating"] == 5 