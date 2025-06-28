#!/usr/bin/env python3
"""
Simple QuickBooks status check using direct SQL
"""
import os
import sqlite3
from datetime import datetime

# Connect to SQLite database
db_path = os.getenv('DATABASE_URL', 'sqlite:///./finwave.db').replace('sqlite:///', '')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== QuickBooks Integration Status ===\n")

# Check integrations
cursor.execute("""
    SELECT workspace_id, source, status, created_at, last_synced_at, 
           last_sync_error, expires_at, metadata_encrypted
    FROM integration_credentials
    WHERE source = 'quickbooks'
""")

integrations = cursor.fetchall()
for integration in integrations:
    workspace_id, source, status, created_at, last_synced_at, last_sync_error, expires_at, metadata = integration
    print(f"Workspace: {workspace_id}")
    print(f"Source: {source}")
    print(f"Status: {status}")
    print(f"Created: {created_at}")
    print(f"Last Synced: {last_synced_at}")
    print(f"Expires At: {expires_at}")
    if last_sync_error:
        print(f"Last Error: {last_sync_error[:500]}...")
    print()

print("\n=== Sync Jobs ===\n")

# Check sync jobs
cursor.execute("""
    SELECT job_name, status, started_at, completed_at, error_message, records_processed
    FROM scheduled_jobs
    WHERE job_name LIKE 'sync_%'
    ORDER BY started_at DESC
    LIMIT 5
""")

jobs = cursor.fetchall()
for job in jobs:
    job_name, status, started_at, completed_at, error_message, records_processed = job
    print(f"Job: {job_name}")
    print(f"Status: {status}")
    print(f"Started: {started_at}")
    print(f"Completed: {completed_at}")
    print(f"Records: {records_processed}")
    if error_message:
        print(f"Error: {error_message[:500]}...")
    print()

print("\n=== Metrics Count ===\n")

# Check metrics
cursor.execute("SELECT COUNT(*) FROM metrics")
metric_count = cursor.fetchone()[0]
print(f"Total metrics in database: {metric_count}")

if metric_count > 0:
    cursor.execute("""
        SELECT workspace_id, metric_id, value, period_date 
        FROM metrics 
        LIMIT 5
    """)
    print("\nSample metrics:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - {row[1]}: {row[2]} ({row[3]})")

conn.close()