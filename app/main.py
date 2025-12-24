from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.router import router
import os
from app.config import UPLOAD_DIR

app = FastAPI(title="LocalShare")

@app.on_event("startup")
async def startup_event():
    url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    print("="*60)
    print(f"INFO: LocalShare Backend Started")
    print(f"INFO: PUBLIC_BASE_URL = {url}")
    print(f"INFO: All share links will use this base URL")
    print("="*60)

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include business logic router
app.include_router(router)
