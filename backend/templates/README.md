# FinWave Board Pack Templates

Professional Excel financial reporting templates with dynamic periods and Chart of Accounts (COA) mapping.

## Overview

This directory contains the template generation and ETL system for FinWave's board pack reports. The system creates Excel workbooks with:

- Dynamic month columns based on fiscal year settings
- Automatic prior year comparisons
- COA mapping for flexible account structures
- Professional formatting and conditional formatting
- Real QuickBooks data integration

## Key Files

- `make_templates.py` - Generates the Excel board pack template
- `etl_qb_to_excel.py` - Populates templates with QuickBooks data
- `template_utils.py` - Shared utilities for template generation
- `test_templates.py` - Comprehensive test suite

## Quick Start

```bash
# Generate template
make templates

# Run ETL to populate with data
make etl

# Run tests
make test-templates
```

## Template Structure

The generated Excel workbook contains:

### Data Sheets (Hidden)
- **SETTINGS** - Fiscal year configuration and parameters
- **DATA_MAP** - Chart of Accounts mapping table
- **DATA_GL** - Current year general ledger entries
- **DATA_GL_PY** - Prior year general ledger entries

### Report Sheets (Visible)
- **REPORT_P&L** - Income statement with dynamic monthly columns
- **REPORT_BS** - Balance sheet with variance analysis
- **REPORT_CF** - Cash flow statement (placeholder)
- **REPORT_AR** - Accounts receivable aging (placeholder)
- **DASH_KPI** - Executive KPI dashboard with charts

## Features

### Dynamic Periods
- Month columns automatically adjust based on SETTINGS sheet
- Uses EOMONTH formulas for fiscal year flexibility
- Supports partial years and custom date ranges

### COA Mapping
- Map any account number to standard report categories
- Flexible account structure support
- Easy to maintain via DATA_MAP sheet

### Prior Year Variance
- Automatic prior year data comparison
- Variance calculations and percentages
- Conditional formatting for variances

### Professional Formatting
- Consistent number formats
- Icon sets for KPI indicators
- Print-ready layouts
- Hidden helper columns

## ETL Process

The ETL extracts data from QuickBooks and transforms it for the templates:

1. Fetches all general ledger entries
2. Calculates signed amounts (expenses as negative)
3. Maps accounts using COA mapping
4. Generates prior year comparison data
5. Populates DATA_GL and DATA_GL_PY sheets
6. Excel formulas automatically update reports

## Testing

Run the test suite to validate all functionality:

```bash
cd backend/templates
python test_templates.py
```

Tests cover:
- Template structure validation
- Formula generation
- COA mapping logic
- Signed amount calculations
- Prior year data handling

## Dependencies

- pandas - Data manipulation
- openpyxl - Excel file generation
- xlsxwriter - Advanced Excel features
- requests - QuickBooks API calls
- python-dateutil - Date handling

## Production Notes

- Templates are designed for Excel 2016+
- Formulas use structured references (table names)
- Compatible with Google Sheets upload
- PDF export ready (from Excel)

## Next Steps

1. Install WeasyPrint for direct PDF generation (optional)
2. Configure Google Sheets credentials for cloud export
3. Set up scheduled ETL runs for automated reporting
4. Customize KPI dashboard metrics