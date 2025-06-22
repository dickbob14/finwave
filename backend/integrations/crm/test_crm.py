#!/usr/bin/env python3
"""
Test CRM integration and field mappings
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from integrations.crm.client import create_crm_client, test_crm_connection
from config.field_mapper import FieldMapper

def test_crm_integration(crm_type: str = 'salesforce'):
    """Test CRM integration with field mapping"""
    
    print(f"🧪 Testing {crm_type.title()} CRM Integration")
    print("=" * 60)
    
    # Test connection
    print(f"\n1️⃣ Testing connection to {crm_type}...")
    if test_crm_connection(crm_type):
        print("   ✅ Connection successful")
    else:
        print("   ❌ Connection failed - check credentials")
        return False
    
    # Test field mapping
    print(f"\n2️⃣ Testing field mappings...")
    try:
        mapper = FieldMapper('config/field_maps/crm.yml')
        print(f"   ✅ Loaded CRM field mappings")
        
        # Show mapped fields
        crm_config = mapper.config.get(crm_type, {})
        print(f"\n   Mapped sections for {crm_type}:")
        for section in crm_config.keys():
            print(f"   - {section}")
            
    except Exception as e:
        print(f"   ❌ Failed to load mappings: {e}")
        return False
    
    # Test data fetch
    print(f"\n3️⃣ Testing data fetch...")
    try:
        client = create_crm_client(crm_type)
        
        # Test date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Fetch opportunities
        print(f"   Fetching opportunities from last 30 days...")
        opps_df = client.fetch_opportunities(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not opps_df.empty:
            print(f"   ✅ Found {len(opps_df)} opportunities")
            
            # Apply field mapping
            mapped_df = mapper.map_dataframe(opps_df, f'{crm_type}.opportunities')
            print(f"   ✅ Successfully mapped fields")
            
            # Show sample data
            print(f"\n   Sample mapped fields:")
            for col in ['Deal_ID', 'Company_Name', 'Deal_Value', 'Sales_Stage', 'Close_Date']:
                if col in mapped_df.columns:
                    print(f"   - {col}: {mapped_df[col].iloc[0] if len(mapped_df) > 0 else 'N/A'}")
        else:
            print("   ⚠️  No opportunities found in date range")
            
        # Test metrics summary
        print(f"\n   Fetching metrics summary...")
        metrics = client.get_metrics_summary()
        
        print(f"   ✅ Metrics retrieved:")
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"   - {key}: ${value:,.0f}" if 'value' in key else f"   - {key}: {value}")
            
    except Exception as e:
        print(f"   ❌ Error fetching data: {e}")
        return False
    
    print(f"\n✨ {crm_type.title()} integration test complete!")
    return True


if __name__ == '__main__':
    # Get CRM type from command line or environment
    crm_type = sys.argv[1] if len(sys.argv) > 1 else os.getenv('CRM_TYPE', 'salesforce')
    
    # Check for credentials
    if crm_type == 'salesforce':
        required_vars = ['SF_INSTANCE_URL', 'SF_ACCESS_TOKEN']
    else:
        required_vars = ['HUBSPOT_ACCESS_TOKEN']
        
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print(f"   Using sample data mode for testing")
    
    # Run test
    success = test_crm_integration(crm_type)
    exit(0 if success else 1)