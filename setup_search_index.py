#!/usr/bin/env python3
"""
Script to set up Azure Search index for Qatar University chatbot
"""

import os
import json
import requests
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=True)

def create_search_index():
    """Create the search index."""
    
    # Get search service details
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "qu-documents")
    
    if not search_endpoint or not search_key:
        print("❌ Missing Azure Search environment variables!")
        print("Please set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY")
        return False
    
    # Load index configuration
    with open("search_index_config.json", "r") as f:
        index_config = json.load(f)
    
    # Create index
    url = f"{search_endpoint}/indexes/{index_name}?api-version=2023-11-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": search_key
    }
    
    try:
        response = requests.put(url, headers=headers, json=index_config)
        if response.status_code in [200, 201]:
            print(f"✅ Search index '{index_name}' created successfully!")
            return True
        else:
            print(f"❌ Failed to create index: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return False

def upload_sample_documents():
    """Upload sample documents to the search index."""
    
    # Get search service details
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "qu-documents")
    
    # Load sample documents
    with open("sample_documents.json", "r") as f:
        documents = json.load(f)
    
    # Upload documents
    url = f"{search_endpoint}/indexes/{index_name}/docs/index?api-version=2023-11-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": search_key
    }
    
    payload = {"value": documents}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"✅ Uploaded {len(documents)} sample documents successfully!")
            return True
        else:
            print(f"❌ Failed to upload documents: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error uploading documents: {e}")
        return False

def test_search():
    """Test the search functionality."""
    
    # Get search service details
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "qu-documents")
    
    # Test search query
    url = f"{search_endpoint}/indexes/{index_name}/docs/search?api-version=2023-11-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": search_key
    }
    
    query = {
        "search": "admission requirements",
        "top": 3,
        "select": "title,content,category"
    }
    
    try:
        response = requests.post(url, headers=headers, json=query)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Search test successful! Found {len(results.get('value', []))} results")
            for result in results.get('value', [])[:2]:
                print(f"   - {result.get('title', 'No title')}: {result.get('content', '')[:100]}...")
            return True
        else:
            print(f"❌ Search test failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Azure Search for Qatar University Chatbot")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv("AZURE_SEARCH_ENDPOINT") or not os.getenv("AZURE_SEARCH_KEY"):
        print("❌ Please set the following environment variables:")
        print("   AZURE_SEARCH_ENDPOINT=https://srch-ai-rd-sc.search.windows.net")
        print("   AZURE_SEARCH_KEY=your-primary-admin-key")
        print("   AZURE_SEARCH_INDEX=qu-documents")
        return False
    
    # Create index
    if not create_search_index():
        return False
    
    # Upload sample documents
    if not upload_sample_documents():
        return False
    
    # Test search
    if not test_search():
        return False
    
    print("\n🎉 Azure Search setup completed successfully!")
    print("Your chatbot can now search through Qatar University documents!")
    return True

if __name__ == "__main__":
    main()
