import os
import shutil
import uuid
import aiofiles
from typing import List
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from app.config import UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Module-level variable to track the last generated share link
LAST_SHARE_LINK = None

@router.get("/", response_class=HTMLResponse)
async def get_sender_ui(request: Request):
    base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    return templates.TemplateResponse("index.html", {"request": request, "base_url": base_url})

@router.get("/last-share")
async def get_last_share():
    """Return the last generated share link for GUI polling."""
    return {"link": LAST_SHARE_LINK}

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    token = str(uuid.uuid4())
    token_dir = os.path.join(UPLOAD_DIR, token)
    os.makedirs(token_dir, exist_ok=True)
    
    file_metadata = []
    
    for file in files:
        if not file.filename:
            continue
            
        file_path = os.path.join(token_dir, file.filename)
        
        # Async write for performance
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)
        
        file_metadata.append(file.filename)
    
    global LAST_SHARE_LINK
    
    base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    share_link = f"{base_url}/share/{token}"
    
    # Store the last generated share link for GUI polling
    LAST_SHARE_LINK = share_link
    
    print("="*60)
    print(f"INFO: Share Link Generated")
    print(f"INFO: Token: {token}")
    print(f"INFO: Base URL: {base_url}")
    print(f"INFO: Full Link: {share_link}")
    print(f"INFO: Files: {file_metadata}")
    print("="*60)
    return {"link": share_link, "token": token, "files": file_metadata}

@router.get("/share/{token}", response_class=HTMLResponse)
async def get_receiver_ui(request: Request, token: str):
    token_dir = os.path.join(UPLOAD_DIR, token)
    if not os.path.exists(token_dir):
        raise HTTPException(status_code=404, detail="Invalid or expired link")
    
    files = []
    for filename in os.listdir(token_dir):
        file_path = os.path.join(token_dir, filename)
        if os.path.isfile(file_path):
            size_bytes = os.path.getsize(file_path)
            # Simple human readable size
            if size_bytes < 1024:
                 size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                 size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            
            files.append({
                "name": filename,
                "size": size_str,
                "url": f"/download/{token}/{filename}"
            })
            
    return templates.TemplateResponse("share.html", {"request": request, "token": token, "files": files})

@router.get("/download/{token}/{filename}")
async def download_file(token: str, filename: str):
    token_dir = os.path.join(UPLOAD_DIR, token)
    if not os.path.exists(token_dir):
        raise HTTPException(status_code=404, detail="Invalid or expired link")
    # Basic directory traversal prevention
    if ".." in token or ".." in filename:
         raise HTTPException(status_code=400, detail="Invalid path")
         
    file_path = os.path.join(token_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path, filename=filename)
