"""
QuickBooks sync service for pulling financial data
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from integrations.quickbooks.client import QuickBooksClient
from integrations.quickbooks.sync import sync_quickbooks_data

from core.database import get_db
from models.financial_data import (
    FinancialStatement, AccountBalance, Transaction,
    Customer, Vendor, SyncLog  # , update_workspace_model
)
from models.integration import IntegrationCredential
from metrics.kpi_calculator import KPICalculator

logger = logging.getLogger(__name__)


class QuickBooksSyncService:
    """Service for syncing data from QuickBooks"""
    
    def __init__(self, company_id: str, integration: IntegrationCredential):
        self.company_id = company_id
        self.integration = integration
        self.qb_client = self._initialize_client()
        self.sync_log_id = None
        
    def _initialize_client(self) -> QuickBooksClient:
        """Initialize QuickBooks client with OAuth credentials"""
        # Use the QuickBooksClient from our local implementation
        return QuickBooksClient(
            workspace_id=self.company_id,
            integration=self.integration
        )
        
    def _start_sync_log(self, db: Session, sync_type: str) -> str:
        """Create a sync log entry"""
        sync_log = SyncLog(
            id=str(uuid.uuid4()),
            company_id=self.company_id,
            sync_type=sync_type,
            sync_status="started",
            started_at=datetime.utcnow(),
            metadata={}
        )
        db.add(sync_log)
        db.commit()
        self.sync_log_id = sync_log.id
        return sync_log.id
        
    def _complete_sync_log(self, db: Session, records_synced: int, error: Optional[str] = None):
        """Update sync log with completion status"""
        if not self.sync_log_id:
            return
            
        sync_log = db.query(SyncLog).filter_by(id=self.sync_log_id).first()
        if sync_log:
            sync_log.completed_at = datetime.utcnow()
            sync_log.records_synced = records_synced
            sync_log.sync_status = "failed" if error else "completed"
            sync_log.error_message = error
            db.commit()
            
    def sync_all(self, db: Session, full_sync: bool = False) -> Dict[str, Any]:
        """Perform a complete sync of all QuickBooks data"""
        logger.info(f"Starting {'full' if full_sync else 'incremental'} sync for company {self.company_id}")
        
        sync_type = "full" if full_sync else "incremental"
        self._start_sync_log(db, sync_type)
        
        try:
            # Update company model relationships
            update_company_model()
            
            results = {
                "accounts": 0,
                "customers": 0,
                "vendors": 0,
                "transactions": 0,
                "statements": 0,
                "errors": []
            }
            
            # Sync accounts and balances
            try:
                results["accounts"] = self._sync_accounts(db)
            except Exception as e:
                logger.error(f"Error syncing accounts: {str(e)}")
                results["errors"].append(f"Accounts: {str(e)}")
                
            # Sync customers
            try:
                results["customers"] = self._sync_customers(db)
            except Exception as e:
                logger.error(f"Error syncing customers: {str(e)}")
                results["errors"].append(f"Customers: {str(e)}")
                
            # Sync vendors
            try:
                results["vendors"] = self._sync_vendors(db)
            except Exception as e:
                logger.error(f"Error syncing vendors: {str(e)}")
                results["errors"].append(f"Vendors: {str(e)}")
                
            # Sync transactions
            try:
                results["transactions"] = self._sync_transactions(db, full_sync)
            except Exception as e:
                logger.error(f"Error syncing transactions: {str(e)}")
                results["errors"].append(f"Transactions: {str(e)}")
                
            # Generate financial statements
            try:
                results["statements"] = self._generate_financial_statements(db)
            except Exception as e:
                logger.error(f"Error generating statements: {str(e)}")
                results["errors"].append(f"Statements: {str(e)}")
                
            # Calculate KPIs
            try:
                kpi_calc = KPICalculator(self.company_id)
                kpi_calc.calculate_all_kpis(db)
            except Exception as e:
                logger.error(f"Error calculating KPIs: {str(e)}")
                results["errors"].append(f"KPIs: {str(e)}")
                
            # Update sync log
            total_records = sum([v for k, v in results.items() if k != "errors" and isinstance(v, int)])
            self._complete_sync_log(db, total_records)
            
            return results
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            self._complete_sync_log(db, 0, str(e))
            raise
            
    def _sync_accounts(self, db: Session) -> int:
        """Sync chart of accounts and current balances"""
        logger.info("Syncing accounts...")
        
        accounts = Account.all(qb=self.qb_client)
        count = 0
        
        for account in accounts:
            # Store account balance
            balance = AccountBalance(
                id=str(uuid.uuid4()),
                company_id=self.company_id,
                account_id=account.Id,
                account_name=account.Name,
                account_type=account.AccountType,
                account_subtype=account.AccountSubType if hasattr(account, 'AccountSubType') else None,
                balance=float(account.CurrentBalance or 0),
                currency=account.CurrencyRef.value if hasattr(account, 'CurrencyRef') else "USD",
                as_of_date=datetime.utcnow()
            )
            
            # Check if we already have this balance for today
            existing = db.query(AccountBalance).filter_by(
                company_id=self.company_id,
                account_id=account.Id,
                as_of_date=balance.as_of_date.date()
            ).first()
            
            if not existing:
                db.add(balance)
                count += 1
                
        db.commit()
        logger.info(f"Synced {count} account balances")
        return count
        
    def _sync_customers(self, db: Session) -> int:
        """Sync customer data"""
        logger.info("Syncing customers...")
        
        customers = QBCustomer.all(qb=self.qb_client)
        count = 0
        
        for qb_customer in customers:
            customer = db.query(Customer).filter_by(
                company_id=self.company_id,
                quickbooks_id=qb_customer.Id
            ).first()
            
            if not customer:
                customer = Customer(
                    id=str(uuid.uuid4()),
                    company_id=self.company_id,
                    quickbooks_id=qb_customer.Id
                )
                db.add(customer)
                
            # Update customer data
            customer.name = qb_customer.DisplayName or qb_customer.CompanyName
            customer.email = qb_customer.PrimaryEmailAddr.Address if hasattr(qb_customer, 'PrimaryEmailAddr') else None
            customer.phone = qb_customer.PrimaryPhone.FreeFormNumber if hasattr(qb_customer, 'PrimaryPhone') else None
            customer.metadata = {
                "active": qb_customer.Active,
                "balance": float(qb_customer.Balance or 0),
                "currency": qb_customer.CurrencyRef.value if hasattr(qb_customer, 'CurrencyRef') else "USD"
            }
            customer.updated_at = datetime.utcnow()
            count += 1
            
        db.commit()
        logger.info(f"Synced {count} customers")
        return count
        
    def _sync_vendors(self, db: Session) -> int:
        """Sync vendor data"""
        logger.info("Syncing vendors...")
        
        vendors = QBVendor.all(qb=self.qb_client)
        count = 0
        
        for qb_vendor in vendors:
            vendor = db.query(Vendor).filter_by(
                company_id=self.company_id,
                quickbooks_id=qb_vendor.Id
            ).first()
            
            if not vendor:
                vendor = Vendor(
                    id=str(uuid.uuid4()),
                    company_id=self.company_id,
                    quickbooks_id=qb_vendor.Id
                )
                db.add(vendor)
                
            # Update vendor data
            vendor.name = qb_vendor.DisplayName or qb_vendor.CompanyName
            vendor.email = qb_vendor.PrimaryEmailAddr.Address if hasattr(qb_vendor, 'PrimaryEmailAddr') else None
            vendor.phone = qb_vendor.PrimaryPhone.FreeFormNumber if hasattr(qb_vendor, 'PrimaryPhone') else None
            vendor.metadata = {
                "active": qb_vendor.Active,
                "balance": float(qb_vendor.Balance or 0),
                "currency": qb_vendor.CurrencyRef.value if hasattr(qb_vendor, 'CurrencyRef') else "USD"
            }
            vendor.updated_at = datetime.utcnow()
            count += 1
            
        db.commit()
        logger.info(f"Synced {count} vendors")
        return count
        
    def _sync_transactions(self, db: Session, full_sync: bool) -> int:
        """Sync all transaction types"""
        logger.info("Syncing transactions...")
        
        count = 0
        
        # Determine date range for sync
        if full_sync:
            # Full sync - get all transactions
            start_date = None
        else:
            # Incremental sync - get transactions from last 7 days
            start_date = datetime.utcnow() - timedelta(days=7)
            
        # Sync different transaction types
        transaction_types = [
            (Invoice, "Invoice"),
            (Bill, "Bill"),
            (Payment, "Payment"),
            (SalesReceipt, "SalesReceipt"),
            (PurchaseOrder, "PurchaseOrder"),
            (JournalEntry, "JournalEntry"),
            (Estimate, "Estimate"),
            (CreditMemo, "CreditMemo"),
            (VendorCredit, "VendorCredit")
        ]
        
        for qb_class, transaction_type in transaction_types:
            try:
                logger.info(f"Syncing {transaction_type} transactions...")
                
                # Build query
                if start_date:
                    where_clause = f"TxnDate >= '{start_date.strftime('%Y-%m-%d')}'"
                    transactions = qb_class.where(where_clause, qb=self.qb_client)
                else:
                    transactions = qb_class.all(qb=self.qb_client)
                    
                for txn in transactions:
                    # Check if transaction already exists
                    existing = db.query(Transaction).filter_by(
                        company_id=self.company_id,
                        quickbooks_id=txn.Id
                    ).first()
                    
                    if not existing:
                        transaction = Transaction(
                            id=str(uuid.uuid4()),
                            company_id=self.company_id,
                            quickbooks_id=txn.Id,
                            transaction_type=transaction_type,
                            transaction_date=datetime.strptime(txn.TxnDate, '%Y-%m-%d'),
                            amount=float(self._get_transaction_amount(txn)),
                            currency=txn.CurrencyRef.value if hasattr(txn, 'CurrencyRef') else "USD",
                            customer_id=txn.CustomerRef.value if hasattr(txn, 'CustomerRef') else None,
                            vendor_id=txn.VendorRef.value if hasattr(txn, 'VendorRef') else None,
                            description=self._get_transaction_description(txn),
                            metadata=self._get_transaction_metadata(txn)
                        )
                        db.add(transaction)
                        count += 1
                        
            except Exception as e:
                logger.error(f"Error syncing {transaction_type}: {str(e)}")
                continue
                
        db.commit()
        logger.info(f"Synced {count} transactions")
        return count
        
    def _get_transaction_amount(self, txn) -> float:
        """Extract amount from different transaction types"""
        if hasattr(txn, 'TotalAmt'):
            return txn.TotalAmt
        elif hasattr(txn, 'Amount'):
            return txn.Amount
        elif hasattr(txn, 'Balance'):
            return txn.Balance
        else:
            return 0.0
            
    def _get_transaction_description(self, txn) -> str:
        """Extract description from different transaction types"""
        if hasattr(txn, 'PrivateNote'):
            return txn.PrivateNote
        elif hasattr(txn, 'Memo'):
            return txn.Memo
        elif hasattr(txn, 'CustomerMemo'):
            return txn.CustomerMemo.value if txn.CustomerMemo else None
        else:
            return None
            
    def _get_transaction_metadata(self, txn) -> Dict[str, Any]:
        """Extract additional metadata from transaction"""
        metadata = {}
        
        # Common fields
        if hasattr(txn, 'DocNumber'):
            metadata['doc_number'] = txn.DocNumber
        if hasattr(txn, 'DueDate'):
            metadata['due_date'] = txn.DueDate
        if hasattr(txn, 'PaymentType'):
            metadata['payment_type'] = txn.PaymentType
        if hasattr(txn, 'Line') and txn.Line:
            metadata['line_items'] = len(txn.Line)
            
        return metadata
        
    def _generate_financial_statements(self, db: Session) -> int:
        """Generate financial statements from QuickBooks data"""
        logger.info("Generating financial statements...")
        
        count = 0
        
        # Get current period
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)
        period_end = now
        
        try:
            # Generate P&L Statement
            pl_data = self._generate_profit_loss(period_start, period_end)
            if pl_data:
                statement = FinancialStatement(
                    id=str(uuid.uuid4()),
                    company_id=self.company_id,
                    statement_type="P&L",
                    period_start=period_start,
                    period_end=period_end,
                    data=pl_data
                )
                db.add(statement)
                count += 1
                
            # Generate Balance Sheet
            bs_data = self._generate_balance_sheet(period_end)
            if bs_data:
                statement = FinancialStatement(
                    id=str(uuid.uuid4()),
                    company_id=self.company_id,
                    statement_type="Balance Sheet",
                    period_start=period_start,
                    period_end=period_end,
                    data=bs_data
                )
                db.add(statement)
                count += 1
                
            # Generate Cash Flow Statement
            cf_data = self._generate_cash_flow(period_start, period_end)
            if cf_data:
                statement = FinancialStatement(
                    id=str(uuid.uuid4()),
                    company_id=self.company_id,
                    statement_type="Cash Flow",
                    period_start=period_start,
                    period_end=period_end,
                    data=cf_data
                )
                db.add(statement)
                count += 1
                
            db.commit()
            
        except Exception as e:
            logger.error(f"Error generating financial statements: {str(e)}")
            
        logger.info(f"Generated {count} financial statements")
        return count
        
    def _generate_profit_loss(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate P&L statement data"""
        try:
            # Use QuickBooks report API
            report = self.qb_client.report_service.profit_and_loss(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Parse report data
            return self._parse_report_data(report)
            
        except Exception as e:
            logger.error(f"Error generating P&L: {str(e)}")
            # Fallback to calculating from transactions
            return self._calculate_pl_from_transactions(start_date, end_date)
            
    def _generate_balance_sheet(self, as_of_date: datetime) -> Dict[str, Any]:
        """Generate balance sheet data"""
        try:
            # Use QuickBooks report API
            report = self.qb_client.report_service.balance_sheet(
                as_of_date=as_of_date.strftime('%Y-%m-%d')
            )
            
            # Parse report data
            return self._parse_report_data(report)
            
        except Exception as e:
            logger.error(f"Error generating balance sheet: {str(e)}")
            # Fallback to calculating from account balances
            return self._calculate_bs_from_accounts(as_of_date)
            
    def _generate_cash_flow(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate cash flow statement data"""
        try:
            # Use QuickBooks report API if available
            report = self.qb_client.report_service.cash_flow(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Parse report data
            return self._parse_report_data(report)
            
        except Exception as e:
            logger.error(f"Error generating cash flow: {str(e)}")
            # Fallback to calculating from transactions
            return self._calculate_cf_from_transactions(start_date, end_date)
            
    def _parse_report_data(self, report) -> Dict[str, Any]:
        """Parse QuickBooks report data into standard format"""
        # This would parse the QuickBooks report format
        # Implementation depends on actual QuickBooks API response format
        return {
            "headers": [],
            "rows": [],
            "totals": {}
        }
        
    def _calculate_pl_from_transactions(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate P&L from transaction data"""
        with next(get_db()) as db:
            # Get revenue transactions
            revenue = db.query(Transaction).filter(
                Transaction.company_id == self.company_id,
                Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            ).all()
            
            # Get expense transactions
            expenses = db.query(Transaction).filter(
                Transaction.company_id == self.company_id,
                Transaction.transaction_type.in_(["Bill", "VendorCredit"]),
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            ).all()
            
            total_revenue = sum(t.amount for t in revenue)
            total_expenses = sum(t.amount for t in expenses)
            
            return {
                "revenue": total_revenue,
                "expenses": total_expenses,
                "net_income": total_revenue - total_expenses,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
    def _calculate_bs_from_accounts(self, as_of_date: datetime) -> Dict[str, Any]:
        """Calculate balance sheet from account balances"""
        with next(get_db()) as db:
            # Get all account balances as of date
            balances = db.query(AccountBalance).filter(
                AccountBalance.company_id == self.company_id,
                AccountBalance.as_of_date <= as_of_date
            ).all()
            
            # Group by account type
            assets = sum(b.balance for b in balances if b.account_type == "Asset")
            liabilities = sum(b.balance for b in balances if b.account_type == "Liability")
            equity = sum(b.balance for b in balances if b.account_type == "Equity")
            
            return {
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity,
                "total": assets,
                "as_of_date": as_of_date.isoformat()
            }
            
    def _calculate_cf_from_transactions(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate cash flow from transactions"""
        with next(get_db()) as db:
            # Get all cash-related transactions
            cash_transactions = db.query(Transaction).filter(
                Transaction.company_id == self.company_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            ).all()
            
            # Simple cash flow calculation
            cash_inflows = sum(t.amount for t in cash_transactions if t.transaction_type in ["Payment", "SalesReceipt"])
            cash_outflows = sum(t.amount for t in cash_transactions if t.transaction_type in ["Bill", "VendorCredit"])
            
            return {
                "operating_activities": cash_inflows - cash_outflows,
                "investing_activities": 0,  # Would need more data
                "financing_activities": 0,  # Would need more data
                "net_change": cash_inflows - cash_outflows,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
    def update_customer_metrics(self, db: Session):
        """Update customer metrics like revenue, churn, etc."""
        logger.info("Updating customer metrics...")
        
        customers = db.query(Customer).filter_by(company_id=self.company_id).all()
        
        for customer in customers:
            # Get all transactions for this customer
            transactions = db.query(Transaction).filter(
                Transaction.company_id == self.company_id,
                Transaction.customer_id == customer.quickbooks_id,
                Transaction.transaction_type.in_(["Invoice", "SalesReceipt"])
            ).all()
            
            if transactions:
                customer.total_revenue = sum(t.amount for t in transactions)
                customer.transaction_count = len(transactions)
                customer.first_transaction_date = min(t.transaction_date for t in transactions)
                customer.last_transaction_date = max(t.transaction_date for t in transactions)
                
                # Check for churn (no transactions in last 90 days)
                days_since_last = (datetime.utcnow() - customer.last_transaction_date).days
                if days_since_last > 90 and customer.status == "active":
                    customer.status = "churned"
                    customer.churn_date = datetime.utcnow()
                elif days_since_last <= 90 and customer.status == "churned":
                    customer.status = "active"
                    customer.churn_date = None
                    
        db.commit()
        logger.info("Customer metrics updated")
        
    def update_vendor_metrics(self, db: Session):
        """Update vendor metrics"""
        logger.info("Updating vendor metrics...")
        
        vendors = db.query(Vendor).filter_by(company_id=self.company_id).all()
        
        for vendor in vendors:
            # Get all transactions for this vendor
            transactions = db.query(Transaction).filter(
                Transaction.company_id == self.company_id,
                Transaction.vendor_id == vendor.quickbooks_id,
                Transaction.transaction_type.in_(["Bill", "VendorCredit"])
            ).all()
            
            if transactions:
                vendor.total_spend = sum(t.amount for t in transactions)
                vendor.transaction_count = len(transactions)
                
        db.commit()
        logger.info("Vendor metrics updated")