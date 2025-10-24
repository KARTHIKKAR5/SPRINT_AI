
# Create a comprehensive deployment guide
deployment_guide = '''# 🚀 SPRINT.AI Complete Deployment Guide

## Overview
SPRINT.AI consists of two parts:
1. **Frontend**: React web application (already deployed)
2. **Backend**: FastAPI + MediaPipe AI analysis server (you need to deploy this)

---

## Part 1: Deploy the Backend (Required for AI Analysis)

### Option A: Deploy to Render.com (Recommended - Free Tier Available)

1. **Create GitHub Repository**
   ```bash
   # Create a new repo on GitHub
   # Upload the sprint_ai_backend folder contents
   ```

2. **Deploy on Render**
   - Go to https://render.com
   - Sign up/Login with GitHub
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the sprint_ai_backend folder
   - Render auto-detects Python and uses:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment
   - Copy your service URL (e.g., https://sprint-ai-api.onrender.com)

3. **Verify Backend is Running**
   - Visit: `https://your-backend-url.onrender.com/health`
   - You should see: `{"status": "healthy", "timestamp": "..."}`

### Option B: Deploy with Docker (Alternative)

```bash
cd sprint_ai_backend
docker build -t sprint-ai-api .
docker run -p 8000:8000 sprint-ai-api
```

### Option C: Local Testing

```bash
cd sprint_ai_backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## Part 2: Configure Frontend

1. **Access the Frontend**
   - Go to the deployed frontend URL (provided below)

2. **Admin Login**
   - Email: buildorburn0@gmail.com
   - Password: burntobuild

3. **Configure API URL**
   - Go to Admin Dashboard → Settings
   - Enter your backend URL: `https://your-backend-url.onrender.com`
   - Click "Test Connection"
   - If green checkmark appears, you're ready!

---

## Part 3: Test the System

1. **Register as Athlete**
   - Click "Register" on landing page
   - Fill in details, select running distance
   - Login to dashboard

2. **Upload Test Video**
   - Go to "Upload Video"
   - Select a side-view running video (MP4, MOV, or AVI)
   - Ensure video shows:
     - Full body visible
     - Side angle
     - Minimum 30 FPS
   - Click "Analyze with AI"
   - Wait 30-60 seconds for processing

3. **View Results**
   - Real biomechanics report will appear
   - All metrics calculated from actual pose detection
   - Report saves automatically to Firebase

---

## Important Notes

### Video Requirements for Best Accuracy:
- **Angle**: Side view (90° to running direction)
- **Framing**: Full body visible throughout
- **Quality**: Minimum 720p, 30+ FPS
- **Lighting**: Good visibility, minimal shadows
- **Background**: Stable camera, minimal movement
- **Distance**: Include track markers if possible for calibration

### Calibration:
- Default: 100 pixels = 1 meter
- For better accuracy: Measure a known distance in your video
- Example: Track lane width = 1.22m
  - Count pixels for that distance
  - Calibration value = 1.22 / pixel_count

### Backend Performance:
- Free Render tier may sleep after 15 min inactivity
- First request after sleep takes 30-60 seconds (cold start)
- Subsequent requests are fast (5-15 seconds per video)
- For production: Upgrade to paid tier for always-on service

### Firestore Setup:
- Firebase is already configured in the app
- Collections are created automatically
- No additional setup needed

---

## Troubleshooting

### Backend shows "Offline"
1. Check backend URL is correct in Settings
2. Visit backend /health endpoint directly
3. Check Render logs for errors
4. Ensure backend service is not sleeping

### Analysis fails
1. Check video format (MP4/MOV/AVI)
2. Ensure video file size < 100MB
3. Check backend logs for errors
4. Try with a shorter video first (10-30 seconds)

### No pose detected
1. Ensure runner is clearly visible
2. Check video quality and lighting
3. Try different camera angle (pure side view)
4. Ensure full body is in frame

---

## File Structure

```
sprint-ai/
├── frontend/               (deployed at provided URL)
│   ├── index.html
│   ├── Firebase config
│   └── React components
│
└── backend/                (deploy this to Render)
    ├── main.py            (FastAPI + MediaPipe)
    ├── requirements.txt   (Python dependencies)
    ├── Dockerfile         (Docker config)
    ├── render.yaml        (Render config)
    └── README.md          (Backend docs)
```

---

## Cost Breakdown

- **Frontend**: FREE (static hosting)
- **Firebase**: FREE (generous free tier)
- **Backend (Render Free)**: 
  - FREE for 750 hours/month
  - Sleeps after 15 min inactivity
  - Good for testing and demo
- **Backend (Render Paid)**: 
  - $7/month for always-on
  - Recommended for competition/production

---

## Support

For backend deployment issues:
- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com

For frontend issues:
- Check browser console for errors
- Verify Firebase config is correct

---

## Ready to Go! 🎉

Once backend is deployed and configured:
1. Athletes can register and upload videos
2. AI analyzes with real MediaPipe calculations
3. Detailed biomechanics reports generated
4. Officials can review and rank athletes
5. National leaderboard tracks top performers

Perfect for NCC Innovation Competition! 🇮🇳
'''

with open("sprint_ai_backend/DEPLOYMENT_GUIDE.md", "w") as f:
    f.write(deployment_guide)

print("✅ Deployment guide created")
print("\n" + "="*60)
print("SPRINT.AI COMPLETE PACKAGE READY!")
print("="*60)
