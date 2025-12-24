from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.router import router, cleanup_shares
import os
import asyncio
from app.config import UPLOAD_DIR

app = FastAPI(title="LocalShare")

async def cleanup_task():
    while True:
        try:
            cleanup_shares()
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    print("="*60)
    print(f"INFO: LocalShare Backend Started")
    print(f"INFO: PUBLIC_BASE_URL = {url}")
    print(f"INFO: All share links will use this base URL")
    print("="*60)
    asyncio.create_task(cleanup_task())

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include business logic router
app.include_router(router)
