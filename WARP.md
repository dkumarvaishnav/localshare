# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

LocalShare is a temporary file sharing tool that runs a local FastAPI web server, allowing users to share files directly from their machine via unique token-based URLs. Files are shared via ngrok tunneling for external access.

## Architecture

### Core Components

**FastAPI Backend (`app/`)**
- `main.py`: Application entry point, configures FastAPI, mounts static files, manages startup events
- `router.py`: All HTTP endpoints (upload, download, share pages), token generation, file storage logic
- `config.py`: Configuration management, primarily `UPLOAD_DIR` location
- `templates/`: Jinja2 HTML templates (index.html for sender, share.html for receiver)
- `static/`: CSS styling

**Token-Based File Isolation**
- Each upload generates a UUID token
- Files stored in `shares/{token}/` directories
- Share links format: `{base_url}/share/{token}`
- Download links format: `{base_url}/download/{token}/{filename}`

**GUI Launcher (`localshare_gui.py`)**
- Tkinter GUI for starting/stopping the application
- Manages both uvicorn and ngrok subprocesses
- Polls backend for generated share links and displays them
- Sets `PUBLIC_BASE_URL` environment variable for ngrok URL

### Environment Variables

- `PUBLIC_BASE_URL`: Base URL for share links (set by GUI or manually for ngrok deployment). Defaults to `http://localhost:8000`
- `LOCALSHARE_UPLOAD_DIR`: Directory for storing uploaded files. Defaults to `shares/`

### Key Flows

**Upload Flow**: Files POSTed to `/upload` → UUID token generated → files saved to `shares/{token}/` → share link returned

**Download Flow**: User opens `/share/{token}` → sees file list with sizes → clicks download → `/download/{token}/{filename}` serves file via FileResponse

**GUI Flow**: Start button → launches ngrok → waits for tunnel URL → sets PUBLIC_BASE_URL → starts uvicorn → opens browser → polls for share links

## Development Commands

### Setup
```powershell
pip install -r requirements.txt
```

### Run Server (Development)
```powershell
uvicorn app.main:app --reload
```

### Run Server (With Custom Base URL)
```powershell
$env:PUBLIC_BASE_URL="https://your-ngrok-url.ngrok.io"; uvicorn app.main:app
```

### Run GUI Launcher (Windows)
```powershell
python localshare_gui.py
```

### Run Tests
```powershell
# Ensure server is running first
python verify.py
```

### Public Sharing via ngrok
```powershell
ngrok http 8000
# Copy the https URL and restart server with PUBLIC_BASE_URL set to that URL
```

## Testing

**Manual Testing**
1. Start server: `uvicorn app.main:app`
2. Open http://localhost:8000
3. Upload files, verify share link generation
4. Open share link, verify file list and download

**Automated Testing**
- `verify.py` contains integration tests for upload/download flows and error handling
- Tests require server running on localhost:8000
- Creates temporary test.txt file and cleans up after

## Security Considerations

- Basic directory traversal protection in download endpoint (checks for `..` in paths)
- No authentication (by design for Phase 1)
- Token isolation prevents cross-token file access
- Files stored locally in `shares/` directory (git-ignored)

## Implementation Notes

- Uses `aiofiles` for async file I/O with 1MB chunks for upload performance
- File size formatting in receiver UI (B/KB/MB conversion)
- Global `LAST_SHARE_LINK` variable in router.py for GUI polling (single-user assumption)
- GUI uses `taskkill` to forcefully clean up lingering processes on Windows
- No file expiry or auto-deletion in Phase 1 (planned for Phase 2)

## File Organization

- Python source: `app/` directory
- Uploaded files: `shares/` (git-ignored, created at runtime)
- Frontend assets: `app/static/` and `app/templates/`
- Documentation: `README.md` (user guide), `PRD.md` (product requirements)
