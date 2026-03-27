#!/usr/bin/env python3
"""
NetApp DataOps Toolkit - GCNV Authentication Setup

Configures secure authentication using service account impersonation.

Usage:
    python3 setup_gcnv_auth.py
    python3 -m netapp_dataops.traditional.gcnv.setup_gcnv_auth
"""

import subprocess
import sys
import os


def run(cmd: list, capture: bool = False) -> subprocess.CompletedProcess:
    if capture:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, check=False)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result
    return subprocess.run(cmd, text=True, check=True)


def get_value(cmd: list) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ''


def sa_exists(email: str) -> bool:
    try:
        run(['gcloud', 'iam', 'service-accounts', 'describe', email], capture=True)
        return True
    except subprocess.CalledProcessError:
        return False


def setup_gcnv_auth() -> None:

    print("\nNetApp DataOps Toolkit - GCNV Authentication Setup")
    print("=" * 52)
    print()

    # Check gcloud is installed
    try:
        version = get_value(['gcloud', 'version']).split('\n')[0]
        print(f"gcloud CLI exists: {version}\n")
    except FileNotFoundError:
        print("gcloud CLI not found!")
        print("  Install: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)

    # Gather inputs
    print("Configuration")
    print("-" * 13)

    
    project_id = input(f"  Enter Project ID: ").strip()
    if not project_id:
        print("Error: Project ID is required.")
        sys.exit(1)

    user_email = input(f"  Enter Your email: ").strip()
    if not user_email:
        print("Error: Email is required.")
        sys.exit(1)

    sa_name = input("  Enter Service account name [gcnv-dataops]: ").strip() or "gcnv-dataops"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"

    if input("\nContinue? (yes/no): ").strip().lower() != "yes":
        print("Cancelled.")
        sys.exit(0)

    print()

    # Step 1: User authentication
    print("Step 1/8  User authentication (browser will open)...")
    run(['gcloud', 'config', 'unset', 'auth/impersonate_service_account'], capture=True)
    run(['gcloud', 'auth', 'login'], capture=True)
    print("Authenticated")

    # Step 2: Set project
    print("\nStep 2/8  Set project...")
    run(['gcloud', 'config', 'set', 'project', project_id], capture=True)
    print(f"Project set to '{project_id}'")

    # Step 3: Enable APIs (must run as user, before impersonation is configured)
    print("\nStep 3/8  Enable APIs (running as your user account)...")
    run(['gcloud', 'services', 'enable',
         'netapp.googleapis.com',
         'iamcredentials.googleapis.com'], capture=True)
    print("netapp.googleapis.com enabled")
    print("iamcredentials.googleapis.com enabled")

    # Step 4: Application Default Credentials
    print("\nStep 4/8  Application Default Credentials (browser will open)...")
    run(['gcloud', 'auth', 'application-default', 'login'], capture=True)
    cloudsdk_config = os.environ.get("CLOUDSDK_CONFIG", os.path.expanduser("~/.config/gcloud"))
    adc_file = os.path.join(cloudsdk_config, "application_default_credentials.json")
    if os.path.exists(adc_file):
        os.chmod(adc_file, 0o600)
    print("ADC configured and credentials secured (chmod 600)")

    # Step 5: Create service account
    print("\nStep 5/8  Create service account...")
    if sa_exists(sa_email):
        print(f"Already exists, skipping creation: {sa_email}")
    else:
        run(['gcloud', 'iam', 'service-accounts', 'create', sa_name,
             '--display-name=NetApp DataOps GCNV'])
        print(f"Created: {sa_email}")

    # Step 6: Grant NetApp permissions
    print("\nStep 6/8  Grant NetApp permissions...")
    run(['gcloud', 'projects', 'add-iam-policy-binding', project_id,
         f'--member=serviceAccount:{sa_email}',
         '--role=roles/netappcloudvolumes.admin'],
        capture=True)
    print("roles/netappcloudvolumes.admin granted")

    # Step 7: Grant impersonation permission
    print("\nStep 7/8  Grant impersonation permission...")
    run(['gcloud', 'iam', 'service-accounts', 'add-iam-policy-binding',
         sa_email,
         f'--member=user:{user_email}',
         '--role=roles/iam.serviceAccountTokenCreator'],
        capture=True)
    print(f"{user_email} can impersonate {sa_email}")

    # Step 8: Configure auto-impersonation
    print("\nStep 8/8  Configure impersonation...")
    run(['gcloud', 'config', 'set', 'auth/impersonate_service_account', sa_email], capture=True)
    print(f"Impersonation active: {sa_email}")

    # Complete
    print()
    print("=" * 52)
    print("Setup Complete!")
    print("=" * 52)


if __name__ == "__main__":
    try:
        setup_gcnv_auth()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"\nError: {e.stderr or str(e)}")
        sys.exit(1)
