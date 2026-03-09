"""
Configuration file for DOCX2MD pipeline

Contains folder names and other configurable settings.
All folders are in Google Drive.
"""

# Google Drive folder names (all steps use Drive)
FOLDER_DOCX_SOURCES = '0-docx-sources'
FOLDER_NATIVE_GDOCS = '1-native-gdocs'
FOLDER_BASELINE_MARKDOWNS = '2-baseline-markdowns'
FOLDER_RAG_MARKDOWNS = '3-AI-fixed-header-markdowns'
FOLDER_RUNTIME_LOGS = 'last-runtime-logs'

# Run ID settings
RUN_ID_PREFIX = 'run_'  # Prefix for run IDs in filenames

# Local artifacts folder (for debugging)
FOLDER_ARTIFACTS = 'artifacts'

# AI Processing settings
MAX_DOCUMENT_SIZE_FOR_AI = 400000  # Characters
GEMINI_MODEL = 'gemini-2.5-flash-lite'  # Fast and cost-effective model

# Google API settings
SERVICE_ACCOUNT_FILE = 'service-account.json'
OAUTH_CREDENTIALS_FILE = 'credentials.json'
OAUTH_TOKEN_FILE = 'token.json'
CONFIG_FILE = '.config'

# Authentication method: 'service_account' or 'oauth'
# Note: Service accounts have NO storage quota, so OAuth is required for all file creation operations
AUTH_METHOD_STEP1 = 'oauth'  # DOCX conversion needs user storage
AUTH_METHOD_STEP2_3 = 'oauth'  # Markdown file creation also needs user storage
