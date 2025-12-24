# LocalShare

A fast, private, and temporary file sharing tool that runs directly from your machine.

## Features

-   **Direct Sharing**: Share files from your local machine via a temporary web server.
-   **No Accounts**: No login required for sender or receiver.
-   **Privacy Focused**: Files are stored locally and only accessible via a unique token link.
-   **GUI Launcher**: Easy-to-use graphical interface to manage the server and public sharing.
-   **Expiration Control**: Set automatic expiration times for your links.
-   **Revocation**: Manually revoke links at any time to stop access immediately.
-   **Zip Download**: Receivers can download all shared files as a single ZIP archive.
-   **Automatic Cleanup**: Expired and revoked shares are automatically deleted from your disk.

## Setup

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application**

    **Option A: GUI Launcher (Recommended)**
    This manages the web server and the ngrok tunnel automatically.
    ```bash
    python localshare_gui.py
    ```

    **Option B: Command Line**
    Run the server manually.
    ```bash
    uvicorn app.main:app
    ```

3.  **Access the App**
    -   If using the GUI, it will open the browser automatically.
    -   Otherwise, open `http://localhost:8000` in your browser.

## Usage

### Sending Files
1.  Open the application.
2.  Drag and drop files or use the "Browse Files" button.
3.  **Choose Expiration**:
    -   **Manual revoking**: The link stays active until you revoke it or shut down the app.
    -   **Revoke automatically**: Set a timer (in minutes) for the link to expire.
4.  Click "Share Files".
5.  Copy the generated link to send to the receiver.
6.  **Manage**: You can click "Revoke Link Now" on the result screen to immediately disable the link.

### Receiving Files
1.  Open the shared link (e.g., `https://.../share/<token>`).
2.  View the list of files and their sizes.
3.  Click "Download" next to specific files or "Download All" to get a ZIP of everything.

## Public Sharing
The GUI launcher automatically integrates with **ngrok** to provide a public URL.
-   When you click "Start Sharing" in the GUI, it launches ngrok and updates the share links to use the public address.
-   The public URL is displayed in the GUI for easy copying.

## Development

### Project Structure

-   `localshare_gui.py`: Tkinter GUI launcher.
-   `app/main.py`: FastAPI application entry point.
-   `app/router.py`: API routes, logic, and cleanup tasks.
-   `app/templates/`: HTML templates (Jinja2).
-   `app/static/`: CSS and static assets.
-   `shares/`: Directory where uploaded files are temporarily stored.
-   `verify.py`: Integration test script.

### Running Tests
To run the integration tests (requires the server to be running on port 8000):
```bash
python verify.py
```