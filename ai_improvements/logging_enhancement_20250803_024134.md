# Logging Enhancement

**File**: `./frontend/streamlit_app.py`  
**Time**: 02:41:34  
**Type**: logging_enhancement

## Improvement

```python
import streamlit as st
import requests
import json
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
API_BASE_URL = "http://localhost:8000"

def fetch_products(query: str, category: str = None):
    """
    Fetches product recommendations from the API based on a query and optional category.
    """
    logging.info(f"Fetching products for query: '{query}' and category: '{category}'")  # Log input parameters
    
    url = f"{API_BASE_URL}/products/"
    params = {"query": query}
    if category:
        params["category"] = category

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        products = response.json()
        logging.info(f"Successfully fetched {len(products)} products.")  # Log success and number of products
        return products
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching products: {e}")  # Log the specific error
        st.error(f"An error occurred while fetching products: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON response: {e}")
        st.error(f"Error decoding JSON response: {e}")
        return []
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}") # Log unexpected exceptions with traceback
        st.error(f"An unexpected error occurred: {e}")
        return []


def main():
    st.set_page_config(
        page_title="Product Assistant",
        page_icon="🛍️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for dark theme
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ffffff;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #bdc3c7;
        text-align: center;
        margin-bottom: 2rem;
    }
    .product-card {
        border: 1px solid #34495e;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        background: #2c3e50;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .product-name {
        font-size: 1.2rem;
        font-weight: 600;
        color: #ffffff;
    

```

Key improvements and explanations:

* **`import logging`**:  Adds the necessary import.
* **`logging.basicConfig(...)`**:  Critically important!  This configures the logging system.  Without it, you won't see any logs.  `level=logging.INFO` means you'll see INFO, WARNING, ERROR, and CRITICAL messages.  The `format` specifies the structure of the log messages (timestamp, level, message).  You can customize this to your needs.
* **`logging.info(f"Fetching products for query: '{query}' and category: '{category}'")`**: Logs the input parameters to the function. This is crucial for debugging, so you know what the function was called with.
* **`response.raise_for_status()`**:  This is *essential* for robust API interaction.  It will raise an `HTTPError` exception if the HTTP response status code indicates an error (4xx or 5xx).  This allows you to catch and handle API errors gracefully.
* **`logging.info(f"Successfully fetched {len(products)} products.")`**: Logs the successful retrieval of data, along with the number of items retrieved.
* **`except requests.exceptions.RequestException as e:`**: This catches network-related errors during the API request (e.g., connection refused, timeout, DNS resolution failure).  It's important to catch these, as they are common when dealing with external APIs. The specific error message is logged.
* **`except json.JSONDecodeError as e:`**: This catches errors that occur when the API response is not valid JSON.  This can happen if the API is down or returns an unexpected format. Again, the specific error is logged.
* **`except Exception as e:`**: Catches *any* other unexpected exception.  This is a general catch-all and *must* be the last `except` block.  Using `logging.exception(f"An unexpected error occurred: {e}")` is critical here, as it logs the full traceback, which is invaluable for diagnosing unexpected errors.  Critically important to use `logging.exception` to include the traceback.
* **`st.error(f"An error occurred while fetching products: {e}")`**: Displays an error message in the Streamlit app to inform the user that something went wrong.  This provides feedback to the user and prevents the app from crashing silently.
* **Return `[]` on error**:  The function now consistently returns an empty list (`[]`) when an error occurs.  This prevents downstream code from trying to process invalid data and causing further errors. This is crucial for making your code more robust.
* **Clearer Error Messages:** The error messages passed to `st.error` are more informative, making it easier to understand what went wrong.

This revised version provides comprehensive logging and error handling, making your function much more robust and easier to debug.  The use of `logging.exception` for the general `except` block is particularly important for catching unexpected errors.  The addition of `response.raise_for_status()` is also crucial for handling HTTP errors from the API.

---
*Generated by Smart AI Bot*
