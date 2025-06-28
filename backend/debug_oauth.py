#!/usr/bin/env python3
"""Debug OAuth setup"""

import sys
sys.path.append('.')
import sqlite3
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

print("=== OAuth Debug Info ===\n")

print("1. Environment variables:")
print(f"   QB_CLIENT_ID: {os.getenv('QB_CLIENT_ID', 'NOT SET')}")
print(f"   QB_CLIENT_SECRET: {'SET' if os.getenv('QB_CLIENT_SECRET') else 'NOT SET'}")
print(f"   DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")
print(f"   API_BASE_URL: {os.getenv('API_BASE_URL', 'NOT SET')}")
print()

# Check database
db_url = os.getenv('DATABASE_URL', 'sqlite:///test_finwave.db')
db_path = db_url.replace('sqlite:///', '')
print(f"2. Database path: {db_path}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\n3. Tables in database:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Check for oauth_app_configs table
    if ('oauth_app_configs',) in tables:
        cursor.execute("SELECT workspace_id, source, client_id FROM oauth_app_configs")
        configs = cursor.fetchall()
        print(f"\n4. OAuth configs in database: {len(configs)}")
        for config in configs:
            print(f"   - Workspace: {config[0]}, Source: {config[1]}, Client ID: {config[2][:10]}...")
    else:
        print("\n4. No oauth_app_configs table found - will use env vars")
    
    # Check for workspaces
    if ('workspaces',) in tables:
        cursor.execute("SELECT id, name FROM workspaces")
        workspaces = cursor.fetchall()
        print("\n5. Workspaces:")
        for ws in workspaces:
            print(f"   - {ws[0]}: {ws[1]}")
    else:
        print("\n5. No workspaces table found")
    
    # Check for integration_credentials
    if ('integration_credentials',) in tables:
        cursor.execute("SELECT workspace_id, source, status FROM integration_credentials")
        integrations = cursor.fetchall()
        print(f"\n6. Integration credentials: {len(integrations)}")
        for integ in integrations:
            print(f"   - Workspace: {integ[0]}, Source: {integ[1]}, Status: {integ[2]}")
    
    conn.close()
else:
    print("\nDatabase file not found!")

print("\n7. Expected redirect URL:")
print("   http://localhost:8000/api/oauth/callback")
print("\n8. Make sure this EXACT URL is configured in your QuickBooks app settings!")