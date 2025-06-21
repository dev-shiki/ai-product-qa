#!/usr/bin/env python3
"""
Simple script to run the Product Assistant application
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import streamlit
        import google
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting backend server...")
    
    # Change to app directory
    app_dir = Path(__file__).parent / "app"
    os.chdir(app_dir)
    
    try:
        # Start uvicorn server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is running on http://localhost:8000")
                return process
            else:
                print("❌ Backend server failed to start properly")
                return None
        except requests.exceptions.RequestException:
            print("❌ Backend server failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    print("🎨 Starting frontend...")
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    try:
        # Start streamlit
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501", "--server.address", "localhost"
        ])
        
        print("✅ Frontend is starting on http://localhost:8501")
        return process
        
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None

def main():
    """Main function to run the application"""
    print("🛍️ Product Assistant - Starting Application")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend. Exiting.")
        return
    
    # Wait a moment for backend to fully start
    time.sleep(2)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend. Exiting.")
        backend_process.terminate()
        return
    
    print("\n🎉 Application is running!")
    print("📱 Frontend: http://localhost:8501")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n💡 Tips:")
    print("- Press Ctrl+C to stop the application")
    print("- The frontend will automatically reload when you make changes")
    print("- Check the terminal for any error messages")
    
    try:
        # Keep the application running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
        
        # Terminate processes
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        
        print("✅ Application stopped")

if __name__ == "__main__":
    main() 