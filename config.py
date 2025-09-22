"""
Configuration file for Qatar University Chatbot
Optimized for existing Azure resources without additional costs
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Azure Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://oai-ai-rd-sc.openai.azure.com")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

# Cosmos DB Configuration
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://cosno-ai-rd-sc.documents.azure.com:443")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE_NAME = os.getenv("COSMOS_DB", "chatbot-qu-2")
COSMOS_CONTAINER_DOCUMENTS = os.getenv("COSMOS_CONTAINER", "123")
COSMOS_CONTAINER_CONVERSATIONS = os.getenv("COSMOS_CONTAINER", "123")
COSMOS_PARTITION_KEY = os.getenv("COSMOS_PARTITION_KEY", "/sessionId")

# Azure AI Search Configuration
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT", "https://srch-ai-rd-sc.search.windows.net")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX", "qu-docss")

# Storage Account Configuration
STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
STORAGE_CONTAINER_NAME = "university-documents"
SEARCH_SEMANTIC_CONFIG = os.getenv("SEARCH_SEMANTIC_CONFIG", "default")

# Chatbot Configuration
CHATBOT_SYSTEM_PROMPT = """
You are an intelligent assistant for Qatar University students, faculty, and staff. 
Your primary role is to provide accurate, helpful, and contextually relevant information 
about Qatar University based on the uploaded documents and knowledge base.

Key guidelines:
1. Always prioritize information from the Qatar University documents and knowledge base
2. Maintain a professional, helpful, and culturally sensitive tone
3. Provide specific, actionable answers rather than generic responses
4. If you cannot find information in the knowledge base, clearly state this limitation
5. Focus on academic, administrative, and student life topics relevant to Qatar University
6. Respect Qatari culture and Islamic values in all interactions

When answering questions:
- Cite specific documents or sections when possible
- Provide step-by-step guidance for procedures
- Include relevant contact information or departments when available
- Offer to help with follow-up questions
"""

# RAG Configuration
MAX_SEARCH_RESULTS = 5
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TEMPERATURE = 0.1  # Lower temperature for more consistent, factual responses

# Performance Optimization
CACHE_TTL_SECONDS = 3600  # 1 hour cache for frequently accessed documents
MAX_CONVERSATION_HISTORY = 10  # Limit conversation history for context management
