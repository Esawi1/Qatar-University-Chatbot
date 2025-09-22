"""
Qatar University Chatbot - Streamlit Web Interface
High-performance chatbot with RAG capabilities
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from chatbot_engine import QatarUniversityChatbot
import config

# Page configuration
st.set_page_config(
    page_title="Qatar University AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #8B0000, #DC143C);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #8B0000;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #8B0000;
    }
    .bot-message {
        background-color: #e8f4f8;
        border-left-color: #DC143C;
    }
    .document-source {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        border-left: 3px solid #8B0000;
    }
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    .stat-item {
        text-align: center;
        padding: 0.5rem;
        background-color: #e8f4f8;
        border-radius: 5px;
        margin: 0 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = QatarUniversityChatbot()

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'document_uploaded' not in st.session_state:
    st.session_state.document_uploaded = False

def display_chat_message(message: str, is_user: bool = True, sources: list = None):
    """Display a chat message with proper styling"""
    message_class = "user-message" if is_user else "bot-message"
    
    st.markdown(f"""
    <div class="chat-message {message_class}">
        <strong>{'You' if is_user else 'Qatar University Assistant'}</strong><br>
        {message}
    </div>
    """, unsafe_allow_html=True)
    
    # Display sources if provided
    if sources and not is_user:
        st.markdown("**Sources:**")
        for source in sources:
            st.markdown(f"""
            <div class="document-source">
                📄 {source['title']} ({source['type']})
                <br><small>Relevance: {source['relevance_score']:.2f}</small>
            </div>
            """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Qatar University AI Assistant</h1>
        <p>Your intelligent guide to Qatar University information and services</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📚 Document Management")
        
        # Document upload
        uploaded_file = st.file_uploader(
            "Upload Qatar University Document (PDF)",
            type=['pdf'],
            help="Upload PDF documents to expand the knowledge base"
        )
        
        if uploaded_file is not None:
            if st.button("Process Document"):
                with st.spinner("Processing document..."):
                    file_content = uploaded_file.read()
                    result = st.session_state.chatbot.process_and_store_document(
                        uploaded_file.name, file_content
                    )
                    
                    if result["success"]:
                        st.success(result["message"])
                        st.session_state.document_uploaded = True
                    else:
                        st.error(result["message"])
        
        # Document statistics
        st.markdown("## 📊 Knowledge Base Statistics")
        try:
            stats = st.session_state.chatbot.get_document_statistics()
            st.markdown(f"""
            <div class="stats-container">
                <div class="stat-item">
                    <strong>{stats['total_documents']}</strong><br>
                    Total Documents
                </div>
                <div class="stat-item">
                    <strong>{stats['academic_documents']}</strong><br>
                    Academic
                </div>
                <div class="stat-item">
                    <strong>{stats['administrative_documents']}</strong><br>
                    Administrative
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.warning("Unable to load statistics")
        
        # Document type filter
        st.markdown("## 🔍 Search Options")
        document_type = st.selectbox(
            "Filter by Document Type",
            ["All", "admissions", "academic", "policy", "service", "general"],
            help="Filter responses to specific document types"
        )
        
        # Suggested questions
        st.markdown("## 💡 Suggested Questions")
        suggestions = st.session_state.chatbot.get_suggested_questions(
            document_type if document_type != "All" else None
        )
        
        for suggestion in suggestions:
            if st.button(suggestion, key=f"suggest_{suggestion}"):
                st.session_state.user_input = suggestion
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.conversation_history = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("## 💬 Chat with Qatar University Assistant")
        
        # Display conversation history
        for message in st.session_state.conversation_history:
            display_chat_message(
                message["content"], 
                message["is_user"],
                message.get("sources", [])
            )
        
        # Chat input
        user_input = st.text_input(
            "Ask me anything about Qatar University...",
            key="user_input",
            placeholder="e.g., What are the admission requirements? How do I apply for financial aid?"
        )
        
        col_send, col_clear = st.columns([1, 1])
        
        with col_send:
            if st.button("Send", type="primary"):
                if user_input:
                    # Add user message to history
                    st.session_state.conversation_history.append({
                        "content": user_input,
                        "is_user": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Generate response
                    with st.spinner("Thinking..."):
                        response = st.session_state.chatbot.generate_response(
                            user_input, 
                            st.session_state.session_id,
                            document_type if document_type != "All" else None
                        )
                    
                    if response["success"]:
                        # Add bot response to history
                        st.session_state.conversation_history.append({
                            "content": response["response"],
                            "is_user": False,
                            "sources": response.get("document_sources", []),
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Clear input
                        st.session_state.user_input = ""
                        st.rerun()
                    else:
                        st.error(f"Error: {response['message']}")
        
        with col_clear:
            if st.button("Clear Input"):
                st.session_state.user_input = ""
                st.rerun()
    
    with col2:
        st.markdown("## 🎯 Quick Actions")
        
        # Quick search
        search_query = st.text_input(
            "Quick Document Search",
            placeholder="Search documents..."
        )
        
        if st.button("Search Documents"):
            if search_query:
                with st.spinner("Searching..."):
                    results = st.session_state.chatbot.search_documents(
                        search_query,
                        document_type if document_type != "All" else None
                    )
                
                if results:
                    st.markdown("### Search Results:")
                    for result in results[:3]:
                        st.markdown(f"""
                        **{result['title']}** ({result['document_type']})
                        <br><small>{result['chunks'][0]['content'][:100]}...</small>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No documents found matching your search.")
        
        # Session info
        st.markdown("## 📋 Session Info")
        st.info(f"Session ID: `{st.session_state.session_id[:8]}...`")
        st.info(f"Messages: {len(st.session_state.conversation_history)}")
        
        if st.session_state.conversation_history:
            last_message = st.session_state.conversation_history[-1]
            st.info(f"Last: {last_message['timestamp'][:19]}")

if __name__ == "__main__":
    main()
