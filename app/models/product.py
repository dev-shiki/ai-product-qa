from pydantic import BaseModel, Field
from typing import Dict, Optional, List

class ProductSpecifications(BaseModel):
    rating: Optional[float] = 0.0
    sold: Optional[int] = 0
    stock: Optional[int] = 0
    condition: Optional[str] = "Baru"
    shop_location: Optional[str] = "Indonesia"
    shop_name: Optional[str] = "Online Store"
    storage: Optional[str] = None
    color: Optional[str] = None
    warranty: Optional[str] = None

class Product(BaseModel):
    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    brand: str = Field(..., description="Product brand")
    price: int = Field(..., description="Product price in IDR")
    currency: str = Field(default="IDR", description="Currency code")
    description: str = Field(..., description="Product description")
    specifications: ProductSpecifications = Field(..., description="Product specifications")
    images: Optional[List[str]] = Field(default=[], description="Product images")
    url: Optional[str] = Field(default="", description="Product URL")

class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    price: int
    currency: str = "IDR"
    description: str
    specifications: Dict
    images: List[str] = []
    url: str = ""

class QueryResponse(BaseModel):
    answer: str
    products: List[dict]
    question: str
    note: Optional[str] = None 