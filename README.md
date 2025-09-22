# 🎓 Qatar University AI Chatbot

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Azure](https://img.shields.io/badge/Azure-AI%20Services-0078d4.svg)](https://azure.microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A powerful, high-accuracy chatbot for Qatar University built with Azure AI services. This chatbot leverages Azure's AI ecosystem to provide intelligent, context-aware responses based on university documents and policies using Retrieval Augmented Generation (RAG).

## 🎯 Features

- **Retrieval Augmented Generation (RAG)**: Pulls information from uploaded PDFs stored in Azure Cosmos DB
- **Semantic Search**: Uses Azure AI Search for intelligent document retrieval
- **Cost-Optimized**: Leverages existing Azure resources without additional costs
- **High Accuracy**: Context-aware responses specifically for Qatar University
- **Real-time Processing**: Upload and process documents instantly
- **Conversation History**: Maintains context across conversations
- **Performance Monitoring**: Built-in optimization and cost tracking

## 🏗️ Architecture

The chatbot uses your existing Azure resources:

- **Azure OpenAI** (`oai-ai-rd-sc`) - GPT-4 for intelligent responses
- **Azure AI Search** (`srch-ai-rd-sc`) - Semantic search and RAG
- **Cosmos DB** (`cosmo-ai-rd-sc`) - Document storage and conversation history
- **Storage Account** (`stairdsc`) - PDF file storage
- **Function App** (`func-ai-rd-sc`) - Serverless processing (optional)
- **App Service** (`app-ai-rd-sc-01`) - Web application hosting

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Azure subscription with the following services:
  - Azure OpenAI Service
  - Azure Cosmos DB
  - Azure AI Search
  - Azure Blob Storage

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Qatar-University-Chatbot.git
cd Qatar-University-Chatbot
```

### 2. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Azure Services

1. Copy the environment template:
```bash
cp env.example .env
```

2. Edit `.env` file with your Azure service credentials:
```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Cosmos DB Configuration
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443
COSMOS_KEY=your_cosmos_db_key_here
COSMOS_DB=your_database_name
COSMOS_CONTAINER=your_container_name

# Azure AI Search Configuration
SEARCH_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_API_KEY=your_search_api_key_here
SEARCH_INDEX=your_index_name

# Storage Account Configuration
STORAGE_CONNECTION_STRING=your_storage_connection_string_here
```

### 4. Run the Application

```bash
streamlit run app.py
```

The chatbot will be available at `http://localhost:8501`

> **Note**: Make sure to replace all placeholder values in `.env` with your actual Azure service credentials.

## 📚 Usage

### Uploading Documents

1. Use the sidebar to upload Qatar University PDF documents
2. The system will automatically:
   - Extract text from PDFs
   - Chunk content for optimal retrieval
   - Store in Cosmos DB
   - Index in Azure AI Search

### Chatting with the Bot

1. Ask questions about Qatar University policies, procedures, or services
2. Use document type filters to focus on specific areas:
   - **Admissions**: Application requirements, deadlines
   - **Academic**: Course information, graduation requirements
   - **Services**: Student support, IT services
   - **Policy**: University regulations and procedures

### Advanced Features

- **Semantic Search**: Find relevant documents even with different wording
- **Context Awareness**: Maintains conversation history for better responses
- **Source Citation**: Shows which documents were used for each response
- **Performance Monitoring**: Track response times and costs

## 🔧 Configuration

### Optimizing for Your Use Case

Edit `config.py` to customize:

```python
# Response quality vs speed
TEMPERATURE = 0.1  # Lower = more consistent responses
MAX_SEARCH_RESULTS = 5  # More results = better context, higher cost

# Performance optimization
CACHE_TTL_SECONDS = 3600  # Cache duration
MAX_CONVERSATION_HISTORY = 10  # Context window
```

### Cost Optimization

The chatbot is designed to minimize costs:

- **Intelligent Caching**: Reduces duplicate API calls
- **Optimized Chunking**: Balances context quality with token usage
- **TTL Policies**: Automatic cleanup of old conversation data
- **Performance Monitoring**: Track and optimize usage patterns

## 🚀 Deployment to Azure

### Option 1: Azure App Service (Recommended)

1. **Create App Service**:
```bash
# Create resource group
az group create --name qatar-chatbot-rg --location eastus

# Create App Service plan
az appservice plan create --name qatar-chatbot-plan --resource-group qatar-chatbot-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group qatar-chatbot-rg --plan qatar-chatbot-plan --name qatar-university-chatbot --runtime "PYTHON|3.9"
```

2. **Configure Environment Variables**:
```bash
# Set all environment variables from your .env file
az webapp config appsettings set --resource-group qatar-chatbot-rg --name qatar-university-chatbot --settings @appsettings.json
```

3. **Deploy Application**:
```bash
# Deploy using ZIP
az webapp deployment source config-zip --resource-group qatar-chatbot-rg --name qatar-university-chatbot --src deployment.zip
```

### Option 2: GitHub Actions (CI/CD)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'qatar-university-chatbot'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

### Option 3: Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📊 Monitoring and Optimization

### Performance Dashboard

The chatbot includes built-in performance monitoring:

- Response time tracking
- Token usage and cost estimation
- Cache hit rates
- Error monitoring
- System resource usage

### Optimization Recommendations

The system automatically suggests optimizations:

- Cache improvements
- Response time optimizations
- Cost reduction strategies
- Resource scaling recommendations

## 🔒 Security and Privacy

- All data is stored in your existing Azure resources
- No external API calls beyond Azure services
- Conversation data has configurable TTL
- Document access is controlled through Azure RBAC

## 🛠️ Troubleshooting

### Common Issues

1. **Azure Service Connection Errors**
   - Verify your `.env` file has correct endpoints and keys
   - Check Azure service status and quotas

2. **Document Processing Failures**
   - Ensure PDFs are not password-protected
   - Check file size limits (recommended < 50MB)

3. **Slow Response Times**
   - Monitor performance dashboard for bottlenecks
   - Consider increasing cache TTL
   - Check Azure Search index performance

### Performance Tuning

1. **For High Volume**: Increase App Service tier
2. **For Better Accuracy**: Increase `MAX_SEARCH_RESULTS`
3. **For Cost Savings**: Decrease `TEMPERATURE` and optimize caching

## 📈 Future Enhancements

- Multi-language support (Arabic/English)
- Voice interface integration
- Advanced analytics dashboard
- Integration with university systems
- Mobile app development

## 🤝 Contributing

We welcome contributions to improve the Qatar University Chatbot! Here's how you can help:

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test thoroughly
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Areas for Contribution

- **Document Processing**: Improve PDF text extraction and chunking
- **UI/UX**: Enhance the Streamlit interface
- **Performance**: Optimize search and response times
- **Features**: Add new capabilities like voice interface
- **Documentation**: Improve setup guides and API documentation
- **Testing**: Add unit tests and integration tests

### Code Style

- Follow PEP 8 for Python code
- Add docstrings to functions and classes
- Include type hints where possible
- Write clear commit messages

## 📊 Project Structure

```
Qatar-University-Chatbot/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── services/            # Core services
│   ├── chatbot_engine.py    # Main chatbot logic
│   ├── cosmos_service.py    # Cosmos DB operations
│   ├── azure_search_service.py # Search functionality
│   └── document_processor.py   # PDF processing
├── deployment/          # Deployment scripts
├── optimization/        # Performance monitoring
└── README.md           # This file
```

## 🔒 Security

- Never commit API keys or sensitive credentials
- Use environment variables for all configuration
- Regularly rotate Azure service keys
- Monitor usage and costs in Azure Portal

## 📞 Support

For technical issues:
- Check [Issues](https://github.com/yourusername/Qatar-University-Chatbot/issues) for known problems
- Review Azure service logs
- Consult Azure documentation for service-specific issues
- Create a new issue with detailed error information

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Powered by [Azure AI Services](https://azure.microsoft.com/en-us/services/cognitive-services/)
- Inspired by Qatar University's commitment to innovation in education

---

**Built with ❤️ for Qatar University using Azure AI Services**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/Qatar-University-Chatbot.svg?style=social&label=Star)](https://github.com/yourusername/Qatar-University-Chatbot)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/Qatar-University-Chatbot.svg?style=social&label=Fork)](https://github.com/yourusername/Qatar-University-Chatbot/fork)
