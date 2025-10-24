
import zipfile
import os

# Create a complete package zip
zip_filename = "SPRINT_AI_BACKEND.zip"

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("sprint_ai_backend"):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, ".")
            zipf.write(file_path, arcname)

print(f"✅ Created complete package: {zip_filename}")
print(f"📦 Package size: {os.path.getsize(zip_filename) / 1024:.2f} KB")
print("\n📂 Package contains:")
print("   ├── main.py (FastAPI + MediaPipe AI)")
print("   ├── requirements.txt (Dependencies)")
print("   ├── Dockerfile (Container config)")
print("   ├── render.yaml (Render deployment)")
print("   ├── README.md (Backend docs)")
print("   ├── DEPLOYMENT_GUIDE.md (Full guide)")
print("   ├── QUICK_START.md (5-min setup)")
print("   └── SUMMARY.md (Everything you need)")
print("\n✨ Download this ZIP and deploy to Render.com!")
