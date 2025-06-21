import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

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
        margin-bottom: 0.5rem;
    }
    .product-price {
        font-size: 1.3rem;
        font-weight: bold;
        color: #e74c3c;
        margin-bottom: 0.5rem;
    }
    .product-specs {
        font-size: 0.9rem;
        color: #bdc3c7;
        line-height: 1.4;
    }
    .recommendation-section {
        background: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .recommendation-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .recommendation-text {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #ecf0f1;
        background: #34495e;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        border: 1px solid #34495e;
    }
    .suggestion-button {
        background: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        transition: all 0.2s ease;
        cursor: pointer;
        text-align: left;
        width: 100%;
        color: #ffffff;
    }
    .suggestion-button:hover {
        background: #34495e;
        border-color: #3498db;
    }
    .input-section {
        background: #2c3e50;
        border: 2px solid #34495e;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-online {
        background: #27ae60;
    }
    .status-offline {
        background: #e74c3c;
    }
    .feature-list {
        background: #34495e;
        border: 1px solid #34495e;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        color: #ecf0f1;
    }
    .feature-list br {
        color: #ecf0f1;
    }
    .category-button {
        background: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        transition: all 0.2s ease;
        cursor: pointer;
        text-align: left;
        width: 100%;
        color: #ffffff;
    }
    .category-button:hover {
        background: #34495e;
        border-color: #3498db;
    }
    .recent-question {
        background: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        transition: all 0.2s ease;
        cursor: pointer;
        text-align: left;
        width: 100%;
        color: #ffffff;
    }
    .recent-question:hover {
        background: #34495e;
        border-color: #3498db;
    }
    /* Override Streamlit's default backgrounds for dark theme */
    .stApp {
        background-color: #1a252f;
    }
    .main .block-container {
        background-color: #1a252f;
    }
    .sidebar .sidebar-content {
        background-color: #1a252f;
    }
    /* Dark theme for Streamlit elements */
    .stTextInput > div > div > input {
        background-color: #34495e;
        color: #ffffff;
        border-color: #34495e;
    }
    .stButton > button {
        background-color: #2c3e50;
        color: #ffffff;
        border-color: #34495e;
    }
    .stButton > button:hover {
        background-color: #34495e;
        border-color: #3498db;
    }
    /* Headers and text in dark theme */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    p, div {
        color: #ecf0f1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🛍️ Product Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Temukan produk yang tepat untuk kebutuhan Anda</p>', unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_main_content()
    
    with col2:
        render_sidebar()

def render_main_content():
    """Render main content area"""
    st.header("💬 Cari Produk")
    
    # Initialize session state
    if 'question_count' not in st.session_state:
        st.session_state.question_count = 0
    if 'recent_questions' not in st.session_state:
        st.session_state.recent_questions = []
    
    # Input section
    with st.container():
        st.markdown("### 📝 Apa yang Anda cari?")
        
        with st.form(key="search_form", clear_on_submit=False):
            question = st.text_input(
                "Ketik pertanyaan Anda di sini...",
                key="question_input",
                placeholder="Contoh: Saya mencari laptop untuk kerja"
            )
            submitted = st.form_submit_button("🔍 Cari Produk", use_container_width=True)
            clear = st.form_submit_button("🗑️ Bersihkan", use_container_width=True)
        
        if submitted and question.strip():
            process_question(question.strip())
        elif clear:
            clear_results()
    
    # Display results
    if 'current_response' in st.session_state:
        display_results()
    
    # Show suggestions
    render_suggestions()

def render_sidebar():
    """Render sidebar content"""
    with st.sidebar:
        st.header("ℹ️ Informasi")
        
        # Status check
        status = check_api_status()
        if status:
            st.success("✅ Sistem siap")
        else:
            st.error("❌ Sistem offline")
        
        st.markdown("---")
        
        # Features
        st.markdown("### ✨ Fitur")
        st.markdown("""
        <div class="feature-list">
        • 🔍 Pencarian produk cerdas<br>
        • 📊 Rekomendasi personal<br>
        • 💰 Perbandingan harga<br>
        • ⭐ Ulasan dan rating<br>
        • 🚚 Info pengiriman
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Kategori")
        categories = ["Elektronik", "Fashion", "Kesehatan", "Rumah Tangga", "Olahraga", "Kecantikan"]
        for category in categories:
            if st.button(f"🏷️ {category}", key=f"cat_{category}", use_container_width=True):
                process_question(f"Produk kategori {category}")
        
        st.markdown("---")
        
        # Recent questions
        if st.session_state.recent_questions:
            st.markdown("### 📝 Pertanyaan Terakhir")
            for i, q in enumerate(st.session_state.recent_questions[-5:]):
                if st.button(f"💬 {q[:30]}...", key=f"recent_{i}", use_container_width=True):
                    process_question(q)

def render_suggestions():
    """Render suggestion buttons"""
    st.markdown("### 💡 Pertanyaan Populer")
    
    suggestions = [
        "Laptop terbaik untuk gaming",
        "Smartphone dengan kamera bagus",
        "Headphone wireless berkualitas",
        "Produk skincare untuk jerawat",
        "Sepatu olahraga yang nyaman",
        "Gadget untuk produktivitas kerja"
    ]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                process_question(suggestion)

def process_question(question: str):
    """Process user question"""
    try:
        with st.spinner("Mencari produk yang sesuai..."):
            response = ask_question(question)
            
            if response:
                st.session_state.current_response = response
                st.session_state.question_count += 1
                
                # Add to recent questions
                if question not in st.session_state.recent_questions:
                    st.session_state.recent_questions.append(question)
                    if len(st.session_state.recent_questions) > 10:
                        st.session_state.recent_questions.pop(0)
                
                st.rerun()
            else:
                st.error("Maaf, terjadi kesalahan saat mencari produk.")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def display_results():
    """Display search results"""
    response = st.session_state.current_response
    
    # Recommendation section
    st.markdown("### 💡 Rekomendasi")
    with st.container():
        st.markdown(f"""
        <div class="recommendation-section">
            <div class="recommendation-title">📋 Hasil Pencarian</div>
            <div class="recommendation-text">{response['answer']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Products section
    if response.get('products'):
        st.markdown("### 🛍️ Produk yang Ditemukan")
        for product in response['products']:
            display_product_card(product)

def display_product_card(product: dict):
    """Display a product card"""
    name = product.get('name', 'Unknown Product')
    price = product.get('price', 0)
    description = product.get('description', 'No description available')
    category = product.get('category', 'Unknown')
    brand = product.get('brand', 'Unknown')
    
    # Get specifications
    specs = product.get('specifications', {})
    rating = specs.get('rating', 0)
    sold = specs.get('sold', 0)
    stock = specs.get('stock', 0)
    
    st.markdown(f"""
    <div class="product-card">
        <div class="product-name">{name}</div>
        <div class="product-price">Rp {price:,.0f}</div>
        <div class="product-specs">
            <strong>Brand:</strong> {brand}<br>
            <strong>Kategori:</strong> {category}<br>
            <strong>Rating:</strong> ⭐ {rating}/5<br>
            <strong>Terjual:</strong> {sold} unit<br>
            <strong>Stok:</strong> {stock} unit<br>
            <strong>Deskripsi:</strong> {description[:100]}{'...' if len(description) > 100 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

def ask_question(question: str):
    """Send question to API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/queries/ask",
            json={"question": question},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def check_api_status():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def clear_results():
    """Clear current results"""
    if 'current_response' in st.session_state:
        del st.session_state.current_response
    st.rerun()

if __name__ == "__main__":
    main() 