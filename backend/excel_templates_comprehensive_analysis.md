# Excel Templates Comprehensive Analysis

## Overview
This analysis examines two Excel templates to understand their structure and identify data sources for automation:
1. **Basic 3-Statement Model-2.xlsx** - A financial model with standard financial statements
2. **Cube - KPI Dashboard-1.xlsx** - A KPI dashboard with revenue and operational metrics

## 1. Basic 3-Statement Model-2.xlsx

### Structure Summary
- **Total Sheets**: 4
- **Sheet Types**: 
  - 1 About/Info sheet
  - 3 Financial statement sheets (Income Statement, Balance Sheet, Cash Flow Statement)
- **No explicit data sheets or tables found**
- **Heavy use of formulas**: 834 total formulas across the workbook

### Sheet Details

#### About Sheet
- **Purpose**: Information and navigation sheet
- **Size**: 54 rows × 14 columns
- **Key Features**: 
  - 19 merged cells (typical of presentation sheets)
  - Contains metadata about input cells and instructions

#### Income Statement
- **Purpose**: Financial reporting sheet
- **Size**: 281 rows × 16 columns
- **Data Structure**:
  - Headers at row 4: Multiple "Actual" columns (likely representing different time periods)
  - Data region: Rows 4-81 (77 rows)
  - First row contains dates (e.g., "2022-11-30")
  - Subsequent rows contain financial values
- **Formulas**: 199 formulas indicating calculated values

#### Balance Sheet
- **Purpose**: Financial position reporting
- **Size**: 94 rows × 17 columns
- **Data Structure**:
  - Headers at row 3: Multiple "Actuals" columns
  - Data region: Rows 3-37 (34 rows)
  - Similar structure to Income Statement with dates and values
- **Formulas**: 407 formulas (most formula-heavy sheet)

#### Cash Flow Statement
- **Purpose**: Cash flow reporting
- **Size**: 122 rows × 14 columns
- **Data Structure**:
  - Headers at row 4: Multiple "Actual" columns
  - Data region: Rows 4-38 (34 rows)
  - Consistent with other financial statements
- **Formulas**: 228 formulas

### Data Source Analysis
**No separate data sheets identified.** The financial data appears to be:
1. Either manually entered directly into the report sheets
2. Or pulled from external sources via formulas
3. The repeating "Actual" column headers suggest time-series data

### JSON Schema for Financial Data
Since all sheets follow a similar pattern, here's a unified schema:

```json
{
  "type": "object",
  "properties": {
    "date": {
      "type": "string",
      "format": "date",
      "description": "Period date (e.g., 2022-11-30)"
    },
    "line_item": {
      "type": "string",
      "description": "Financial statement line item name"
    },
    "value": {
      "type": "number",
      "description": "Financial value"
    },
    "statement_type": {
      "type": "string",
      "enum": ["income_statement", "balance_sheet", "cash_flow"],
      "description": "Which financial statement this belongs to"
    }
  },
  "required": ["date", "line_item", "value", "statement_type"]
}
```

## 2. Cube - KPI Dashboard-1.xlsx

### Structure Summary
- **Total Sheets**: 5
- **Sheet Types**:
  - 1 About/Info sheet
  - 3 Dashboard/Report sheets (Revenue, Financial Metrics, OpEx Analysis)
  - 1 Data sheet (Drivers)
- **Mixed approach**: Some embedded data, some separate data sheet
- **Moderate formula use**: 453 total formulas

### Sheet Details

#### About Sheet
- **Purpose**: Information and navigation
- **Size**: 52 rows × 10 columns
- **Features**: 14 merged cells, navigation information

#### Revenue Sheet
- **Purpose**: Revenue analysis dashboard
- **Size**: 1042 rows × 33 columns (large sheet)
- **Data Regions**:
  - Region 1 (Rows 44-63): Actuals vs Budget comparison
  - Region 2 (Rows 68-89): Product-based breakdown
- **Formulas**: 139 formulas for calculations

#### Financial Metrics Sheet
- **Purpose**: Key financial metrics dashboard
- **Size**: 1044 rows × 30 columns
- **Data Region**: Rows 55-79 with Actuals/Budget columns
- **Formulas**: 106 formulas

#### OpEx Analysis Sheet
- **Purpose**: Operating expense analysis
- **Size**: 1059 rows × 30 columns
- **Multiple Data Regions**:
  - Monthly breakdown (Rows 62-100)
  - Department comparison (Rows 105-116)
- **Interactive Elements**: Uses dropdowns for filtering (Department, Entity, Month, Type)
- **Formulas**: 208 formulas (most complex sheet)

#### Drivers Sheet (DATA SOURCE)
- **Purpose**: Raw data table
- **Size**: 21 rows × 7 columns
- **Structure**: Clean tabular data starting at row 4
- **Columns**:
  - Cost Center
  - Month
  - Entity
  - Time
  - Products
  - Market
  - Account

### JSON Schemas

#### Drivers Data Schema
```json
{
  "type": "object",
  "properties": {
    "cost_center": {
      "type": "string",
      "description": "Department or cost center"
    },
    "month": {
      "type": "string",
      "description": "Month or period (e.g., Jan-22, Q1-22)"
    },
    "entity": {
      "type": "string",
      "description": "Business entity (e.g., Global Co, Gco US)"
    },
    "time": {
      "type": "string",
      "enum": ["Month", "YTD"],
      "description": "Time aggregation type"
    },
    "products": {
      "type": "string",
      "description": "Product category"
    },
    "market": {
      "type": "string",
      "description": "Geographic market"
    },
    "account": {
      "type": "string",
      "description": "Account or metric type"
    }
  },
  "required": ["cost_center", "month", "entity", "account"]
}
```

#### OpEx Analysis Filter Schema
```json
{
  "type": "object",
  "properties": {
    "department": {
      "type": "string",
      "description": "Selected department filter"
    },
    "entity": {
      "type": "string",
      "description": "Selected entity filter"
    },
    "month": {
      "type": "string",
      "description": "Selected month filter"
    },
    "type": {
      "type": "string",
      "enum": ["Month", "YTD"],
      "description": "Time view type"
    }
  }
}
```

## Key Findings for Automation

### Basic 3-Statement Model
1. **No separate data tables** - Data is embedded in report sheets
2. **Time-series structure** - Each column represents a time period
3. **Formula-driven** - Heavy reliance on Excel formulas for calculations
4. **Automation approach**: 
   - Extract data from the report sheets themselves
   - Parse the column headers to identify time periods
   - Map row labels to line items

### Cube KPI Dashboard
1. **Mixed data approach** - Some data in separate sheet (Drivers), some embedded
2. **Interactive filters** - Uses dropdown selections to filter views
3. **Multiple data views** - Same data presented in different aggregations
4. **Automation approach**:
   - Use Drivers sheet as primary data source
   - Implement filtering logic to replicate dropdown functionality
   - Calculate aggregations based on filter selections

## Recommendations for Automation

1. **Data Extraction**:
   - For Basic 3-Statement Model: Create parser to extract data from report sheets
   - For Cube Dashboard: Use Drivers sheet as primary data source

2. **Data Transformation**:
   - Implement time-series handling for financial statements
   - Build aggregation logic for KPI calculations
   - Support multiple time views (Month, YTD, Quarter)

3. **Report Generation**:
   - Maintain the original Excel formatting and structure
   - Preserve formula relationships where possible
   - Support interactive elements (filters, dropdowns)

4. **Data Input Format**:
   - Design unified JSON format that can feed both templates
   - Support hierarchical data (entities, departments, products)
   - Include temporal dimensions (dates, periods)