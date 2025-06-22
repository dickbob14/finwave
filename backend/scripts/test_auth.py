#!/usr/bin/env python3
"""
Test authentication and workspace setup
"""

import os
import sys
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_auth_bypass():
    """Test API with auth bypass enabled"""
    print("🧪 Testing Auth Bypass Mode")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api"
    
    # Test without token (should work in bypass mode)
    print("\n1️⃣ Testing /workspaces/current without token...")
    try:
        response = requests.get(f"{base_url}/workspaces/current")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data}")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test templates endpoint
    print("\n2️⃣ Testing /templates/ without token...")
    try:
        response = requests.get(f"{base_url}/templates/")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Found {len(data.get('templates', []))} templates")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test CRM status
    print("\n3️⃣ Testing /crm/status without token...")
    try:
        response = requests.get(f"{base_url}/crm/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: CRM {data.get('crm_type')} - Connected: {data.get('connected')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_auth_enabled():
    """Test API with real auth"""
    print("\n🔐 Testing Real Auth Mode")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api"
    
    # Test without token (should fail)
    print("\n1️⃣ Testing /workspaces/current without token...")
    try:
        response = requests.get(f"{base_url}/workspaces/current")
        
        if response.status_code == 401:
            print("   ✅ Correctly rejected (401 Unauthorized)")
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test with invalid token
    print("\n2️⃣ Testing with invalid token...")
    headers = {"Authorization": "Bearer invalid-token"}
    try:
        response = requests.get(f"{base_url}/workspaces/current", headers=headers)
        
        if response.status_code == 401:
            print("   ✅ Correctly rejected invalid token")
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def check_environment():
    """Check environment setup"""
    print("\n🔍 Environment Check")
    print("=" * 60)
    
    vars_to_check = [
        "AUTH0_DOMAIN",
        "AUTH0_API_AUDIENCE",
        "BYPASS_AUTH",
        "DATABASE_URL",
        "COMPANY_SLUG"
    ]
    
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "token" in var.lower() or "secret" in var.lower():
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Check auth mode
    bypass_auth = os.getenv("BYPASS_AUTH", "false").lower() == "true"
    print(f"\n   Auth Mode: {'BYPASSED (Dev)' if bypass_auth else 'ENABLED (Production)'}")


def main():
    print("🔒 FinWave Auth System Test")
    print("=" * 60)
    
    # Check environment
    check_environment()
    
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
    
    # Run appropriate test based on auth mode
    bypass_auth = os.getenv("BYPASS_AUTH", "false").lower() == "true"
    
    if bypass_auth:
        test_auth_bypass()
        print("\n⚠️  Auth is bypassed for development")
        print("   Set BYPASS_AUTH=false for production mode")
    else:
        test_auth_enabled()
        print("\n✅ Auth is enabled (production mode)")
    
    print("\n✨ Auth test complete!")


if __name__ == '__main__':
    main()