# Block D - Financial Reporting & Insights

## Overview

Block D extends FinWave with comprehensive financial reporting capabilities, variance analysis, and multi-source data integration. This implementation provides enterprise-grade financial intelligence with AI-powered insights.

## Architecture

```
finwave/backend/
├── models/financial.py          # SQLAlchemy models for financial data
├── etl/qb_ingest.py            # QuickBooks full-ledger ingestion
├── templates/                   # Report generation
│   ├── excel_templates.py      # Excel/Google Sheets exports
│   ├── pdf_reports.py          # PDF report generation
│   └── pdf/                    # Jinja2 templates
├── insights/                   # AI-powered analysis
│   ├── variance_analyzer.py    # Statistical variance detection
│   └── llm_commentary.py       # LLM-powered commentary
├── integrations/               # External data sources
│   ├── salesforce_hook.py      # Salesforce CRM integration
│   ├── hubspot_hook.py         # HubSpot marketing integration
│   ├── nue_hook.py             # Nue compensation integration
│   └── integration_manager.py  # Centralized orchestration
└── routes/                     # FastAPI endpoints
    ├── export.py               # Excel/Sheets export endpoints
    ├── report.py               # PDF report endpoints
    ├── insight.py              # Variance analysis endpoints
    └── charts.py               # Chart data endpoints
```

## Core Features

### 1. Full-Ledger Ingestion

Complete QuickBooks data ingestion using Reports & Accounting APIs:

```bash
# Run full ingestion for date range
python -m etl.qb_ingest --since 2024-01-01 --until 2024-12-31

# Idempotent re-runs supported via ingestion_history table
python -m etl.qb_ingest --since 2024-01-01  # Won't duplicate data
```

**What gets ingested:**
- General Ledger transactions with full detail
- Chart of Accounts with hierarchy
- Customers, Vendors, Items/Products
- Classes, Departments, Locations, Employees
- Trial Balance, P&L, Balance Sheet data

### 2. Excel & Google Sheets Templates

Formula-driven spreadsheet generation with separate data and report tabs:

```bash
# Test Excel export
curl "http://localhost:8000/export/excel?start_date=2024-01-01&end_date=2024-01-31" \
  -o financial_report.xlsx

# Test Google Sheets export (requires credentials)
curl "http://localhost:8000/export/google-sheets?start_date=2024-01-01&end_date=2024-01-31&sheet_title=Board%20Report"
```

**Generated templates include:**
- Trial Balance with automated variance calculations
- P&L Statement with period comparisons
- Balance Sheet with ratio formulas
- Cash Flow Statement with projections
- Variance Analysis with conditional formatting

### 3. Narrative PDF Reports

Professional PDF reports with AI-generated commentary:

```bash
# Generate executive summary
curl "http://localhost:8000/report/executive?start_date=2024-09-01&end_date=2024-09-30" \
  -o executive_summary.pdf

# Generate detailed financial report
curl "http://localhost:8000/report/detailed?start_date=2024-09-01&end_date=2024-09-30" \
  -o detailed_report.pdf

# Generate board pack for specific month
curl "http://localhost:8000/report/board-pack?period=2024-09" \
  -o board_pack_sep2024.pdf
```

**Report features:**
- Executive summary with key metrics
- Complete financial statements
- KPI tiles (profit margin, runway, AR days)
- AI-generated commentary and insights
- Variance analysis with explanations

### 4. Interactive Insight Layer

AI-powered variance analysis answering "WHY" questions:

```bash
# Ask WHY questions about variances
curl -X POST "http://localhost:8000/insight/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why are expenses higher this month?",
    "start_date": "2024-09-01", 
    "end_date": "2024-09-30"
  }'

# Get comprehensive variance analysis
curl "http://localhost:8000/insight/variance?start_date=2024-09-01&end_date=2024-09-30&severity_filter=critical"

# Get trend analysis
curl "http://localhost:8000/insight/trends?lookback_months=12&trend_direction=declining"

# Detect anomalies
curl "http://localhost:8000/insight/anomalies?start_date=2024-09-01&end_date=2024-09-30&sensitivity=2.0"
```

**Insight capabilities:**
- Statistical variance detection (budget, trend, seasonal, outlier, ratio)
- LLM-powered explanations and recommendations
- Trend analysis with projections
- Anomaly detection using Z-score analysis
- Cross-account correlation analysis

### 5. Multi-Source Data Integration

Hooks for external systems with correlation analysis:

```bash
# Test integration status
curl "http://localhost:8000/insight/status"

# Sync all active data sources
python -c "
import asyncio
from integrations.integration_manager import sync_all_sources
result = asyncio.run(sync_all_sources('2024-09-01', '2024-09-30'))
print(result)
"

# Get cross-platform correlation analysis
python -c "
import asyncio  
from integrations.integration_manager import get_all_correlations
result = asyncio.run(get_all_correlations('2024-09-01', '2024-09-30'))
print(result['cross_platform_insights'])
"
```

**Supported integrations:**
- **Salesforce**: Sales pipeline correlation with revenue
- **HubSpot**: Marketing attribution analysis
- **Nue**: Compensation correlation with payroll expenses

### 6. Chart Data REST API

Plotly JSON endpoints for frontend consumption:

```bash
# Revenue trend chart
curl "http://localhost:8000/charts/revenue-trend?start_date=2024-01-01&end_date=2024-09-30&grouping=monthly"

# Expense breakdown (pie chart)
curl "http://localhost:8000/charts/expense-breakdown?start_date=2024-09-01&end_date=2024-09-30&chart_type=pie"

# Profit margin trend
curl "http://localhost:8000/charts/profit-margin?start_date=2024-01-01&end_date=2024-09-30&grouping=quarterly"

# KPI dashboard
curl "http://localhost:8000/charts/kpi-dashboard?start_date=2024-09-01&end_date=2024-09-30"

# Available chart types
curl "http://localhost:8000/charts/available-charts"
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://finwave:finwave@localhost:5432/finwave

# QuickBooks (existing)
QB_CLIENT_ID=your_client_id
QB_CLIENT_SECRET=your_client_secret
QB_REDIRECT_URI=http://localhost:8000/qb_callback
QB_ENVIRONMENT=sandbox

# LLM for commentary (optional)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Google Sheets export (optional)
GOOGLE_SHEETS_CREDENTIALS=/path/to/service-account.json

# External integrations (optional)
SALESFORCE_INSTANCE_URL=https://company.salesforce.com
SALESFORCE_ACCESS_TOKEN=your_access_token
SALESFORCE_CLIENT_ID=your_sf_client_id
SALESFORCE_CLIENT_SECRET=your_sf_client_secret

HUBSPOT_API_KEY=your_hubspot_key

NUE_API_KEY=your_nue_key
```

### Database Setup

```bash
# Run Alembic migration
cd backend
source .venv/bin/activate
alembic upgrade head

# Verify tables created
psql postgresql://finwave:finwave@localhost:5432/finwave -c "\\dt"
```

## API Endpoints Summary

### Export Routes (`/export`)
- `GET /export/excel` - Export financial data to Excel
- `GET /export/google-sheets` - Export to Google Sheets
- `GET /export/template/{type}` - Download empty templates
- `POST /export/custom` - Export custom data
- `GET /export/formats` - List supported formats

### Report Routes (`/report`)
- `GET /report/executive` - Executive summary PDF
- `GET /report/detailed` - Detailed financial report PDF
- `GET /report/board-pack` - Monthly board pack PDF
- `POST /report/commentary` - AI-generated commentary JSON
- `GET /report/templates` - Available report templates
- `GET /report/periods` - Available reporting periods

### Insight Routes (`/insight`)
- `POST /insight/analyze` - Analyze financial questions
- `GET /insight/variance` - Variance analysis
- `GET /insight/trends` - Trend analysis
- `GET /insight/anomalies` - Anomaly detection
- `POST /insight/explain` - Explain specific variances
- `GET /insight/dashboard` - Insights dashboard data

### Chart Routes (`/charts`)
- `GET /charts/revenue-trend` - Revenue trend chart data
- `GET /charts/expense-breakdown` - Expense breakdown chart
- `GET /charts/profit-margin` - Profit margin trend
- `GET /charts/cash-flow` - Cash flow analysis
- `GET /charts/account-balance` - Account balance trend
- `GET /charts/kpi-dashboard` - KPI dashboard
- `GET /charts/available-charts` - List all chart types

## Generating a Monthly Board Pack

Complete workflow for generating a comprehensive board pack:

```bash
# 1. Ensure data is current
python -m etl.qb_ingest --since 2024-09-01

# 2. Generate board pack PDF
curl "http://localhost:8000/report/board-pack?period=2024-09" \
  -o board_pack_september_2024.pdf

# 3. Generate supporting Excel file
curl "http://localhost:8000/export/excel?start_date=2024-09-01&end_date=2024-09-30&filename=board_pack_data_sep2024" \
  -o board_pack_data_september_2024.xlsx

# 4. Get AI commentary for discussion points  
curl -X POST "http://localhost:8000/report/commentary" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-09-01", "end_date": "2024-09-30"}' \
  | jq '.recommendations[]'

# 5. Get variance analysis for QA
curl "http://localhost:8000/insight/variance?start_date=2024-09-01&end_date=2024-09-30&severity_filter=high" \
  | jq '.summary'
```

## Testing

### Unit Tests

```bash
# Test insight endpoint with synthetic data
python -c "
import requests
response = requests.post('http://localhost:8000/insight/analyze', json={
    'question': 'Why did revenue increase by 15%?',
    'start_date': '2024-09-01',
    'end_date': '2024-09-30'
})
print(response.json())
"

# Test chart endpoint
curl "http://localhost:8000/charts/status"

# Test export functionality
curl "http://localhost:8000/export/status"
```

### Integration Tests

```bash
# Verify all systems are healthy
curl "http://localhost:8000/report/status"
curl "http://localhost:8000/insight/status" 
curl "http://localhost:8000/charts/status"
curl "http://localhost:8000/export/status"

# Test full workflow
python -c "
import asyncio
from integrations.integration_manager import IntegrationManager

async def test_workflow():
    manager = IntegrationManager()
    status = manager.get_integration_status()
    print(f'Integration health: {status}')

asyncio.run(test_workflow())
"
```

## Performance Considerations

- **Database Indexing**: Key indexes on transaction_date, account_id, customer_id for fast queries
- **Caching**: LLM responses cached for 15 minutes to reduce API costs
- **Parallel Processing**: Multi-source sync can run in parallel
- **Pagination**: Large data exports handled in chunks
- **Connection Pooling**: PostgreSQL connection pooling for concurrent requests

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database connectivity
   psql postgresql://finwave:finwave@localhost:5432/finwave -c "SELECT 1"
   ```

2. **QB Token Expiration**
   ```bash
   # Re-authenticate with QuickBooks
   curl "http://localhost:8000/connect_qb"
   ```

3. **Missing Dependencies**
   ```bash
   # Install PDF generation dependencies
   pip install weasyprint
   
   # Install Google Sheets dependencies  
   pip install pygsheets
   ```

4. **LLM API Errors**
   ```bash
   # Test with mock commentary
   curl -X POST "http://localhost:8000/report/commentary?llm_provider=mock"
   ```

## Future Enhancements

- **Real-time Data Streaming**: WebSocket connections for live updates
- **Advanced ML Models**: Custom financial forecasting models
- **Multi-tenant Support**: Isolated data per organization
- **Mobile API**: Optimized endpoints for mobile apps
- **Audit Trail**: Complete change tracking for compliance

---

**BLOCK D FINISHED** ✅

The financial reporting and insights system is now fully operational with comprehensive variance analysis, multi-format exports, AI-powered commentary, and external data integration capabilities.