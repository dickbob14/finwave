#!/usr/bin/env python3
"""
Simple database initialization for DuckDB
"""

import duckdb
import os
from pathlib import Path

print("Initializing FinWave database...")

# Create database
db_path = "dev.duckdb"
conn = duckdb.connect(db_path)

# Create tables
print("Creating tables...")

# Workspaces table
conn.execute("""
CREATE TABLE IF NOT EXISTS workspaces (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    billing_status VARCHAR DEFAULT 'trial',
    features_enabled JSON,
    settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Integration credentials table  
conn.execute("""
CREATE TABLE IF NOT EXISTS integration_credentials (
    id VARCHAR PRIMARY KEY DEFAULT (gen_random_uuid()::VARCHAR),
    workspace_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    company_id VARCHAR,
    settings JSON,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, source)
)
""")

# Metrics table
conn.execute("""
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY,
    workspace_id VARCHAR NOT NULL,
    metric_id VARCHAR NOT NULL,
    date DATE NOT NULL,
    value DOUBLE NOT NULL,
    source VARCHAR,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, metric_id, date)
)
""")

# Alerts table
conn.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR PRIMARY KEY DEFAULT (gen_random_uuid()::VARCHAR),
    workspace_id VARCHAR NOT NULL,
    metric_id VARCHAR NOT NULL,
    rule_name VARCHAR,
    severity VARCHAR,
    status VARCHAR DEFAULT 'active',
    message TEXT,
    current_value DOUBLE,
    threshold_value DOUBLE,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    notes TEXT
)
""")

# OAuth app configurations table
conn.execute("""
CREATE TABLE IF NOT EXISTS oauth_app_configs (
    workspace_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    client_id VARCHAR NOT NULL,
    client_secret_encrypted TEXT NOT NULL,
    environment VARCHAR DEFAULT 'production',
    settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    updated_by VARCHAR,
    PRIMARY KEY (workspace_id, source)
)
""")

print("✅ Database initialized successfully!")
print(f"Database file: {os.path.abspath(db_path)}")

# Show tables
print("\nCreated tables:")
tables = conn.execute("SHOW TABLES").fetchall()
for table in tables:
    print(f"  - {table[0]}")

conn.close()