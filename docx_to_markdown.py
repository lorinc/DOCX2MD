#!/usr/bin/env python3
"""
Google Docs to Markdown Converter with AI Cleanup

This script allows users to:
1. Select a Google Doc file from Google Drive
2. Export it to Markdown format
3. Extract text styling information (font sizes)
4. Use Gemini AI to fix header hierarchy and improve consistency
5. Save the cleaned Markdown file back to the same folder with a timestamp
"""

import os
import io
import json
import re
import sys
import requests
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Scopes required for Google Drive and Docs APIs
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly'
]

def authenticate():
    """Authenticate using service account and return credentials for Google APIs."""
    service_account_file = 'service-account.json'
    
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

def list_google_docs(drive_service, max_results=20):
    """List Google Docs files in the user's Drive."""
    query = "mimeType='application/vnd.google-apps.document' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
    
    results = drive_service.files().list(
        q=query,
        pageSize=max_results,
        fields="files(id, name, mimeType, parents)"
    ).execute()
    
    return results.get('files', [])

def print_files_list(files):
    """Display available files."""
    if not files:
        print("No Google Docs or .docx files found in your Drive.")
        return
    
    print("\n=== Available Documents ===")
    for idx, file in enumerate(files, 1):
        file_type = "Google Doc" if file['mimeType'] == 'application/vnd.google-apps.document' else "DOCX"
        print(f"{idx}. {file['name']} (ID: {file['id']}) ({file_type})")
    print(f"\nTo process a file, run: python docx_to_markdown.py <file_id>")

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

def convert_docx_to_google_doc(drive_service, docx_file_id, docx_name):
    """Convert a DOCX file to native Google Docs format using Drive API copy."""
    print(f"\n⚙️  Converting DOCX to Google Docs format...")
    print(f"   Note: This creates a temporary converted copy in your Drive")
    
    # Use Drive API's copy feature with mimeType conversion
    file_metadata = {
        'name': f"{docx_name} (Temp Conversion)",
        'mimeType': 'application/vnd.google-apps.document'
    }
    
    try:
        converted_file = drive_service.files().copy(
            fileId=docx_file_id,
            body=file_metadata,
            fields='id, name, mimeType'
        ).execute()
        
        print(f"✓ Converted to Google Doc: {converted_file['name']} (ID: {converted_file['id']})")
        print(f"   You can delete this temporary file after processing if needed")
        return converted_file
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        print(f"\n💡 Workaround: Manually convert the DOCX to Google Docs format:")
        print(f"   1. Open the DOCX file in Google Drive")
        print(f"   2. File → Save as Google Docs")
        print(f"   3. Use the new Google Doc's ID with this script")
        raise

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

def strip_image_data(markdown):
    """Remove base64 image data from markdown to reduce prompt size."""
    # Replace data:image/... base64 strings with placeholder
    import re
    pattern = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+'
    cleaned = re.sub(pattern, '[IMAGE_DATA_REMOVED]', markdown)
    return cleaned

def clean_markdown_with_ai(api_key, raw_markdown, text_styles):
    """Use Gemini AI to fix header hierarchy and improve consistency."""
    prompt = f"""You are an expert document formatter. Given a raw Markdown document and text styling information, your task is to:

1. Fix header hierarchy based on font sizes (larger sizes = higher-level headers)
2. Ensure consistent header formatting throughout the document
3. Fix any obvious typos or formatting inconsistencies
4. Maintain all original content and meaning
5. Preserve tables, lists, and other formatting

Raw Markdown Document:
```markdown
{raw_markdown}
```

Text Styling Information (text and font size):
```json
{json.dumps(text_styles, indent=2)}
```

Output only the cleaned Markdown document with proper headers. Do not add explanations or comments."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    # Check for truncation
    candidate = result['candidates'][0]
    finish_reason = candidate.get('finishReason', 'UNKNOWN')
    
    if finish_reason not in ['STOP', 'UNKNOWN']:
        print(f"\n⚠️  WARNING: Gemini response may be truncated!")
        print(f"   Finish reason: {finish_reason}")
        print(f"   This usually means the output was cut off due to length limits")
    
    return result['candidates'][0]['content']['parts'][0]['text']

def generate_filename(original_title):
    """Generate a timestamped filename."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cleaned_title = re.sub(r'[^a-zA-Z0-9\s\-_]', '', original_title)
    cleaned_title = cleaned_title.replace(' ', '_').lower()
    
    return f"{cleaned_title}_{timestamp}.md"

def save_to_drive(drive_service, content, filename, parent_folder_id):
    """Save the cleaned Markdown file to Google Drive."""
    file_metadata = {
        'name': filename,
        'mimeType': 'text/markdown',
        'parents': [parent_folder_id] if parent_folder_id else []
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

def save_locally(content, filename, output_dir='output'):
    """Save the cleaned Markdown file locally."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def save_artifact(content, filename, artifacts_dir):
    """Save intermediate artifact for debugging."""
    os.makedirs(artifacts_dir, exist_ok=True)
    filepath = os.path.join(artifacts_dir, filename)
    
    if isinstance(content, str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    
    return filepath

def load_api_key():
    """Load Gemini API key from .config file or environment variable."""
    config_path = os.path.join(os.path.dirname(__file__), '.config')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    return line.strip().split('=', 1)[1]
    
    return os.getenv('GEMINI_API_KEY')

def main():
    """Main execution flow."""
    print("=== Google Docs to Markdown Converter ===\n")
    
    # Check for Gemini API key
    gemini_api_key = load_api_key()
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY not found.")
        print("Please set it in .config file or as environment variable.")
        return
    
    # Authenticate
    print("Authenticating with Google...")
    creds = authenticate()
    
    # Build services
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    
    # Check for command-line argument
    if len(sys.argv) < 2:
        print("\nFetching your documents...")
        files = list_google_docs(drive_service)
        print_files_list(files)
        print("\n💡 Usage: python docx_to_markdown.py <file_id>")
        print("   Or:     python docx_to_markdown.py --list  (to see this list again)")
        return
    
    file_id = sys.argv[1]
    
    if file_id == '--list':
        print("\nFetching your documents...")
        files = list_google_docs(drive_service)
        print_files_list(files)
        return
    
    # Get file metadata
    selected_file = get_file_by_id(drive_service, file_id)
    if not selected_file:
        return
    
    # Check if it's a DOCX file and convert if needed
    if selected_file['mimeType'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        print(f"\n❌ Cannot process DOCX file directly: {selected_file['name']}")
        print(f"\n📋 DOCX files must be converted to Google Docs format first.")
        print(f"\nTo convert manually:")
        print(f"   1. Open the file in Google Drive web interface")
        print(f"   2. Click: File → Save as Google Docs")
        print(f"   3. Copy the new Google Doc's ID from the URL")
        print(f"   4. Run this script with the new ID")
        print(f"\nAlternatively, if you have OAuth credentials (not service account):")
        print(f"   The script can auto-convert DOCX files.")
        return
    
    file_name = selected_file['name']
    parent_folder_id = selected_file.get('parents', [None])[0]
    
    # Create timestamped artifacts directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    artifacts_dir = os.path.join('artifacts', f"{timestamp}_{file_id[:10]}")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print(f"\n✓ Processing: {file_name}")
    print(f"   Artifacts will be saved to: {artifacts_dir}")
    
    # Export to Markdown
    print("\n[1/4] Exporting to Markdown...")
    raw_markdown = export_to_markdown(drive_service, file_id)
    print(f"✓ Exported {len(raw_markdown)} characters ({len(raw_markdown.encode('utf-8'))} bytes)")
    print(f"   First 200 chars: {raw_markdown[:200]}")
    print(f"   Last 200 chars: {raw_markdown[-200:]}")
    
    # Save raw markdown
    save_artifact(raw_markdown, '1_raw_markdown.md', artifacts_dir)
    print(f"   Saved: {artifacts_dir}/1_raw_markdown.md")
    
    # Extract text styles
    print("\n[2/4] Extracting text styling information...")
    text_styles = extract_text_styles(docs_service, file_id)
    print(f"✓ Extracted {len(text_styles)} text elements")
    print(f"   Total text in styles: {sum(len(s['text']) for s in text_styles)} characters")
    
    # Save text styles
    save_artifact(text_styles, '2_text_styles.json', artifacts_dir)
    print(f"   Saved: {artifacts_dir}/2_text_styles.json")
    
    # Clean with AI
    print("\n[3/4] Cleaning with Gemini AI...")
    
    # Strip image data before processing
    markdown_for_ai = strip_image_data(raw_markdown)
    size_reduction = len(raw_markdown) - len(markdown_for_ai)
    
    print(f"   Original markdown: {len(raw_markdown):,} chars")
    if size_reduction > 0:
        print(f"   Stripped {size_reduction:,} chars of base64 image data")
        print(f"   Sending to Gemini: {len(markdown_for_ai):,} chars + {len(text_styles)} style elements")
    else:
        print(f"   Sending to Gemini: {len(markdown_for_ai):,} chars + {len(text_styles)} style elements")
    
    # Check if document is too large for reliable AI processing
    if len(markdown_for_ai) > 100000:
        print(f"\n⚠️  Document is very large ({len(markdown_for_ai):,} chars)")
        print(f"   AI processing may truncate content. Using raw markdown instead.")
        cleaned_markdown = raw_markdown
        save_artifact({"warning": "Document too large for AI processing", "used_raw": True}, '3_ai_skipped.json', artifacts_dir)
    else:
        cleaned_markdown = clean_markdown_with_ai(gemini_api_key, markdown_for_ai, text_styles)
        print(f"✓ AI cleanup complete")
        print(f"   Received from Gemini: {len(cleaned_markdown)} characters ({len(cleaned_markdown.encode('utf-8'))} bytes)")
        print(f"   First 200 chars: {cleaned_markdown[:200]}")
        print(f"   Last 200 chars: {cleaned_markdown[-200:]}")
        
        # Save cleaned markdown
        save_artifact(cleaned_markdown, '3_cleaned_markdown.md', artifacts_dir)
        print(f"   Saved: {artifacts_dir}/3_cleaned_markdown.md")
    
    # Save output
    print("\n[4/4] Saving output...")
    output_filename = generate_filename(file_name)
    
    try:
        new_file = save_to_drive(drive_service, cleaned_markdown, output_filename, parent_folder_id)
        print(f"\n✅ Success! Saved to Google Drive")
        print(f"   File: {new_file['name']}")
        print(f"   ID: {new_file['id']}")
        print(f"   Link: {new_file.get('webViewLink', 'N/A')}")
    except Exception as e:
        if 'storageQuotaExceeded' in str(e) or 'Service Accounts do not have storage quota' in str(e):
            print(f"\n⚠️  Cannot save to Drive (service accounts don't have storage quota)")
            print(f"   Saving locally instead...")
            filepath = save_locally(cleaned_markdown, output_filename)
            print(f"\n✅ Success! Saved locally")
            print(f"   File: {filepath}")
        else:
            raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
