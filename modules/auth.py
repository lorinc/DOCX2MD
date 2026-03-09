"""
Authentication Module

Handles Google API authentication using service account credentials.
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import SERVICE_ACCOUNT_FILE

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly'
]

def authenticate():
    """Authenticate using service account and return credentials for Google APIs."""
    service_account_file = SERVICE_ACCOUNT_FILE
    
    if not os.path.exists(service_account_file):
        raise FileNotFoundError(
            f"\n❌ Service account file '{service_account_file}' not found.\n\n"
            "Please create a service account and download the JSON key file:\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Select your project\n"
            "3. Go to 'IAM & Admin' > 'Service Accounts'\n"
            "4. Create a service account (or use existing)\n"
            "5. Create a JSON key and download it\n"
            "6. Save it as 'service-account.json' in this directory\n"
            "7. Share your Google Drive files/folders with the service account email"
        )
    
    creds = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )
    
    return creds

def get_drive_service(creds=None):
    """Build and return Google Drive service."""
    if creds is None:
        creds = authenticate()
    return build('drive', 'v3', credentials=creds)

def get_docs_service(creds=None):
    """Build and return Google Docs service."""
    if creds is None:
        creds = authenticate()
    return build('docs', 'v1', credentials=creds)
