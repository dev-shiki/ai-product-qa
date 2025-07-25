from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import products, queries
from app.utils.config import settings

app = FastAPI(
    title="Product Assistant",
    description="Smart product recommendation system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(queries.router, prefix="/api/queries", tags=["queries"])

@app.get("/")
async def root():
    return {"message": "Product Assistant API - Ready to help you find products"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"} 