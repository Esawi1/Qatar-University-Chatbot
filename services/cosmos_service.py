"""
Cosmos DB service for Qatar University Chatbot
Handles document storage, conversation history, and metadata management
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import config

class CosmosService:
    def __init__(self):
        self.client = CosmosClient(config.COSMOS_ENDPOINT, config.COSMOS_KEY)
        self.database = self._get_or_create_database()
        self.documents_container = self._get_or_create_container(
            config.COSMOS_CONTAINER_DOCUMENTS, "/document_type"
        )
        self.conversations_container = self._get_or_create_container(
            config.COSMOS_CONTAINER_CONVERSATIONS, "/session_id"
        )

    def _get_or_create_database(self):
        try:
            return self.client.get_database_client(config.COSMOS_DATABASE_NAME)
        except CosmosResourceNotFoundError:
            return self.client.create_database(config.COSMOS_DATABASE_NAME)

    def _get_or_create_container(self, container_name: str, partition_key: str):
        try:
            return self.database.get_container_client(container_name)
        except CosmosResourceNotFoundError:
            return self.database.create_container(
                id=container_name,
                partition_key=PartitionKey(path=partition_key),
                offer_throughput=400  # Minimum for cost efficiency
            )

    def store_document(self, document_data: Dict[str, Any]) -> str:
        """Store processed document in Cosmos DB"""
        document_id = str(uuid.uuid4())
        document = {
            "id": document_id,
            "document_type": document_data.get("type", "university_document"),
            "title": document_data.get("title", ""),
            "content": document_data.get("content", ""),
            "metadata": document_data.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat(),
            "source_file": document_data.get("source_file", ""),
            "chunks": document_data.get("chunks", []),
            "processed": True
        }
        
        self.documents_container.create_item(document)
        return document_id

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document by ID"""
        try:
            return self.documents_container.read_item(document_id, document_id)
        except CosmosResourceNotFoundError:
            return None

    def search_documents(self, query: str, document_type: str = None) -> List[Dict[str, Any]]:
        """Search documents using Cosmos DB SQL queries"""
        where_clause = "CONTAINS(LOWER(c.content), LOWER(@query))"
        if document_type:
            where_clause += " AND c.document_type = @document_type"
        
        query_text = f"""
        SELECT c.id, c.title, c.content, c.metadata, c.created_at
        FROM c
        WHERE {where_clause}
        ORDER BY c.created_at DESC
        """
        
        parameters = [{"name": "@query", "value": query}]
        if document_type:
            parameters.append({"name": "@document_type", "value": document_type})
        
        items = list(self.documents_container.query_items(
            query=query_text,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items

    def store_conversation(self, session_id: str, user_message: str, bot_response: str, 
                          context_documents: List[str] = None) -> str:
        """Store conversation turn in Cosmos DB - either update existing session or create new"""
        timestamp = datetime.utcnow().isoformat()
        
        # First, try to get existing session document
        try:
            query_text = """
            SELECT * FROM c 
            WHERE c.session_id = @session_id AND c.document_type = 'session'
            """
            existing_sessions = list(self.conversations_container.query_items(
                query=query_text,
                parameters=[{"name": "@session_id", "value": session_id}],
                enable_cross_partition_query=True
            ))
            
            if existing_sessions:
                # Update existing session
                session_doc = existing_sessions[0]
                session_doc["conversation_history"].append({
                    "user_message": user_message,
                    "bot_response": bot_response,
                    "timestamp": timestamp
                })
                session_doc["last_updated"] = timestamp
                session_doc["message_count"] = len(session_doc["conversation_history"])
                
                self.conversations_container.replace_item(session_doc, session_doc)
                return session_doc["id"]
            else:
                # Create new session document
                session_id_doc = str(uuid.uuid4())
                session_doc = {
                    "id": session_id_doc,
                    "session_id": session_id,
                    "document_type": "session",
                    "conversation_history": [{
                        "user_message": user_message,
                        "bot_response": bot_response,
                        "timestamp": timestamp
                    }],
                    "created_at": timestamp,
                    "last_updated": timestamp,
                    "message_count": 1,
                    "ttl": 86400 * 30  # 30 days TTL for cost efficiency
                }
                
                self.conversations_container.create_item(session_doc)
                return session_id_doc
                
        except Exception as e:
            # Fallback to old method if there's an error
            conversation_id = str(uuid.uuid4())
            conversation = {
                "id": conversation_id,
                "session_id": session_id,
                "user_message": user_message,
                "bot_response": bot_response,
                "context_documents": context_documents or [],
                "timestamp": timestamp,
                "ttl": 86400 * 30
            }
            
            self.conversations_container.create_item(conversation)
            return conversation_id

    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve conversation history for context"""
        try:
            # First try to get the session document
            query_text = """
            SELECT * FROM c 
            WHERE c.session_id = @session_id AND c.document_type = 'session'
            """
            session_docs = list(self.conversations_container.query_items(
                query=query_text,
                parameters=[{"name": "@session_id", "value": session_id}],
                enable_cross_partition_query=True
            ))
            
            if session_docs:
                # Return conversation history from session document
                session_doc = session_docs[0]
                conversation_history = session_doc.get("conversation_history", [])
                # Limit the results if needed
                if limit > 0:
                    conversation_history = conversation_history[-limit:]
                return conversation_history
            else:
                # Fallback to old method for backward compatibility
                query_text = """
                SELECT TOP @limit c.user_message, c.bot_response, c.timestamp
                FROM c
                WHERE c.session_id = @session_id
                ORDER BY c.timestamp DESC
                """
                
                items = list(self.conversations_container.query_items(
                    query=query_text,
                    parameters=[
                        {"name": "@session_id", "value": session_id},
                        {"name": "@limit", "value": limit}
                    ],
                    enable_cross_partition_query=True
                ))
                
                # Reverse to get chronological order
                return list(reversed(items))
                
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    def get_document_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored documents"""
        query = "SELECT VALUE COUNT(1) FROM c"
        total_docs = list(self.documents_container.query_items(query, enable_cross_partition_query=True))[0]
        
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.document_type = 'academic'"
        academic_docs = list(self.documents_container.query_items(query, enable_cross_partition_query=True))[0]
        
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.document_type = 'administrative'"
        admin_docs = list(self.documents_container.query_items(query, enable_cross_partition_query=True))[0]
        
        return {
            "total_documents": total_docs,
            "academic_documents": academic_docs,
            "administrative_documents": admin_docs,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about conversation sessions"""
        try:
            # Count session documents
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.document_type = 'session'"
            session_count = list(self.conversations_container.query_items(query, enable_cross_partition_query=True))[0]
            
            # Count individual conversation turns (legacy)
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.document_type != 'session' OR NOT IS_DEFINED(c.document_type)"
            turn_count = list(self.conversations_container.query_items(query, enable_cross_partition_query=True))[0]
            
            return {
                "total_sessions": session_count,
                "total_conversation_turns": turn_count,
                "container_name": self.conversations_container.id
            }
        except Exception as e:
            return {
                "error": str(e),
                "container_name": self.conversations_container.id
            }
