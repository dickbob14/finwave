#!/usr/bin/env python3
"""
Comprehensive fix for all QuickBooks OAuth issues
"""
import os
import sys
import sqlite3
from datetime import datetime

print("🔧 Comprehensive OAuth Fix")
print("=" * 40)

# 1. Remove old database to start fresh
print("\n1. Cleaning up old database...")
if os.path.exists('test_finwave.db'):
    os.remove('test_finwave.db')
    print("   ✓ Removed old database")

# 2. Create new database with ALL required tables
print("\n2. Creating new database with complete schema...")
conn = sqlite3.connect('test_finwave.db')
cursor = conn.cursor()

# Create workspaces table
cursor.execute("""
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create integration_credentials table
cursor.execute("""
CREATE TABLE IF NOT EXISTS integration_credentials (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    expires_at TIMESTAMP,
    token_type TEXT DEFAULT 'Bearer',
    scope TEXT,
    metadata_encrypted TEXT,
    connected_by TEXT,
    last_synced_at TIMESTAMP,
    last_sync_error TEXT,
    sync_frequency_minutes TEXT DEFAULT '60',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, source),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
)
""")

# Create metrics table
cursor.execute("""
CREATE TABLE IF NOT EXISTS metrics (
    workspace_id TEXT NOT NULL,
    metric_id TEXT NOT NULL,
    period_date DATE NOT NULL,
    value REAL NOT NULL,
    source_template TEXT NOT NULL,
    currency TEXT DEFAULT 'USD',
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, metric_id, period_date)
)
""")

# Create scheduled_jobs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    records_processed INTEGER,
    error_message TEXT,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create oauth_app_configs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS oauth_app_configs (
    workspace_id TEXT NOT NULL,
    source TEXT NOT NULL,
    client_id TEXT,
    client_secret_encrypted TEXT,
    environment TEXT DEFAULT 'production',
    settings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, source)
)
""")

# Create report tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS report_configs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    template_type TEXT NOT NULL,
    config TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS report_history (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    config_id TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    file_path TEXT,
    metadata_encrypted TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (config_id) REFERENCES report_configs(id)
)
""")

# Create QuickBooks-specific tables (using correct table names from model)
cursor.execute("""
CREATE TABLE IF NOT EXISTS qb_financial_statements (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES workspaces(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS qb_account_balances (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    account_subtype TEXT,
    balance REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    as_of_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES workspaces(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS qb_transactions (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    quickbooks_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    customer_id TEXT,
    vendor_id TEXT,
    account_id TEXT,
    description TEXT,
    transaction_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES workspaces(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS qb_customers (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    quickbooks_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    first_transaction_date TIMESTAMP,
    last_transaction_date TIMESTAMP,
    total_revenue REAL DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    churn_date TIMESTAMP,
    customer_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES workspaces(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS qb_vendors (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    quickbooks_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    total_spend REAL DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    vendor_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES workspaces(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS kpi_metrics (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    calculation_method TEXT,
    kpi_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES workspaces(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sync_logs (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    sync_type TEXT NOT NULL,
    sync_status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    records_synced INTEGER DEFAULT 0,
    error_message TEXT,
    sync_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES workspaces(id)
)
""")

print("   ✓ Created all tables")

# 3. Create workspaces
print("\n3. Creating workspaces...")
cursor.execute("""
    INSERT INTO workspaces (id, name, created_at, updated_at)
    VALUES ('default', 'Default Workspace', datetime('now'), datetime('now'))
""")
cursor.execute("""
    INSERT INTO workspaces (id, name, created_at, updated_at)
    VALUES ('demo', 'Demo Workspace', datetime('now'), datetime('now'))
""")
print("   ✓ Created 'default' and 'demo' workspaces")

# 4. Commit changes
conn.commit()
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
table_count = cursor.fetchone()[0]
print(f"\n4. Database created successfully with {table_count} tables")

conn.close()

# 5. Clean up duplicate files
print("\n5. Cleaning up duplicate files...")
duplicates_removed = []

# Remove duplicate migration
duplicate_migration = "migrations/009_add_financial_sync_tables.py"
if os.path.exists(duplicate_migration):
    os.rename(duplicate_migration, duplicate_migration + ".backup")
    duplicates_removed.append(duplicate_migration)
    print(f"   ✓ Backed up duplicate migration: {duplicate_migration}")

print("\n✅ All issues fixed!")
print("\nNext steps:")
print("1. The backend server should auto-reload due to file changes")
print("2. Wait a few seconds for the reload to complete")
print("3. Try connecting QuickBooks again at http://localhost:3000/settings")
print("\nIf issues persist, restart the server manually:")
print("   - Press Ctrl+C to stop the server")
print("   - Run: ./quick_start.sh")