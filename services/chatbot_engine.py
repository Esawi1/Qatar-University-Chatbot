"""
Qatar University Chatbot Engine
Integrates all Azure services for high-accuracy responses
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from openai import AzureOpenAI
from services.cosmos_service import CosmosService
from services.azure_search_service import AzureSearchService
from services.document_processor import DocumentProcessor
import config

class QatarUniversityChatbot:
    def __init__(self):
        # Initialize services first (these are more reliable)
        self.cosmos_service = CosmosService()
        self.search_service = AzureSearchService()
        self.document_processor = DocumentProcessor()
        
        # Initialize Azure OpenAI client (lazy initialization)
        self.openai_client = None
        
        # Cache for frequently accessed information
        self._response_cache = {}
        self._context_cache = {}
    
    def _get_openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self.openai_client is None:
            self.openai_client = AzureOpenAI(
                api_key=config.AZURE_OPENAI_API_KEY,
                api_version=config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT
            )
        return self.openai_client

    def process_and_store_document(self, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """Process PDF document and store in all services"""
        try:
            # Process document
            document_data = self.document_processor.process_document(file_path, file_content)
            
            # Store in Cosmos DB
            document_id = self.cosmos_service.store_document(document_data)
            document_data["id"] = document_id
            
            # Upload chunks to Azure AI Search
            self.search_service.upload_document_chunks(document_data)
            
            return {
                "success": True,
                "document_id": document_id,
                "title": document_data["title"],
                "type": document_data["type"],
                "chunks_created": len(document_data["chunks"]),
                "message": f"Document '{document_data['title']}' processed and stored successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process document: {str(e)}"
            }

    def _build_context_from_documents(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results for RAG"""
        if not search_results:
            return "No relevant documents found in the knowledge base."
        
        context_parts = []
        for i, doc in enumerate(search_results[:3], 1):  # Limit to top 3 documents
            context_parts.append(f"Document {i}: {doc['title']}")
            context_parts.append(f"Type: {doc['document_type']}")
            context_parts.append(f"Content: {doc['chunks'][0]['content'][:500]}...")
            context_parts.append("---")
        
        return "\n".join(context_parts)

    def _build_conversation_context(self, session_id: str) -> str:
        """Build conversation history context"""
        history = self.cosmos_service.get_conversation_history(
            session_id, config.MAX_CONVERSATION_HISTORY
        )
        
        if not history:
            return ""
        
        context_parts = ["Previous conversation:"]
        for turn in history:
            context_parts.append(f"User: {turn['user_message']}")
            context_parts.append(f"Assistant: {turn['bot_response']}")
        
        return "\n".join(context_parts)

    def _enhance_query(self, user_query: str, document_type: str = None) -> str:
        """Enhance user query for better search results"""
        # Add Qatar University context to the query
        enhanced_query = f"Qatar University {user_query}"
        
        if document_type:
            enhanced_query += f" {document_type} document"
        
        return enhanced_query

    def generate_response(self, user_message: str, session_id: str = None, 
                         document_type: str = None) -> Dict[str, Any]:
        """Generate chatbot response using RAG pipeline"""
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Check cache first for cost optimization
            cache_key = f"{user_message}_{document_type}"
            if cache_key in self._response_cache:
                cached_response = self._response_cache[cache_key]
                cached_response["cached"] = True
                return cached_response
            
            # Enhance query for better search
            enhanced_query = self._enhance_query(user_message, document_type)
            
            # Retrieve relevant documents using hybrid search
            search_results = self.search_service.get_relevant_documents(
                enhanced_query, document_type
            )
            
            # Build context from documents
            document_context = self._build_context_from_documents(search_results)
            
            # Build conversation context
            conversation_context = self._build_conversation_context(session_id)
            
            # Create system message with context
            system_message = config.CHATBOT_SYSTEM_PROMPT
            if document_context and document_context != "No relevant documents found in the knowledge base.":
                system_message += f"\n\nRelevant Qatar University Information:\n{document_context}"
            
            if conversation_context:
                system_message += f"\n\n{conversation_context}"
            
            # Generate response using Azure OpenAI
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            response = self._get_openai_client().chat.completions.create(
                model=config.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=config.TEMPERATURE,
                max_tokens=1000,
                top_p=0.9
            )
            
            bot_response = response.choices[0].message.content
            
            # Store conversation in Cosmos DB
            context_documents = [doc["document_id"] for doc in search_results]
            self.cosmos_service.store_conversation(
                session_id, user_message, bot_response, context_documents
            )
            
            # Cache the response
            response_data = {
                "success": True,
                "response": bot_response,
                "session_id": session_id,
                "context_documents": len(search_results),
                "document_sources": [
                    {
                        "title": doc["title"],
                        "type": doc["document_type"],
                        "relevance_score": doc["max_score"]
                    }
                    for doc in search_results[:3]
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False
            }
            
            self._response_cache[cache_key] = response_data
            
            return response_data
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate response: {str(e)}",
                "session_id": session_id
            }

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return self.cosmos_service.get_conversation_history(session_id)

    def search_documents(self, query: str, document_type: str = None) -> List[Dict[str, Any]]:
        """Search documents directly"""
        enhanced_query = self._enhance_query(query, document_type)
        return self.search_service.get_relevant_documents(enhanced_query, document_type)

    def get_document_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored documents"""
        return self.cosmos_service.get_document_statistics()

    def clear_conversation_cache(self):
        """Clear response cache to free memory"""
        self._response_cache.clear()

    def get_suggested_questions(self, document_type: str = None) -> List[str]:
        """Get suggested questions based on available documents"""
        suggestions = [
            "What are the admission requirements for Qatar University?",
            "How can I apply for financial aid?",
            "What academic programs are available?",
            "How do I register for courses?",
            "What are the university policies on academic integrity?",
            "How can I access library resources?",
            "What student services are available?",
            "How do I contact academic advisors?",
            "What are the graduation requirements?",
            "How can I get help with my studies?"
        ]
        
        if document_type == "admissions":
            return [
                "What are the admission requirements?",
                "How do I apply for admission?",
                "What documents do I need to submit?",
                "When are the application deadlines?",
                "How much does it cost to apply?"
            ]
        elif document_type == "academic":
            return [
                "What courses are required for my program?",
                "How do I register for classes?",
                "What are the graduation requirements?",
                "How can I change my major?",
                "What is the academic calendar?"
            ]
        elif document_type == "service":
            return [
                "What student services are available?",
                "How can I get academic support?",
                "Where can I find career guidance?",
                "How do I access IT services?",
                "What health services are available?"
            ]
        
        return suggestions[:5]  # Return top 5 suggestions
