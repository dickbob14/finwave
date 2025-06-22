"""
QuickBooks full-ledger ingestion using Reports and Accounting APIs
Handles trial balance, P&L, balance sheet, and transaction detail extraction
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import get_db_session
from models.financial import (
    IngestionHistory, GeneralLedger, Account, Customer, Vendor, Item,
    FinancialPeriod, DataSource, Base
)

logger = logging.getLogger(__name__)

class QuickBooksIngestor:
    """Full-ledger QuickBooks data ingestion using Reports and Accounting APIs"""
    
    def __init__(self, access_token: str, company_id: str, base_url: str = "https://sandbox-quickbooks.api.intuit.com"):
        self.access_token = access_token
        self.company_id = company_id
        self.base_url = base_url
        self.session = httpx.AsyncClient()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to QB API"""
        url = f"{self.base_url}/v3/company/{self.company_id}/{endpoint}"
        
        try:
            response = await self.session.get(
                url, 
                headers=self._get_headers(),
                params=params or {}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"QB API error for {endpoint}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise
    
    async def get_company_info(self) -> Dict:
        """Get company information"""
        return await self._make_request("companyinfo/1")
    
    async def ingest_full_ledger(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Full ledger ingestion from QuickBooks
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            
        Returns:
            Dict with counts of ingested records by entity type
        """
        ingestion_stats = {}
        
        with get_db_session() as db:
            # Create ingestion history records
            ingestion_start = datetime.now()
            
            try:
                # 1. Ingest Chart of Accounts
                accounts_count = await self._ingest_accounts(db, start_date, end_date)
                ingestion_stats['accounts'] = accounts_count
                
                # 2. Ingest Customers
                customers_count = await self._ingest_customers(db, start_date, end_date)
                ingestion_stats['customers'] = customers_count
                
                # 3. Ingest Vendors
                vendors_count = await self._ingest_vendors(db, start_date, end_date)
                ingestion_stats['vendors'] = vendors_count
                
                # 4. Ingest Items
                items_count = await self._ingest_items(db, start_date, end_date)
                ingestion_stats['items'] = items_count
                
                # 5. Ingest General Ledger from Trial Balance
                gl_count = await self._ingest_trial_balance(db, start_date, end_date)
                ingestion_stats['trial_balance'] = gl_count
                
                # 6. Ingest detailed transactions
                transactions_count = await self._ingest_transactions(db, start_date, end_date)
                ingestion_stats['transactions'] = transactions_count
                
                logger.info(f"Full ledger ingestion completed: {ingestion_stats}")
                return ingestion_stats
                
            except Exception as e:
                logger.error(f"Ingestion failed: {str(e)}")
                # Mark failed ingestion records
                failed_records = db.query(IngestionHistory).filter(
                    and_(
                        IngestionHistory.period_start == datetime.fromisoformat(start_date),
                        IngestionHistory.period_end == datetime.fromisoformat(end_date),
                        IngestionHistory.status == 'pending'
                    )
                ).all()
                
                for record in failed_records:
                    record.status = 'failed'
                    record.error_message = str(e)
                    
                db.commit()
                raise
    
    async def _ingest_accounts(self, db: Session, start_date: str, end_date: str) -> int:
        """Ingest chart of accounts"""
        # Create ingestion history record
        ingestion_record = IngestionHistory(
            source='quickbooks',
            entity_type='accounts',
            period_start=datetime.fromisoformat(start_date),
            period_end=datetime.fromisoformat(end_date),
            status='pending'
        )
        db.add(ingestion_record)
        db.commit()
        
        try:
            # Get accounts from QB
            response = await self._make_request("query", {
                "query": "SELECT * FROM Account MAXRESULTS 1000"
            })
            
            accounts_data = response.get('QueryResponse', {}).get('Account', [])
            count = 0
            
            for account_data in accounts_data:
                # Check if account already exists
                existing = db.query(Account).filter(
                    Account.source_id == account_data['Id']
                ).first()
                
                if existing:
                    # Update existing account
                    self._update_account_from_qb(existing, account_data)
                else:
                    # Create new account
                    account = self._create_account_from_qb(account_data)
                    db.add(account)
                
                count += 1
            
            # Update ingestion record
            ingestion_record.status = 'completed'
            ingestion_record.records_count = count
            db.commit()
            
            logger.info(f"Ingested {count} accounts")
            return count
            
        except Exception as e:
            ingestion_record.status = 'failed'
            ingestion_record.error_message = str(e)
            db.commit()
            raise
    
    async def _ingest_customers(self, db: Session, start_date: str, end_date: str) -> int:
        """Ingest customers"""
        ingestion_record = IngestionHistory(
            source='quickbooks',
            entity_type='customers',
            period_start=datetime.fromisoformat(start_date),
            period_end=datetime.fromisoformat(end_date),
            status='pending'
        )
        db.add(ingestion_record)
        db.commit()
        
        try:
            response = await self._make_request("query", {
                "query": "SELECT * FROM Customer MAXRESULTS 1000"
            })
            
            customers_data = response.get('QueryResponse', {}).get('Customer', [])
            count = 0
            
            for customer_data in customers_data:
                existing = db.query(Customer).filter(
                    Customer.source_id == customer_data['Id']
                ).first()
                
                if existing:
                    self._update_customer_from_qb(existing, customer_data)
                else:
                    customer = self._create_customer_from_qb(customer_data)
                    db.add(customer)
                
                count += 1
            
            ingestion_record.status = 'completed'
            ingestion_record.records_count = count
            db.commit()
            
            logger.info(f"Ingested {count} customers")
            return count
            
        except Exception as e:
            ingestion_record.status = 'failed'
            ingestion_record.error_message = str(e)
            db.commit()
            raise
    
    async def _ingest_vendors(self, db: Session, start_date: str, end_date: str) -> int:
        """Ingest vendors"""
        ingestion_record = IngestionHistory(
            source='quickbooks',
            entity_type='vendors',
            period_start=datetime.fromisoformat(start_date),
            period_end=datetime.fromisoformat(end_date),
            status='pending'
        )
        db.add(ingestion_record)
        db.commit()
        
        try:
            response = await self._make_request("query", {
                "query": "SELECT * FROM Vendor MAXRESULTS 1000"
            })
            
            vendors_data = response.get('QueryResponse', {}).get('Vendor', [])
            count = 0
            
            for vendor_data in vendors_data:
                existing = db.query(Vendor).filter(
                    Vendor.source_id == vendor_data['Id']
                ).first()
                
                if existing:
                    self._update_vendor_from_qb(existing, vendor_data)
                else:
                    vendor = self._create_vendor_from_qb(vendor_data)
                    db.add(vendor)
                
                count += 1
            
            ingestion_record.status = 'completed'
            ingestion_record.records_count = count
            db.commit()
            
            logger.info(f"Ingested {count} vendors")
            return count
            
        except Exception as e:
            ingestion_record.status = 'failed'
            ingestion_record.error_message = str(e)
            db.commit()
            raise
    
    async def _ingest_items(self, db: Session, start_date: str, end_date: str) -> int:
        """Ingest items/products"""
        ingestion_record = IngestionHistory(
            source='quickbooks',
            entity_type='items',
            period_start=datetime.fromisoformat(start_date),
            period_end=datetime.fromisoformat(end_date),
            status='pending'
        )
        db.add(ingestion_record)
        db.commit()
        
        try:
            response = await self._make_request("query", {
                "query": "SELECT * FROM Item MAXRESULTS 1000"
            })
            
            items_data = response.get('QueryResponse', {}).get('Item', [])
            count = 0
            
            for item_data in items_data:
                existing = db.query(Item).filter(
                    Item.source_id == item_data['Id']
                ).first()
                
                if existing:
                    self._update_item_from_qb(existing, item_data)
                else:
                    item = self._create_item_from_qb(item_data)
                    db.add(item)
                
                count += 1
            
            ingestion_record.status = 'completed'
            ingestion_record.records_count = count
            db.commit()
            
            logger.info(f"Ingested {count} items")
            return count
            
        except Exception as e:
            ingestion_record.status = 'failed'
            ingestion_record.error_message = str(e)
            db.commit()
            raise
    
    async def _ingest_trial_balance(self, db: Session, start_date: str, end_date: str) -> int:
        """Ingest trial balance report data"""
        ingestion_record = IngestionHistory(
            source='quickbooks',
            entity_type='trial_balance',
            period_start=datetime.fromisoformat(start_date),
            period_end=datetime.fromisoformat(end_date),
            status='pending'
        )
        db.add(ingestion_record)
        db.commit()
        
        try:
            # Get trial balance report
            response = await self._make_request("reports/TrialBalance", {
                "start_date": start_date,
                "end_date": end_date,
                "summarize_column_by": "Total",
                "minorversion": "65"
            })
            
            count = await self._process_trial_balance_response(db, response, start_date, end_date)
            
            ingestion_record.status = 'completed'
            ingestion_record.records_count = count
            db.commit()
            
            logger.info(f"Ingested {count} trial balance entries")
            return count
            
        except Exception as e:
            ingestion_record.status = 'failed'
            ingestion_record.error_message = str(e)
            db.commit()
            raise
    
    async def _ingest_transactions(self, db: Session, start_date: str, end_date: str) -> int:
        """Ingest detailed transactions"""
        ingestion_record = IngestionHistory(
            source='quickbooks',
            entity_type='transactions',
            period_start=datetime.fromisoformat(start_date),
            period_end=datetime.fromisoformat(end_date),
            status='pending'
        )
        db.add(ingestion_record)
        db.commit()
        
        try:
            count = 0
            # Get various transaction types
            transaction_types = ['Invoice', 'Bill', 'Payment', 'Purchase', 'JournalEntry']
            
            for txn_type in transaction_types:
                txn_count = await self._ingest_transaction_type(db, txn_type, start_date, end_date)
                count += txn_count
            
            ingestion_record.status = 'completed'
            ingestion_record.records_count = count
            db.commit()
            
            logger.info(f"Ingested {count} detailed transactions")
            return count
            
        except Exception as e:
            ingestion_record.status = 'failed'
            ingestion_record.error_message = str(e)
            db.commit()
            raise
    
    async def _ingest_transaction_type(self, db: Session, txn_type: str, start_date: str, end_date: str) -> int:
        """Ingest specific transaction type"""
        query = f"SELECT * FROM {txn_type} WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}' MAXRESULTS 1000"
        
        response = await self._make_request("query", {"query": query})
        
        transactions = response.get('QueryResponse', {}).get(txn_type, [])
        count = 0
        
        for txn_data in transactions:
            gl_entries = self._create_gl_entries_from_transaction(txn_data, txn_type)
            
            for gl_entry in gl_entries:
                # Check for duplicates
                existing = db.query(GeneralLedger).filter(
                    and_(
                        GeneralLedger.source_id == gl_entry.source_id,
                        GeneralLedger.source_type == gl_entry.source_type,
                        GeneralLedger.account_id == gl_entry.account_id
                    )
                ).first()
                
                if not existing:
                    db.add(gl_entry)
                    count += 1
        
        db.commit()
        return count
    
    async def _process_trial_balance_response(self, db: Session, response: Dict, start_date: str, end_date: str) -> int:
        """Process trial balance report response"""
        count = 0
        report_data = response.get('QueryResponse', {})
        
        # Extract trial balance data structure
        if 'Row' in report_data:
            for row in report_data['Row']:
                if row.get('Type') == 'Data':
                    account_entries = self._extract_trial_balance_entries(row, start_date, end_date)
                    
                    for entry in account_entries:
                        existing = db.query(GeneralLedger).filter(
                            and_(
                                GeneralLedger.source_id == entry.source_id,
                                GeneralLedger.account_id == entry.account_id,
                                GeneralLedger.transaction_date == entry.transaction_date
                            )
                        ).first()
                        
                        if not existing:
                            db.add(entry)
                            count += 1
        
        db.commit()
        return count
    
    def _create_account_from_qb(self, account_data: Dict) -> Account:
        """Create Account model from QB data"""
        return Account(
            source_id=account_data['Id'],
            name=account_data.get('Name', ''),
            fully_qualified_name=account_data.get('FullyQualifiedName', ''),
            account_type=account_data.get('AccountType', ''),
            account_subtype=account_data.get('AccountSubType', ''),
            classification=account_data.get('Classification', ''),
            parent_account_id=account_data.get('ParentRef', {}).get('value'),
            is_active=account_data.get('Active', True),
            current_balance=Decimal(str(account_data.get('CurrentBalance', 0))),
            raw_data=account_data
        )
    
    def _update_account_from_qb(self, account: Account, account_data: Dict):
        """Update existing Account with QB data"""
        account.name = account_data.get('Name', account.name)
        account.fully_qualified_name = account_data.get('FullyQualifiedName', account.fully_qualified_name)
        account.account_type = account_data.get('AccountType', account.account_type)
        account.account_subtype = account_data.get('AccountSubType', account.account_subtype)
        account.classification = account_data.get('Classification', account.classification)
        account.parent_account_id = account_data.get('ParentRef', {}).get('value', account.parent_account_id)
        account.is_active = account_data.get('Active', account.is_active)
        account.current_balance = Decimal(str(account_data.get('CurrentBalance', account.current_balance)))
        account.raw_data = account_data
    
    def _create_customer_from_qb(self, customer_data: Dict) -> Customer:
        """Create Customer model from QB data"""
        return Customer(
            source_id=customer_data['Id'],
            name=customer_data.get('Name', ''),
            display_name=customer_data.get('DisplayName', ''),
            company_name=customer_data.get('CompanyName', ''),
            email=customer_data.get('PrimaryEmailAddr', {}).get('Address', ''),
            phone=customer_data.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
            balance=Decimal(str(customer_data.get('Balance', 0))),
            is_active=customer_data.get('Active', True),
            raw_data=customer_data
        )
    
    def _update_customer_from_qb(self, customer: Customer, customer_data: Dict):
        """Update existing Customer with QB data"""
        customer.name = customer_data.get('Name', customer.name)
        customer.display_name = customer_data.get('DisplayName', customer.display_name)
        customer.company_name = customer_data.get('CompanyName', customer.company_name)
        customer.email = customer_data.get('PrimaryEmailAddr', {}).get('Address', customer.email)
        customer.phone = customer_data.get('PrimaryPhone', {}).get('FreeFormNumber', customer.phone)
        customer.balance = Decimal(str(customer_data.get('Balance', customer.balance)))
        customer.is_active = customer_data.get('Active', customer.is_active)
        customer.raw_data = customer_data
    
    def _create_vendor_from_qb(self, vendor_data: Dict) -> Vendor:
        """Create Vendor model from QB data"""
        return Vendor(
            source_id=vendor_data['Id'],
            name=vendor_data.get('Name', ''),
            display_name=vendor_data.get('DisplayName', ''),
            company_name=vendor_data.get('CompanyName', ''),
            email=vendor_data.get('PrimaryEmailAddr', {}).get('Address', ''),
            phone=vendor_data.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
            balance=Decimal(str(vendor_data.get('Balance', 0))),
            is_active=vendor_data.get('Active', True),
            raw_data=vendor_data
        )
    
    def _update_vendor_from_qb(self, vendor: Vendor, vendor_data: Dict):
        """Update existing Vendor with QB data"""
        vendor.name = vendor_data.get('Name', vendor.name)
        vendor.display_name = vendor_data.get('DisplayName', vendor.display_name)
        vendor.company_name = vendor_data.get('CompanyName', vendor.company_name)
        vendor.email = vendor_data.get('PrimaryEmailAddr', {}).get('Address', vendor.email)
        vendor.phone = vendor_data.get('PrimaryPhone', {}).get('FreeFormNumber', vendor.phone)
        vendor.balance = Decimal(str(vendor_data.get('Balance', vendor.balance)))
        vendor.is_active = vendor_data.get('Active', vendor.is_active)
        vendor.raw_data = vendor_data
    
    def _create_item_from_qb(self, item_data: Dict) -> Item:
        """Create Item model from QB data"""
        return Item(
            source_id=item_data['Id'],
            name=item_data.get('Name', ''),
            sku=item_data.get('Sku', ''),
            description=item_data.get('Description', ''),
            item_type=item_data.get('Type', ''),
            unit_price=Decimal(str(item_data.get('UnitPrice', 0))),
            quantity_on_hand=Decimal(str(item_data.get('QtyOnHand', 0))),
            is_active=item_data.get('Active', True),
            raw_data=item_data
        )
    
    def _update_item_from_qb(self, item: Item, item_data: Dict):
        """Update existing Item with QB data"""
        item.name = item_data.get('Name', item.name)
        item.sku = item_data.get('Sku', item.sku)
        item.description = item_data.get('Description', item.description)
        item.item_type = item_data.get('Type', item.item_type)
        item.unit_price = Decimal(str(item_data.get('UnitPrice', item.unit_price)))
        item.quantity_on_hand = Decimal(str(item_data.get('QtyOnHand', item.quantity_on_hand)))
        item.is_active = item_data.get('Active', item.is_active)
        item.raw_data = item_data
    
    def _create_gl_entries_from_transaction(self, txn_data: Dict, txn_type: str) -> List[GeneralLedger]:
        """Create GeneralLedger entries from transaction data"""
        entries = []
        
        # Extract transaction-level info
        txn_date = datetime.fromisoformat(txn_data.get('TxnDate', ''))
        txn_id = txn_data.get('Id', '')
        
        # Handle different transaction types
        if txn_type == 'JournalEntry' and 'Line' in txn_data:
            for line in txn_data['Line']:
                if line.get('JournalEntryLineDetail'):
                    entry = self._create_gl_entry_from_line(line, txn_data, txn_type)
                    if entry:
                        entries.append(entry)
        
        elif 'Line' in txn_data:
            # Handle other transaction types with line items
            for line in txn_data['Line']:
                entry = self._create_gl_entry_from_line(line, txn_data, txn_type)
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _create_gl_entry_from_line(self, line_data: Dict, txn_data: Dict, txn_type: str) -> Optional[GeneralLedger]:
        """Create a single GL entry from line data"""
        account_ref = None
        amount = 0
        debit_amount = 0
        credit_amount = 0
        
        # Extract account and amount based on transaction type
        if 'JournalEntryLineDetail' in line_data:
            detail = line_data['JournalEntryLineDetail']
            account_ref = detail.get('AccountRef', {})
            amount = Decimal(str(line_data.get('Amount', 0)))
            
            posting_type = detail.get('PostingType', 'Debit')
            if posting_type == 'Debit':
                debit_amount = amount
            else:
                credit_amount = amount
                amount = -amount  # Credit amounts are negative
        
        elif 'AccountBasedExpenseLineDetail' in line_data:
            detail = line_data['AccountBasedExpenseLineDetail']
            account_ref = detail.get('AccountRef', {})
            amount = Decimal(str(line_data.get('Amount', 0)))
            debit_amount = amount
        
        elif 'SalesItemLineDetail' in line_data:
            detail = line_data['SalesItemLineDetail']
            # For sales items, we need to get the income account
            amount = Decimal(str(line_data.get('Amount', 0)))
            credit_amount = amount
            amount = -amount
        
        if not account_ref or not account_ref.get('value'):
            return None
        
        return GeneralLedger(
            source_id=f"{txn_data.get('Id', '')}_{line_data.get('Id', '')}",
            source_type=txn_type,
            transaction_date=datetime.fromisoformat(txn_data.get('TxnDate', '')),
            reference_number=txn_data.get('DocNumber', ''),
            description=line_data.get('Description', txn_data.get('PrivateNote', '')),
            account_id=account_ref.get('value', ''),
            account_name=account_ref.get('name', ''),
            account_type='',  # Will be filled from account lookup
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            amount=amount,
            customer_id=txn_data.get('CustomerRef', {}).get('value'),
            customer_name=txn_data.get('CustomerRef', {}).get('name'),
            vendor_id=txn_data.get('VendorRef', {}).get('value'),
            vendor_name=txn_data.get('VendorRef', {}).get('name'),
            raw_data={"transaction": txn_data, "line": line_data}
        )
    
    def _extract_trial_balance_entries(self, row_data: Dict, start_date: str, end_date: str) -> List[GeneralLedger]:
        """Extract GL entries from trial balance row data"""
        entries = []
        
        # Trial balance structure varies, this is a simplified implementation
        # In practice, you'd parse the specific QB trial balance format
        if 'ColData' in row_data:
            account_name = row_data['ColData'][0].get('value', '')
            balance = Decimal(str(row_data['ColData'][1].get('value', '0').replace(',', '')))
            
            if balance != 0:
                entry = GeneralLedger(
                    source_id=f"tb_{start_date}_{account_name}",
                    source_type='trial_balance',
                    transaction_date=datetime.fromisoformat(end_date),
                    description=f"Trial Balance - {account_name}",
                    account_name=account_name,
                    account_id=account_name.replace(' ', '_').lower(),
                    account_type='',
                    amount=balance,
                    debit_amount=balance if balance > 0 else 0,
                    credit_amount=-balance if balance < 0 else 0,
                    raw_data=row_data
                )
                entries.append(entry)
        
        return entries


# Convenience functions for external use
async def run_qb_ingestion(access_token: str, company_id: str, start_date: str, end_date: str) -> Dict[str, int]:
    """Run full QB ingestion process"""
    async with QuickBooksIngestor(access_token, company_id) as ingestor:
        return await ingestor.ingest_full_ledger(start_date, end_date)

async def get_qb_company_info(access_token: str, company_id: str) -> Dict:
    """Get QB company information"""
    async with QuickBooksIngestor(access_token, company_id) as ingestor:
        return await ingestor.get_company_info()


if __name__ == "__main__":
    # Example usage
    import os
    import asyncio
    
    async def main():
        token = os.getenv("QB_ACCESS_TOKEN")
        company_id = os.getenv("QB_COMPANY_ID")
        
        if not token or not company_id:
            print("QB_ACCESS_TOKEN and QB_COMPANY_ID env vars required")
            return
        
        # Ingest last 30 days
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
        
        print(f"Starting QB ingestion for {start_date} to {end_date}")
        
        try:
            stats = await run_qb_ingestion(token, company_id, start_date, end_date)
            print(f"Ingestion completed: {stats}")
        except Exception as e:
            print(f"Ingestion failed: {e}")
    
    asyncio.run(main())