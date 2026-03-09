"""
Google Drive Utilities

Helper functions for interacting with Google Drive folders and files.
"""

def find_folder_by_name(drive_service, folder_name):
    """Find a folder by name in Google Drive."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    
    results = drive_service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()
    
    folders = results.get('files', [])
    return folders[0] if folders else None

def list_files_in_folder(drive_service, folder_id, mime_type=None):
    """List files in a specific folder, optionally filtered by MIME type."""
    if mime_type:
        query = f"'{folder_id}' in parents and mimeType='{mime_type}' and trashed=false"
    else:
        query = f"'{folder_id}' in parents and trashed=false"
    
    results = drive_service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()
    
    return results.get('files', [])

def list_docx_files_in_folder(drive_service, folder_id):
    """List DOCX files in a specific folder."""
    return list_files_in_folder(
        drive_service, 
        folder_id, 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

def list_google_docs_in_folder(drive_service, folder_id):
    """List Google Docs in a specific folder."""
    return list_files_in_folder(
        drive_service,
        folder_id,
        'application/vnd.google-apps.document'
    )

def get_file_by_id(drive_service, file_id):
    """Get file metadata by ID."""
    try:
        file = drive_service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, parents'
        ).execute()
        return file
    except Exception as e:
        print(f"❌ Error: Could not find file with ID '{file_id}'")
        print(f"   {str(e)}")
        return None
