"""
OAuth Authentication Module

Handles Google API authentication using OAuth 2.0 for user accounts.
This is required for operations that need user storage quota (like DOCX conversion).
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import OAUTH_CREDENTIALS_FILE, OAUTH_TOKEN_FILE

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly'
]

def authenticate_oauth():
    """
    Authenticate using OAuth 2.0 and return credentials.
    
    This will:
    1. Check for existing token.json (saved credentials)
    2. If valid, use it
    3. If expired, refresh it
    4. If no token exists, run OAuth flow (opens browser)
    """
    creds = None
    
    # Check if we have saved credentials
    if os.path.exists(OAUTH_TOKEN_FILE):
        with open(OAUTH_TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired credentials
            print("Refreshing OAuth credentials...")
            creds.refresh(Request())
        else:
            # Run OAuth flow
            if not os.path.exists(OAUTH_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"\n❌ OAuth credentials file '{OAUTH_CREDENTIALS_FILE}' not found.\n\n"
                    "Please create OAuth credentials:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Select your project\n"
                    "3. Go to 'APIs & Services' > 'Credentials'\n"
                    "4. Click 'Create Credentials' > 'OAuth client ID'\n"
                    "5. Choose 'Desktop app' as application type\n"
                    "6. Download the JSON file\n"
                    "7. Save it as 'credentials.json' in this directory\n"
                )
            
            print("\n🔐 Starting OAuth authentication flow...")
            print("   A browser window will open for you to authorize the application")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next time
        with open(OAUTH_TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print("✓ OAuth credentials saved")
    
    return creds

def get_drive_service_oauth(creds=None):
    """Build and return Google Drive service using OAuth."""
    if creds is None:
        creds = authenticate_oauth()
    return build('drive', 'v3', credentials=creds)

def get_docs_service_oauth(creds=None):
    """Build and return Google Docs service using OAuth."""
    if creds is None:
        creds = authenticate_oauth()
    return build('docs', 'v1', credentials=creds)
