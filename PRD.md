# LocalShare – Product Requirements Document

## 1. Overview

### Product Name
**LocalShare**

### Problem
Sharing files via cloud services is:
- Slow for large files
- Requires trusting third parties
- Requires accounts or uploads
- Breaks privacy expectations

Users want a fast, temporary, direct way to share files from their own machine.

---

## 2. Goal

Enable a user to:
- Select files from their local machine via a web UI
- Generate a temporary share link
- Send that link to a receiver
- Allow receiver to download files without any setup

---

## 3. Non-Goals

- Long-term storage
- Multi-user accounts
- Syncing
- Collaboration
- Permanent hosting

This is temporary file transfer, not a cloud drive.

---

## 4. Personas

### Sender
- Runs the tool locally
- Selects files to share
- Gets a link

### Receiver
- Opens the link
- Downloads files
- No login, no install

---

## 5. User Flows

### 5.1 Sender Flow

1. Open `http://localhost:8000`
2. UI shows file picker and Share button
3. Select files
4. Click Share
5. Backend:
   - Generates token
   - Creates `D:/shares/{token}`
   - Stores files
6. Backend returns share link
7. Sender sends link

### 5.2 Receiver Flow

1. Open `https://<ngrok-url>/share/{token}`
2. See download page
3. Download files

---

## 6. Functional Requirements

### 6.1 Sender UI
- Multi-file picker
- Drag & drop optional
- Share button

### 6.2 Backend
- Accept multipart uploads
- Store files per token
- Generate unique token
- Serve file list
- Serve downloads

### 6.3 Receiver UI
- File list
- File size
- Download buttons
- No upload

---

## 7. API Design

| Endpoint | Method | Purpose |
|----------|--------|----------|
| `/` | GET | Sender UI |
| `/upload` | POST | Upload |
| `/share/{token}` | GET | Receiver UI |
| `/download/{token}/{filename}` | GET | Download |

---

## 8. Storage

- Base: `D:/shares/`
- Subfolder per token
- Files stored as-is

---

## 9. Security

- No auth (Phase 1)
- UUID tokens
- Token isolation
- Prevent directory traversal

---

## 10. Tech Stack

| Layer | Choice |
|------|--------|
Backend | Python + FastAPI |
Frontend | HTML/CSS |
Tunnel | ngrok |
Storage | Local FS |

---

## 11. Phase Plan

### Phase 1
- Upload
- Share link
- Download
- Token isolation

### Phase 2
- Expiry
- Auto-delete
- Passwords

### Phase 3
- One-time links
- Upload-only links
- UI polish

---

## 12. Success Criteria

- Share in <10 seconds
- Receiver needs no setup
- No accidental exposure

---

## 13. Risks

| Risk | Mitigation |
|------|------------|
Accidental exposure | Restrict to `D:/shares` |
Link leaks | Token entropy |
Disk full | Cleanup |

---

## 14. Future

- LAN mode
- QR sharing
- Mobile UI
- Desktop wrapper

---

## 15. Open Questions

- Upload-only?
- Rate limiting?
- Folder sharing?
