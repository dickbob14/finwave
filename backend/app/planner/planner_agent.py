import os
from openai import OpenAI
from ..mcp_schema import Plan

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

_SYSTEM = """You are a financial planning AI that converts user questions into execution plans.

Available roles:
1. fetch_qb - Get data from QuickBooks (entities: Account, Invoice, Bill, Item, Customer, Vendor, etc.)
2. analyze_data - Perform calculations and analysis on fetched data  
3. chart - Create visualizations

Return ONLY valid JSON with steps array. Each step has "role" and "args".

QuickBooks entities available: Account, Bill, BillPayment, Customer, Employee, Expense, Invoice, Item, JournalEntry, Payment, Purchase, SalesReceipt, Vendor, and more.

Analysis types: cash_flow, revenue_analysis, expense_breakdown, profit_margins, inventory_turnover, accounts_receivable, budget_variance, trend_analysis, customer_profitability, vendor_analysis.

Chart types: line, bar, pie, scatter, area, waterfall, treemap, heatmap, table."""

_EXAMPLES = [
    {
        "role": "user", 
        "content": "show cash flow trends"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Account","JournalEntry"],"filters":{"account_type":"Bank","days":365}}},{"role":"analyze_data","args":{"type":"cash_flow","period":"monthly"}},{"role":"chart","args":{"type":"line","title":"Cash Flow Trends","x_axis":"month","y_axis":"cash_flow"}}]}'
    },
    {
        "role": "user", 
        "content": "inventory spend analysis"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Item","Purchase","Bill"],"filters":{"item_type":"Inventory","days":180}}},{"role":"analyze_data","args":{"type":"inventory_turnover","groupby":"item"}},{"role":"chart","args":{"type":"bar","title":"Inventory Spend Analysis","x_axis":"item","y_axis":"total_cost"}}]}'
    },
    {
        "role": "user", 
        "content": "top customers by revenue"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Customer","Invoice","SalesReceipt"],"filters":{"days":365}}},{"role":"analyze_data","args":{"type":"customer_profitability","sort":"revenue","limit":10}},{"role":"chart","args":{"type":"bar","title":"Top Customers by Revenue","x_axis":"customer","y_axis":"revenue"}}]}'
    },
    {
        "role": "user", 
        "content": "expense breakdown by category"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Expense","Bill","Purchase"],"filters":{"days":90}}},{"role":"analyze_data","args":{"type":"expense_breakdown","groupby":"category"}},{"role":"chart","args":{"type":"pie","title":"Expense Breakdown","values":"amount","labels":"category"}}]}'
    },
    {
        "role": "user", 
        "content": "monthly revenue vs expenses"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Invoice","SalesReceipt","Expense","Bill"],"filters":{"days":365}}},{"role":"analyze_data","args":{"type":"comparative_analysis","metrics":["revenue","expenses"],"period":"monthly"}},{"role":"chart","args":{"type":"line","title":"Revenue vs Expenses","x_axis":"month","y_axis":"amount","series":["revenue","expenses"]}}]}'
    },
    {
        "role": "user", 
        "content": "vendor payment analysis"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Vendor","Bill","BillPayment"],"filters":{"days":180}}},{"role":"analyze_data","args":{"type":"vendor_analysis","metrics":["total_billed","total_paid","outstanding"]}},{"role":"chart","args":{"type":"table","title":"Vendor Payment Analysis","columns":["vendor","total_billed","total_paid","outstanding"]}}]}'
    },
    {
        "role": "user", 
        "content": "profit margins by product"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Item","Invoice","Purchase"],"filters":{"item_type":"Service,Inventory","days":180}}},{"role":"analyze_data","args":{"type":"profit_margins","groupby":"item"}},{"role":"chart","args":{"type":"bar","title":"Profit Margins by Product","x_axis":"item","y_axis":"margin_percent"}}]}'
    },
    {
        "role": "user", 
        "content": "accounts receivable aging"
    },
    {
        "role": "assistant", 
        "content": '{"steps":[{"role":"fetch_qb","args":{"entities":["Invoice","Payment","Customer"],"filters":{"status":"unpaid"}}},{"role":"analyze_data","args":{"type":"accounts_receivable","aging_buckets":[30,60,90]}},{"role":"chart","args":{"type":"bar","title":"Accounts Receivable Aging","x_axis":"aging_bucket","y_axis":"amount"}}]}'
    }
]

def create_plan(user_query: str) -> Plan:
    messages = [{"role": "system", "content": _SYSTEM}]
    
    # Add examples
    for example in _EXAMPLES:
        messages.append(example)
    
    # Add user query
    messages.append({"role": "user", "content": user_query})
    
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=messages,
    )
    
    return Plan.model_validate_json(resp.choices[0].message.content)