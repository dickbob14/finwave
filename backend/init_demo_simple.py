#!/usr/bin/env python3
"""
Simple demo initialization for FinWave
Creates a demo workspace with mock data
"""

import duckdb
import json
from datetime import datetime, timedelta
import random

print("🚀 Initializing FinWave Demo Environment...")

# Connect to database
conn = duckdb.connect("dev.duckdb")

# Create demo workspace
print("Creating demo workspace...")
conn.execute("""
INSERT INTO workspaces (id, name, slug, billing_status, features_enabled, settings)
VALUES (
    'demo-workspace-001',
    'Craig''s Design & Landscaping Services',
    'demo',
    'active',
    '{"board_reports": true, "variance_alerts": true, "scenario_planning": true, "ai_insights": true}',
    '{"company_name": "Craig''s Design & Landscaping Services", "fiscal_year_start_month": 1}'
)
ON CONFLICT (id) DO NOTHING
""")

# Add QuickBooks integration (mock credentials for demo)
print("Adding QuickBooks integration...")
conn.execute("""
INSERT INTO integration_credentials (
    workspace_id, 
    source, 
    status, 
    company_id,
    settings
)
VALUES (
    'demo-workspace-001',
    'quickbooks',
    'connected',
    '9341453129374037',
    '{"sandbox": true, "company_name": "Craig''s Design & Landscaping Services"}'
)
ON CONFLICT (workspace_id, source) DO NOTHING
""")

# Add some sample metrics
print("Adding sample metrics...")

# Generate dates for the last 12 months
base_date = datetime.now().replace(day=1)
dates = []
for i in range(12):
    date = base_date - timedelta(days=30*i)
    dates.append(date.replace(day=1))

# Sample metric values
metrics_data = [
    ('revenue', [125000, 132000, 128000, 135000, 142000, 138000, 145000, 150000, 148000, 155000, 160000, 158000]),
    ('gross_profit', [75000, 79200, 76800, 81000, 85200, 82800, 87000, 90000, 88800, 93000, 96000, 94800]),
    ('opex', [45000, 46000, 47000, 48000, 49000, 50000, 51000, 52000, 53000, 54000, 55000, 56000]),
    ('ebitda', [30000, 33200, 29800, 33000, 36200, 32800, 36000, 38000, 35800, 39000, 41000, 38800]),
    ('cash', [250000, 265000, 258000, 273000, 285000, 278000, 295000, 310000, 305000, 320000, 335000, 330000]),
    ('mrr', [12500, 13200, 12800, 13500, 14200, 13800, 14500, 15000, 14800, 15500, 16000, 15800]),
    ('new_customers', [5, 8, 6, 7, 9, 6, 8, 10, 8, 9, 11, 9]),
    ('churn_rate', [0.02, 0.018, 0.022, 0.019, 0.017, 0.021, 0.018, 0.016, 0.019, 0.015, 0.014, 0.016]),
]

for metric_id, values in metrics_data:
    for i, date in enumerate(dates):
        if i < len(values):
            # Generate a unique ID for the metric
            metric_record_id = i * 100 + hash(metric_id) % 100
            conn.execute("""
            INSERT INTO metrics (id, workspace_id, metric_id, date, value, source)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (workspace_id, metric_id, date) DO UPDATE SET value = excluded.value
            """, [
                metric_record_id,
                'demo-workspace-001',
                metric_id,
                date.strftime('%Y-%m-%d'),
                values[i],
                'quickbooks'
            ])

# Add some sample alerts
print("Adding sample alerts...")
conn.execute("""
INSERT INTO alerts (
    workspace_id,
    metric_id,
    rule_name,
    severity,
    status,
    message,
    current_value,
    threshold_value
)
VALUES (
    'demo-workspace-001',
    'gross_profit',
    'Gross Margin Below Target',
    'warning',
    'active',
    'Gross margin is 59.5%, below the 60% target',
    94800,
    96000
)
""")

print("✅ Demo environment initialized!")
print("\nDemo credentials:")
print("  Workspace ID: demo-workspace-001")
print("  Company: Craig's Design & Landscaping Services")
print("  QuickBooks: Connected (Sandbox)")

# Show summary
workspace_count = conn.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]
metrics_count = conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
alerts_count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]

print(f"\nDatabase summary:")
print(f"  Workspaces: {workspace_count}")
print(f"  Metrics: {metrics_count}")
print(f"  Alerts: {alerts_count}")

conn.close()