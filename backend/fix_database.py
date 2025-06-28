#!/usr/bin/env python3
"""Fix missing database tables"""

import sqlite3
import os
from datetime import datetime

# Connect to database
db_path = 'test_finwave.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create scheduled_jobs table if missing
cursor.execute("""
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id TEXT PRIMARY KEY,
    job_name TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,
    records_processed INTEGER,
    error_message TEXT,
    result_json TEXT
)
""")

# Create oauth_app_configs table if missing
cursor.execute("""
CREATE TABLE IF NOT EXISTS oauth_app_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,
    source TEXT NOT NULL,
    client_id TEXT NOT NULL,
    client_secret_encrypted TEXT NOT NULL,
    environment TEXT DEFAULT 'production',
    settings TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    UNIQUE(workspace_id, source)
)
""")

# Check if integration_credentials exists and has the right schema
cursor.execute("""
CREATE TABLE IF NOT EXISTS integration_credentials (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    metadata TEXT DEFAULT '{}',
    connected_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    last_sync_error TEXT,
    UNIQUE(workspace_id, source)
)
""")

conn.commit()

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Database tables:")
for table in tables:
    print(f"  - {table[0]}")

# Check integration status
cursor.execute("SELECT workspace_id, source, status FROM integration_credentials")
integrations = cursor.fetchall()
print(f"\nIntegrations: {len(integrations)}")
for integ in integrations:
    print(f"  - Workspace: {integ[0]}, Source: {integ[1]}, Status: {integ[2]}")

conn.close()
print("\nDatabase fixed!")