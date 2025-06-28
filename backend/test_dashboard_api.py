#!/usr/bin/env python3
"""
Test dashboard API endpoints
"""

import requests
import json

def test_metrics_api():
    """Test the metrics API endpoints"""
    
    base_url = "http://localhost:8000/api"
    workspace_id = "default"
    
    print("=== Testing Dashboard API Endpoints ===\n")
    
    # Test 1: Metrics Summary
    print("1. Testing Metrics Summary:")
    try:
        response = requests.get(f"{base_url}/{workspace_id}/metrics/summary")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Revenue: ${data.get('revenue', {}).get('value', 0):,.2f}")
            print(f"   Expenses: ${data.get('expenses', {}).get('value', 0):,.2f}")
            print(f"   Cash: ${data.get('cash', {}).get('value', 0):,.2f}")
            print(f"   Runway: {data.get('runway', {}).get('value', 0):.1f} months")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 2: Metrics List
    print("\n2. Testing Metrics List:")
    try:
        response = requests.get(f"{base_url}/{workspace_id}/metrics")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            metrics = response.json()
            print(f"   Total metrics: {len(metrics)}")
            # Show first 5
            for m in metrics[:5]:
                print(f"   - {m['metric_id']}: {m['value']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test 3: Specific Metric Time Series
    print("\n3. Testing Time Series (revenue):")
    try:
        response = requests.get(f"{base_url}/{workspace_id}/metrics/revenue")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Data points: {len(data)}")
            for point in data:
                print(f"   - {point['period']}: ${point['value']:,.2f}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    print("\n✅ API test completed")


if __name__ == "__main__":
    test_metrics_api()