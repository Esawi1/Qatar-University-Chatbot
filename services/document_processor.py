"""
Document processing service for Qatar University Chatbot
Handles PDF processing, chunking, and metadata extraction
"""

import io
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import PyPDF2
from azure.storage.blob import BlobServiceClient
import config

class DocumentProcessor:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            config.STORAGE_CONNECTION_STRING
        )
        self.container_client = self.blob_service_client.get_container_client(
            config.STORAGE_CONTAINER_NAME
        )

    def upload_pdf_to_storage(self, file_path: str, file_content: bytes) -> str:
        """Upload PDF file to Azure Blob Storage"""
        blob_name = f"documents/{datetime.now().strftime('%Y/%m/%d')}/{file_path}"
        
        try:
            self.container_client.upload_blob(
                name=blob_name,
                data=file_content,
                overwrite=True
            )
            return blob_name
        except Exception as e:
            raise Exception(f"Failed to upload PDF: {str(e)}")

    def extract_text_from_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Extract text and metadata from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                page_texts.append({
                    "page_number": page_num + 1,
                    "text": page_text
                })
                full_text += page_text + "\n"
            
            # Extract metadata
            metadata = pdf_reader.metadata or {}
            
            # Generate content hash for deduplication
            content_hash = hashlib.md5(full_text.encode()).hexdigest()
            
            return {
                "full_text": full_text,
                "page_texts": page_texts,
                "metadata": {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "creation_date": metadata.get("/CreationDate", ""),
                    "modification_date": metadata.get("/ModDate", ""),
                    "page_count": len(pdf_reader.pages),
                    "content_hash": content_hash
                },
                "page_count": len(pdf_reader.pages)
            }
            
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks for better retrieval"""
        if chunk_size is None:
            chunk_size = config.CHUNK_SIZE
        if overlap is None:
            overlap = config.CHUNK_OVERLAP
            
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size // 2, end - 200), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                    "metadata": {
                        "chunk_size": len(chunk_text),
                        "word_count": len(chunk_text.split())
                    }
                })
                chunk_index += 1
            
            start = end - overlap
            
        return chunks

    def extract_university_specific_metadata(self, text: str) -> Dict[str, Any]:
        """Extract Qatar University specific metadata and entities"""
        metadata = {
            "document_type": "general",
            "departments": [],
            "programs": [],
            "services": [],
            "contact_info": [],
            "dates": [],
            "keywords": []
        }
        
        # Common Qatar University departments and programs
        qu_departments = [
            "College of Engineering", "College of Business and Economics",
            "College of Arts and Sciences", "College of Medicine",
            "College of Education", "College of Law",
            "College of Pharmacy", "College of Dental Medicine",
            "College of Health Sciences", "College of Islamic Studies"
        ]
        
        qu_services = [
            "Student Affairs", "Academic Affairs", "Registrar",
            "Financial Aid", "Admissions", "Career Services",
            "Library Services", "IT Services", "International Affairs"
        ]
        
        # Extract departments
        for dept in qu_departments:
            if dept.lower() in text.lower():
                metadata["departments"].append(dept)
        
        # Extract services
        for service in qu_services:
            if service.lower() in text.lower():
                metadata["services"].append(service)
        
        # Extract email addresses
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@qu\.edu\.qa\b'
        metadata["contact_info"] = re.findall(email_pattern, text)
        
        # Extract phone numbers (Qatar format)
        phone_pattern = r'\+974\s?\d{8}|\d{8}'
        metadata["contact_info"].extend(re.findall(phone_pattern, text))
        
        # Determine document type based on content
        if any(word in text.lower() for word in ["admission", "apply", "application", "requirements"]):
            metadata["document_type"] = "admissions"
        elif any(word in text.lower() for word in ["course", "curriculum", "syllabus", "academic"]):
            metadata["document_type"] = "academic"
        elif any(word in text.lower() for word in ["policy", "regulation", "rule", "procedure"]):
            metadata["document_type"] = "policy"
        elif any(word in text.lower() for word in ["service", "support", "help", "assistance"]):
            metadata["document_type"] = "service"
        
        return metadata

    def process_document(self, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """Complete document processing pipeline"""
        try:
            # Upload to blob storage
            blob_path = self.upload_pdf_to_storage(file_path, file_content)
            
            # Extract text from PDF
            pdf_data = self.extract_text_from_pdf(file_content)
            
            # Extract university-specific metadata
            university_metadata = self.extract_university_specific_metadata(pdf_data["full_text"])
            
            # Combine metadata
            combined_metadata = {
                **pdf_data["metadata"],
                **university_metadata
            }
            
            # Chunk the text
            chunks = self.chunk_text(pdf_data["full_text"])
            
            # Create document data structure
            document_data = {
                "id": hashlib.md5(file_content).hexdigest(),
                "title": pdf_data["metadata"]["title"] or file_path,
                "content": pdf_data["full_text"],
                "type": university_metadata["document_type"],
                "metadata": combined_metadata,
                "source_file": blob_path,
                "created_at": datetime.utcnow().isoformat(),
                "chunks": chunks,
                "page_count": pdf_data["page_count"],
                "processed": True
            }
            
            return document_data
            
        except Exception as e:
            raise Exception(f"Failed to process document: {str(e)}")

    def get_document_from_storage(self, blob_path: str) -> bytes:
        """Retrieve document from blob storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=config.STORAGE_CONTAINER_NAME,
                blob=blob_path
            )
            return blob_client.download_blob().readall()
        except Exception as e:
            raise Exception(f"Failed to retrieve document: {str(e)}")

    def list_documents_in_storage(self) -> List[Dict[str, Any]]:
        """List all documents in storage"""
        documents = []
        try:
            blobs = self.container_client.list_blobs(name_starts_with="documents/")
            for blob in blobs:
                documents.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type
                })
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
        
        return documents
