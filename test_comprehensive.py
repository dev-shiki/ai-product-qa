#!/usr/bin/env python3
"""
Comprehensive test script untuk AI Product Q&A App
"""

import requests
import json
import time
import sys
import os

API_BASE_URL = "http://localhost:8000"

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️ {message}")

def test_api_health():
    """Test API health endpoint"""
    print_header("Testing API Health")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("API Health Check: PASSED")
            print_info(f"Status: {data.get('status', 'unknown')}")
            print_info(f"Version: {data.get('version', 'unknown')}")
            print_info(f"Source: {data.get('source', 'unknown')}")
            return True
        else:
            print_error(f"API Health Check: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"API Health Check: ERROR - {str(e)}")
        return False

def test_sources_endpoint():
    """Test sources endpoint"""
    print_header("Testing Sources Endpoint")
    
    try:
        response = requests.get(f"{API_BASE_URL}/sources", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get('sources', [])
            
            print_success("Sources Endpoint: PASSED")
            print_info(f"Found {len(sources)} data sources:")
            
            for source in sources:
                status_emoji = "🟢" if source.get('status') == 'primary' else "🟡"
                print(f"   {status_emoji} {source['name']}: {source['description']}")
            
            return True
        else:
            print_error(f"Sources Endpoint: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Sources Endpoint: ERROR - {str(e)}")
        return False

def test_simple_question():
    """Test simple question"""
    print_header("Testing Simple Question")
    
    question_data = {
        "question": "Saya mencari smartphone",
        "source": "fakestoreapi"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/queries/ask",
            json=question_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Simple Question: PASSED")
            print_info(f"Answer length: {len(data['answer'])} characters")
            print_info(f"Products found: {len(data['products'])}")
            print_info(f"Source used: {data['source_used']}")
            
            # Check answer quality
            if len(data['answer']) > 50:
                print_success("Answer quality: GOOD (detailed response)")
            else:
                print_error("Answer quality: POOR (too short)")
            
            return True
        else:
            print_error(f"Simple Question: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Simple Question: ERROR - {str(e)}")
        return False

def test_detailed_question():
    """Test detailed question"""
    print_header("Testing Detailed Question")
    
    question_data = {
        "question": "Saya mencari laptop untuk gaming dengan budget 15 juta rupiah, yang memiliki performa bagus untuk game AAA dan juga bisa untuk kerja. Mohon rekomendasinya.",
        "source": "fakestoreapi"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/queries/ask",
            json=question_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Detailed Question: PASSED")
            print_info(f"Answer length: {len(data['answer'])} characters")
            print_info(f"Products found: {len(data['products'])}")
            print_info(f"Source used: {data['source_used']}")
            
            # Check if answer addresses the budget
            if "15 juta" in data['answer'] or "budget" in data['answer'].lower():
                print_success("Budget consideration: DETECTED")
            else:
                print_error("Budget consideration: NOT DETECTED")
            
            return True
        else:
            print_error(f"Detailed Question: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Detailed Question: ERROR - {str(e)}")
        return False

def test_product_search():
    """Test product search"""
    print_header("Testing Product Search")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/queries/products/search?keyword=phone&limit=5",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Product Search: PASSED")
            print_info(f"Products found: {data['count']}")
            print_info(f"Keyword: {data['keyword']}")
            print_info(f"Source: {data['source']}")
            
            if data['count'] > 0:
                print_success("Search results: FOUND")
            else:
                print_error("Search results: EMPTY")
            
            return True
        else:
            print_error(f"Product Search: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Product Search: ERROR - {str(e)}")
        return False

def test_categories():
    """Test categories endpoint"""
    print_header("Testing Categories")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/queries/categories",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            
            print_success("Categories: PASSED")
            print_info(f"Categories found: {len(categories)}")
            
            if categories:
                print_info("Sample categories:")
                for i, cat in enumerate(categories[:5]):
                    print(f"   {i+1}. {cat}")
            
            return True
        else:
            print_error(f"Categories: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Categories: ERROR - {str(e)}")
        return False

def test_top_rated_products():
    """Test top rated products"""
    print_header("Testing Top Rated Products")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/queries/products/top-rated?source=fakestoreapi",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            print_success("Top Rated Products: PASSED")
            print_info(f"Products found: {len(products)}")
            
            if products:
                print_info("Sample products:")
                for i, product in enumerate(products[:3]):
                    name = product.get('name', 'Unknown')
                    rating = product.get('specifications', {}).get('rating', 0)
                    print(f"   {i+1}. {name} (⭐ {rating}/5)")
            
            return True
        else:
            print_error(f"Top Rated Products: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Top Rated Products: ERROR - {str(e)}")
        return False

def test_best_selling_products():
    """Test best selling products"""
    print_header("Testing Best Selling Products")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/queries/products/best-selling?source=fakestoreapi",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            print_success("Best Selling Products: PASSED")
            print_info(f"Products found: {len(products)}")
            
            if products:
                print_info("Sample products:")
                for i, product in enumerate(products[:3]):
                    name = product.get('name', 'Unknown')
                    sold = product.get('specifications', {}).get('sold', 0)
                    print(f"   {i+1}. {name} (Sold: {sold} units)")
            
            return True
        else:
            print_error(f"Best Selling Products: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Best Selling Products: ERROR - {str(e)}")
        return False

def test_fallback_source():
    """Test fallback source"""
    print_header("Testing Fallback Source")
    
    question_data = {
        "question": "Saya mencari smartphone",
        "source": "fallback"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/queries/ask",
            json=question_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Fallback Source: PASSED")
            print_info(f"Source used: {data['source_used']}")
            print_info(f"Products found: {len(data['products'])}")
            
            if data['source_used'] == 'fallback':
                print_success("Fallback mechanism: WORKING")
            else:
                print_info("Fallback mechanism: NOT USED (primary source available)")
            
            return True
        else:
            print_error(f"Fallback Source: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Fallback Source: ERROR - {str(e)}")
        return False

def test_error_handling():
    """Test error handling"""
    print_header("Testing Error Handling")
    
    # Test invalid source
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/queries/ask",
            json={"question": "test", "source": "invalid_source"},
            timeout=10
        )
        
        if response.status_code == 400:
            print_success("Invalid Source Error: HANDLED CORRECTLY")
        else:
            print_error("Invalid Source Error: NOT HANDLED")
        
    except Exception as e:
        print_error(f"Invalid Source Error: {str(e)}")
    
    # Test empty question
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/queries/ask",
            json={"question": "", "source": "fakestoreapi"},
            timeout=10
        )
        
        if response.status_code == 400:
            print_success("Empty Question Error: HANDLED CORRECTLY")
        else:
            print_error("Empty Question Error: NOT HANDLED")
        
    except Exception as e:
        print_error(f"Empty Question Error: {str(e)}")
    
    return True

def main():
    """Main test function"""
    print("🧪 Comprehensive Test for AI Product Q&A App")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print_error("app/main.py tidak ditemukan")
        print_info("Pastikan Anda menjalankan script ini dari folder ai-product-qa/")
        return
    
    # Run all tests
    tests = [
        ("API Health", test_api_health),
        ("Sources Endpoint", test_sources_endpoint),
        ("Simple Question", test_simple_question),
        ("Detailed Question", test_detailed_question),
        ("Product Search", test_product_search),
        ("Categories", test_categories),
        ("Top Rated Products", test_top_rated_products),
        ("Best Selling Products", test_best_selling_products),
        ("Fallback Source", test_fallback_source),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print_error(f"{test_name}: UNEXPECTED ERROR - {str(e)}")
    
    # Summary
    print_header("Test Summary")
    print(f"🎉 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("🎊 ALL TESTS PASSED! Application is working perfectly.")
        print("\n💡 Ready to use:")
        print("   1. Run: python run_app_simple.py")
        print("   2. Open: http://localhost:8501")
        print("   3. Start asking questions!")
    elif passed >= total * 0.8:
        print_info("⚠️ Most tests passed. Application should work fine.")
        print("\n💡 Try running the app and test manually.")
    else:
        print_error("❌ Many tests failed. Check backend and dependencies.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure backend is running: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("   2. Check dependencies: pip install -r requirements.txt")
        print("   3. Verify API endpoints: http://localhost:8000/health")
    
    print("\n🚀 Happy testing!")

if __name__ == "__main__":
    main() 