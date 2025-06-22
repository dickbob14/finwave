#!/usr/bin/env python3
"""
Test metric store functionality
"""

import os
import sys
import requests
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_metric_ingestion():
    """Test ingesting metrics from Excel file"""
    print("🧪 Testing Metric Store")
    print("=" * 60)
    
    # Find a populated Excel file
    populated_dir = Path("templates/populated")
    excel_files = list(populated_dir.glob("*.xlsx")) if populated_dir.exists() else []
    
    if not excel_files:
        print("❌ No populated Excel files found")
        print("   Run: make populate-3statement-real")
        return False
    
    test_file = excel_files[0]
    print(f"📊 Using file: {test_file.name}")
    
    # Test ingestion via CLI
    print("\n1️⃣ Testing CLI ingestion...")
    cmd = f"python -m metrics.ingest --workspace demo --file {test_file}"
    result = os.system(cmd)
    
    if result == 0:
        print("   ✅ CLI ingestion successful")
    else:
        print("   ❌ CLI ingestion failed")
        return False
    
    return True

def test_metrics_api():
    """Test metrics API endpoints"""
    print("\n2️⃣ Testing Metrics API...")
    
    base_url = "http://localhost:8000/api"
    workspace = "demo"
    
    # Test 1: Get all metrics
    print("   Testing GET /metrics...")
    try:
        response = requests.get(f"{base_url}/{workspace}/metrics")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['count']} metrics")
            
            # Show sample metrics
            if data['metrics']:
                print("\n   Sample metrics:")
                for m in data['metrics'][:3]:
                    print(f"   - {m['metric_id']}: {m['value']:,.2f} ({m['period_date']})")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Get metrics summary
    print("\n   Testing GET /metrics/summary...")
    try:
        response = requests.get(f"{base_url}/{workspace}/metrics/summary")
        if response.status_code == 200:
            data = response.json()
            if data['period']:
                print(f"   ✅ Latest period: {data['period']}")
                print(f"   ✅ Metrics available: {len(data['metrics'])}")
                
                # Show key metrics
                key_metrics = ['revenue', 'ebitda', 'mrr', 'burn_rate']
                print("\n   Key metrics:")
                for metric in key_metrics:
                    if metric in data['metrics']:
                        value = data['metrics'][metric]['value']
                        unit = data['metrics'][metric].get('unit', '')
                        if unit == 'dollars':
                            print(f"   - {metric}: ${value:,.0f}")
                        elif unit == 'percentage':
                            print(f"   - {metric}: {value:.1f}%")
                        else:
                            print(f"   - {metric}: {value}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get time series
    print("\n   Testing GET /metrics/timeseries...")
    try:
        response = requests.get(f"{base_url}/{workspace}/metrics/timeseries?metric_id=revenue&periods=6")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Time series for {data['metric_id']}: {data['periods']} periods")
            
            if data['series']:
                print("\n   Revenue trend:")
                for point in data['series'][-3:]:
                    print(f"   - {point['period']}: ${point['value']:,.0f}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get available metrics
    print("\n   Testing GET /metrics/available...")
    try:
        response = requests.get(f"{base_url}/{workspace}/metrics/available")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Available metrics: {data['count']}")
            
            # List metrics
            if data['metrics']:
                print("\n   Available metrics:")
                for m in data['metrics'][:5]:
                    print(f"   - {m['metric_id']} ({m['display_name']})")
                if data['count'] > 5:
                    print(f"   ... and {data['count'] - 5} more")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return True

def test_database_setup():
    """Test database configuration"""
    print("\n3️⃣ Testing Database Setup...")
    
    # Check metric store setting
    metric_store = os.getenv("METRIC_STORE", "postgres")
    print(f"   Metric store: {metric_store}")
    
    if metric_store == "duckdb":
        duckdb_path = os.getenv("DUCKDB_PATH", "metrics.duckdb")
        if Path(duckdb_path).exists():
            print(f"   ✅ DuckDB file exists: {duckdb_path}")
        else:
            print(f"   ⚠️  DuckDB file not found: {duckdb_path}")
            print("   It will be created on first use")
    else:
        db_url = os.getenv("DATABASE_URL", "")
        if "postgresql" in db_url:
            print("   ✅ PostgreSQL configured")
        else:
            print("   ⚠️  DATABASE_URL not set")
    
    return True

def main():
    print("📊 FinWave Metric Store Test")
    print("=" * 60)
    
    # Check if server is running
    print("\n🌐 Checking API server...")
    try:
        response = requests.get("http://localhost:8000/api/docs")
        if response.status_code == 200:
            print("   ✅ API server is running")
        else:
            print("   ❌ API server returned:", response.status_code)
            print("\n   💡 Start the server with: make server")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ API server is not running")
        print("\n   💡 Start the server with: make server")
        return
    
    # Run tests
    test_database_setup()
    
    if test_metric_ingestion():
        test_metrics_api()
    
    print("\n✨ Metric store test complete!")
    print("\nNext steps:")
    print("1. Update populators to add named ranges")
    print("2. Update Templates page to use /metrics API")
    print("3. Update Insight Engine to query metric store")

if __name__ == '__main__':
    main()