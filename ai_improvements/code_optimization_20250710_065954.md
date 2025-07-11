# Code Optimization

**File**: `./app/utils/config.py`  
**Time**: 06:59:54  
**Type**: code_optimization

## Improvement

**Improvement:**

Remove the custom `__init__` method from the `Settings` class.

**Explanation:**

Pydantic's `BaseSettings` automatically handles loading environment variables and validating them. The custom `__init__` method duplicates some of this functionality and isn't necessary. Specifically,  Pydantic offers validation capabilities.  We can leverage Pydantic's validation to check for the API key.

Here's the improved code:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache
import logging
from pydantic import validator

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

    @validator("GOOGLE_API_KEY")
    def google_api_key_must_be_set(cls, v):
        if not v or v == "your-google-api-key-here":
            logger.error("GOOGLE_API_KEY is not set or is using default value")
            raise ValueError("GOOGLE_API_KEY must be set in .env file")
        return v


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

By using a Pydantic validator, we get the validation with better integration into the Pydantic way of doing things, and removing the custom init allows Pydantic to function at its best. This makes the code cleaner, more maintainable, and potentially slightly more efficient.  It also avoids any potential conflicts between your custom initialization and Pydantic's built-in initialization process.

---
*Generated by Smart AI Bot*
