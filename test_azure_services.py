#!/usr/bin/env python3
"""
Test script to verify Azure services configuration
Run this locally to test your Azure services before deploying
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=True)

def test_environment_variables():
    """Test if all required environment variables are set."""
    print("🔍 Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": "Azure OpenAI endpoint",
        "AZURE_OPENAI_KEY": "Azure OpenAI API key", 
        "AZURE_OPENAI_DEPLOYMENT": "Azure OpenAI deployment name",
        "AZURE_SEARCH_ENDPOINT": "Azure Search endpoint",
        "AZURE_SEARCH_INDEX": "Azure Search index name",
        "AZURE_SEARCH_KEY": "Azure Search API key",
        "COSMOS_ENDPOINT": "Cosmos DB endpoint",
        "COSMOS_KEY": "Cosmos DB key",
        "COSMOS_DB": "Cosmos DB database name",
        "COSMOS_CONTAINER": "Cosmos DB container name"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {description} - Set")
        else:
            print(f"❌ {var}: {description} - MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing {len(missing_vars)} required environment variables!")
        return False
    else:
        print(f"\n✅ All {len(required_vars)} environment variables are set!")
        return True

def test_azure_openai():
    """Test Azure OpenAI connection."""
    print("\n🤖 Testing Azure OpenAI...")
    print("=" * 50)
    
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
        )
        
        response = client.chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=50
        )
        
        answer = response.choices[0].message.content
        print(f"✅ Azure OpenAI working! Response: {answer}")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI failed: {e}")
        return False

def test_azure_search():
    """Test Azure Search connection."""
    print("\n🔍 Testing Azure Search...")
    print("=" * 50)
    
    try:
        from search_client import run_search, HAVE_SEARCH
        
        if not HAVE_SEARCH:
            print("❌ Azure Search not configured (missing environment variables)")
            return False
        
        results = run_search("test query", top=3)
        print(f"✅ Azure Search working! Found {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. {result.get('name', 'Unknown')}: {result.get('snippet', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure Search failed: {e}")
        return False

def test_cosmos_db():
    """Test Cosmos DB connection."""
    print("\n💾 Testing Cosmos DB...")
    print("=" * 50)
    
    try:
        from db_service import get_session_info
        
        # Test with a dummy session
        test_session_id = "test-session-123"
        info = get_session_info(test_session_id)
        
        if info is not None:
            print(f"✅ Cosmos DB working! Session info retrieved")
            print(f"   Database: {os.getenv('COSMOS_DB')}")
            print(f"   Container: {os.getenv('COSMOS_CONTAINER')}")
            return True
        else:
            print("⚠️ Cosmos DB connected but no session info (this might be normal for new sessions)")
            return True
            
    except Exception as e:
        print(f"❌ Cosmos DB failed: {e}")
        return False

def test_local_knowledge():
    """Test local knowledge base."""
    print("\n📚 Testing Local Knowledge Base...")
    print("=" * 50)
    
    try:
        about_qu_path = os.getenv("ABOUT_QU_PATH", os.path.join("kb", "about_qu.md"))
        
        if os.path.exists(about_qu_path):
            with open(about_qu_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if content:
                print(f"✅ Local knowledge base loaded! ({len(content)} characters)")
                print(f"   File: {about_qu_path}")
                return True
            else:
                print(f"❌ Local knowledge base file is empty: {about_qu_path}")
                return False
        else:
            print(f"❌ Local knowledge base file not found: {about_qu_path}")
            return False
            
    except Exception as e:
        print(f"❌ Local knowledge base failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Qatar University Chatbot - Azure Services Test")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Azure OpenAI", test_azure_openai),
        ("Azure Search", test_azure_search),
        ("Cosmos DB", test_cosmos_db),
        ("Local Knowledge", test_local_knowledge),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your configuration looks good.")
        return 0
    else:
        print("⚠️ Some tests failed. Please fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
