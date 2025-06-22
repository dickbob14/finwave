#!/usr/bin/env python3
"""
Comprehensive test suite for Block D functionality
Tests all major endpoints and features
"""
import requests
import json
import tempfile
import os
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_system_health():
    """Test all system health endpoints"""
    print("🏥 Testing system health...")
    
    endpoints = [
        "/export/status",
        "/report/status", 
        "/insight/status",
        "/charts/status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status = response.json()
            print(f"✓ {endpoint}: {status.get('status', 'unknown')}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_chart_endpoints():
    """Test chart data endpoints"""
    print("\n📊 Testing chart endpoints...")
    
    # Date range for testing
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    chart_tests = [
        ("/charts/available-charts", {}),
        ("/charts/revenue-trend", {
            "start_date": start_date,
            "end_date": end_date,
            "grouping": "monthly"
        }),
        ("/charts/expense-breakdown", {
            "start_date": start_date,
            "end_date": end_date,
            "chart_type": "pie"
        }),
        ("/charts/profit-margin", {
            "start_date": start_date,
            "end_date": end_date,
            "grouping": "monthly"
        }),
        ("/charts/kpi-dashboard", {
            "start_date": start_date,
            "end_date": end_date
        })
    ]
    
    for endpoint, params in chart_tests:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {endpoint}: {data.get('data_points', 'N/A')} data points")
                
                # Check if Plotly data is present
                if 'plotly_data' in data:
                    print(f"   └─ Plotly data ready for frontend")
            else:
                print(f"⚠️  {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_insight_endpoints():
    """Test insight and variance analysis"""
    print("\n🧠 Testing insight endpoints...")
    
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    # Test variance analysis
    try:
        response = requests.get(f"{BASE_URL}/insight/variance", params={
            "start_date": start_date,
            "end_date": end_date
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Variance analysis: {data['summary']['total_variances']} variances found")
        else:
            print(f"⚠️  Variance analysis: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Variance analysis: {e}")
    
    # Test WHY question
    try:
        response = requests.post(f"{BASE_URL}/insight/analyze", json={
            "question": "Why are expenses higher this month?",
            "start_date": start_date,
            "end_date": end_date
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✓ WHY question analysis: {data['analysis']['answer_type']}")
        else:
            print(f"⚠️  WHY question: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ WHY question: {e}")
    
    # Test trend analysis
    try:
        response = requests.get(f"{BASE_URL}/insight/trends", params={
            "lookback_months": 6
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Trend analysis: {data['summary']['total_accounts_analyzed']} accounts analyzed")
        else:
            print(f"⚠️  Trend analysis: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Trend analysis: {e}")

def test_export_endpoints():
    """Test export functionality"""
    print("\n📤 Testing export endpoints...")
    
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    # Test Excel export
    try:
        response = requests.get(f"{BASE_URL}/export/excel", params={
            "start_date": start_date,
            "end_date": end_date,
            "filename": "test_export"
        })
        if response.status_code == 200:
            print(f"✓ Excel export: {len(response.content)} bytes generated")
            
            # Save to temp file to verify
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                f.write(response.content)
                print(f"   └─ Saved to: {f.name}")
        else:
            print(f"⚠️  Excel export: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Excel export: {e}")
    
    # Test formats endpoint
    try:
        response = requests.get(f"{BASE_URL}/export/formats")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Export formats: {len(data['formats'])} formats available")
        else:
            print(f"⚠️  Export formats: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Export formats: {e}")

def test_report_endpoints():
    """Test PDF report generation"""
    print("\n📋 Testing report endpoints...")
    
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    # Test executive report
    try:
        response = requests.get(f"{BASE_URL}/report/executive", params={
            "start_date": start_date,
            "end_date": end_date,
            "include_commentary": True
        })
        if response.status_code == 200:
            print(f"✓ Executive report: {len(response.content)} bytes PDF generated")
        else:
            print(f"⚠️  Executive report: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Executive report: {e}")
    
    # Test commentary generation
    try:
        response = requests.post(f"{BASE_URL}/report/commentary", params={
            "start_date": start_date,
            "end_date": end_date,
            "llm_provider": "mock"  # Use mock to avoid API key requirements
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✓ AI commentary: {len(data['recommendations'])} recommendations")
        else:
            print(f"⚠️  AI commentary: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ AI commentary: {e}")

def test_integration_features():
    """Test integration manager features"""
    print("\n🔗 Testing integration features...")
    
    try:
        # Import integration manager
        import sys
        sys.path.append('.')
        from integrations.integration_manager import IntegrationManager
        
        manager = IntegrationManager()
        status = manager.get_integration_status()
        
        print(f"✓ Integration manager: {status['total_configured']}/{status['total_active']} integrations")
        
        for name, config in status['integrations'].items():
            creds_status = "✓" if config['credentials_configured'] else "⚠️"
            print(f"   {creds_status} {name}: {config['status']}")
            
    except Exception as e:
        print(f"❌ Integration manager: {e}")

def generate_sample_frontend_code():
    """Generate sample frontend integration code"""
    print("\n💻 Sample frontend integration code:")
    
    frontend_code = '''
// React component for FinWave charts
import { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';

function FinWaveChart({ chartType, startDate, endDate }) {
  const [chartData, setChartData] = useState(null);
  
  useEffect(() => {
    // Fetch chart data from FinWave API
    fetch(`/api/charts/${chartType}?start_date=${startDate}&end_date=${endDate}`)
      .then(res => res.json())
      .then(data => {
        setChartData(data.plotly_data);
      });
  }, [chartType, startDate, endDate]);
  
  if (!chartData) return <div>Loading chart...</div>;
  
  return (
    <Plot
      data={chartData.data}
      layout={chartData.layout}
      style={{width: "100%", height: "400px"}}
    />
  );
}

// Usage examples:
// <FinWaveChart chartType="revenue-trend" startDate="2024-01-01" endDate="2024-12-31" />
// <FinWaveChart chartType="expense-breakdown" startDate="2024-09-01" endDate="2024-09-30" />

// Get financial insights
async function getFinancialInsights(question, startDate, endDate) {
  const response = await fetch('/api/insight/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      start_date: startDate,
      end_date: endDate
    })
  });
  
  return response.json();
}

// Download reports
function downloadReport(type, startDate, endDate) {
  const url = `/api/report/${type}?start_date=${startDate}&end_date=${endDate}`;
  window.open(url, '_blank');
}
    '''
    
    print(frontend_code)

def main():
    """Run complete test suite"""
    print("🚀 Starting Block D comprehensive test suite...\n")
    
    test_system_health()
    test_chart_endpoints()
    test_insight_endpoints() 
    test_export_endpoints()
    test_report_endpoints()
    test_integration_features()
    generate_sample_frontend_code()
    
    print("\n✅ Test suite complete!")
    print("\n📝 Next steps:")
    print("1. Check all endpoints returned 200 status")
    print("2. Review generated files in temp directory")
    print("3. Test frontend integration with sample code above")
    print("4. Configure external integrations (Salesforce, HubSpot, Nue)")

if __name__ == "__main__":
    main()
    