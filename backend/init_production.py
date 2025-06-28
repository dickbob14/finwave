#!/usr/bin/env python3
"""
Production initialization for FinWave
Sets up the system to work with real credentials
"""

import duckdb
import json
import os
from datetime import datetime

print("🚀 Initializing FinWave Production Environment...")

# Connect to database
conn = duckdb.connect("dev.duckdb")

# Check if we have required environment variables
required_vars = {
    'QUICKBOOKS': ['QB_CLIENT_ID', 'QB_CLIENT_SECRET'],
    'SALESFORCE': ['SALESFORCE_CLIENT_ID', 'SALESFORCE_CLIENT_SECRET'],
    'HUBSPOT': ['HUBSPOT_CLIENT_ID', 'HUBSPOT_CLIENT_SECRET'],
    'GUSTO': ['GUSTO_CLIENT_ID', 'GUSTO_CLIENT_SECRET']
}

print("\n📋 Checking OAuth credentials:")
configured_sources = []

for source, vars in required_vars.items():
    all_present = all(os.getenv(var) for var in vars)
    if all_present:
        print(f"  ✅ {source}: Configured")
        configured_sources.append(source.lower())
    else:
        missing = [var for var in vars if not os.getenv(var)]
        print(f"  ⚠️  {source}: Missing {', '.join(missing)}")

if not configured_sources:
    print("\n⚠️  No OAuth credentials configured in .env")
    print("This is fine! You can configure OAuth credentials through the UI.")
    print("This is actually the recommended approach for demos.")
else:
    print(f"\n✅ Found credentials for: {', '.join(configured_sources)}")

# Create initial workspace if needed
print("\n📁 Creating initial workspace...")
workspace_id = 'workspace-' + datetime.now().strftime('%Y%m%d%H%M%S')

conn.execute("""
INSERT INTO workspaces (id, name, slug, billing_status, features_enabled, settings)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT (id) DO NOTHING
""", [
    workspace_id,
    'My Company',
    'my-company',
    'active',
    json.dumps({
        "board_reports": True,
        "variance_alerts": True,
        "scenario_planning": True,
        "ai_insights": True
    }),
    json.dumps({
        "company_name": "My Company",
        "fiscal_year_start_month": 1
    })
])

print(f"  Created workspace: {workspace_id}")

# Show next steps
print("\n🎯 Next Steps:")
print("1. Start the backend server: cd backend && uvicorn main:app --reload")
print("2. Start the frontend: cd frontend && npm run dev")
print("3. Visit http://localhost:3000")
print("4. Connect your data sources through the UI")
print("\nThe system will pull real data after you complete the OAuth flow!")

# Show summary
workspace_count = conn.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]
print(f"\n📊 Database summary:")
print(f"  Workspaces: {workspace_count}")
print(f"  Ready for OAuth connections: {', '.join(configured_sources)}")

conn.close()