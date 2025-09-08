# Qatar University Chatbot

A comprehensive AI-powered chatbot for Qatar University admissions and general information, built with modern cloud technologies and advanced AI orchestration.

## 🚀 Features

### Core Functionality
- **Intelligent Query Routing**: Automatically routes queries to ADMISSIONS, ABOUT_QU, or CHITCHAT modes based on content analysis
- **Multi-Source Knowledge**: Combines Azure Search (PDF documents) with local knowledge base for comprehensive answers
- **Conversation-Aware AI**: Maintains full conversation context for consistent and relevant responses
- **Session Management**: Persistent multi-session support with individual conversation histories
- **Real-time Chat Interface**: Modern, responsive web UI with session controls

### Advanced AI Capabilities
- **Azure OpenAI Integration**: GPT-4/GPT-3.5-turbo powered responses with conversation awareness
- **Semantic Kernel Framework**: Advanced AI orchestration and prompt management
- **Context-Aware Responses**: Uses conversation history to provide consistent and relevant answers
- **Source Attribution**: Provides citations and source references for all information

### Data Management
- **Azure Cognitive Search**: Full-text search through indexed PDF documents with highlighting
- **Azure Cosmos DB**: Scalable NoSQL storage for conversation persistence
- **Simplified Message Structure**: Clean, efficient data storage (role + content only)
- **Automatic History Management**: Smart conversation trimming and session management

### User Experience
- **Modern Web Interface**: Clean, responsive chat UI built with Tailwind CSS
- **Session Controls**: Create new sessions, clear history, view statistics
- **Real-time Updates**: Live session information and conversation statistics
- **Mobile Responsive**: Optimized for all device sizes

## 🏗️ Project Architecture

### Technology Stack
- **Backend Framework**: FastAPI (Python 3.8+)
- **AI Services**: Azure OpenAI (GPT-4/GPT-3.5-turbo)
- **Search Engine**: Azure Cognitive Search
- **Database**: Azure Cosmos DB (NoSQL)
- **AI Orchestration**: Microsoft Semantic Kernel
- **Frontend**: HTML5 + Tailwind CSS + Vanilla JavaScript
- **Server**: Uvicorn ASGI server

### Project Structure
```
QU_Chatbot/
├── main.py                    # 🚀 FastAPI application with chat endpoints and routing logic
├── search_client.py           # 🔍 Azure Cognitive Search integration
├── db_service.py             # 💾 Azure Cosmos DB operations and session management
├── chat_history_manager.py   # 📚 Advanced conversation history with Semantic Kernel
├── ai.py                     # 🤖 Standalone AI query handler (alternative approach)
├── start.py                  # ⚡ Startup script with environment validation
├── requirements.txt          # 📦 Python dependencies
├── .env                      # 🔐 Environment variables (create from template)
├── .gitignore               # 🚫 Git ignore file for security and cleanliness
├── web/
│   └── index.html           # 🎨 Modern chat UI with session management
├── kb/
│   └── about_qu.md          # 📖 Local knowledge base about Qatar University
└── README.md                # 📋 This comprehensive documentation
```

### Core Components

#### 1. **main.py** - FastAPI Application
- **Chat Endpoints**: `/chat`, `/search`, session management
- **Intelligent Routing**: ADMISSIONS, ABOUT_QU, CHITCHAT modes
- **Conversation Management**: Session-based chat history
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Error Handling**: Comprehensive error management and logging

#### 2. **search_client.py** - Azure Search Integration
- **Full-Text Search**: Advanced search through indexed PDF documents
- **Result Highlighting**: Search term highlighting in results
- **Flexible Queries**: Support for various search patterns
- **Error Resilience**: Graceful fallback when search fails

#### 3. **db_service.py** - Cosmos DB Operations
- **Session Management**: Create, read, update session documents
- **Message Storage**: Simplified message structure (role + content)
- **History Management**: Automatic conversation trimming
- **Scalable Design**: Partition-based storage for performance

#### 4. **chat_history_manager.py** - Conversation Management
- **Semantic Kernel Integration**: Advanced AI orchestration
- **Multi-Session Support**: Individual conversation histories
- **History Reduction**: Automatic conversation trimming
- **Fallback Support**: Works with or without Semantic Kernel

#### 5. **web/index.html** - Modern Chat Interface
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Session Controls**: New session, clear history, view stats
- **Real-time Updates**: Live session information
- **User-Friendly**: Intuitive chat experience

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 1GB free space for dependencies

### Azure Services Required
- **Azure OpenAI Service**: GPT-4 or GPT-3.5-turbo deployment
- **Azure Cognitive Search**: Search service with indexed PDF documents
- **Azure Cosmos DB**: NoSQL database for conversation storage
- **Azure Subscription**: Active Azure subscription with billing enabled

### Development Tools (Optional)
- **Git**: For version control
- **VS Code**: Recommended IDE with Python extension
- **Postman**: For API testing

## 🛠️ Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd QU_Chatbot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Quick Start (Using start.py)

The easiest way to get started is using the included startup script:

```bash
python start.py
```

This script will:
- ✅ Check all required environment variables
- ✅ Validate Azure service connections
- ✅ Start the FastAPI server on port 8010
- ✅ Provide helpful startup information

### 3. Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
# 🔐 Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-api-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-06-01

# 🔍 Azure Cognitive Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX=your-search-index-name
AZURE_SEARCH_KEY=your-search-api-key

# 💾 Azure Cosmos DB Configuration
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443
COSMOS_KEY=your-cosmos-primary-key
COSMOS_DB=qu_chat
COSMOS_CONTAINER=conversations

# ⚙️ Chat Configuration (Optional)
HISTORY_PAIRS=3
SNIPPET_CHARS=300
CONTEXT_MAX_CHARS=1000
AOAI_MAX_TOKENS=256
MAX_HISTORY_PAIRS=50
```

> **⚠️ Security Note**: Never commit your `.env` file to version control. It contains sensitive API keys and credentials.

### 4. Azure Services Setup

#### 🤖 Azure OpenAI Service
1. **Create Resource**: Go to Azure Portal → Create Resource → Azure OpenAI
2. **Deploy Model**: Deploy GPT-4 or GPT-3.5-turbo model
3. **Get Credentials**: Note the endpoint, API key, and deployment name
4. **Configure Access**: Ensure your Azure subscription has access to Azure OpenAI

#### 🔍 Azure Cognitive Search
1. **Create Service**: Create a new Azure Cognitive Search service
2. **Create Index**: Set up an index with these fields:
   - `content` (text, searchable, retrievable)
   - `metadata_storage_name` (text, retrievable)
   - `metadata_storage_path` (text, retrievable)
3. **Upload Documents**: Index your PDF documents using Azure Search indexers
4. **Get Credentials**: Note the endpoint, index name, and API key

#### 💾 Azure Cosmos DB
1. **Create Account**: Create a new Azure Cosmos DB account
2. **Create Database**: Create a database named `qu_chat`
3. **Create Container**: Create a container named `conversations` with:
   - Partition key: `/sessionId`
   - Throughput: 400 RU/s (minimum)
4. **Get Credentials**: Note the endpoint and primary key

### 5. Run the Application

#### Option A: Using the Startup Script (Recommended)
```bash
python start.py
```

#### Option B: Manual Start
```bash
# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8010
```

### 6. Access the Application

Once the server is running, you can access:

- **🎨 Chat Interface**: http://localhost:8010/chat-ui
- **📚 API Documentation**: http://localhost:8010/docs
- **🔍 Health Check**: http://localhost:8010/
- **🧪 Test Azure OpenAI**: http://localhost:8010/test-aoai
- **🔧 Debug Environment**: http://localhost:8010/debug-env

## 🔌 API Endpoints

### 💬 Chat Endpoints
- `POST /chat` - Send a message and get an AI response
- `GET /chat/history/stats` - Get chat history statistics
- `POST /chat/history/clear` - Clear chat history for a session
- `GET /chat/history/recent` - Get recent chat history

### 🔍 Search Endpoints
- `POST /search` - Search through indexed PDF documents

### 📊 Session Management
- `POST /session/new` - Create a new chat session
- `GET /session/{session_id}/info` - Get session information
- `GET /sessions/list` - List all active sessions

### 🛠️ Utility Endpoints
- `GET /` - Health check and system status
- `GET /test-aoai` - Test Azure OpenAI connection
- `GET /debug-env` - Debug environment variables

## 🚨 Troubleshooting

### Common Issues

#### 1. **Environment Variables**
- **Problem**: Missing or incorrect environment variables
- **Solution**: 
  - Verify all required variables are set in `.env`
  - Use `/debug-env` endpoint to check configuration
  - Ensure no typos in variable names

#### 2. **Azure Service Connections**
- **Problem**: Cannot connect to Azure services
- **Solution**:
  - Verify endpoints and API keys are correct
  - Check Azure service status in Azure Portal
  - Ensure your IP is not blocked by firewall rules
  - Test individual services using `/test-aoai` endpoint

#### 3. **Semantic Kernel Issues**
- **Problem**: Import errors or version conflicts
- **Solution**:
  - Reinstall: `pip install semantic-kernel==1.35.3`
  - Clear Python cache: `rm -rf __pycache__/`
  - Check Python version compatibility

#### 4. **Database Connection Issues**
- **Problem**: Cosmos DB connection failures
- **Solution**:
  - Verify database and container exist
  - Check partition key is set to `/sessionId`
  - Ensure sufficient RU/s allocation
  - Verify network connectivity

### Error Messages & Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Chat history manager not available" | Cosmos DB connection issue | Check database credentials and connectivity |
| "SK routing failed" | Semantic Kernel or Azure OpenAI issue | Verify Azure OpenAI configuration |
| "Search failed" | Azure Search connection issue | Check search service credentials |
| "Environment variable not found" | Missing .env configuration | Add missing variables to .env file |
| "Module not found" | Missing dependencies | Run `pip install -r requirements.txt` |

## 🛠️ Development

### Key Dependencies

The project uses these main Python packages:

```python
# Core Framework
fastapi==0.116.1          # Web framework
uvicorn==0.35.0           # ASGI server

# Azure Services
azure-cosmos==4.5.1       # Cosmos DB client
azure-search-documents==11.5.3  # Search client
openai>=1.98.0            # Azure OpenAI client

# AI Orchestration
semantic-kernel==1.35.3   # Microsoft Semantic Kernel

# Utilities
python-dotenv==1.1.1      # Environment management
pydantic==2.5.3           # Data validation
```

### Development Workflow

#### 1. **Testing the Application**
```bash
# Test individual components
python -c "from search_client import run_search; print(run_search('test'))"
python -c "from db_service import get_session_info; print(get_session_info('test'))"

# Test chat history functionality
python -c "from chat_history_manager import QUChatHistoryManager; print('OK')"
```

#### 2. **Adding New Knowledge**
- **PDF Documents**: Upload to Azure Search index
- **Local Knowledge**: Update `kb/about_qu.md`
- **Restart**: Restart the application to load changes

#### 3. **Customizing Responses**
- **Prompts**: Modify system prompts in `main.py` (lines 85-130)
- **Routing**: Adjust query routing logic in chat endpoint
- **UI**: Update the web interface in `web/index.html`

#### 4. **Database Schema**
The simplified message structure stores:
```json
{
  "role": "user|assistant|system",
  "content": "message content"
}
```

### Performance Optimization

- **History Management**: Adjust `MAX_HISTORY_PAIRS` for memory usage
- **Search Results**: Configure `SNIPPET_CHARS` for response quality
- **Token Limits**: Set `AOAI_MAX_TOKENS` for response length
- **Caching**: Consider implementing response caching for common queries

## 🔒 Security Considerations

### Best Practices
- **Environment Variables**: Never commit `.env` files to version control
- **API Keys**: Keep Azure service keys secure and rotate regularly
- **Network Security**: Use HTTPS in production environments
- **Access Control**: Implement authentication for production deployments
- **Data Privacy**: Ensure compliance with data protection regulations

### Production Deployment
- **Authentication**: Add user authentication and authorization
- **Rate Limiting**: Implement API rate limiting
- **Monitoring**: Set up Azure monitoring and alerting
- **Backup**: Regular backup of Cosmos DB data
- **SSL/TLS**: Use secure connections for all communications

## 📈 Performance & Monitoring

### Optimization Tips
- **Memory Usage**: Adjust `MAX_HISTORY_PAIRS` based on available memory
- **Response Quality**: Configure `SNIPPET_CHARS` and `CONTEXT_MAX_CHARS`
- **Token Management**: Set appropriate `AOAI_MAX_TOKENS` limits
- **Caching**: Implement response caching for common queries
- **Database**: Monitor Cosmos DB RU/s usage and scale as needed

### Monitoring
- **Azure Monitor**: Track service health and performance
- **Application Insights**: Monitor application metrics
- **Cost Management**: Track Azure service costs
- **Error Tracking**: Monitor and alert on application errors

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** thoroughly
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for new features
- Ensure all tests pass before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Contact

### Getting Help
1. **Check** the troubleshooting section above
2. **Review** Azure service documentation
3. **Search** existing issues in the repository
4. **Open** a new issue with detailed information

### Contact Information
- **Repository**: [GitHub Issues](https://github.com/your-username/QU_Chatbot/issues)
- **Documentation**: This README file
- **Azure Support**: [Azure Support Center](https://azure.microsoft.com/support/)

---

## 🎯 Project Summary

This Qatar University Chatbot is a comprehensive AI-powered solution that combines:

- **Modern Web Technologies**: FastAPI, Tailwind CSS, JavaScript
- **Advanced AI Services**: Azure OpenAI, Semantic Kernel
- **Cloud Infrastructure**: Azure Search, Cosmos DB
- **Intelligent Features**: Conversation awareness, multi-session support
- **Production Ready**: Comprehensive error handling, monitoring, security

The system provides a seamless experience for students and staff to get information about Qatar University admissions, programs, and general information through an intelligent, conversation-aware chatbot interface.
