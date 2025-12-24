import tkinter as tk
import subprocess
import requests
import time
import os
import webbrowser
import signal

uvicorn_proc = None
ngrok_proc = None
polling_active = False

def start():
    global uvicorn_proc, ngrok_proc

    # 1. Clean stop first
    stop()
    
    # 1.1 Force kill any lingering processes to be absolutely sure
    print("INFO: Enforcing clean slate...")
    subprocess.run(["taskkill", "/F", "/IM", "uvicorn.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    status.set("Starting ngrok...")
    print("INFO: Starting ngrok process...")
    
    # 2. Start Ngrok
    ngrok_proc = subprocess.Popen(
        ["ngrok", "http", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    status.set("Waiting for tunnel URL...")
    
    # 3. Wait for URL
    url = None
    for i in range(30):
        try:
            r = requests.get("http://127.0.0.1:4040/api/tunnels").json()
            tunnels = r.get("tunnels", [])
            if tunnels:
                url = tunnels[0]["public_url"]
                print(f"INFO: Tunnel found: {url}")
                break
        except Exception as e:
            pass
        time.sleep(1)

    if not url:
        status.set("Failed to get tunnel URL")
        print("ERROR: Failed to obtain ngrok URL after 30 seconds.")
        stop() # Cleanup ngrok
        return

    share_url.set(url)
    status.set("Starting server...")

    # 4. Start Uvicorn ONCE with the URL
    env = os.environ.copy()
    env["PUBLIC_BASE_URL"] = url
    
    print(f"INFO: Starting Uvicorn with PUBLIC_BASE_URL={url}")
    
    uvicorn_proc = subprocess.Popen(
        ["uvicorn", "app.main:app"], # No --reload
        env=env,
        # We let uvicorn print to stdout so we can see its logs in the console
    )

    status.set("Running")
    
    # Optional: Open browser to the localhost address to show the UI
    # The UI will use the PUBLIC_BASE_URL for generating links
    time.sleep(2) # Give uvicorn a moment to start
    webbrowser.open("http://localhost:8000")
    
    # Start polling for share link updates
    start_polling()


def poll_share_link():
    """Poll the backend for the last generated share link."""
    global polling_active
    
    if not polling_active:
        return
    
    try:
        resp = requests.get("http://localhost:8000/last-share", timeout=1)
        if resp.status_code == 200:
            data = resp.json()
            link = data.get("link")
            
            if link:
                # Update GUI with full share link
                current_link = share_url.get()
                if current_link != link:
                    share_url.set(link)
                    print(f"INFO: GUI updated with full share link: {link}")
                    # Stop polling once we have a link
                    polling_active = False
                    return
    except Exception as e:
        # Silently ignore errors during polling
        pass
    
    # Continue polling if still active
    if polling_active:
        root.after(1500, poll_share_link)  # Poll every 1.5 seconds


def start_polling():
    """Start polling for share link updates."""
    global polling_active
    polling_active = True
    print("INFO: Started polling for share link updates")
    root.after(1000, poll_share_link)  # Start after 1 second


def stop_polling():
    """Stop polling for share link updates."""
    global polling_active
    polling_active = False


def stop():
    global uvicorn_proc, ngrok_proc
    
    # Stop polling
    stop_polling()

    if uvicorn_proc:
        print("INFO: Killing uvicorn...")
        uvicorn_proc.kill()
        uvicorn_proc = None
    
    if ngrok_proc:
        print("INFO: Killing ngrok...")
        ngrok_proc.kill()
        ngrok_proc = None

    status.set("Stopped")
    share_url.set("")


def copy_link():
    root.clipboard_clear()
    root.clipboard_append(share_url.get())


root = tk.Tk()
root.title("LocalShare")
root.geometry("400x250")

status = tk.StringVar(value="Stopped")
share_url = tk.StringVar(value="")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill="both", expand=True)

tk.Label(frame, text="Status:").pack(anchor="w")
tk.Label(frame, textvariable=status, fg="blue").pack(anchor="w", pady=(0, 10))

tk.Button(frame, text="Start Sharing", command=start, bg="#e1effe").pack(fill="x", pady=5)
tk.Button(frame, text="Stop Sharing", command=stop, bg="#fde8e8").pack(fill="x", pady=5)

tk.Label(frame, text="Public URL:").pack(anchor="w", pady=(15, 0))
entry = tk.Entry(frame, textvariable=share_url, state="readonly")
entry.pack(fill="x", pady=5)

tk.Button(frame, text="Copy Link", command=copy_link).pack(fill="x")

# Clean cleanup on window close
def on_closing():
    stop()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
