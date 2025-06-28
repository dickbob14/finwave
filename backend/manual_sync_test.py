#!/usr/bin/env python3
"""
Manual QuickBooks sync test
Run this to check status and trigger sync
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"
WORKSPACE_ID = "default"  # or "demo"

def check_status():
    """Check QuickBooks connection status"""
    print("\n=== Checking QuickBooks Status ===")
    try:
        response = requests.get(f"{API_BASE}/api/{WORKSPACE_ID}/quickbooks/status")
        data = response.json()
        
        print(f"Status: {data.get('status')}")
        print(f"Realm ID: {data.get('realm_id')}")
        print(f"Token Valid: {data.get('token_valid')}")
        print(f"Last Synced: {data.get('last_synced')}")
        if data.get('last_error'):
            print(f"Last Error: {data.get('last_error')}")
        
        return data.get('status') == 'connected'
    except Exception as e:
        print(f"Error checking status: {e}")
        return False

def trigger_sync():
    """Manually trigger QuickBooks sync"""
    print("\n=== Triggering Manual Sync ===")
    try:
        response = requests.post(f"{API_BASE}/api/{WORKSPACE_ID}/quickbooks/sync")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Sync successful!")
            print(f"Records processed: {data.get('records_processed')}")
            print(f"Details: {json.dumps(data.get('details', {}), indent=2)}")
        else:
            print(f"✗ Sync failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error triggering sync: {e}")

def check_metrics():
    """Check stored metrics"""
    print("\n=== Checking Metrics ===")
    try:
        response = requests.get(f"{API_BASE}/api/{WORKSPACE_ID}/metrics")
        data = response.json()
        
        print(f"Total metrics: {data.get('count')}")
        print(f"Unique metrics: {data.get('unique_metrics')}")
        
        if data.get('metrics'):
            print("\nStored metrics:")
            for metric_id, values in data['metrics'].items():
                if values:
                    print(f"  {metric_id}: {values[0]['value']}")
    except Exception as e:
        print(f"Error checking metrics: {e}")

def check_dashboard_data():
    """Check dashboard data endpoint"""
    print("\n=== Checking Dashboard Data ===")
    try:
        response = requests.get(f"{API_BASE}/api/{WORKSPACE_ID}/dashboard/data")
        data = response.json()
        
        if data.get('has_data'):
            summary = data.get('summary', {})
            print(f"Revenue: ${summary.get('revenue', 0):,.2f}")
            print(f"Expenses: ${summary.get('expenses', 0):,.2f}")
            print(f"Net Profit: ${summary.get('net_profit', 0):,.2f}")
            print(f"Profit Margin: {summary.get('profit_margin', 0):.1f}%")
            print(f"Cash: ${summary.get('cash', 0):,.2f}")
            print(f"AR: ${summary.get('accounts_receivable', 0):,.2f}")
            print(f"Last sync: {data.get('last_sync')}")
        else:
            print("No data available - run sync first")
    except Exception as e:
        print(f"Error checking dashboard: {e}")

if __name__ == "__main__":
    print("QuickBooks Integration Test")
    print(f"API Base: {API_BASE}")
    print(f"Workspace: {WORKSPACE_ID}")
    
    # Check status
    connected = check_status()
    
    if connected:
        # Ask to trigger sync
        response = input("\nTrigger sync? (y/n): ")
        if response.lower() == 'y':
            trigger_sync()
            check_metrics()
            check_dashboard_data()
    else:
        print("\n✗ QuickBooks not connected. Please connect via Settings page first.")