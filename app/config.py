import os

# Base directory for storing shares
# In a real deployed environment this might be D:/shares
# For development/MVP we use a local directory
UPLOAD_DIR = os.getenv("LOCALSHARE_UPLOAD_DIR", "shares")

