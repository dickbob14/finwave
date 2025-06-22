#!/usr/bin/env python3
"""
Test script for template generation fixes
"""

import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the enhanced modules
from template_utils import (
    get_month_columns, build_coa_mapping, calculate_signed_amount,
    format_excel_date, get_prior_year_period, create_icon_set_rule
)

def test_month_columns():
    """Test dynamic month column generation"""
    months = get_month_columns("2025-01-01", "2025-06-30")
    assert len(months) == 6
    assert months[0][0] == "Jan 2025"
    assert months[-1][0] == "Jun 2025"
    print("✅ Month columns test passed")

def test_coa_mapping():
    """Test COA mapping functionality"""
    # Create sample COA DataFrame
    coa_data = pd.DataFrame([
        {'Account_Code': '4000', 'Group': 'Revenue', 'SubGroup': 'Product Revenue'},
        {'Account_Code': '6000', 'Group': 'Operating Expenses', 'SubGroup': 'G&A'},
    ])
    
    acct_to_group, acct_to_subgroup = build_coa_mapping(coa_data)
    
    assert acct_to_group['4000'] == 'Revenue'
    assert acct_to_subgroup['6000'] == 'G&A'
    print("✅ COA mapping test passed")

def test_signed_amounts():
    """Test signed amount calculation"""
    # Revenue (Income) - credit positive
    revenue = calculate_signed_amount(0, 1000, "Income")
    assert revenue == 1000
    
    # Expense - debit positive
    expense = calculate_signed_amount(500, 0, "Expense")
    assert expense == -500
    
    # Asset - debit positive
    asset = calculate_signed_amount(2000, 500, "Asset")
    assert asset == 1500
    
    # Liability - credit positive
    liability = calculate_signed_amount(0, 3000, "Liability")
    assert liability == 3000
    
    print("✅ Signed amount calculation test passed")

def test_date_formatting():
    """Test Excel date formatting"""
    formatted = format_excel_date("2025-01-15")
    assert formatted == "2025-01-15"
    
    # Test with datetime string
    formatted2 = format_excel_date("2025-01-15 10:30:00")
    assert formatted2 == "2025-01-15"
    
    print("✅ Date formatting test passed")

def test_prior_year_period():
    """Test prior year period calculation"""
    py_start, py_end = get_prior_year_period("2025-01-01", "2025-12-31")
    assert py_start == "2024-01-01"
    assert py_end == "2024-12-31"
    
    print("✅ Prior year period test passed")

def test_template_generation():
    """Test template generation with enhanced features"""
    try:
        from make_templates import FinWaveTemplateBuilder
        
        # Create builder
        builder = FinWaveTemplateBuilder()
        
        # Build template
        wb = builder.build_template()
        
        # Verify sheets
        expected_sheets = [
            'DATA_GL', 'DATA_GL_PY', 'DATA_COA', 'DATA_MAP',
            'REPORT_P&L', 'REPORT_BS', 'DASH_KPI', 'SETTINGS', 'README'
        ]
        
        for sheet in expected_sheets:
            assert sheet in wb.sheetnames, f"Missing sheet: {sheet}"
        
        # Check for dynamic month formulas in P&L
        pl_sheet = wb['REPORT_P&L']
        month_formula = pl_sheet['C3'].value
        assert 'EOMONTH' in month_formula, "P&L should use EOMONTH for dynamic months"
        
        # Check for COA-based formulas
        assert 'tblGL[Account]' in str(pl_sheet['C6'].value), "Should use tblGL references"
        
        # Check for prior year sheet
        assert 'DATA_GL_PY' in wb.sheetnames, "Should have prior year GL sheet"
        
        # Run self-test
        assert builder.self_test(), "Self-test should pass"
        
        print("✅ Template generation test passed")
        
    except Exception as e:
        print(f"❌ Template generation test failed: {e}")
        raise

def test_etl_enhancements():
    """Test ETL script enhancements"""
    try:
        from etl_qb_to_excel import QuickBooksToExcelETL
        
        # Create ETL instance
        etl = QuickBooksToExcelETL()
        
        # Test signed amount calculation in transform
        test_data = {
            "transactions": {
                "invoices": [{
                    "TxnDate": "2025-01-15",
                    "DocNumber": "INV-001",
                    "TotalAmt": "1000.00",
                    "Id": "123",
                    "CustomerRef": {"name": "Test Customer"},
                    "PrivateNote": "Test invoice"
                }],
                "expenses": []
            }
        }
        
        df = etl.transform_to_gl_format(test_data)
        
        # Check that we have 2 entries (revenue + AR)
        assert len(df) == 2, "Should have 2 GL entries for invoice"
        
        # Check signed amounts
        revenue_row = df[df['Account'] == '4000'].iloc[0]
        ar_row = df[df['Account'] == '1200'].iloc[0]
        
        assert revenue_row['Amount'] > 0, "Revenue should be positive (credit)"
        assert ar_row['Amount'] > 0, "AR should be positive (debit)"
        
        # Check date format
        assert df['Date'].iloc[0] == '2025-01-15', "Date should be in ISO format"
        
        print("✅ ETL enhancements test passed")
        
    except Exception as e:
        print(f"❌ ETL test failed: {e}")
        raise

def test_weasyprint_guards():
    """Test WeasyPrint import guards"""
    from template_utils import WEASYPRINT_AVAILABLE
    
    print(f"WeasyPrint available: {WEASYPRINT_AVAILABLE}")
    
    # Test PDF reports module
    try:
        from pdf_reports_v2 import generate_executive_pdf
        
        if not WEASYPRINT_AVAILABLE:
            # Should raise ImportError
            try:
                generate_executive_pdf("2025-01-01", "2025-01-31")
                assert False, "Should have raised ImportError"
            except ImportError as e:
                assert "WeasyPrint is not installed" in str(e)
                print("✅ WeasyPrint guard test passed (not installed)")
        else:
            print("✅ WeasyPrint is available")
            
    except Exception as e:
        print(f"❌ WeasyPrint guard test failed: {e}")
        raise

def run_all_tests():
    """Run all tests"""
    print("Running template enhancement tests...\n")
    
    tests = [
        test_month_columns,
        test_coa_mapping,
        test_signed_amounts,
        test_date_formatting,
        test_prior_year_period,
        test_template_generation,
        test_etl_enhancements,
        test_weasyprint_guards
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} failed: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)