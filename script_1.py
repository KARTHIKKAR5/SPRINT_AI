
# Create requirements.txt for backend
requirements = '''fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
mediapipe==0.10.14
opencv-python-headless==4.10.0.84
numpy==1.26.4
'''

with open("sprint_ai_backend/requirements.txt", "w") as f:
    f.write(requirements)

# Create Dockerfile for easy deployment
dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    libglib2.0-0 \\
    libsm6 \\
    libxext6 \\
    libxrender-dev \\
    libgomp1 \\
    libgthread-2.0-0 \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

with open("sprint_ai_backend/Dockerfile", "w") as f:
    f.write(dockerfile)

# Create render.yaml for one-click deployment
render_yaml = '''services:
  - type: web
    name: sprint-ai-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
'''

with open("sprint_ai_backend/render.yaml", "w") as f:
    f.write(render_yaml)

# Create README for backend
readme = '''# SPRINT.AI Backend API

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
'''

with open("sprint_ai_backend/README.md", "w") as f:
    f.write(readme)

print("✅ Backend deployment files created")
print("✅ requirements.txt created")
print("✅ Dockerfile created")
print("✅ render.yaml created")
print("✅ README.md created")
