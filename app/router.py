import os
import shutil
import uuid
import aiofiles
import io
import zipfile
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.config import UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Module-level variable to track the last generated share link
LAST_SHARE_LINK = None

def check_share_validity(token_dir: str):
    """Checks if a share is valid (exists, not revoked, not expired)."""
    if not os.path.exists(token_dir):
        raise HTTPException(status_code=404, detail="Share not found")
    
    meta_path = os.path.join(token_dir, "meta.json")
    if not os.path.exists(meta_path):
        return True # Treat shares without metadata as valid (manual)

    try:
        with open(meta_path, "r") as f:
            meta = json.load(f)
        
        if meta.get("revoked"):
            raise HTTPException(status_code=410, detail="This link has been revoked")
        
        expires_at_str = meta.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                raise HTTPException(status_code=410, detail="This link has expired")
                
    except json.JSONDecodeError:
        pass # Ignore corrupt metadata
    
    return True

def save_metadata(token_dir: str, duration: str):
    """Saves metadata for the share."""
    now = datetime.now()
    expires_at = None
    
    if duration != "manual":
        try:
            minutes = int(duration)
            if minutes > 0:
                 expires_at = now + timedelta(minutes=minutes)
        except ValueError:
            pass # Treat as manual if parsing fails
        
    meta = {
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "revoked": False
    }
    
    with open(os.path.join(token_dir, "meta.json"), "w") as f:
        json.dump(meta, f)

    return meta

def cleanup_shares():
    """Removes expired or revoked shares."""
    if not os.path.exists(UPLOAD_DIR):
        return
        
    for token in os.listdir(UPLOAD_DIR):
        token_dir = os.path.join(UPLOAD_DIR, token)
        if not os.path.isdir(token_dir):
            continue
            
        meta_path = os.path.join(token_dir, "meta.json")
        if not os.path.exists(meta_path):
            continue
            
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
            
            should_delete = False
            if meta.get("revoked"):
                should_delete = True
            elif meta.get("expires_at"):
                expires_at = datetime.fromisoformat(meta["expires_at"])
                if datetime.now() > expires_at:
                    should_delete = True
            
            if should_delete:
                print(f"INFO: Cleaning up expired/revoked share: {token}")
                shutil.rmtree(token_dir)
                
        except Exception as e:
            print(f"ERROR: Failed to cleanup {token}: {e}")

@router.get("/", response_class=HTMLResponse)
async def get_sender_ui(request: Request):
    base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    return templates.TemplateResponse("index.html", {"request": request, "base_url": base_url})

@router.get("/last-share")
async def get_last_share():
    """Return the last generated share link for GUI polling."""
    return {"link": LAST_SHARE_LINK}

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), duration: str = Form("manual")):
    token = str(uuid.uuid4())
    token_dir = os.path.join(UPLOAD_DIR, token)
    os.makedirs(token_dir, exist_ok=True)
    
    meta = save_metadata(token_dir, duration)
    
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
    print(f"INFO: Expires: {meta['expires_at']}")
    print("="*60)
    return {"link": share_link, "token": token, "files": file_metadata, "expires_at": meta['expires_at']}

def format_size(size_bytes):
    """Formats bytes into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

@router.get("/share/{token}", response_class=HTMLResponse)
async def get_receiver_ui(request: Request, token: str):
    token_dir = os.path.join(UPLOAD_DIR, token)
    check_share_validity(token_dir)
    
    files = []
    total_bytes = 0
    for filename in os.listdir(token_dir):
        if filename == "meta.json": continue
        
        file_path = os.path.join(token_dir, filename)
        if os.path.isfile(file_path):
            size_bytes = os.path.getsize(file_path)
            total_bytes += size_bytes
            
            files.append({
                "name": filename,
                "size": format_size(size_bytes),
                "url": f"/download/{token}/{filename}"
            })
            
    return templates.TemplateResponse("share.html", {
        "request": request, 
        "token": token, 
        "files": files,
        "total_size": format_size(total_bytes)
    })

@router.get("/download-all/{token}")
async def download_all_files(token: str):
    token_dir = os.path.join(UPLOAD_DIR, token)
    check_share_validity(token_dir)
    
    # Create in-memory zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(token_dir):
            if filename == "meta.json": continue
            
            file_path = os.path.join(token_dir, filename)
            if os.path.isfile(file_path):
                zip_file.write(file_path, arcname=filename)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=shared_files.zip"}
    )

@router.get("/download/{token}/{filename}")
async def download_file(token: str, filename: str):
    token_dir = os.path.join(UPLOAD_DIR, token)
    # Basic directory traversal prevention
    if ".." in token or ".." in filename:
         raise HTTPException(status_code=400, detail="Invalid path")

    check_share_validity(token_dir)
    
    file_path = os.path.join(token_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path, filename=filename)

@router.post("/revoke/{token}")
async def revoke_share(token: str):
    token_dir = os.path.join(UPLOAD_DIR, token)
    if not os.path.exists(token_dir):
         raise HTTPException(status_code=404, detail="Share not found")
    
    meta_path = os.path.join(token_dir, "meta.json")
    meta = {}
    
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
        except:
            pass
            
    meta["revoked"] = True
    
    with open(meta_path, "w") as f:
        json.dump(meta, f)
        
    return {"status": "revoked"}

