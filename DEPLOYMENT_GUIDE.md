# 🚀 Qatar University Chatbot - Azure App Service Deployment Guide

## 📋 Prerequisites

1. **Azure CLI** installed ([Download here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
2. **Azure Subscription** with appropriate permissions
3. **Existing Azure Resources** (as per your setup):
   - Azure OpenAI Service
   - Cosmos DB
   - Azure AI Search
   - Storage Account

## 🎯 Step-by-Step Deployment

### Step 1: Prepare Your Environment Variables

1. **Update `appsettings.json`** with your actual API keys:
   ```json
   {
     "name": "AZURE_OPENAI_API_KEY",
     "value": "YOUR_ACTUAL_OPENAI_API_KEY"
   }
   ```

2. **Replace all placeholder values** in `appsettings.json` with your actual keys from `.env` file

### Step 2: Create Deployment Package

Run the package creation script:
```bash
create_deployment_package.bat
```

This creates `deployment.zip` with all necessary files.

### Step 3: Update Deployment Configuration

Edit `deploy.bat` and update these variables:
```batch
set APP_NAME=qatar-university-chatbot
set RESOURCE_GROUP=your-resource-group-name
set LOCATION=eastus
```

### Step 4: Deploy to Azure

1. **Login to Azure CLI**:
   ```bash
   az login
   ```

2. **Run deployment script**:
   ```bash
   deploy.bat
   ```

### Step 5: Verify Deployment

1. **Check deployment status** in Azure Portal
2. **Test your chatbot** at: `https://YOUR_APP_NAME.azurewebsites.net`
3. **Monitor logs** in Azure Portal → App Service → Log stream

## 🔧 Manual Deployment (Alternative)

### Option 1: Azure Portal Deployment

1. **Create App Service**:
   - Go to Azure Portal
   - Create new App Service
   - Choose Python 3.9 runtime
   - Select appropriate pricing tier

2. **Upload deployment package**:
   - Go to Deployment Center
   - Choose "Local Git" or "ZIP Deploy"
   - Upload your `deployment.zip`

3. **Configure Application Settings**:
   - Go to Configuration → Application settings
   - Add all environment variables from `appsettings.json`

### Option 2: Azure CLI Commands

```bash
# Create resource group
az group create --name qatar-chatbot-rg --location eastus

# Create App Service plan
az appservice plan create --name qatar-chatbot-plan --resource-group qatar-chatbot-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group qatar-chatbot-rg --plan qatar-chatbot-plan --name qatar-university-chatbot --runtime "PYTHON|3.9"

# Configure app settings
az webapp config appsettings set --resource-group qatar-chatbot-rg --name qatar-university-chatbot --settings @appsettings.json

# Deploy application
az webapp deployment source config-zip --resource-group qatar-chatbot-rg --name qatar-university-chatbot --src deployment.zip
```

## 🔍 Troubleshooting

### Common Issues:

1. **App won't start**:
   - Check logs in Azure Portal → App Service → Log stream
   - Verify all environment variables are set correctly
   - Ensure Python 3.9 runtime is selected

2. **Import errors**:
   - Verify `requirements.txt` has all dependencies
   - Check that all Python files are included in deployment package

3. **Environment variable issues**:
   - Double-check all API keys and endpoints in Application Settings
   - Ensure no extra spaces or quotes in values

4. **Performance issues**:
   - Consider upgrading to higher App Service plan (S1, P1V2)
   - Monitor resource usage in Azure Portal

## 📊 Monitoring & Maintenance

1. **Application Insights** (Optional):
   - Enable in Azure Portal for detailed monitoring
   - Track usage, performance, and errors

2. **Log Analytics**:
   - Monitor logs in Azure Portal → App Service → Log stream
   - Set up alerts for critical errors

3. **Cost Optimization**:
   - Monitor usage in Azure Cost Management
   - Consider auto-scaling for variable traffic

## 🔒 Security Best Practices

1. **Environment Variables**:
   - Never commit API keys to source control
   - Use Azure Key Vault for sensitive data (optional)

2. **Network Security**:
   - Configure CORS settings if needed
   - Consider Azure Front Door for additional security

3. **Authentication** (Optional):
   - Consider adding Azure AD authentication
   - Implement rate limiting for API endpoints

## 📞 Support

If you encounter issues:
1. Check Azure Portal logs first
2. Verify all environment variables
3. Test locally with same configuration
4. Check Azure service status

---

**🎉 Your Qatar University Chatbot will be live at: `https://YOUR_APP_NAME.azurewebsites.net`**
