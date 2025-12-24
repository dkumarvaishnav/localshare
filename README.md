# LocalShare

A fast, private, and temporary file sharing tool that runs directly from your machine.

## Features

-   **Direct Sharing**: Share files from your local machine via a temporary web server.
-   **No Accounts**: No login required for sender or receiver.
-   **Privacy Focused**: Files are stored locally and only accessible via a unique token link.
-   **Simple UI**: Drag & drop interface for sending, simple download list for receiving.

## Setup

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Server**
    ```bash
    uvicorn app.main:app
    ```

3.  **Access the App**
    -   Open `http://localhost:8000` in your browser.

## Usage

### Sending Files
1.  Go to the home page (`http://localhost:8000`).
2.  Drag and drop files or browse to select them.
3.  Click "Share Files".
4.  Copy the generated link.

### Receiving Files
1.  Open the shared link (e.g., `http://localhost:8000/share/<token>`).
2.  Click "Download" next to the desired file.

## Public Sharing (Optional)
To share with someone outside your local network, you can use a tunneling service like [ngrok](https://ngrok.com/).

```bash
ngrok http 8000
```

Then share the https URL provided by ngrok.

## Project Structure

-   `app/main.py`: FastAPI application entry point.
-   `app/router.py`: API routes and logic.
-   `app/templates/`: HTML templates (Jinja2).
-   `app/static/`: CSS and static assets.
-   `shares/`: Directory where uploaded files are temporarily stored.
