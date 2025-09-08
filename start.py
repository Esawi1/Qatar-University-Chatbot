#!/usr/bin/env python3
"""
Startup script for Qatar University Chatbot
Checks environment variables and starts the FastAPI application
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv

def check_environment():
    """Check if all required environment variables are set."""
    load_dotenv(find_dotenv(), override=True)
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX",
        "AZURE_SEARCH_KEY",
        "COSMOS_ENDPOINT",
        "COSMOS_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease update your .env file with the missing variables.")
        print("See README.md for setup instructions.")
        return False
    
    print("✅ All required environment variables are set.")
    return True

def main():
    """Main startup function."""
    print("🚀 Starting Qatar University Chatbot...")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check if uvicorn is available
    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn not found. Installing...")
        os.system("pip install uvicorn")
        import uvicorn
    
    print("✅ Starting FastAPI server...")
    print("📱 Chat UI will be available at: http://localhost:8010/chat-ui")
    print("📚 API docs will be available at: http://localhost:8010/docs")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
