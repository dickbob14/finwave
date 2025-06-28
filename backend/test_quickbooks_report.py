#!/usr/bin/env python3
"""
Test script to fetch and display QuickBooks Balance Sheet report structure.
This helps understand the exact format QuickBooks returns.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integrations.quickbooks.client import QuickBooksClient
from core.database import get_db
from models.workspace import Workspace
from models.integration import IntegrationCredential

# Load environment variables
load_dotenv()

def fetch_balance_sheet_structure():
    """Fetch and display the structure of a QuickBooks Balance Sheet report."""
    
    print("=== QuickBooks Balance Sheet Report Structure Test ===\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get the first workspace with QuickBooks integration
        integration = db.query(IntegrationCredential).filter(
            IntegrationCredential.source == "quickbooks",
            IntegrationCredential.status == "connected"
        ).first()
        
        if not integration:
            print("ERROR: No active QuickBooks integration found.")
            print("Please connect QuickBooks first through the web interface.")
            return
        
        print(f"Using workspace ID: {integration.workspace_id}")
        
        # Decrypt tokens and metadata
        from core.crypto import decrypt
        access_token = decrypt(integration.access_token_encrypted)
        refresh_token = decrypt(integration.refresh_token_encrypted) if integration.refresh_token_encrypted else None
        
        # Get company ID from metadata
        metadata = {}
        if integration.metadata_encrypted:
            import json
            metadata = json.loads(decrypt(integration.metadata_encrypted))
        
        company_id = metadata.get('realm_id') or metadata.get('company_id')
        print(f"QuickBooks Company ID: {company_id or 'N/A'}\n")
        
        # Initialize QuickBooks client
        qb_client = QuickBooksClient(
            client_id=os.getenv("QUICKBOOKS_CLIENT_ID"),
            client_secret=os.getenv("QUICKBOOKS_CLIENT_SECRET"),
            company_id=company_id
        )
        
        # Set tokens
        qb_client.access_token = access_token
        qb_client.refresh_token_value = refresh_token
        
        # Calculate date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"Fetching Balance Sheet for period: {start_date.date()} to {end_date.date()}\n")
        
        # Fetch balance sheet (uses as_of_date)
        as_of_date = end_date.strftime("%Y-%m-%d")
        balance_sheet = qb_client.get_balance_sheet_report(as_of_date)
        
        # Display the raw JSON structure
        print("=== RAW BALANCE SHEET JSON STRUCTURE ===")
        print(json.dumps(balance_sheet, indent=2))
        
        # Analyze the structure
        print("\n=== STRUCTURE ANALYSIS ===")
        
        # Top-level keys
        print("\nTop-level keys:")
        for key in balance_sheet.keys():
            print(f"  - {key}: {type(balance_sheet[key]).__name__}")
        
        # Header structure
        if "Header" in balance_sheet:
            print("\nHeader structure:")
            header = balance_sheet["Header"]
            for key, value in header.items():
                print(f"  - {key}: {value}")
        
        # Column structure
        if "Columns" in balance_sheet:
            print("\nColumns structure:")
            columns = balance_sheet["Columns"]
            if "Column" in columns:
                for i, col in enumerate(columns["Column"]):
                    print(f"  Column {i}: {col}")
        
        # Rows structure (first few rows)
        if "Rows" in balance_sheet:
            print("\nRows structure (first 5 rows):")
            rows = balance_sheet["Rows"]
            if "Row" in rows:
                for i, row in enumerate(rows["Row"][:5]):
                    print(f"\n  Row {i}:")
                    print(f"    Type: {row.get('type', 'N/A')}")
                    if "group" in row:
                        print(f"    Group: {row.get('group', 'N/A')}")
                    
                    # Show ColData if present
                    if "ColData" in row:
                        print("    ColData:")
                        for j, col in enumerate(row["ColData"]):
                            print(f"      [{j}]: {col}")
                    
                    # Show Summary if present
                    if "Summary" in row:
                        print(f"    Summary: {row['Summary']}")
                    
                    # Show Rows (nested) if present
                    if "Rows" in row and row["Rows"]:
                        print(f"    Has nested rows: {len(row['Rows'].get('Row', []))} rows")
        
        # Also fetch and display Profit & Loss for comparison
        print("\n\n=== PROFIT & LOSS REPORT STRUCTURE (for comparison) ===")
        
        pnl = qb_client.get_profit_loss_report(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        print("\nTop-level keys:")
        for key in pnl.keys():
            print(f"  - {key}: {type(pnl[key]).__name__}")
        
        # Save full structures to files for reference
        with open("balance_sheet_structure.json", "w") as f:
            json.dump(balance_sheet, f, indent=2)
        print("\n✓ Full Balance Sheet structure saved to: balance_sheet_structure.json")
        
        with open("profit_loss_structure.json", "w") as f:
            json.dump(pnl, f, indent=2)
        print("✓ Full Profit & Loss structure saved to: profit_loss_structure.json")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    fetch_balance_sheet_structure()