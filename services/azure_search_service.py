"""
Azure AI Search service for Qatar University Chatbot
Handles semantic search and retrieval augmented generation (RAG)
"""

import json
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import config

class AzureSearchService:
    def __init__(self):
        self.search_client = SearchClient(
            endpoint=config.SEARCH_ENDPOINT,
            index_name=config.SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(config.SEARCH_API_KEY)
        )
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Ensure the search index exists and is properly configured"""
        try:
            # Try to get index info to check if it exists
            self.search_client.get_search_index()
        except Exception:
            # Index doesn't exist, create it
            self._create_search_index()

    def _create_search_index(self):
        """Create the search index with optimal configuration for Qatar University documents"""
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            SearchIndex, SimpleField, SearchableField, VectorSearch,
            VectorSearchProfile, HnswAlgorithmConfiguration
        )
        
        index_client = SearchIndexClient(
            endpoint=config.SEARCH_ENDPOINT,
            credential=AzureKeyCredential(config.SEARCH_API_KEY)
        )
        
        # Define fields optimized for university documents
        fields = [
            SimpleField(name="id", type="Edm.String", key=True),
            SimpleField(name="document_id", type="Edm.String", filterable=True),
            SearchableField(name="title", type="Edm.String", analyzer="en.microsoft"),
            SearchableField(name="content", type="Edm.String", analyzer="en.microsoft"),
            SimpleField(name="document_type", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="source_file", type="Edm.String"),
            SimpleField(name="created_at", type="Edm.DateTimeOffset"),
            SimpleField(name="chunk_index", type="Edm.Int32"),
            SimpleField(name="metadata", type="Edm.String")
        ]
        
        # Vector search configuration for semantic search
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="my-vector-config",
                    algorithm_configuration_name="my-algorithms-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="my-algorithms-config"
                )
            ]
        )
        
        search_index = SearchIndex(
            name=config.SEARCH_INDEX_NAME,
            fields=fields,
            vector_search=vector_search
        )
        
        index_client.create_index(search_index)

    def upload_document_chunks(self, document_data: Dict[str, Any]):
        """Upload document chunks to Azure AI Search"""
        chunks = document_data.get("chunks", [])
        search_documents = []
        
        for i, chunk in enumerate(chunks):
            search_doc = {
                "id": f"{document_data['id']}_chunk_{i}",
                "document_id": document_data["id"],
                "title": document_data["title"],
                "content": chunk["content"],
                "document_type": document_data.get("document_type", "university_document"),
                "source_file": document_data.get("source_file", ""),
                "created_at": document_data.get("created_at", ""),
                "chunk_index": i,
                "metadata": json.dumps(chunk.get("metadata", {}))
            }
            search_documents.append(search_doc)
        
        if search_documents:
            self.search_client.upload_documents(search_documents)

    def semantic_search(self, query: str, document_type: str = None, 
                       top: int = None) -> List[Dict[str, Any]]:
        """Perform semantic search with filters"""
        if top is None:
            top = config.MAX_SEARCH_RESULTS
            
        search_filter = None
        if document_type:
            search_filter = f"document_type eq '{document_type}'"
        
        # Semantic search with ranking
        search_results = self.search_client.search(
            search_text=query,
            filter=search_filter,
            top=top,
            include_total_count=True,
            query_type="semantic",
            query_language="en",
            semantic_configuration_name="default"
        )
        
        results = []
        for result in search_results:
            results.append({
                "id": result["id"],
                "document_id": result["document_id"],
                "title": result["title"],
                "content": result["content"],
                "document_type": result["document_type"],
                "source_file": result["source_file"],
                "chunk_index": result["chunk_index"],
                "score": result.get("@search.score", 0),
                "metadata": json.loads(result.get("metadata", "{}"))
            })
        
        return results

    def hybrid_search(self, query: str, document_type: str = None, 
                     top: int = None) -> List[Dict[str, Any]]:
        """Perform hybrid search combining keyword and semantic search"""
        if top is None:
            top = config.MAX_SEARCH_RESULTS
            
        search_filter = None
        if document_type:
            search_filter = f"document_type eq '{document_type}'"
        
        # Hybrid search combining multiple strategies
        search_results = self.search_client.search(
            search_text=query,
            filter=search_filter,
            top=top,
            include_total_count=True,
            query_type="semantic",
            semantic_configuration_name="default",
            query_caption="extractive",
            query_answer="extractive"
        )
        
        results = []
        for result in search_results:
            results.append({
                "id": result["id"],
                "document_id": result["document_id"],
                "title": result["title"],
                "content": result["content"],
                "document_type": result["document_type"],
                "source_file": result["source_file"],
                "chunk_index": result["chunk_index"],
                "score": result.get("@search.score", 0),
                "answer": result.get("@search.answers", []),
                "captions": result.get("@search.captions", []),
                "metadata": json.loads(result.get("metadata", "{}"))
            })
        
        return results

    def get_relevant_documents(self, query: str, document_type: str = None) -> List[Dict[str, Any]]:
        """Get most relevant documents for RAG context"""
        # Use hybrid search for best results
        search_results = self.hybrid_search(query, document_type)
        
        # Group by document to avoid duplicate context
        document_groups = {}
        for result in search_results:
            doc_id = result["document_id"]
            if doc_id not in document_groups:
                document_groups[doc_id] = {
                    "document_id": doc_id,
                    "title": result["title"],
                    "document_type": result["document_type"],
                    "source_file": result["source_file"],
                    "chunks": [],
                    "max_score": 0
                }
            
            document_groups[doc_id]["chunks"].append({
                "content": result["content"],
                "score": result["score"],
                "chunk_index": result["chunk_index"]
            })
            
            if result["score"] > document_groups[doc_id]["max_score"]:
                document_groups[doc_id]["max_score"] = result["score"]
        
        # Sort by max score and return top documents
        sorted_docs = sorted(
            document_groups.values(), 
            key=lambda x: x["max_score"], 
            reverse=True
        )
        
        return sorted_docs[:config.MAX_SEARCH_RESULTS]

    def delete_document(self, document_id: str):
        """Delete all chunks for a document"""
        # Find all chunks for this document
        search_results = self.search_client.search(
            search_text="*",
            filter=f"document_id eq '{document_id}'",
            select=["id"]
        )
        
        # Delete each chunk
        for result in search_results:
            self.search_client.delete_documents([{"id": result["id"]}])
