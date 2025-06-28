# QuickBooks Report Structure Analysis

## Overview
This document summarizes the key findings from analyzing QuickBooks Balance Sheet and Profit & Loss report structures.

## Balance Sheet Structure

### Top-Level Structure
```json
{
  "Header": { /* Report metadata */ },
  "Columns": { /* Column definitions */ },
  "Rows": { /* Hierarchical data */ }
}
```

### Header Information
- **Time**: Report generation timestamp
- **ReportName**: "BalanceSheet"
- **DateMacro**: Human-readable date range
- **ReportBasis**: "Accrual" or "Cash"
- **StartPeriod/EndPeriod**: Date range
- **Currency**: "USD"
- **Options**: Array of report options (e.g., AccountingStandard: GAAP)

### Column Structure
Typically two columns:
1. Account name/description (ColType: "Account")
2. Amount value (ColType: "Money")

### Row Structure (Hierarchical)
The report uses a nested structure with these key patterns:

#### Row Types
- **Section**: Major groupings (Assets, Liabilities, Equity)
- **Data**: Individual account lines

#### Row Properties
- **Header**: Contains ColData array with section/group names
- **Rows**: Nested Row array for sub-sections
- **Summary**: Section totals
- **type**: "Section" or "Data"
- **group**: Semantic grouping (e.g., "CurrentAssets", "BankAccounts")

### Key Groups in Balance Sheet
1. **Assets**
   - CurrentAssets
     - BankAccounts
     - AR (Accounts Receivable)
     - OtherCurrentAssets
   - FixedAssets

2. **Liabilities**
   - CurrentLiabilities
     - AP (Accounts Payable)
     - CreditCards
     - OtherCurrentLiabilities
   - LongTermLiabilities

3. **Equity**
   - Opening Balance Equity
   - Retained Earnings
   - NetIncome

### Data Row Structure
Individual account lines contain:
```json
{
  "ColData": [
    {"value": "Account Name", "id": "account_id"},
    {"value": "amount"}
  ],
  "type": "Data"
}
```

## Parsing Strategy

To parse these reports effectively:

1. **Recursive traversal**: Navigate through nested Rows
2. **Type detection**: Handle "Section" vs "Data" rows differently
3. **Group tracking**: Use the "group" property for categorization
4. **Value extraction**: Parse monetary values from ColData[1].value
5. **Hierarchy preservation**: Maintain parent-child relationships

## Key Differences from Standard JSON
- Deeply nested structure requiring recursive parsing
- Mixed content types (sections vs data rows)
- Summary rows separate from detail rows
- Account IDs embedded in ColData objects

## Implementation Notes
When implementing the parser:
- Handle missing/optional fields gracefully
- Convert string amounts to floats/decimals
- Preserve account hierarchy for drill-down capabilities
- Map QuickBooks groups to FinWave categories