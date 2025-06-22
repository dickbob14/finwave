#!/usr/bin/env python3
"""
Integration test for QuickBooks client with field mapping
Tests signed amount logic and edge cases
"""

import unittest
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from integrations.quickbooks.client import QuickBooksClient
from config.field_mapper import get_field_mapper

class TestQuickBooksIntegration(unittest.TestCase):
    """Test QuickBooks integration with field mapping"""
    
    def setUp(self):
        self.mapper = get_field_mapper()
    
    def test_signed_amount_calculations(self):
        """Test signed amount logic for different account types"""
        test_cases = [
            # (account, name, debit, credit, expected_signed, description)
            # Assets - debit positive, credit negative
            ('1000', 'Cash', 1000, 0, 1000, 'Asset debit should be positive'),
            ('1000', 'Cash', 0, 500, -500, 'Asset credit should be negative'),
            ('1200', 'Accounts Receivable', 1500, 0, 1500, 'AR debit should be positive'),
            
            # Liabilities - credit positive, debit negative
            ('2000', 'Accounts Payable', 0, 1000, 1000, 'Liability credit should be positive'),
            ('2000', 'Accounts Payable', 500, 0, -500, 'Liability debit should be negative'),
            ('2500', 'Long-term Debt', 0, 10000, 10000, 'Debt credit should be positive'),
            
            # Equity - credit positive, debit negative
            ('3000', 'Common Stock', 0, 5000, 5000, 'Equity credit should be positive'),
            ('3100', 'Retained Earnings', 1000, 0, -1000, 'Equity debit should be negative'),
            
            # Revenue - credit positive, debit negative
            ('4000', 'Sales Revenue', 0, 2000, 2000, 'Revenue credit should be positive'),
            ('4000', 'Sales Revenue', 100, 0, -100, 'Revenue debit should be negative (returns)'),
            
            # Expenses - show as negative (outflows)
            ('5000', 'Cost of Goods Sold', 1000, 0, -1000, 'COGS debit should be negative'),
            ('6000', 'Operating Expenses', 500, 0, -500, 'OpEx debit should be negative'),
            ('5100', 'Salaries Expense', 5000, 0, -5000, 'Expense debit should be negative'),
            
            # Edge cases
            ('1400', 'Accumulated Depreciation', 0, 1000, -1000, 'Contra-asset credit should be negative'),
            ('5000', 'Expense Reversal', 0, 200, 200, 'Expense credit should be positive (reversal)'),
        ]
        
        for account, name, debit, credit, expected, description in test_cases:
            result = self.mapper.calculate_signed_amount(debit, credit, account, name)
            self.assertAlmostEqual(result, expected, places=2, 
                                 msg=f"{description}: {account} {name} Dr:{debit} Cr:{credit}")
    
    def test_multi_currency_adjustments(self):
        """Test handling of multi-currency adjustments"""
        # Test currency conversion entries
        gl_entries = [
            {'Account': '1000', 'Account_Name': 'Cash USD', 'Debit': 1000, 'Credit': 0},
            {'Account': '1001', 'Account_Name': 'Cash EUR', 'Debit': 0, 'Credit': 850},
            {'Account': '7500', 'Account_Name': 'Currency Gain/Loss', 'Debit': 0, 'Credit': 150}
        ]
        
        total_signed = 0
        for entry in gl_entries:
            signed = self.mapper.calculate_signed_amount(
                entry['Debit'], entry['Credit'], 
                entry['Account'], entry['Account_Name']
            )
            total_signed += signed
        
        # Total should be zero (balanced entry)
        self.assertAlmostEqual(total_signed, 0, places=2,
                             msg="Multi-currency adjustment should balance to zero")
    
    def test_balance_validation(self):
        """Test that GL entries balance (debits = credits)"""
        # Sample journal entry
        journal_entry = [
            {'Account': '5000', 'Debit': 1000, 'Credit': 0},    # Expense
            {'Account': '1000', 'Debit': 0, 'Credit': 1000},    # Cash
        ]
        
        total_debits = sum(e['Debit'] for e in journal_entry)
        total_credits = sum(e['Credit'] for e in journal_entry)
        
        self.assertEqual(total_debits, total_credits, 
                        "Journal entry debits should equal credits")
    
    def test_coa_mapping(self):
        """Test COA category mapping"""
        test_accounts = [
            ('1000', 'Current Assets'),
            ('1500', 'Fixed Assets'),
            ('2000', 'Current Liabilities'),
            ('3000', 'Equity'),
            ('4000', 'Revenue'),
            ('5000', 'Cost of Sales'),
            ('6000', 'Operating Expenses'),
        ]
        
        for account, expected_category in test_accounts:
            category = self.mapper.map_to_coa_category(account)
            self.assertEqual(category, expected_category,
                           f"Account {account} should map to {expected_category}")
    
    def test_gl_dataframe_totals(self):
        """Test that processed GL DataFrame maintains balance"""
        # Create sample GL data
        gl_data = {
            'Date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02'],
            'Account': ['4000', '1200', '5000', '1000'],
            'Account_Name': ['Revenue', 'AR', 'Expense', 'Cash'],
            'Debit': [0, 1000, 500, 0],
            'Credit': [1000, 0, 0, 500]
        }
        
        df = pd.DataFrame(gl_data)
        
        # Add signed amounts
        df['Signed_Amount'] = df.apply(
            lambda row: self.mapper.calculate_signed_amount(
                row['Debit'], row['Credit'], row['Account'], row['Account_Name']
            ),
            axis=1
        )
        
        # Check individual entries
        expected_signed = [1000, 1000, -500, -500]  # Revenue +, AR +, Expense -, Cash -
        for i, expected in enumerate(expected_signed):
            self.assertAlmostEqual(df.iloc[i]['Signed_Amount'], expected, places=2,
                                 msg=f"Row {i} signed amount mismatch")
        
        # Total signed amounts should be zero (balanced books)
        total_signed = df['Signed_Amount'].sum()
        self.assertAlmostEqual(total_signed, 0, places=2,
                             msg="Total signed amounts should balance to zero")


class TestFieldMapperEdgeCases(unittest.TestCase):
    """Test field mapper edge cases"""
    
    def setUp(self):
        self.mapper = get_field_mapper()
    
    def test_nested_field_mapping(self):
        """Test mapping of nested QuickBooks fields"""
        qb_data = {
            'TxnDate': '2024-01-15',
            'AccountRef': {
                'value': '4000',
                'name': 'Sales Revenue'
            },
            'ClassRef': {
                'name': 'Sales - US'
            },
            'DepartmentRef': None,  # Missing department
            'Amount': 1000
        }
        
        mapped = self.mapper.map_gl_fields(qb_data)
        
        self.assertEqual(mapped['Date'], '2024-01-15')
        self.assertEqual(mapped['Account'], '4000')
        self.assertEqual(mapped['Account_Name'], 'Sales Revenue')
        self.assertEqual(mapped['Class'], 'Sales - US')
        self.assertIsNone(mapped.get('Department'))
    
    def test_account_type_edge_cases(self):
        """Test account type detection edge cases"""
        edge_cases = [
            # Contra accounts
            ('1400', 'Accumulated Depreciation', 'assets'),  # Contra-asset
            ('4100', 'Sales Returns', 'revenue'),  # Contra-revenue
            
            # Unusual naming
            ('1050', 'Petty Cash Fund', 'assets'),
            ('2100', 'Credit Card Payable', 'liabilities'),
            
            # No number match - use keywords
            ('CUSTOM1', 'Custom Revenue Account', 'revenue'),
            ('CUSTOM2', 'Custom Expense Account', 'expenses'),
        ]
        
        for account, name, expected_type in edge_cases:
            result = self.mapper.get_account_type(account, name)
            self.assertEqual(result, expected_type,
                           f"{account} {name} should be type {expected_type}")


def run_integration_test():
    """Run integration tests and print summary"""
    print("🧪 Running QuickBooks Integration Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestQuickBooksIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestFieldMapperEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        print(f"   Ran {result.testsRun} tests")
    else:
        print("❌ Some tests failed")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_test()
    exit(0 if success else 1)