# SPRINT.AI Backend API

## Quick Deploy to Render

1. Push this folder to GitHub
2. Go to https://render.com
3. Click "New" → "Web Service"
4. Connect your GitHub repo
5. Select this directory
6. Render will auto-detect and deploy!

## Local Testing

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit: http://localhost:8000/docs for API documentation

## API Endpoints

- `POST /analyze` - Analyze running video
- `GET /health` - Health check
- `GET /` - Service info
