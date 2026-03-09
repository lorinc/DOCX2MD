# DOCX2MD

Converts Google Docs to Markdown with AI-powered header cleanup.

## What It Is

Python script that exports Google Docs to Markdown and uses Gemini AI to fix header hierarchy based on font sizes.

## Requirements

- **Google Cloud Service Account** (`service-account.json`)
  - Google Drive API enabled
  - Google Docs API enabled
  - Share your Drive files/folders with the service account email

- **Gemini API Key** (in `.config` file)
  - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Format: `GEMINI_API_KEY=your-key-here`

## What It Does

1. Lists Google Docs in your Drive (or accepts file ID)
2. Exports document to Markdown
3. Extracts text style information (font sizes)
4. Strips base64 image data to reduce prompt size
5. Sends to Gemini AI for header cleanup (documents < 100KB)
6. Saves timestamped artifacts for debugging
7. Outputs cleaned Markdown locally

## Output

- **Cleaned Markdown file**: `output/filename_YYYYMMDD_HHMMSS.md`
- **Debug artifacts**: `artifacts/YYYYMMDD_HHMMSS_<file_id>/`
  - `1_raw_markdown.md` - Original export
  - `2_text_styles.json` - Font size metadata
  - `3_cleaned_markdown.md` - AI-processed output

## Usage

```bash
# List documents
python docx_to_markdown.py --list

# Process a document
python docx_to_markdown.py <file_id>
```

## Notes

- **DOCX files**: Must be manually converted to Google Docs format first (File → Save as Google Docs)
- **Large documents** (>100KB after image stripping): AI processing skipped, raw markdown used
- **Service accounts**: Cannot save to Drive due to quota limits, saves locally instead
