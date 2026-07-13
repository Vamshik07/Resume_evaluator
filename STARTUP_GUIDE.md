# 🚀 Resume Evaluator - Startup Guide

## ✅ System is Now Running!

### Running Services:
- **Backend API**: http://localhost:8000
  - API Docs: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health
- **Frontend Dashboard**: http://localhost:8501

---

## 📋 Quick Commands (from project root)

### Install Dependencies:
```powershell
pip install -r requirements.txt
```

### Start Backend (Terminal 1):
```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Start Frontend (Terminal 2):
```powershell
$env:API_BASE_URL='http://localhost:8000'
streamlit run frontend\streamlit_app.py --server.port 8501
```

---

## 🔧 Configuration

### Enable Gemini AI (Optional):
Add to your environment or `.env` file:
```
ENABLE_GEMINI=true
GOOGLE_API_KEY=your_api_key_here
```

### Change API URL:
```powershell
$env:API_BASE_URL='http://your-custom-url:port'
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'backend'"
**Fix**: Always run `uvicorn backend.main:app` from the **project root**, not from inside the `backend/` folder.

### "Could not connect to API"
**Fix**: Ensure backend is running on http://localhost:8000 and `API_BASE_URL` env var points to it.

### Semantic matching disabled
**Normal**: LLM analysis is disabled by default. Set `ENABLE_GEMINI=true` to enable (requires Google API key).

---

## 📝 What Was Fixed

1. ✅ **Frontend JD filter** - Now correctly maps selected job to `job_description_id`
2. ✅ **API base URL** - Defaults to local backend instead of remote hosted service
3. ✅ **Gemini guard** - LLM calls are now optional and gracefully disabled without errors
4. ✅ **Documentation** - Aligned with actual file structure and startup flow
5. ✅ **Requirements** - Removed network-failing langchain packages (not needed)

---

## 🎯 Next Steps

1. Open http://localhost:8501 in your browser
2. Choose your role (Placement Officer or Student)
3. Upload job descriptions and resumes
4. Get instant AI-powered evaluation results!

---

**Happy evaluating! 🎉**
