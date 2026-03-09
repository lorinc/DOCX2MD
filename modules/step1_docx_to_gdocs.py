"""
Step 1: DOCX to Native Google Docs Converter

Reads DOCX files from configured source folder and converts them to 
native Google Docs format in configured target folder.

Note: This step requires OAuth authentication (user account) because
service accounts don't have Drive storage quota needed for file conversion.
"""

from config import FOLDER_DOCX_SOURCES, FOLDER_NATIVE_GDOCS, AUTH_METHOD_STEP1
from .drive_utils import find_folder_by_name, list_docx_files_in_folder

def convert_docx_to_google_doc(drive_service, docx_file_id, docx_name, target_folder_id):
    """Convert a DOCX file to native Google Docs format and save to target folder."""
    print(f"\n⚙️  Converting '{docx_name}' to Google Docs format...")
    
    # Remove .docx extension if present
    clean_name = docx_name.replace('.docx', '').replace('.DOCX', '')
    
    # Use Drive API's copy feature with mimeType conversion
    file_metadata = {
        'name': clean_name,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [target_folder_id]
    }
    
    try:
        converted_file = drive_service.files().copy(
            fileId=docx_file_id,
            body=file_metadata,
            fields='id, name, mimeType, webViewLink'
        ).execute()
        
        print(f"✓ Converted to Google Doc: {converted_file['name']}")
        print(f"   ID: {converted_file['id']}")
        print(f"   Link: {converted_file.get('webViewLink', 'N/A')}")
        return converted_file
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        raise

def run_step1(drive_service, use_oauth=None):
    """
    Execute Step 1: Convert all DOCX files to native Google Docs.
    
    Args:
        drive_service: Google Drive API service
        use_oauth: If True, expects OAuth-authenticated service (has storage quota)
    
    Returns:
        tuple: (successful_count, failed_count)
    """
    print("=== STEP 1: DOCX to Native Google Docs ===\n")
    
    # Check authentication method
    if use_oauth is None:
        use_oauth = (AUTH_METHOD_STEP1 == 'oauth')
    
    if use_oauth:
        print("ℹ️  Using OAuth authentication (user account with storage quota)")
    else:
        print("⚠️  Using service account (may fail due to storage quota limits)")
    
    # Find source folder
    print(f"Looking for '{FOLDER_DOCX_SOURCES}' folder...")
    source_folder = find_folder_by_name(drive_service, FOLDER_DOCX_SOURCES)
    if not source_folder:
        print(f"❌ Error: '{FOLDER_DOCX_SOURCES}' folder not found in Google Drive")
        print("   Please create this folder and share it with the service account")
        return 0, 0
    
    print(f"✓ Found source folder: {source_folder['name']} (ID: {source_folder['id']})")
    
    # Find target folder
    print(f"\nLooking for '{FOLDER_NATIVE_GDOCS}' folder...")
    target_folder = find_folder_by_name(drive_service, FOLDER_NATIVE_GDOCS)
    if not target_folder:
        print(f"❌ Error: '{FOLDER_NATIVE_GDOCS}' folder not found in Google Drive")
        print("   Please create this folder and share it with the service account")
        return 0, 0
    
    print(f"✓ Found target folder: {target_folder['name']} (ID: {target_folder['id']})")
    
    # List DOCX files in source folder
    print(f"\nFetching DOCX files from '{FOLDER_DOCX_SOURCES}'...")
    docx_files = list_docx_files_in_folder(drive_service, source_folder['id'])
    
    if not docx_files:
        print(f"\n⚠️  No DOCX files found in '{FOLDER_DOCX_SOURCES}' folder")
        print("   Please upload DOCX files to this folder")
        return 0, 0
    
    print(f"\nFound {len(docx_files)} DOCX file(s):")
    for idx, file in enumerate(docx_files, 1):
        print(f"  {idx}. {file['name']}")
    
    # Process each DOCX file
    print(f"\n\n=== Processing {len(docx_files)} DOCX file(s) ===\n")
    
    successful = 0
    failed = 0
    
    for idx, docx_file in enumerate(docx_files, 1):
        print(f"\n[{idx}/{len(docx_files)}] Processing: {docx_file['name']}")
        print("="*60)
        
        try:
            convert_docx_to_google_doc(
                drive_service,
                docx_file['id'],
                docx_file['name'],
                target_folder['id']
            )
            successful += 1
        except Exception as e:
            print(f"❌ Failed to convert {docx_file['name']}: {e}")
            failed += 1
    
    # Summary
    print("\n\n" + "="*60)
    print("=== Step 1 Summary ===")
    print("="*60)
    print(f"✓ Successfully converted: {successful}")
    if failed > 0:
        print(f"❌ Failed: {failed}")
    print(f"\nAll converted files are now in '{FOLDER_NATIVE_GDOCS}' folder.")
    
    return successful, failed
