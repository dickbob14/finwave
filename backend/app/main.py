from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .planner.planner_agent import create_plan
from .mcp_schema import Plan
from .executors.fetch_qb import fetch_qb
from .executors.analyze_data import analyze_data
from .executors.chart import make_chart

app = FastAPI(
    title="FinWave Analytics API",
    description="Advanced financial analytics powered by QuickBooks data and AI",
    version="2.0.0"
)

class Ask(BaseModel):
    query: str

@app.post("/ask")
def ask(body: Ask):
    """
    Enhanced ask endpoint supporting multi-step financial analysis
    
    Execution flow:
    1. Plan generation (OpenAI)
    2. Data fetching (QuickBooks API)
    3. Data analysis (pandas/calculations)
    4. Chart generation (Plotly)
    """
    try:
        plan: Plan = create_plan(body.query)
        print(f"📋 Generated plan: {plan.model_dump()}")
        
        # Execute plan steps sequentially
        context = {}
        
        for i, step in enumerate(plan.steps):
            print(f"🔄 Executing step {i+1}/{len(plan.steps)}: {step.role}")
            
            if step.role == "fetch_qb":
                # Fetch QuickBooks data
                qb_result = fetch_qb(**step.args)
                context["transactions"] = qb_result["transactions"]
                context["qb_metadata"] = qb_result
                print(f"✓ Fetched {len(context['transactions'])} transactions")
                
            elif step.role == "analyze_data":
                # Analyze fetched data
                if "transactions" not in context:
                    raise HTTPException(status_code=500, detail="No data available for analysis")
                
                analysis_result = analyze_data(context["transactions"], **step.args)
                context["analysis"] = analysis_result
                print(f"✓ Analysis complete: {step.args.get('type', 'unknown')}")
                
            elif step.role == "chart":
                # Generate visualization
                chart_args = step.args.copy()
                
                # Pass analysis result if available, otherwise raw transactions
                if "analysis" in context:
                    result = make_chart(analysis_result=context["analysis"], **chart_args)
                elif "transactions" in context:
                    result = make_chart(data=context["transactions"], **chart_args)
                else:
                    raise HTTPException(status_code=500, detail="No data available for charting")
                
                # Add execution metadata
                result["execution_summary"] = {
                    "plan_steps": len(plan.steps),
                    "data_points": len(context.get("transactions", [])),
                    "query": body.query
                }
                
                print(f"✓ Chart generated: {chart_args.get('title', 'Untitled')}")
                return result
        
        # If no chart step was executed
        return {
            "error": "Plan did not include chart generation",
            "plan": plan.model_dump(),
            "context_keys": list(context.keys())
        }
        
    except Exception as e:
        print(f"❌ Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")

@app.get("/")
def ping():
    return {
        "status": "FinWave Analytics API v2.0",
        "features": [
            "QuickBooks OAuth integration",
            "Multi-entity data fetching", 
            "Advanced financial analysis",
            "Multiple chart types",
            "AI-powered query planning"
        ],
        "supported_queries": [
            "inventory spend analysis",
            "customer profitability",
            "expense breakdown",
            "cash flow trends", 
            "vendor payment analysis",
            "profit margins by product",
            "accounts receivable aging",
            "revenue vs expenses"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    from .quickbooks_auth import ensure_token
    
    qb_status = "connected" if ensure_token() else "disconnected"
    
    return {
        "status": "healthy",
        "quickbooks": qb_status,
        "version": "2.0.0"
    }

# ---------------- QuickBooks OAuth routes ----------------
from fastapi.responses import RedirectResponse
from .quickbooks_auth import get_auth_url, exchange_code

@app.get("/connect_qb")
def connect_qb():
    return RedirectResponse(get_auth_url())

@app.get("/qb_callback")
def qb_callback(code: str = None, realmId: str = None, state: str = None, error: str = None):
    if error:
        return {"error": f"OAuth error: {error}"}
    
    if not code or not realmId:
        return {
            "error": "Missing required parameters",
            "received_params": {
                "code": "present" if code else "missing",
                "realmId": "present" if realmId else "missing", 
                "state": state,
                "error": error
            },
            "help": "Make sure you're redirected from QuickBooks with code and realmId parameters"
        }
    
    try:
        exchange_code(code, realmId)
        return {"detail": "QuickBooks connected. You can now hit /ask."}
    except Exception as e:
        return {"error": f"Failed to exchange code: {str(e)}"}