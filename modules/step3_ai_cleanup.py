"""
Step 3: AI-Powered Markdown Cleanup

Reads baseline Markdown files from configured source folder,
applies AI cleanup for better RAG accessibility, and saves to
configured target folder.
"""

import os
import re
import json
import requests
from datetime import datetime
from config import (
    FOLDER_BASELINE_MARKDOWNS,
    FOLDER_RAG_MARKDOWNS,
    FOLDER_RUNTIME_LOGS,
    FOLDER_ARTIFACTS,
    MAX_DOCUMENT_SIZE_FOR_AI,
    GEMINI_MODEL,
    CONFIG_FILE
)

def load_api_key():
    """Load Gemini API key from .config file or environment variable."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), CONFIG_FILE)
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    return line.strip().split('=', 1)[1]
    
    return os.getenv('GEMINI_API_KEY')

def strip_image_data(markdown):
    """Remove base64 image data and image markdown syntax entirely."""
    # Remove entire image markdown with base64 data: ![alt](data:image/...)
    pattern = r'!\[([^\]]*)\]\(data:image/[^;]+;base64,[A-Za-z0-9+/=]+\)'
    cleaned = re.sub(pattern, '', markdown)
    
    # Also remove any remaining standalone base64 data
    pattern2 = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+'
    cleaned = re.sub(pattern2, '', cleaned)
    
    return cleaned

def contains_image_data(text):
    """Check if text contains any base64 image data."""
    # Check for base64 image patterns
    if 'data:image/' in text:
        return True
    if ';base64,' in text:
        return True
    # Check for suspiciously long base64-like strings (>1000 chars of base64 characters)
    import re
    base64_pattern = r'[A-Za-z0-9+/]{1000,}={0,2}'
    if re.search(base64_pattern, text):
        return True
    return False

def clean_markdown_with_ai(api_key, raw_markdown, text_styles=None):
    """Use Gemini AI to fix header hierarchy and improve consistency."""
    
    # SAFETY CHECK: Verify no image data is present
    if contains_image_data(raw_markdown):
        raise ValueError("SAFETY GATE: Image data detected in markdown before sending to Gemini API. Aborting to prevent credit waste.")
    
    style_info = ""
    if text_styles:
        style_info = f"""
Text Styling Information (text and font size):
```json
{json.dumps(text_styles, indent=2)}
```
"""
    
    prompt = f"""You are an expert document formatter optimizing documents for RAG (Retrieval-Augmented Generation) systems.

Your task is to:
1. Fix header hierarchy based on font sizes (larger sizes = higher-level headers)
2. Ensure consistent header formatting throughout the document
3. Improve document structure for better semantic chunking
4. Fix any obvious typos or formatting inconsistencies
5. Maintain all original content and meaning
6. Preserve tables, lists, and other formatting
7. Add clear section breaks where appropriate
8. Ensure headers are descriptive and searchable

Raw Markdown Document:
```markdown
{raw_markdown}
```
{style_info}
Output only the cleaned Markdown document with proper headers. Do not add explanations or comments."""

    # SAFETY CHECK: Validate prompt size before sending
    prompt_size = len(prompt)
    if prompt_size > 500000:  # 500K character hard limit
        raise ValueError(f"SAFETY GATE: Prompt too large ({prompt_size:,} chars). Possible image data leak. Aborting API call.")
    
    # Log the actual size being sent
    print(f"      → Prompt size: {prompt_size:,} characters")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    
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

def read_markdown_from_drive(drive_service, file_id):
    """Read markdown file content from Google Drive."""
    import io
    from googleapiclient.http import MediaIoBaseDownload
    
    request = drive_service.files().get_media(fileId=file_id)
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    return file_content.getvalue().decode('utf-8')

def save_markdown_to_drive(drive_service, content, filename, parent_folder_id):
    """Save Markdown content to Google Drive."""
    import io
    from googleapiclient.http import MediaIoBaseUpload
    
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
    import io
    from googleapiclient.http import MediaIoBaseUpload
    
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

def save_artifact(content, filename, artifacts_subdir):
    """Save intermediate artifact for debugging (local only)."""
    os.makedirs(artifacts_subdir, exist_ok=True)
    filepath = os.path.join(artifacts_subdir, filename)
    
    if isinstance(content, str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    
    return filepath

def run_step3(drive_service, docs_service=None, run_id=None):
    """
    Execute Step 3: Apply AI cleanup to baseline Markdown files.
    
    Args:
        drive_service: Google Drive API service (required)
        docs_service: Google Docs API service (optional, for extracting text styles)
        run_id: Optional run ID to filter input files (if None, processes all files)
        
    Returns:
        tuple: (successful_count, failed_count)
    """
    print("=== STEP 3: AI Cleanup for RAG Accessibility ===\n")
    
    if run_id:
        print(f"🆔 Run ID: {run_id}")
        print(f"   Only processing files from this run\n")
    
    # Check for API key
    api_key = load_api_key()
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found")
        print("   Please set it in .config file or as environment variable")
        return 0, 0
    
    print("✓ Gemini API key loaded")
    
    # Find source folder
    print(f"\nLooking for '{FOLDER_BASELINE_MARKDOWNS}' folder...")
    from .drive_utils import find_folder_by_name, list_files_in_folder
    
    source_folder = find_folder_by_name(drive_service, FOLDER_BASELINE_MARKDOWNS)
    if not source_folder:
        print(f"❌ Error: '{FOLDER_BASELINE_MARKDOWNS}' folder not found in Google Drive")
        return 0, 0
    
    print(f"✓ Found source folder: {source_folder['name']} (ID: {source_folder['id']})")
    
    # Find target folder
    print(f"\nLooking for '{FOLDER_RAG_MARKDOWNS}' folder...")
    target_folder = find_folder_by_name(drive_service, FOLDER_RAG_MARKDOWNS)
    if not target_folder:
        print(f"❌ Error: '{FOLDER_RAG_MARKDOWNS}' folder not found in Google Drive")
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
    
    # List Markdown files in source folder
    print(f"\nFetching Markdown files from '{FOLDER_BASELINE_MARKDOWNS}'...")
    all_md_files = list_files_in_folder(drive_service, source_folder['id'], 'text/markdown')
    
    # Filter by run_id if provided
    if run_id:
        md_files = [f for f in all_md_files if f['name'].startswith(run_id)]
        print(f"   Filtered to files from run: {run_id}")
    else:
        md_files = all_md_files
    
    if not md_files:
        if run_id:
            print(f"\n⚠️  No Markdown files found for run ID '{run_id}' in '{FOLDER_BASELINE_MARKDOWNS}' folder")
        else:
            print(f"\n⚠️  No Markdown files found in '{FOLDER_BASELINE_MARKDOWNS}' folder")
        return 0, 0
    
    print(f"\nFound {len(md_files)} Markdown file(s) to process:")
    for idx, file in enumerate(md_files, 1):
        print(f"  {idx}. {file['name']}")
    
    # Create artifacts directory
    if run_id:
        artifacts_dir = os.path.join(FOLDER_ARTIFACTS, f'step3_{run_id}')
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        artifacts_dir = os.path.join(FOLDER_ARTIFACTS, f'step3_{timestamp}')
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Process each file
    print(f"\n\n=== Processing {len(md_files)} Markdown file(s) ===\n")
    
    successful = 0
    failed = 0
    
    for idx, md_file in enumerate(md_files, 1):
        print(f"\n[{idx}/{len(md_files)}] Processing: {md_file['name']}")
        print("="*60)
        
        try:
            # Read baseline markdown from Drive
            print(f"  ⬇️  Downloading from Drive...")
            raw_markdown = read_markdown_from_drive(drive_service, md_file['id'])
            print(f"  ✓ Read {len(raw_markdown)} characters")
            
            # Strip image data
            markdown_for_ai = strip_image_data(raw_markdown)
            size_reduction = len(raw_markdown) - len(markdown_for_ai)
            
            if size_reduction > 0:
                print(f"  ✓ Stripped {size_reduction:,} chars of base64 image data")
            
            # SAFETY CHECK: Verify no image data remains after stripping
            if contains_image_data(markdown_for_ai):
                print(f"  ❌ SAFETY GATE TRIGGERED: Image data still present after stripping!")
                print(f"     Skipping AI processing to prevent credit waste")
                cleaned_markdown = markdown_for_ai  # Use stripped version without AI
                successful += 1
                continue
            
            # Check size
            if len(markdown_for_ai) > MAX_DOCUMENT_SIZE_FOR_AI:
                print(f"  ⚠️  Document is very large ({len(markdown_for_ai):,} chars)")
                print(f"     Skipping AI processing (max: {MAX_DOCUMENT_SIZE_FOR_AI:,}), using raw markdown")
                cleaned_markdown = raw_markdown
            else:
                # Apply AI cleanup
                print(f"  ⚙️  Sending to Gemini AI ({len(markdown_for_ai):,} chars)...")
                cleaned_markdown = clean_markdown_with_ai(api_key, markdown_for_ai)
                print(f"  ✓ AI cleanup complete ({len(cleaned_markdown)} chars)")
            
            # Save intermediary files to logs folder
            if logs_folder_id:
                # Remove run_id prefix from filename if present for cleaner log names
                base_name = md_file['name'].replace('.md', '')
                if run_id and base_name.startswith(run_id + '_'):
                    base_name = base_name[len(run_id) + 1:]
                
                log_prefix = f"{run_id}_{base_name}" if run_id else base_name
                
                # Save baseline markdown
                save_log_to_drive(
                    drive_service,
                    raw_markdown,
                    f"{log_prefix}_baseline.md",
                    logs_folder_id,
                    'text/markdown'
                )
                
                # Save cleaned markdown
                save_log_to_drive(
                    drive_service,
                    cleaned_markdown,
                    f"{log_prefix}_cleaned.md",
                    logs_folder_id,
                    'text/markdown'
                )
                print(f"  ✓ Saved intermediary files to logs folder")
            
            # Save cleaned markdown to Drive
            print(f"  ⬆️  Uploading to Drive...")
            new_file = save_markdown_to_drive(
                drive_service,
                cleaned_markdown,
                md_file['name'],
                target_folder['id']
            )
            print(f"  ✓ Saved to Drive: {new_file['name']}")
            print(f"     Link: {new_file.get('webViewLink', 'N/A')}")
            
            # Save artifacts locally for debugging
            file_artifacts_dir = os.path.join(artifacts_dir, md_file['name'].replace('.md', ''))
            save_artifact(raw_markdown, 'baseline.md', file_artifacts_dir)
            save_artifact(cleaned_markdown, 'cleaned.md', file_artifacts_dir)
            
            successful += 1
            
        except Exception as e:
            print(f"❌ Failed to process {md_file['name']}: {e}")
            failed += 1
    
    # Summary
    print("\n\n" + "="*60)
    print("=== Step 3 Summary ===")
    print("="*60)
    print(f"✓ Successfully processed: {successful}")
    if failed > 0:
        print(f"❌ Failed: {failed}")
    print(f"\nRAG-accessible Markdown files saved to '{FOLDER_RAG_MARKDOWNS}' folder in Google Drive.")
    print(f"Debug artifacts saved locally to '{artifacts_dir}' folder.")
    
    return successful, failed
