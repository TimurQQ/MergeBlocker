#!/usr/bin/env python3
"""
Validate GitHub App credentials in CI/CD pipeline.
This script runs automatically before tests to ensure credentials are configured correctly.

Exit codes:
    0 - All checks passed
    1 - Critical error (missing credentials, invalid format, authentication failed)
"""

import os
import sys
from pathlib import Path

try:
    from github import GithubIntegration
    from dotenv import load_dotenv
except ImportError:
    print("❌ Required packages not installed: PyGithub, python-dotenv")
    sys.exit(1)


def main():
    # Load environment
    load_dotenv()

    # Check App ID
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        print("❌ GITHUB_APP_ID not set")
        sys.exit(1)
    
    try:
        app_id = int(app_id)
        print(f"✅ App ID: {app_id}")
    except ValueError:
        print("❌ App ID must be a number")
        sys.exit(1)

    # Check webhook secret
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        print("❌ GITHUB_WEBHOOK_SECRET not set")
        sys.exit(1)
    
    print(f"✅ Webhook secret: {len(webhook_secret)} chars")

    # Check private key
    key_path = Path(os.getenv("GITHUB_PRIVATE_KEY_PATH", "./private-key.pem"))
    if not key_path.exists():
        print(f"❌ Private key file not found: {key_path}")
        sys.exit(1)
    
    print(f"✅ Private key file exists: {key_path}")
    
    # Check key format
    key_content = key_path.read_text()
    if not key_content.startswith("-----BEGIN RSA PRIVATE KEY-----"):
        print("❌ Invalid private key format (missing header)")
        sys.exit(1)
    
    if not key_content.strip().endswith("-----END RSA PRIVATE KEY-----"):
        print("❌ Invalid private key format (missing footer)")
        sys.exit(1)
    
    print("✅ Private key format valid")

    # Test GitHub Integration
    try:
        integration = GithubIntegration(app_id, key_content)
        print("✅ GitHub Integration created")
    except Exception as e:
        print(f"❌ Failed to create GitHub Integration: {e}")
        sys.exit(1)

    # Validate by fetching installations
    try:
        installations = list(integration.get_installations())
        print(f"✅ Found {len(installations)} installation(s)")
        
        if len(installations) == 0:
            print("⚠️  No installations found (app not installed on any repo)")
            sys.exit(1)
        
        # Test access token generation
        for inst in installations:
            try:
                integration.get_access_token(inst.id)
                print(f"✅ Access token generated for installation {inst.id}")
            except Exception as e:
                print(f"❌ Failed to generate access token for installation {inst.id}: {e}")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Failed to fetch installations: {e}")
        print("   This usually means App ID or private key is incorrect")
        sys.exit(1)
    
    print("✅ All credentials validated successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
