from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

# Setup logging
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # API Configuration
    GOOGLE_API_KEY: str
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    FRONTEND_HOST: str = "localhost"
    FRONTEND_PORT: int = 8501
    DEBUG: bool = True

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.GOOGLE_API_KEY or self.GOOGLE_API_KEY == "your-google-api-key-here":
            logger.error("GOOGLE_API_KEY is not set or is using default value")
            raise ValueError("GOOGLE_API_KEY must be set in .env file")

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 