from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional

class Step(BaseModel):
    role: Literal["fetch_qb", "analyze_data", "chart"]
    args: Dict[str, Any]

class Plan(BaseModel):
    steps: List[Step]
    
# Extended QuickBooks entity types
QB_ENTITIES = [
    "Account", "Bill", "BillPayment", "Budget", "Class", "CompanyInfo", 
    "CreditMemo", "Customer", "Department", "Deposit", "Employee", 
    "Estimate", "Expense", "Invoice", "Item", "JournalEntry", 
    "Payment", "PaymentMethod", "Purchase", "PurchaseOrder", 
    "SalesReceipt", "TaxCode", "TimeActivity", "Transfer", "Vendor", 
    "VendorCredit"
]

# Financial analysis types
ANALYSIS_TYPES = [
    "cash_flow", "revenue_analysis", "expense_breakdown", "profit_margins",
    "inventory_turnover", "accounts_receivable", "accounts_payable", 
    "budget_variance", "trend_analysis", "comparative_analysis",
    "customer_profitability", "vendor_analysis", "tax_summary"
]

# Chart types
CHART_TYPES = [
    "line", "bar", "pie", "scatter", "area", "waterfall", "funnel",
    "treemap", "heatmap", "gauge", "table"
]