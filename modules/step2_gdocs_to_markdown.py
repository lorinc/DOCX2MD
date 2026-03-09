"""
Step 2: Google Docs to Baseline Markdown Converter

Reads native Google Docs from configured source folder and exports them
to baseline Markdown format in configured target folder.
"""

import io
import os
import json
from datetime import datetime
from googleapiclient.http import MediaIoBaseUpload
from config import FOLDER_NATIVE_GDOCS, FOLDER_BASELINE_MARKDOWNS, FOLDER_RUNTIME_LOGS
from .drive_utils import find_folder_by_name, list_google_docs_in_folder

def export_to_markdown(drive_service, file_id):
    """Export Google Doc to Markdown format."""
    exported_content = drive_service.files().export(
        fileId=file_id,
        mimeType='text/markdown'
    ).execute()
    
    return exported_content.decode('utf-8')

def extract_text_styles(docs_service, file_id):
    """Extract text content and font sizes from Google Doc."""
    doc_content = docs_service.documents().get(documentId=file_id).execute()
    
    content_summary = []
    for item in doc_content.get('body', {}).get('content', []):
        if 'paragraph' in item:
            text = "".join([
                e.get('textRun', {}).get('content', '') 
                for e in item['paragraph'].get('elements', [])
            ])
            
            size = 11
            if item['paragraph'].get('elements'):
                first_element = item['paragraph']['elements'][0]
                size_data = first_element.get('textRun', {}).get('textStyle', {}).get('fontSize', {})
                size = size_data.get('magnitude', 11)
            
            if text.strip():
                content_summary.append({"text": text.strip(), "size": size})
    
    return content_summary

def save_markdown_to_drive(drive_service, content, filename, parent_folder_id):
    """Save Markdown content to Google Drive as a text file."""
    file_metadata = {
        'name': filename,
        'mimeType': 'text/markdown',
        'parents': [parent_folder_id]
    }
    
    content_bytes = content.encode('utf-8')
    media_body = MediaIoBaseUpload(
        io.BytesIO(content_bytes),
        mimetype='text/markdown',
        resumable=True
    )
    
    new_file = drive_service.files().create(
        body=file_metadata,
        media_body=media_body,
        fields='id, name, webViewLink'
    ).execute()
    
    return new_file

def save_log_to_drive(drive_service, content, filename, parent_folder_id, mime_type='text/plain'):
    """Save log content to Google Drive."""
    file_metadata = {
        'name': filename,
        'mimeType': mime_type,
        'parents': [parent_folder_id]
    }
    
    if isinstance(content, dict) or isinstance(content, list):
        content_bytes = json.dumps(content, indent=2, ensure_ascii=False).encode('utf-8')
        mime_type = 'application/json'
        file_metadata['mimeType'] = mime_type
    else:
        content_bytes = content.encode('utf-8')
    
    media_body = MediaIoBaseUpload(
        io.BytesIO(content_bytes),
        mimetype=mime_type,
        resumable=True
    )
    
    new_file = drive_service.files().create(
        body=file_metadata,
        media_body=media_body,
        fields='id, name'
    ).execute()
    
    return new_file

def save_markdown_locally(content, filename, output_dir=None):
    """Save Markdown content locally."""
    if output_dir is None:
        output_dir = FOLDER_BASELINE_MARKDOWNS
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def run_step2(drive_service, docs_service, run_id=None):
    """
    Execute Step 2: Convert Google Docs to baseline Markdown.
    
    Args:
        drive_service: Google Drive API service
        docs_service: Google Docs API service
        run_id: Optional run ID to tag output files (if None, processes all files)
        
    Returns:
        tuple: (successful_count, failed_count)
    """
    print("=== STEP 2: Google Docs to Baseline Markdown ===\n")
    
    if run_id:
        print(f"🆔 Run ID: {run_id}")
        print("   Output files will be tagged with this run ID\n")
    
    # Find source folder
    print(f"Looking for '{FOLDER_NATIVE_GDOCS}' folder...")
    source_folder = find_folder_by_name(drive_service, FOLDER_NATIVE_GDOCS)
    if not source_folder:
        print(f"❌ Error: '{FOLDER_NATIVE_GDOCS}' folder not found in Google Drive")
        return 0, 0
    
    print(f"✓ Found source folder: {source_folder['name']} (ID: {source_folder['id']})")
    
    # Find target folder
    print(f"\nLooking for '{FOLDER_BASELINE_MARKDOWNS}' folder...")
    target_folder = find_folder_by_name(drive_service, FOLDER_BASELINE_MARKDOWNS)
    if not target_folder:
        print(f"❌ Error: '{FOLDER_BASELINE_MARKDOWNS}' folder not found in Google Drive")
        print("   Please create this folder and share it with the service account")
        return 0, 0
    
    print(f"✓ Found target folder: {target_folder['name']} (ID: {target_folder['id']})")
    
    # Find runtime logs folder
    print(f"\nLooking for '{FOLDER_RUNTIME_LOGS}' folder...")
    logs_folder = find_folder_by_name(drive_service, FOLDER_RUNTIME_LOGS)
    if not logs_folder:
        print(f"⚠️  Warning: '{FOLDER_RUNTIME_LOGS}' folder not found")
        print("   Intermediary files will not be logged")
        logs_folder_id = None
    else:
        print(f"✓ Found logs folder: {logs_folder['name']} (ID: {logs_folder['id']})")
        logs_folder_id = logs_folder['id']
    
    # List Google Docs in source folder
    print(f"\nFetching Google Docs from '{FOLDER_NATIVE_GDOCS}'...")
    gdocs = list_google_docs_in_folder(drive_service, source_folder['id'])
    
    if not gdocs:
        print(f"\n⚠️  No Google Docs found in '{FOLDER_NATIVE_GDOCS}' folder")
        return 0, 0
    
    print(f"\nFound {len(gdocs)} Google Doc(s):")
    for idx, doc in enumerate(gdocs, 1):
        print(f"  {idx}. {doc['name']}")
    
    # Process each Google Doc
    print(f"\n\n=== Processing {len(gdocs)} Google Doc(s) ===\n")
    
    successful = 0
    failed = 0
    
    for idx, gdoc in enumerate(gdocs, 1):
        print(f"\n[{idx}/{len(gdocs)}] Processing: {gdoc['name']}")
        print("="*60)
        
        try:
            # Export to Markdown
            print("  Exporting to Markdown...")
            markdown_content = export_to_markdown(drive_service, gdoc['id'])
            print(f"  ✓ Exported {len(markdown_content)} characters")
            
            # Extract text styles
            print("  Extracting text styles...")
            text_styles = extract_text_styles(docs_service, gdoc['id'])
            print(f"  ✓ Extracted {len(text_styles)} text elements")
            
            # Save intermediary files to logs folder
            if logs_folder_id and run_id:
                log_prefix = f"{run_id}_{gdoc['name']}"
                
                # Save raw markdown
                save_log_to_drive(
                    drive_service,
                    markdown_content,
                    f"{log_prefix}_raw_markdown.md",
                    logs_folder_id,
                    'text/markdown'
                )
                
                # Save text styles
                save_log_to_drive(
                    drive_service,
                    text_styles,
                    f"{log_prefix}_text_styles.json",
                    logs_folder_id,
                    'application/json'
                )
                print(f"  ✓ Saved intermediary files to logs folder")
            
            # Generate filename with run_id prefix
            if run_id:
                filename = f"{run_id}_{gdoc['name']}.md"
            else:
                filename = f"{gdoc['name']}.md"
            
            # Save to Drive
            new_file = save_markdown_to_drive(
                drive_service,
                markdown_content,
                filename,
                target_folder['id']
            )
            print(f"  ✓ Saved to Drive: {new_file['name']}")
            print(f"     Link: {new_file.get('webViewLink', 'N/A')}")
            
            successful += 1
        except Exception as e:
            print(f"❌ Failed to convert {gdoc['name']}: {e}")
            failed += 1
    
    # Summary
    print("\n\n" + "="*60)
    print("=== Step 2 Summary ===")
    print("="*60)
    print(f"✓ Successfully converted: {successful}")
    if failed > 0:
        print(f"❌ Failed: {failed}")
    
    print(f"\nBaseline Markdown files saved to '{FOLDER_BASELINE_MARKDOWNS}' folder in Google Drive.")
    
    return successful, failed
