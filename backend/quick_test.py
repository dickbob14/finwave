#!/usr/bin/env python3
"""
Quick test script for FinWave Block D
Run this after the server is started
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test all major endpoints"""
    print("🧪 Testing FinWave Block D endpoints...")
    
    # Date range for testing
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    tests = [
        # Basic health checks
        ("GET", "/health", {}, "Health check"),
        ("GET", "/export/status", {}, "Export system status"),
        ("GET", "/charts/status", {}, "Charts system status"),
        ("GET", "/insight/status", {}, "Insights system status"),
        
        # Chart endpoints
        ("GET", "/charts/available-charts", {}, "Available chart types"),
        ("GET", "/charts/revenue-trend", {
            "start_date": start_date, 
            "end_date": end_date, 
            "grouping": "monthly"
        }, "Revenue trend chart"),
        ("GET", "/charts/expense-breakdown", {
            "start_date": start_date, 
            "end_date": end_date, 
            "chart_type": "pie"
        }, "Expense breakdown chart"),
        
        # Insight endpoints
        ("GET", "/insight/variance", {
            "start_date": start_date, 
            "end_date": end_date
        }, "Variance analysis"),
        ("POST", "/insight/analyze", {
            "question": "Why are expenses higher this month?",
            "start_date": start_date,
            "end_date": end_date
        }, "WHY question analysis"),
        
        # Export endpoints
        ("GET", "/export/formats", {}, "Export formats"),
    ]
    
    results = []
    
    for method, endpoint, params, description in tests:
        try:
            url = f"{BASE_URL}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, params=params, timeout=10)
            else:
                response = requests.post(url, json=params, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {description}: PASS")
                results.append((description, "PASS", response.status_code))
            else:
                print(f"⚠️ {description}: HTTP {response.status_code}")
                results.append((description, "FAIL", response.status_code))
                
        except Exception as e:
            print(f"❌ {description}: {e}")
            results.append((description, "ERROR", str(e)))
    
    print(f"\n📊 Test Results: {len([r for r in results if r[1] == 'PASS'])}/{len(results)} passed")
    
    return results

def test_chart_data():
    """Test chart data structure"""
    print("\n📊 Testing chart data structure...")
    
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    try:
        response = requests.get(f"{BASE_URL}/charts/revenue-trend", params={
            "start_date": start_date,
            "end_date": end_date,
            "grouping": "monthly"
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Check data structure
            required_keys = ["chart_type", "plotly_data", "data_points", "generated_at"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if not missing_keys:
                print("✅ Chart data structure: VALID")
                print(f"   └─ Data points: {data.get('data_points', 0)}")
                print(f"   └─ Chart type: {data.get('chart_type', 'unknown')}")
                
                # Check Plotly data structure
                plotly_data = data.get("plotly_data", {})
                if "data" in plotly_data and "layout" in plotly_data:
                    print("✅ Plotly data structure: VALID")
                else:
                    print("⚠️ Plotly data structure: INVALID")
            else:
                print(f"⚠️ Chart data missing keys: {missing_keys}")
        else:
            print(f"❌ Chart data request failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Chart data test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 FinWave Block D Test Suite\n")
    
    # Run endpoint tests
    test_endpoints()
    
    # Test chart data structure
    test_chart_data()
    
    print("\n✅ Testing complete!")
    print("\n📝 Frontend Integration:")
    print("Use the chart data from /charts/* endpoints directly in React components")
    print("Example: <Plot data={chartData.plotly_data.data} layout={chartData.plotly_data.layout} />")

if __name__ == "__main__":
    main()
