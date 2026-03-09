# DOCX2MD

Automated pipeline to convert DOCX files to RAG-accessible Markdown with AI-powered cleanup.

## Overview

This project provides a modular 3-step pipeline for converting DOCX documents to optimized Markdown files with AI-powered header fixing. Each pipeline run is tracked with a unique run ID, ensuring files are processed together through all steps.

### Pipeline Workflow

```
0-docx-sources/          →  1-native-gdocs/       →  2-baseline-markdowns/  →  3-AI-fixed-header-markdowns/
(DOCX files)                (Google Docs)            (Raw Markdown)            (AI-cleaned Markdown)
     │                           │                         │                          │
     └─── Step 1 ───────────────┘                         │                          │
                                 └───── Step 2 ───────────┘                          │
                                                           └────── Step 3 ───────────┘
```

## Requirements

### Authentication Setup

The pipeline uses **OAuth 2.0 (User Account)** for all steps:

1. **OAuth 2.0 (User Account)** - Required for all steps
   - Needed because DOCX conversion requires user storage quota
   - Create OAuth credentials:
     1. Go to [Google Cloud Console](https://console.cloud.google.com/)
     2. Select your project
     3. Go to 'APIs & Services' > 'Credentials'
     4. Click 'Create Credentials' > 'OAuth client ID'
     5. Choose 'Desktop app' as application type
     6. Download the JSON file
     7. Save it as `credentials.json` in this directory
   - **Configure OAuth consent screen for testing:**
     1. Go to 'APIs & Services' > 'OAuth consent screen'
     2. Set 'User Type' to 'Internal' (if using Google Workspace) or 'External'
     3. If External, set 'Publishing status' to 'Testing'
     4. Add your email as a test user under 'Test users'
     5. This bypasses the Google verification requirement for testing
   - First run will open a browser for authorization
   - Click "Advanced" → "Go to [app name] (unsafe)" to proceed
   - Credentials are saved in `token.json` for future runs

2. **Service Account** (Optional - not currently used)
   - Service accounts have no storage quota and cannot create files in Drive
   - OAuth is used for all steps instead
   - You can still create a service account if needed for future read-only operations:
     1. Go to [Google Cloud Console](https://console.cloud.google.com/)
     2. Go to 'IAM & Admin' > 'Service Accounts'
     3. Create a service account
     4. Create a JSON key and download it
     5. Save it as `service-account.json` in this directory

### Other Requirements

- **Google APIs Enabled**
  - Google Drive API
  - Google Docs API

- **Gemini API Key** (in `.config` file) - Required for Step 3
  - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Format: `GEMINI_API_KEY=your-key-here`

- **Python Dependencies**: `pip install -r requirements.txt`

## Configuration

All folder names and settings are centralized in `config.py`:

```python
# Google Drive folder names (all steps use Drive)
FOLDER_DOCX_SOURCES = '0-docx-sources'
FOLDER_NATIVE_GDOCS = '1-native-gdocs'
FOLDER_BASELINE_MARKDOWNS = '2-baseline-markdowns'
FOLDER_RAG_MARKDOWNS = '3-RAG-accessible-markdowns'

# Authentication methods
AUTH_METHOD_STEP1 = 'oauth'  # DOCX conversion needs user storage
AUTH_METHOD_STEP2_3 = 'oauth'  # File creation needs user storage

# AI Processing settings
MAX_DOCUMENT_SIZE_FOR_AI = 400000  # Characters
GEMINI_MODEL = 'gemini-2.5-flash-lite'  # Fast and cost-effective model

# Run ID settings
RUN_ID_PREFIX = 'run_'  # Prefix for run IDs in filenames
```

You can customize folder names and authentication methods by editing `config.py`.

## Folder Structure

**All folders are in Google Drive.** Create these folders and share them with your service account:
- `0-docx-sources/` - Source DOCX files (manually uploaded)
- `1-native-gdocs/` - Converted Google Docs (auto-populated by Step 1)
- `2-baseline-markdowns/` - Raw Markdown exports (auto-populated by Step 2, tagged with run ID)
- `3-AI-fixed-header-markdowns/` - AI-cleaned Markdown (auto-populated by Step 3)
- `last-runtime-logs/` - Intermediary files from each run (optional, for debugging)

## Usage

### Run Complete Pipeline
```bash
python main.py --all
```

Each pipeline run generates a unique **Run ID** (e.g., `run_20260309_201500`) that:
- Tags all output files from Steps 2 and 3
- Ensures Step 3 only processes files created in the current run
- Organizes log files and artifacts by run

### Run Individual Steps
```bash
python main.py --step1  # DOCX → Google Docs
python main.py --step2  # Google Docs → Baseline Markdown (tags files with run ID)
python main.py --step3  # AI Cleanup (processes only current run's files)
```

**Note:** When running steps individually, each gets its own run ID. To process files through the complete pipeline, use `--all`.

### Short Flags
```bash
python main.py -a    # All steps
python main.py -1    # Step 1 only
python main.py -2    # Step 2 only
python main.py -3    # Step 3 only
```

## Pipeline Steps

### Step 1: DOCX → Native Google Docs
- **Input**: `0-docx-sources/` (DOCX files in Google Drive)
- **Output**: `1-native-gdocs/` (Native Google Docs in Drive)
- **Module**: `modules/step1_docx_to_gdocs.py`
- **Authentication**: OAuth (user account) - required for storage quota
- Converts DOCX files to native Google Docs format using Drive API
- First run will open browser for OAuth authorization

### Step 2: Google Docs → Baseline Markdown
- **Input**: `1-native-gdocs/` (Google Docs in Drive)
- **Output**: `2-baseline-markdowns/` (Markdown files in Drive)
- **Module**: `modules/step2_gdocs_to_markdown.py`
- Exports Google Docs to Markdown format
- Extracts text styles (font sizes) for AI processing
- Saves as text/markdown files in Drive
- **Logs**: Saves raw markdown and text styles to `last-runtime-logs/` (if folder exists)

### Step 3: AI Cleanup → Header-fixed Markdown
- **Input**: `2-baseline-markdowns/` (Baseline Markdown in Drive, filtered by run ID)
- **Output**: `3-AI-fixed-header-markdowns/` (AI-cleaned Markdown in Drive)
- **Module**: `modules/step3_ai_cleanup.py`
- **Only processes files from the current run** (filtered by run ID prefix)
- Uses Gemini AI (`gemini-2.5-flash-lite`) to fix header hierarchy and improve document structure
- **Multiple safety gates** prevent image data from being sent to Gemini API:
  - Strips base64 image data completely (not just replaced with placeholders)
  - Post-strip verification detects any remaining image patterns
  - 500K character hard limit on prompts
  - Logs actual prompt size before each API call
- Skips AI processing for documents >400KB (configurable in `config.py`)
- Debug artifacts saved locally in `artifacts/step3_[run_id]/` folder

## Module Structure

```
modules/
├── __init__.py                    # Package initialization
├── auth.py                        # Google API authentication
├── drive_utils.py                 # Drive folder/file utilities
├── step1_docx_to_gdocs.py        # Step 1: DOCX conversion
├── step2_gdocs_to_markdown.py    # Step 2: Markdown export
└── step3_ai_cleanup.py           # Step 3: AI cleanup
```

## Runtime Logs

If you create a `last-runtime-logs/` folder in Google Drive, the pipeline will save intermediary files tagged with the run ID:

**Step 2 logs** (per document):
- `[run_id]_[filename]_raw_markdown.md` - Raw markdown export
- `[run_id]_[filename]_text_styles.json` - Font size metadata

**Step 3 logs** (per document):
- `[run_id]_[filename]_baseline.md` - Input markdown
- `[run_id]_[filename]_cleaned.md` - AI-processed output

**Output files** are also tagged:
- Step 2: `[run_id]_[filename].md` in `2-baseline-markdowns/`
- Step 3: `[run_id]_[filename].md` in `3-AI-fixed-header-markdowns/`

This organization makes it easy to track files through the pipeline and compare different runs.

## Debug Artifacts

Step 3 creates local artifacts organized by run ID:
- `artifacts/step3_[run_id]/[filename]/`
  - `baseline.md` - Raw Markdown input (downloaded from Drive)
  - `cleaned.md` - AI-processed output (before uploading to Drive)

All final outputs are stored in Google Drive folders.

## Legacy Script

The original monolithic script is preserved as `docx_to_markdown.py` for reference.
