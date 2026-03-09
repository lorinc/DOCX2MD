#!/usr/bin/env python3
"""
DOCX2MD Pipeline Orchestrator

Main script to run the complete document conversion pipeline:
- Step 1: DOCX → Native Google Docs (0-docx-sources → 1-native-gdocs)
- Step 2: Google Docs → Baseline Markdown (1-native-gdocs → 2-baseline-markdowns)
- Step 3: AI Cleanup → RAG-accessible Markdown (2-baseline-markdowns → 3-RAG-accessible-markdowns)
"""

import sys
from datetime import datetime
from config import AUTH_METHOD_STEP1, AUTH_METHOD_STEP2_3, RUN_ID_PREFIX
from modules.auth import authenticate, get_drive_service, get_docs_service
from modules.auth_oauth import authenticate_oauth, get_drive_service_oauth, get_docs_service_oauth
from modules.step1_docx_to_gdocs import run_step1
from modules.step2_gdocs_to_markdown import run_step2
from modules.step3_ai_cleanup import run_step3

def generate_run_id():
    """Generate a unique run ID based on timestamp."""
    return f"{RUN_ID_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def print_usage():
    """Print usage information."""
    print("\n=== DOCX2MD Pipeline ===\n")
    print("Usage:")
    print("  python main.py [step]")
    print("\nOptions:")
    print("  --all, -a     Run all steps (1 → 2 → 3)")
    print("  --step1, -1   Run Step 1: DOCX → Native Google Docs")
    print("  --step2, -2   Run Step 2: Google Docs → Baseline Markdown")
    print("  --step3, -3   Run Step 3: AI Cleanup → RAG-accessible Markdown")
    print("  --help, -h    Show this help message")
    print("\nExamples:")
    print("  python main.py --all        # Run complete pipeline")
    print("  python main.py --step1      # Only convert DOCX to Google Docs")
    print("  python main.py -2           # Only export to baseline Markdown")
    print()

def main():
    """Main execution flow."""
    
    # Parse command line arguments
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h']:
        print_usage()
        return
    
    step_arg = sys.argv[1].lower()
    
    # Determine which steps to run
    run_all = step_arg in ['--all', '-a']
    run_s1 = run_all or step_arg in ['--step1', '-1']
    run_s2 = run_all or step_arg in ['--step2', '-2']
    run_s3 = run_all or step_arg in ['--step3', '-3']
    
    if not (run_s1 or run_s2 or run_s3):
        print(f"❌ Unknown option: {step_arg}")
        print_usage()
        return
    
    print("\n" + "="*70)
    print("  DOCX2MD CONVERSION PIPELINE")
    print("="*70)
    
    # Generate run ID for this pipeline execution
    run_id = generate_run_id()
    print(f"\n🆔 Run ID: {run_id}")
    
    # Determine which authentication methods to use
    use_oauth_step1 = (AUTH_METHOD_STEP1 == 'oauth')
    use_oauth_step2_3 = (AUTH_METHOD_STEP2_3 == 'oauth')
    
    # Authenticate for Step 1 (if needed)
    drive_service_step1 = None
    if run_s1:
        print("\n🔐 Authenticating for Step 1 (DOCX conversion)...")
        try:
            if use_oauth_step1:
                print("   Using OAuth (user account)")
                creds_oauth = authenticate_oauth()
                drive_service_step1 = get_drive_service_oauth(creds_oauth)
            else:
                print("   Using service account")
                creds_sa = authenticate()
                drive_service_step1 = get_drive_service(creds_sa)
            print("✓ Step 1 authentication successful")
        except Exception as e:
            print(f"❌ Step 1 authentication failed: {e}")
            return
    
    # Authenticate for Steps 2-3 (if needed)
    drive_service = None
    docs_service = None
    if run_s2 or run_s3:
        print("\n🔐 Authenticating for Steps 2-3...")
        try:
            if use_oauth_step2_3:
                print("   Using OAuth (user account)")
                creds_oauth = authenticate_oauth()
                drive_service = get_drive_service_oauth(creds_oauth)
                docs_service = get_docs_service_oauth(creds_oauth)
            else:
                print("   Using service account")
                creds_sa = authenticate()
                drive_service = get_drive_service(creds_sa)
                docs_service = get_docs_service(creds_sa)
            print("✓ Steps 2-3 authentication successful")
        except Exception as e:
            print(f"❌ Steps 2-3 authentication failed: {e}")
            return
    
    # Track overall results
    total_successful = 0
    total_failed = 0
    
    # Run Step 1
    if run_s1:
        print("\n" + "="*70)
        try:
            successful, failed = run_step1(drive_service_step1, use_oauth=use_oauth_step1)
            total_successful += successful
            total_failed += failed
        except Exception as e:
            print(f"\n❌ Step 1 failed: {e}")
            if not run_all:
                return
    
    # Run Step 2
    if run_s2:
        print("\n" + "="*70)
        try:
            successful, failed = run_step2(drive_service, docs_service, run_id=run_id)
            total_successful += successful
            total_failed += failed
        except Exception as e:
            print(f"\n❌ Step 2 failed: {e}")
            if not run_all:
                return
    
    # Run Step 3
    if run_s3:
        print("\n" + "="*70)
        try:
            successful, failed = run_step3(drive_service, docs_service, run_id=run_id)
            total_successful += successful
            total_failed += failed
        except Exception as e:
            print(f"\n❌ Step 3 failed: {e}")
            if not run_all:
                return
    
    # Final summary
    print("\n" + "="*70)
    print("  PIPELINE COMPLETE")
    print("="*70)
    print(f"✓ Total successful operations: {total_successful}")
    if total_failed > 0:
        print(f"❌ Total failed operations: {total_failed}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
