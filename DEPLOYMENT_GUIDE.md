# 🚀 Deployment Guide - Streamlit Cloud

This guide will help you deploy your **Automated Resume Relevance Check System** to Streamlit Cloud for public access.

## 📋 Prerequisites

1. **GitHub Account**: Your code must be in a GitHub repository
2. **Streamlit Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **Google API Key**: For Gemini integration

## 🔧 Pre-Deployment Setup

### 1. Prepare Your Repository

Ensure your GitHub repository contains these files:
```
├── streamlit_app.py              # Main entry point for Streamlit Cloud
├── dashboard.py                  # Your Streamlit dashboard
├── main.py                       # FastAPI backend
├── requirements_streamlit.txt    # Streamlit Cloud dependencies
├── packages.txt                  # System packages
├── .streamlit/config.toml       # Streamlit configuration
├── src/                          # Your source code
└── DEPLOYMENT_GUIDE.md           # This guide
```

### 2. Environment Variables Setup

You'll need to set these secrets in Streamlit Cloud:

#### Required Secrets:
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `DEFAULT_MODEL`: `gemini-pro`
- `EMBEDDING_MODEL`: `sentence-transformers/all-MiniLM-L6-v2`

#### Optional Secrets:
- `UPLOAD_DIR`: `./data/uploads` (default)
- `DATABASE_URL`: SQLite database path (default)

## 🌐 Deployment Steps

### Step 1: Push to GitHub

```bash
# Add all files to git
git add .

# Commit changes
git commit -m "Add Streamlit Cloud deployment files"

# Push to GitHub
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud**: Visit [share.streamlit.io](https://share.streamlit.io)
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Fill in the details**:
   - **Repository**: Select your GitHub repository
   - **Branch**: `main` (or your main branch)
   - **Main file path**: `streamlit_app.py`
   - **App URL**: Choose a unique URL (e.g., `resume-evaluation-system`)

### Step 3: Configure Secrets

1. **Click "Advanced settings"**
2. **Add secrets** in the format:
   ```
   GOOGLE_API_KEY = "your_actual_api_key_here"
   DEFAULT_MODEL = "gemini-pro"
   EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
   ```

### Step 4: Deploy

1. **Click "Deploy!"**
2. **Wait for deployment** (5-10 minutes)
3. **Check logs** for any errors
4. **Access your app** at `https://your-app-name.streamlit.app`

## 🔍 Troubleshooting

### Common Issues:

#### 1. Build Failures
- **Check requirements**: Ensure all dependencies are in `requirements_streamlit.txt`
- **Python version**: Streamlit Cloud uses Python 3.9
- **Memory limits**: Some packages might exceed memory limits

#### 2. Runtime Errors
- **Check logs**: Look for error messages in the Streamlit Cloud logs
- **Environment variables**: Ensure all secrets are set correctly
- **File paths**: Use relative paths, not absolute paths

#### 3. API Connection Issues
- **Backend startup**: The backend starts in a background thread
- **Port conflicts**: Backend uses port 8000, frontend uses 8501
- **CORS issues**: Configured in `.streamlit/config.toml`

### Debug Commands:

```bash
# Check if spaCy model is installed
python -c "import spacy; spacy.load('en_core_web_sm')"

# Test backend startup
python -c "from main import app; print('Backend OK')"

# Test dashboard import
python -c "from dashboard import main; print('Dashboard OK')"
```

## 📊 Performance Considerations

### Streamlit Cloud Limits:
- **Memory**: 1GB RAM
- **CPU**: Shared resources
- **Storage**: 1GB disk space
- **Timeout**: 30 seconds per request

### Optimizations:
- **Lazy loading**: Import heavy modules only when needed
- **Caching**: Use `@st.cache_data` for expensive operations
- **File cleanup**: Remove temporary files after processing
- **Error handling**: Graceful degradation for API failures

## 🔒 Security Notes

### Public Access:
- **Your app will be publicly accessible**
- **Don't expose sensitive data** in logs or error messages
- **Use environment variables** for all secrets
- **Validate all inputs** before processing

### API Key Security:
- **Never commit API keys** to your repository
- **Use Streamlit secrets** for sensitive data
- **Rotate keys regularly** for security

## 🎯 Alternative Deployment Options

### 1. HuggingFace Spaces
```bash
# Create a HuggingFace Space
# Upload your code
# Configure environment variables
# Deploy with Gradio or Streamlit
```

### 2. Railway
```bash
# Connect GitHub repository
# Configure environment variables
# Deploy with automatic scaling
```

### 3. Heroku
```bash
# Create Procfile
# Configure buildpacks
# Deploy with git push
```

## 📈 Monitoring

### Streamlit Cloud Metrics:
- **View count**: Track app usage
- **Error logs**: Monitor for issues
- **Performance**: Check response times

### Custom Monitoring:
- **Health checks**: Implement `/health` endpoint
- **Usage analytics**: Track user interactions
- **Error reporting**: Log errors for debugging

## 🔄 Updates and Maintenance

### Updating Your App:
1. **Make changes** to your local code
2. **Commit and push** to GitHub
3. **Streamlit Cloud auto-deploys** from main branch
4. **Check logs** for any issues

### Maintenance Tasks:
- **Monitor logs** regularly
- **Update dependencies** as needed
- **Rotate API keys** periodically
- **Clean up old data** to manage storage

## 🎉 Success Checklist

- [ ] Code pushed to GitHub repository
- [ ] Streamlit Cloud app created
- [ ] Environment variables configured
- [ ] App deployed successfully
- [ ] Public URL accessible
- [ ] All features working
- [ ] Error handling in place
- [ ] Performance optimized

## 📞 Support

### Streamlit Cloud Support:
- **Documentation**: [docs.streamlit.io](https://docs.streamlit.io)
- **Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues**: Report bugs and feature requests

### Your App Support:
- **Health Check**: `https://your-app.streamlit.app/health`
- **API Docs**: `https://your-app.streamlit.app/docs` (if backend is accessible)
- **Error Logs**: Check Streamlit Cloud dashboard

---

**🚀 Your Resume Evaluation System is now publicly accessible!**

Share your app URL: `https://your-app-name.streamlit.app`
