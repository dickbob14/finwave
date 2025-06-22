#!/usr/bin/env python3
"""
Test data seeder for Block D functionality
Creates sample financial data for testing without requiring QB connection
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_session
from models.financial import (
    GeneralLedger, Account, Customer, Vendor, Item, 
    FinancialPeriod, DataSource, IngestionHistory
)

def seed_test_data():
    """Seed database with test financial data"""
    print("🌱 Seeding test financial data...")
    
    with get_db_session() as db:
        # Clear existing test data
        db.query(GeneralLedger).delete()
        db.query(Account).delete()
        db.query(Customer).delete()
        db.query(Vendor).delete()
        db.query(Item).delete()
        db.commit()
        
        # Create sample accounts
        accounts = [
            {"id": "1000", "name": "Cash - Operating", "type": "Bank", "classification": "Asset"},
            {"id": "1200", "name": "Accounts Receivable", "type": "Accounts Receivable", "classification": "Asset"},
            {"id": "4000", "name": "Product Revenue", "type": "Income", "classification": "Revenue"},
            {"id": "4100", "name": "Service Revenue", "type": "Income", "classification": "Revenue"},
            {"id": "5000", "name": "Cost of Goods Sold", "type": "Expense", "classification": "Expense"},
            {"id": "6000", "name": "Office Expenses", "type": "Expense", "classification": "Expense"},
            {"id": "6100", "name": "Marketing Expenses", "type": "Expense", "classification": "Expense"},
            {"id": "6200", "name": "Payroll Expenses", "type": "Expense", "classification": "Expense"},
            {"id": "2000", "name": "Accounts Payable", "type": "Accounts Payable", "classification": "Liability"}
        ]
        
        for acc in accounts:
            account = Account(
                source_id=acc["id"],
                name=acc["name"],
                account_type=acc["type"],
                classification=acc["classification"],
                is_active=True,
                current_balance=Decimal('0')
            )
            db.add(account)
        
        # Create sample customers
        customers = [
            {"id": "C001", "name": "Acme Corporation", "email": "billing@acme.com"},
            {"id": "C002", "name": "Tech Innovations LLC", "email": "finance@techinnovations.com"},
            {"id": "C003", "name": "Global Solutions Inc", "email": "ap@globalsolutions.com"},
            {"id": "C004", "name": "Startup Ventures", "email": "admin@startupventures.com"}
        ]
        
        for cust in customers:
            customer = Customer(
                source_id=cust["id"],
                name=cust["name"],
                email=cust["email"],
                balance=Decimal(str(random.randint(1000, 15000))),
                is_active=True
            )
            db.add(customer)
        
        # Create sample vendors
        vendors = [
            {"id": "V001", "name": "Office Supplies Co", "email": "billing@officesupplies.com"},
            {"id": "V002", "name": "Cloud Services Ltd", "email": "billing@cloudservices.com"},
            {"id": "V003", "name": "Marketing Agency Pro", "email": "invoices@marketingpro.com"}
        ]
        
        for vend in vendors:
            vendor = Vendor(
                source_id=vend["id"],
                name=vend["name"],
                email=vend["email"],
                balance=Decimal(str(random.randint(500, 8000))),
                is_active=True
            )
            db.add(vendor)
        
        db.commit()
        print("✓ Created accounts, customers, and vendors")
        
        # Generate sample transactions for last 6 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        transaction_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Daily transactions with some randomness
            daily_transactions = random.randint(1, 8)
            
            for _ in range(daily_transactions):
                transaction_count += 1
                
                # Random transaction type
                if random.random() < 0.4:  # 40% revenue transactions
                    _create_revenue_transaction(db, current_date, transaction_count, customers)
                elif random.random() < 0.3:  # 30% expense transactions  
                    _create_expense_transaction(db, current_date, transaction_count, vendors)
                else:  # 30% other transactions
                    _create_other_transaction(db, current_date, transaction_count)
            
            current_date += timedelta(days=1)
        
        db.commit()
        print(f"✓ Created {transaction_count} sample transactions")
        
        # Create ingestion history
        ingestion = IngestionHistory(
            source='test_seeder',
            entity_type='sample_data',
            period_start=start_date,
            period_end=end_date,
            records_count=transaction_count,
            status='completed'
        )
        db.add(ingestion)
        db.commit()
        
        print(f"🎉 Test data seeding complete!")
        print(f"   - {len(accounts)} accounts created")
        print(f"   - {len(customers)} customers created") 
        print(f"   - {len(vendors)} vendors created")
        print(f"   - {transaction_count} transactions created")
        print(f"   - Date range: {start_date.date()} to {end_date.date()}")

def _create_revenue_transaction(db, date, txn_id, customers):
    """Create a revenue transaction"""
    customer = random.choice(customers)
    amount = Decimal(str(random.randint(500, 5000)))
    
    # Revenue entry (credit)
    revenue_gl = GeneralLedger(
        source_id=f"TXN{txn_id:06d}",
        source_type='invoice',
        transaction_date=date,
        description=f"Invoice from {customer['name']}",
        account_id='4000' if random.random() < 0.7 else '4100',
        account_name='Product Revenue' if random.random() < 0.7 else 'Service Revenue',
        account_type='Income',
        credit_amount=amount,
        amount=-amount,  # Negative for revenue
        customer_id=customer['id'],
        customer_name=customer['name']
    )
    db.add(revenue_gl)
    
    # AR entry (debit)
    ar_gl = GeneralLedger(
        source_id=f"TXN{txn_id:06d}",
        source_type='invoice',
        transaction_date=date,
        description=f"Invoice from {customer['name']}",
        account_id='1200',
        account_name='Accounts Receivable',
        account_type='Accounts Receivable',
        debit_amount=amount,
        amount=amount,
        customer_id=customer['id'],
        customer_name=customer['name']
    )
    db.add(ar_gl)

def _create_expense_transaction(db, date, txn_id, vendors):
    """Create an expense transaction"""
    vendor = random.choice(vendors)
    
    # Random expense type
    expense_types = [
        ('5000', 'Cost of Goods Sold', 'Expense'),
        ('6000', 'Office Expenses', 'Expense'), 
        ('6100', 'Marketing Expenses', 'Expense'),
        ('6200', 'Payroll Expenses', 'Expense')
    ]
    
    account_id, account_name, account_type = random.choice(expense_types)
    amount = Decimal(str(random.randint(100, 2000)))
    
    # Expense entry (debit)
    expense_gl = GeneralLedger(
        source_id=f"TXN{txn_id:06d}",
        source_type='bill',
        transaction_date=date,
        description=f"Bill from {vendor['name']}",
        account_id=account_id,
        account_name=account_name,
        account_type=account_type,
        debit_amount=amount,
        amount=amount,
        vendor_id=vendor['id'],
        vendor_name=vendor['name']
    )
    db.add(expense_gl)
    
    # AP entry (credit)
    ap_gl = GeneralLedger(
        source_id=f"TXN{txn_id:06d}",
        source_type='bill',
        transaction_date=date,
        description=f"Bill from {vendor['name']}",
        account_id='2000',
        account_name='Accounts Payable',
        account_type='Accounts Payable',
        credit_amount=amount,
        amount=-amount,
        vendor_id=vendor['id'],
        vendor_name=vendor['name']
    )
    db.add(ap_gl)

def _create_other_transaction(db, date, txn_id):
    """Create other types of transactions"""
    # Cash transactions, transfers, etc.
    amount = Decimal(str(random.randint(50, 1000)))
    
    # Simple cash expense
    cash_gl = GeneralLedger(
        source_id=f"TXN{txn_id:06d}",
        source_type='expense',
        transaction_date=date,
        description="Office supplies purchase",
        account_id='1000',
        account_name='Cash - Operating',
        account_type='Bank',
        credit_amount=amount,
        amount=-amount
    )
    db.add(cash_gl)
    
    expense_gl = GeneralLedger(
        source_id=f"TXN{txn_id:06d}",
        source_type='expense',
        transaction_date=date,
        description="Office supplies purchase",
        account_id='6000',
        account_name='Office Expenses',
        account_type='Expense',
        debit_amount=amount,
        amount=amount
    )
    db.add(expense_gl)

if __name__ == "__main__":
    seed_test_data()