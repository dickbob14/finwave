# Finance-as-Code Template System

Professional financial template automation following enterprise patterns for board-pack quality reports.

## 🎯 Overview

This system implements the "finance-as-code" playbook:
- **Flexibility for analysts** - Real Excel/Sheets files they can edit
- **Repeatable automation** - Templates regenerate in CI or via API
- **Professional quality** - Board-pack ready outputs

## 📊 Available Templates

### 1. Basic 3-Statement Model
- **Use Case**: Month-end close and board reporting
- **Frequency**: Monthly (after close)
- **Delivery**: Excel download + Email attachment
- **Contents**: Income Statement, Balance Sheet, Cash Flow
- **Command**: `make populate-3statement SINCE=2024-01-01 UNTIL=2024-12-31`

### 2. Executive KPI Dashboard
- **Use Case**: Day-to-day ops and variance checks
- **Frequency**: Daily refresh
- **Delivery**: Google Sheets (live link)
- **Contents**: Multi-dimensional KPIs by Entity/Dept/Product
- **Command**: `make populate-kpi SINCE=2024-01-01`

### 3. Board Pack Template (Original)
- **Use Case**: Comprehensive financial reporting
- **Frequency**: Monthly
- **Delivery**: Excel + PDF
- **Command**: `make templates && make etl`

## 🚀 Quick Start

```bash
# List all available templates
make list-templates

# Populate 3-Statement Model for Q1 2024
make populate-3statement SINCE=2024-01-01 UNTIL=2024-03-31

# Populate KPI Dashboard for current month
make populate-kpi

# Generate and populate original board pack
make templates etl
```

## 📁 File Organization

Following S3 storage conventions:
```
s3://finwave-exports/
  └── {company_slug}/
        ├── templates/           # Template versions
        │     ├── Basic 3-Statement Model-2.xlsx
        │     └── Cube - KPI Dashboard-1.xlsx
        ├── populated/           # Generated reports
        │     ├── 2024-05-31_3_statement_model.xlsx
        │     └── 2024-05-31_kpi_dashboard.xlsx
        └── logs/               # Run logs
              └── 2024-05-31_3_statement_model_run.log
```

## 🔧 Template Mechanics

### Data Flow Pattern
1. **Named ranges/tables** in Excel (tblGL, tblCOA, etc.)
2. **Helper sheets** (_XFORM) for transformations
3. **Report sheets** reference helpers, not raw data
4. **Python ETL** overwrites data tables only

### Key Design Principles
- Templates contain all business logic (not Python)
- Data sheets are separate from presentation
- Formulas use structured references
- Version control via template files

## 🌐 Google Sheets Integration

For dashboards that need live updates:
```bash
# Upload to existing Google Sheet
make populate-kpi SHEET_ID=1234567890abcdef

# Template manager handles:
# - Data upload via pygsheets
# - Formula preservation
# - Public viewer link generation
```

## 🤖 Automation Patterns

### Refresh Triggers
| Template | Trigger | Delivery |
|----------|---------|----------|
| 3-Statement | Month-end webhook | Email + S3 |
| KPI Dashboard | Daily cron | Google Sheets |
| Board Pack | Manual/API | Download |
| Scenarios | On-demand | Excel file |

### API Integration
```python
from templates.template_manager import TemplateManager

manager = TemplateManager('acme_corp')
result = manager.populate_template(
    '3_statement_model',
    start_date='2024-01-01',
    end_date='2024-03-31',
    sheet_id='optional_google_sheet_id'
)
```

## 📝 Adding New Templates

1. **Drop template file** in `templates/files/`
2. **Create populator script** following the pattern:
   ```python
   class MyTemplatePopulator:
       def load_template(self)
       def fetch_data(self, start, end)
       def populate_sheets(self, data)
       def save_populated_file(self, output)
   ```
3. **Register in template_manager.py**
4. **Add Makefile target**

## 🔍 Template Development Workflow

```bash
# 1. Analyze new template
python analyze_template.py "New Template.xlsx"

# 2. Generate populator (use Claude)
# Prompt: "Create populator for [template] following populate_3statement.py pattern"

# 3. Test locally
python populate_mytemplate.py --since 2024-01-01 --debug

# 4. Add to registry and test via manager
python template_manager.py populate --template mytemplate --since 2024-01-01
```

## 🏆 Best Practices

1. **Template Design**
   - Keep data and presentation separate
   - Use named ranges for all data references
   - Include a SETTINGS sheet for parameters
   - Version templates with date suffix

2. **Data Population**
   - Never modify formulas or formatting
   - Clear then append (don't update in place)
   - Preserve column headers
   - Log all operations

3. **Delivery**
   - Archive everything to S3
   - Return presigned URLs (not blobs)
   - Track Google Sheets IDs
   - Include run metadata

## 🚦 Production Checklist

- [ ] Templates tested with real data volumes
- [ ] S3 permissions configured
- [ ] Google Sheets service account ready
- [ ] Email delivery configured
- [ ] Monitoring for failed runs
- [ ] Retention policy for archives

## 📚 Next Steps

1. **Integrate with QuickBooks API** - Replace sample data
2. **Add more templates** - Budget vs Actual, Scenario Planning
3. **Build frontend UI** - Template browser with download/refresh
4. **Setup automation** - Cron jobs, webhooks, event triggers
5. **Add validations** - Data quality checks before population

---

This system provides the foundation for scaling financial automation while maintaining the flexibility analysts need. Each template is a self-contained unit that can evolve independently while following consistent patterns.