"""
FinWave QuickBooks Server - Real QuickBooks data integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import sys
import json
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.quickbooks_auth import get_auth_url, exchange_code, ensure_token
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="FinWave QuickBooks Integration",
    description="Real-time financial analytics with QuickBooks data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Ask(BaseModel):
    query: str

def get_qb_headers():
    """Get headers for QuickBooks API requests"""
    token_data = ensure_token()
    if not token_data:
        raise HTTPException(status_code=401, detail="QuickBooks not connected. Please visit /connect_qb")
    
    return {
        "Authorization": f"Bearer {token_data['access_token']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_qb_base_url():
    """Get QuickBooks API base URL"""
    token_data = ensure_token()
    if not token_data:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    env = os.getenv("QB_ENVIRONMENT", "sandbox")
    if env == "sandbox":
        return f"https://sandbox-quickbooks.api.intuit.com/v3/company/{token_data['realm_id']}"
    else:
        return f"https://quickbooks.api.intuit.com/v3/company/{token_data['realm_id']}"

@app.get("/")
def root():
    return {
        "message": "FinWave QuickBooks Integration",
        "status": "running",
        "endpoints": [
            "/health - Check connection status",
            "/connect_qb - Connect to QuickBooks",
            "/real/insights - Get real financial insights",
            "/real/charts/{chart_type} - Get real data charts",
            "/real/transactions - Get real transactions",
            "/ask - AI analysis of real data"
        ]
    }

@app.get("/health")
def health():
    token_data = ensure_token()
    qb_connected = token_data is not None
    
    return {
        "status": "healthy",
        "quickbooks": "connected" if qb_connected else "not_connected",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
        "environment": os.getenv("QB_ENVIRONMENT", "sandbox"),
        "realm_id": token_data.get("realm_id") if token_data else None
    }

@app.get("/connect_qb")
def connect_qb():
    """Redirect to QuickBooks OAuth"""
    return RedirectResponse(get_auth_url())

@app.get("/qb_callback")
def qb_callback(code: str = None, realmId: str = None, state: str = None, error: str = None):
    """Handle QuickBooks OAuth callback"""
    if error:
        return {"error": f"OAuth error: {error}"}
    
    if not code or not realmId:
        return {"error": "Missing required parameters"}
    
    try:
        exchange_code(code, realmId)
        return {
            "message": "QuickBooks connected successfully!",
            "realm_id": realmId,
            "next_steps": "You can now use /real/insights and other endpoints"
        }
    except Exception as e:
        return {"error": f"Failed to exchange code: {str(e)}"}

@app.get("/real/company")
def get_company_info():
    """Get company information from QuickBooks"""
    try:
        response = requests.get(
            f"{get_qb_base_url()}/companyinfo/1",
            headers=get_qb_headers()
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/real/transactions")
def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Get real transactions from QuickBooks"""
    try:
        # Default to last 6 months if no dates provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        # Get invoices
        invoice_query = f"SELECT * FROM Invoice WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}' MAXRESULTS {limit}"
        invoice_response = requests.get(
            f"{get_qb_base_url()}/query?query={invoice_query}",
            headers=get_qb_headers()
        )
        invoices = invoice_response.json().get("QueryResponse", {}).get("Invoice", [])
        
        # Get expenses
        expense_query = f"SELECT * FROM Purchase WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}' MAXRESULTS {limit}"
        expense_response = requests.get(
            f"{get_qb_base_url()}/query?query={expense_query}",
            headers=get_qb_headers()
        )
        expenses = expense_response.json().get("QueryResponse", {}).get("Purchase", [])
        
        return {
            "period": {"start": start_date, "end": end_date},
            "invoices": invoices,
            "expenses": expenses,
            "summary": {
                "total_invoices": len(invoices),
                "total_expenses": len(expenses),
                "revenue": sum(float(inv.get("TotalAmt", 0)) for inv in invoices),
                "expenses_total": sum(float(exp.get("TotalAmt", 0)) for exp in expenses)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/real/insights")
def get_real_insights():
    """Get financial insights from real QuickBooks data"""
    try:
        # Get transactions
        transactions = get_transactions()
        
        # Calculate key metrics
        revenue = transactions["summary"]["revenue"]
        expenses = transactions["summary"]["expenses_total"]
        profit = revenue - expenses
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0
        
        # Get accounts receivable
        ar_query = "SELECT * FROM Invoice WHERE Balance > '0' MAXRESULTS 100"
        ar_response = requests.get(
            f"{get_qb_base_url()}/query?query={ar_query}",
            headers=get_qb_headers()
        )
        ar_invoices = ar_response.json().get("QueryResponse", {}).get("Invoice", [])
        total_ar = sum(float(inv.get("Balance", 0)) for inv in ar_invoices)
        
        return {
            "summary": "Real-time QuickBooks Financial Analysis",
            "key_metrics": {
                "total_revenue": f"${revenue:,.2f}",
                "total_expenses": f"${expenses:,.2f}",
                "net_profit": f"${profit:,.2f}",
                "profit_margin": f"{profit_margin:.1f}%",
                "accounts_receivable": f"${total_ar:,.2f}",
                "outstanding_invoices": len(ar_invoices)
            },
            "ai_recommendations": [
                f"Focus on collecting ${total_ar:,.2f} in outstanding receivables",
                f"Profit margin of {profit_margin:.1f}% indicates {'healthy' if profit_margin > 15 else 'room for improvement in'} operations",
                "Consider expense optimization strategies" if expenses > revenue * 0.7 else "Expense ratio is well-controlled"
            ],
            "variance_alerts": [
                f"Revenue: ${revenue:,.2f} for the period",
                f"Expenses: ${expenses:,.2f} ({(expenses/revenue*100):.1f}% of revenue)" if revenue > 0 else "No revenue recorded"
            ],
            "generated_by": "FinWave QuickBooks Analytics",
            "data_source": "Live QuickBooks Data"
        }
    except Exception as e:
        if "401" in str(e):
            raise HTTPException(status_code=401, detail="QuickBooks not connected. Please visit /connect_qb")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/real/charts/{chart_type}")
def get_real_chart(chart_type: str):
    """Generate charts from real QuickBooks data"""
    try:
        transactions = get_transactions()
        
        if chart_type == "revenue-trend":
            # Group invoices by month
            monthly_revenue = {}
            for invoice in transactions["invoices"]:
                date = datetime.strptime(invoice["TxnDate"], "%Y-%m-%d")
                month_key = date.strftime("%b %Y")
                monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + float(invoice.get("TotalAmt", 0))
            
            # Sort by date
            sorted_months = sorted(monthly_revenue.items(), key=lambda x: datetime.strptime(x[0], "%b %Y"))
            
            return {
                "chart_type": "line",
                "title": "Revenue Trend - QuickBooks Data",
                "plotly_data": {
                    "data": [{
                        "x": [month for month, _ in sorted_months],
                        "y": [revenue for _, revenue in sorted_months],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "name": "Revenue",
                        "line": {"color": "#3b82f6", "width": 3}
                    }],
                    "layout": {
                        "title": "Monthly Revenue from QuickBooks",
                        "xaxis": {"title": "Month"},
                        "yaxis": {"title": "Revenue ($)"},
                        "hovermode": "x"
                    }
                },
                "data_points": len(sorted_months),
                "ai_insight": f"Revenue data from {len(transactions['invoices'])} invoices",
                "generated_at": datetime.now().isoformat()
            }
        
        elif chart_type == "expense-breakdown":
            # Group expenses by type
            expense_categories = {}
            for expense in transactions["expenses"]:
                category = expense.get("AccountRef", {}).get("name", "Other")
                expense_categories[category] = expense_categories.get(category, 0) + float(expense.get("TotalAmt", 0))
            
            return {
                "chart_type": "pie",
                "title": "Expense Breakdown - QuickBooks Data",
                "plotly_data": {
                    "data": [{
                        "labels": list(expense_categories.keys()),
                        "values": list(expense_categories.values()),
                        "type": "pie",
                        "hole": 0.4
                    }],
                    "layout": {
                        "title": "Expense Categories from QuickBooks"
                    }
                },
                "data_points": len(expense_categories),
                "ai_insight": f"Expense data from {len(transactions['expenses'])} transactions",
                "generated_at": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=404, detail=f"Chart type '{chart_type}' not found")
            
    except Exception as e:
        if "401" in str(e):
            raise HTTPException(status_code=401, detail="QuickBooks not connected. Please visit /connect_qb")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_ai(body: Ask):
    """AI-powered analysis of real QuickBooks data"""
    if not os.getenv("OPENAI_API_KEY"):
        return {"error": "OpenAI API key not configured"}
    
    try:
        # Get real data
        transactions = get_transactions()
        insights = get_real_insights()
        
        # Use OpenAI to analyze
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        context = f"""
        QuickBooks Financial Data Summary:
        - Total Revenue: {insights['key_metrics']['total_revenue']}
        - Total Expenses: {insights['key_metrics']['total_expenses']}
        - Net Profit: {insights['key_metrics']['net_profit']}
        - Profit Margin: {insights['key_metrics']['profit_margin']}
        - Accounts Receivable: {insights['key_metrics']['accounts_receivable']}
        - Number of Invoices: {transactions['summary']['total_invoices']}
        - Number of Expenses: {transactions['summary']['total_expenses']}
        
        User Query: {body.query}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial analyst with access to real QuickBooks data. Provide insights based on the actual data."},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            "query": body.query,
            "ai_analysis": response.choices[0].message.content,
            "data_context": {
                "source": "Live QuickBooks Data",
                "invoices": transactions['summary']['total_invoices'],
                "expenses": transactions['summary']['total_expenses'],
                "period": transactions['period']
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        if "401" in str(e):
            return {"error": "QuickBooks not connected. Please visit /connect_qb first"}
        return {"error": f"Analysis failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    print("Starting FinWave QuickBooks Server...")
    print("Visit http://localhost:8000/connect_qb to connect to QuickBooks")
    uvicorn.run(app, host="0.0.0.0", port=8000)