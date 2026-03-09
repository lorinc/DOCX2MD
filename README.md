# Google Docs to Markdown Converter

A streamlined Python script that converts Google Docs to clean Markdown files with AI-powered header hierarchy correction.

## Features

1. **Interactive file selection** - Browse and select from your Google Drive documents
2. **Automatic Markdown export** - Uses Google Drive API for clean conversion
3. **Style extraction** - Captures font sizes and text formatting
4. **AI-powered cleanup** - Gemini AI fixes header hierarchy and consistency issues
5. **Timestamped output** - Saves cleaned Markdown back to the same folder with timestamp

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Docs API
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name (e.g., "docx-to-markdown")
   - Click "Create and Continue"
   - Skip role assignment (click "Continue")
   - Click "Done"
5. Create and download the JSON key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose "JSON" format
   - Download the file
   - Save it as `service-account.json` in this directory
6. **Important**: Share your Google Drive files/folders with the service account email
   - The email looks like: `your-service-account@your-project.iam.gserviceaccount.com`
   - Share the folders containing documents you want to convert with this email (Viewer access is enough)

### 3. Set up Gemini API Key

1. Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set the environment variable:

```bash
export GEMINI_API_KEY='your-api-key-here'
```

Or add it to your `~/.bashrc` or `~/.zshrc` for persistence:

```bash
echo "export GEMINI_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

## Usage

List available documents:
```bash
python docx_to_markdown.py --list
```

Process a specific document:
```bash
python docx_to_markdown.py <file_id>
```

### DOCX File Support

**Important:** When using service account authentication, DOCX files cannot be automatically converted due to Google Drive storage quota limitations for service accounts.

**Workaround for DOCX files:**
1. Open the DOCX file in Google Drive (web interface)
2. Click: **File → Save as Google Docs**
3. Copy the new Google Doc's ID from the URL
4. Run the script with the converted Google Doc's ID

The script will list both Google Docs and DOCX files, but can only process native Google Docs format.

The script will:
1. Authenticate with Google (first time only - opens browser)
2. Display your Google Docs and .docx files
3. Let you select a file
4. Process and clean the document
5. Save the result back to Google Drive with a timestamp

## What It Fixes

The script addresses issues in the original notebook:

### Original Problems
- ❌ Hardcoded document ID (no file selection)
- ❌ Scattered across 25+ notebook cells
- ❌ Missing error handling
- ❌ Incomplete workflow (manual steps required)
- ❌ No user feedback during processing
- ❌ Overcomplicated with unnecessary intermediate outputs

### Improvements
- ✅ Interactive file selection from Drive
- ✅ Single cohesive script
- ✅ Proper error handling and user feedback
- ✅ Fully automated workflow
- ✅ Clear progress indicators
- ✅ Clean, maintainable code structure

## Example Output

```
=== Google Docs to Markdown Converter ===

Authenticating with Google...

Fetching your documents...

=== Available Documents ===
1. Project Proposal (Google Doc)
2. Meeting Notes (Google Doc)
3. Report Draft (DOCX)

Select a file (1-3) or 'q' to quit: 1

✓ Selected: Project Proposal

[1/4] Exporting to Markdown...
✓ Exported 15234 characters

[2/4] Extracting text styling information...
✓ Extracted 87 text elements

[3/4] Cleaning with Gemini AI...
✓ AI cleanup complete

[4/4] Saving to Google Drive...

✅ Success!
   File: project_proposal_20260309_150423.md
   ID: 1ABC...xyz
   Link: https://drive.google.com/file/d/1ABC...xyz/view
```

## Troubleshooting

**"Service account file not found"**: Make sure `service-account.json` is in the same directory as the script

**"No files found"**: Ensure you've shared your Google Drive folders with the service account email address

**API not enabled**: Ensure Google Drive API and Google Docs API are enabled in your Cloud Console

**Gemini API errors**: Verify your API key is set correctly in `.config` file

**Permission denied**: The service account needs Viewer access to the files/folders you want to convert
