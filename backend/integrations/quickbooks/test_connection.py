#!/usr/bin/env python3
"""
Test QuickBooks connection with real credentials
Run this first to ensure OAuth is working
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from integrations.quickbooks.client import QuickBooksClient, test_connection
from config.field_mapper import get_field_mapper

def test_quickbooks_connection():
    """Test QuickBooks connection and basic data fetching"""
    
    print("🔌 Testing QuickBooks Connection")
    print("=" * 60)
    
    # Check for credentials in environment
    required_vars = ['QB_CLIENT_ID', 'QB_CLIENT_SECRET', 'QB_COMPANY_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("   ❌ Missing environment variables:")
        for var in missing_vars:
            print(f"      - {var}")
        print("\n   💡 Run: ./scripts/secure_setup.sh to configure credentials")
        return False
    
    # Set sandbox environment if not specified
    if not os.getenv('QB_ENVIRONMENT'):
        os.environ['QB_ENVIRONMENT'] = 'sandbox'
    
    # Test basic connection
    print("\n1️⃣ Testing basic connection...")
    if test_connection():
        print("   ✅ Successfully connected to QuickBooks!")
    else:
        print("   ❌ Connection failed - check credentials")
        return False
    
    # Create client
    client = QuickBooksClient()
    
    # Test company info fetch
    print("\n2️⃣ Fetching company information...")
    try:
        company_info = client.fetch_company_info()
        print(f"   ✅ Company: {company_info.get('CompanyName', 'Unknown')}")
        print(f"   📍 Country: {company_info.get('Country', 'Unknown')}")
        print(f"   💰 Currency: {company_info.get('Currency', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test GL fetch
    print("\n3️⃣ Testing GL data fetch...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        gl_df = client.fetch_gl(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if gl_df.empty:
            print("   ⚠️  No GL data found for the last 30 days")
            print("   💡 Trying last year...")
            
            # Try previous year
            end_date = end_date - timedelta(days=365)
            start_date = end_date - timedelta(days=30)
            
            gl_df = client.fetch_gl(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
        
        if not gl_df.empty:
            print(f"   ✅ Fetched {len(gl_df)} GL entries")
            print(f"   📅 Date range: {gl_df['Date'].min()} to {gl_df['Date'].max()}")
            
            # Show sample entries
            print("\n   Sample entries:")
            sample = gl_df.head(3)
            for _, row in sample.iterrows():
                print(f"      {row['Date'].strftime('%Y-%m-%d')} | {row['Account_Name'][:30]:30} | "
                      f"Dr: ${row['Debit']:8.2f} | Cr: ${row['Credit']:8.2f}")
        else:
            print("   ⚠️  No GL data found")
            
    except Exception as e:
        print(f"   ❌ GL fetch error: {e}")
        return False
    
    # Test field mapper
    print("\n4️⃣ Testing field mapper...")
    mapper = get_field_mapper()
    
    test_cases = [
        ('1000', 'Cash', 1000, 0),
        ('4000', 'Revenue', 0, 1000),
        ('5000', 'Expense', 500, 0),
    ]
    
    print("   Signed amount calculations:")
    for account, name, debit, credit in test_cases:
        signed = mapper.calculate_signed_amount(debit, credit, account, name)
        print(f"      {name:15} Dr:{debit:6} Cr:{credit:6} = {signed:+8.2f}")
    
    print("\n✨ QuickBooks integration is ready!")
    return True


if __name__ == '__main__':
    print("\n🔒 Using credentials from environment variables")
    print("   Run: export $(grep -v '^#' .env | xargs)")
    print("   Or: ./scripts/secure_setup.sh\n")
    
    success = test_quickbooks_connection()
    
    if success:
        print("\n🚀 Next steps:")
        print("   1. Move credentials to .env file")
        print("   2. Run: make populate-3statement-real")
        print("   3. Test API: POST /templates/3statement/refresh")
    
    exit(0 if success else 1)