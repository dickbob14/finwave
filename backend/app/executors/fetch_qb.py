import datetime as dt, requests, os, json, pathlib
from typing import Dict, List, Any, Optional
from ..quickbooks_auth import ensure_token

_SAMPLE = pathlib.Path(__file__).with_name("sample_qb.json")

def _sandbox_company_id() -> str:
    from ..quickbooks_auth import _load
    tok = _load()
    return tok.get("realm_id") if tok else ""

def _build_qb_query(entities: List[str], filters: Dict[str, Any]) -> List[str]:
    """Build QuickBooks SQL queries for multiple entities with filters"""
    queries = []
    
    for entity in entities:
        query_parts = [f"SELECT * FROM {entity}"]
        where_conditions = []
        
        # Date filters
        if "days" in filters:
            date_threshold = (dt.date.today() - dt.timedelta(days=filters["days"])).strftime("%Y-%m-%d")
            if entity in ["Invoice", "Bill", "Expense", "Purchase", "SalesReceipt"]:
                where_conditions.append(f"TxnDate >= '{date_threshold}'")
            elif entity == "JournalEntry":
                where_conditions.append(f"TxnDate >= '{date_threshold}'")
        
        # Account type filters
        if "account_type" in filters and entity == "Account":
            where_conditions.append(f"AccountType = '{filters['account_type']}'")
        
        # Item type filters  
        if "item_type" in filters and entity == "Item":
            types = filters["item_type"].split(",")
            type_conditions = " OR ".join([f"Type = '{t.strip()}'" for t in types])
            where_conditions.append(f"({type_conditions})")
        
        # Status filters
        if "status" in filters:
            if entity == "Invoice" and filters["status"] == "unpaid":
                where_conditions.append("Balance > 0")
            elif entity == "Bill" and filters["status"] == "unpaid":
                where_conditions.append("Balance > 0")
        
        # Add WHERE clause if conditions exist
        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))
        
        # Add MAXRESULTS to avoid large responses
        query_parts.append("MAXRESULTS 100")
        
        queries.append(" ".join(query_parts))
    
    return queries

def _execute_qb_queries(queries: List[str], headers: Dict[str, str], base_url: str) -> Dict[str, List[Dict]]:
    """Execute multiple QuickBooks queries and return organized results"""
    results = {}
    
    for query in queries:
        try:
            resp = requests.get(f"{base_url}/query", headers=headers, params={"query": query})
            resp.raise_for_status()
            result = resp.json()
            
            # Extract entity type from query
            entity = query.split("FROM ")[1].split(" ")[0]
            
            # Store results
            query_response = result.get("QueryResponse", {})
            if entity in query_response:
                results[entity] = query_response[entity]
                print(f"✓ Found {len(results[entity])} {entity} records")
            else:
                results[entity] = []
                print(f"✗ No {entity} records found")
                
        except Exception as e:
            print(f"✗ Error querying {entity}: {e}")
            entity = query.split("FROM ")[1].split(" ")[0]
            results[entity] = []
    
    return results

def _normalize_qb_data(results: Dict[str, List[Dict]]) -> List[Dict]:
    """Convert QuickBooks entity data into normalized transaction format"""
    transactions = []
    
    for entity_type, records in results.items():
        for record in records:
            try:
                # Extract common fields with fallbacks
                transaction = {
                    "id": record.get("Id", f"{entity_type}_{len(transactions)}"),
                    "entity_type": entity_type,
                    "date": record.get("TxnDate") or record.get("MetaData", {}).get("CreateTime", str(dt.date.today())),
                    "name": (record.get("Name") or 
                            record.get("FullyQualifiedName") or 
                            record.get("DisplayName") or 
                            f"{entity_type} {record.get('Id', '')}"),
                }
                
                # Extract amount based on entity type
                if entity_type == "Invoice":
                    transaction["amount"] = float(record.get("TotalAmt", 0))
                    transaction["type"] = "revenue"
                    transaction["customer"] = record.get("CustomerRef", {}).get("name", "Unknown")
                    
                elif entity_type == "Bill":
                    transaction["amount"] = -float(record.get("TotalAmt", 0))  # Negative for expenses
                    transaction["type"] = "expense" 
                    transaction["vendor"] = record.get("VendorRef", {}).get("name", "Unknown")
                    
                elif entity_type == "Expense":
                    transaction["amount"] = -float(record.get("TotalAmt", 0))
                    transaction["type"] = "expense"
                    transaction["vendor"] = record.get("EntityRef", {}).get("name", "Unknown")
                    
                elif entity_type == "Purchase":
                    transaction["amount"] = -float(record.get("TotalAmt", 0))
                    transaction["type"] = "expense"
                    transaction["vendor"] = record.get("EntityRef", {}).get("name", "Unknown")
                    
                elif entity_type == "SalesReceipt":
                    transaction["amount"] = float(record.get("TotalAmt", 0))
                    transaction["type"] = "revenue"
                    transaction["customer"] = record.get("CustomerRef", {}).get("name", "Unknown")
                    
                elif entity_type == "Item":
                    transaction["amount"] = float(record.get("UnitPrice", 0))
                    transaction["type"] = "inventory"
                    transaction["item_type"] = record.get("Type", "Unknown")
                    transaction["quantity_on_hand"] = record.get("QtyOnHand", 0)
                    
                elif entity_type == "Account":
                    transaction["amount"] = float(record.get("CurrentBalance", 0))
                    transaction["type"] = "account"
                    transaction["account_type"] = record.get("AccountType", "Unknown")
                    
                elif entity_type == "Customer":
                    transaction["amount"] = float(record.get("Balance", 0))
                    transaction["type"] = "customer"
                    
                elif entity_type == "Vendor":
                    transaction["amount"] = -float(record.get("Balance", 0))
                    transaction["type"] = "vendor"
                    
                else:
                    # Generic handling for other entities
                    transaction["amount"] = float(record.get("Amount", record.get("TotalAmt", 0)))
                    transaction["type"] = "other"
                
                # Add raw data for analysis
                transaction["raw_data"] = record
                transactions.append(transaction)
                
            except Exception as e:
                print(f"✗ Error normalizing {entity_type} record: {e}")
                continue
    
    return transactions

def fetch_qb(entities: List[str] = None, filters: Dict[str, Any] = None, **kwargs) -> Dict:
    """
    Enhanced QuickBooks data fetcher supporting multiple entities and complex queries
    
    Args:
        entities: List of QB entities to fetch (Invoice, Bill, Item, Customer, etc.)
        filters: Query filters (days, account_type, item_type, status, etc.)
        **kwargs: Legacy support for simple queries
    """
    # Handle legacy calls
    if entities is None:
        entities = ["Item", "Account", "Customer", "Vendor"]
    if filters is None:
        filters = kwargs
        if "days" not in filters:
            filters["days"] = 90
    
    tokens = ensure_token()
    if not tokens:
        print("No QB tokens found, using sample data")
        # Enhanced sample data for testing
        sample_data = [
            {"id": "inv_001", "entity_type": "Invoice", "date": "2025-06-01", "amount": 5000, "type": "revenue", "customer": "ABC Corp"},
            {"id": "bill_001", "entity_type": "Bill", "date": "2025-06-05", "amount": -1200, "type": "expense", "vendor": "Office Supplies Inc"},
            {"id": "item_001", "entity_type": "Item", "date": "2025-06-10", "amount": 500, "type": "inventory", "name": "Widget A", "quantity_on_hand": 100},
            {"id": "exp_001", "entity_type": "Expense", "date": "2025-06-15", "amount": -300, "type": "expense", "vendor": "Gas Station"},
        ]
        return {"transactions": sample_data}

    # Build and execute queries
    company_id = _sandbox_company_id()
    base_url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{company_id}"
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }
    
    try:
        queries = _build_qb_query(entities, filters)
        print(f"Executing {len(queries)} QuickBooks queries...")
        
        raw_results = _execute_qb_queries(queries, headers, base_url)
        normalized_data = _normalize_qb_data(raw_results)
        
        print(f"✓ Successfully fetched {len(normalized_data)} transactions from QuickBooks")
        return {"transactions": normalized_data}
        
    except Exception as e:
        print(f"✗ QuickBooks API error: {e}")
        # Fallback to sample data with error info
        return {
            "transactions": [
                {"id": "sample_1", "entity_type": "Sample", "date": str(dt.date.today()), "amount": 1000, "type": "revenue", "name": "Sample Data"},
                {"id": "sample_2", "entity_type": "Sample", "date": str(dt.date.today() - dt.timedelta(days=30)), "amount": -500, "type": "expense", "name": "Sample Expense"}
            ],
            "error": f"QB API Error: {str(e)}"
        }