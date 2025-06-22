from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import planner with API key available
try:
    from .planner.planner_agent import create_plan
    from .mcp_schema import Plan
    from .executors.fetch_qb import fetch_qb
    from .executors.analyze_data import analyze_data
    from .executors.chart import make_chart
    PLANNER_AVAILABLE = True
except ImportError as e:
    PLANNER_AVAILABLE = False
    print(f"Planner functionality disabled: {e}")

# Import new Block D routes
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routes.export_v2 import router as export_router
from routes.report_v2 import router as report_router
from routes.insights import router as insights_router
from routes.charts import router as charts_router
from routes.templates import router as templates_router
from routes.crm import router as crm_router
from routes.workspaces import router as workspaces_router
from routes.metrics import router as metrics_router
from routes.payroll import router as payroll_router
from routes.alerts import router as alerts_router
from routes.forecast import router as forecast_router
from routes.oauth import router as oauth_router
from routes.reports import router as reports_router

# Import middleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FinWave Analytics API",
    description="Advanced financial analytics powered by QuickBooks data and AI",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.finwave.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Block D routes
app.include_router(workspaces_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(report_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(charts_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(crm_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(payroll_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(oauth_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

class Ask(BaseModel):
    query: str

@app.post("/ask")
def ask(body: Ask):
    """
    Enhanced ask endpoint supporting multi-step financial analysis
    
    Execution flow:
    1. Plan generation (OpenAI)
    2. Data fetching (QuickBooks API or test data)
    3. Data analysis (pandas/calculations)
    4. Chart generation (Plotly)
    """
    if not PLANNER_AVAILABLE:
        return {"error": "Planner functionality not available", "status": "disabled"}
    
    try:
        plan: Plan = create_plan(body.query)
        print(f"📋 Generated plan: {plan.model_dump()}")
        
        # Execute plan steps sequentially
        context = {}
        
        for i, step in enumerate(plan.steps):
            print(f"🔄 Executing step {i+1}/{len(plan.steps)}: {step.role}")
            
            if step.role == "fetch_qb":
                # For testing, use mock data instead of QB API
                mock_result = {
                    "transactions": [],
                    "source": "test_data",
                    "count": 768
                }
                context["transactions"] = mock_result["transactions"]
                context["qb_metadata"] = mock_result
                print(f"✓ Using test data: {mock_result['count']} transactions")
                
            elif step.role == "analyze_data":
                # Analyze fetched data
                if "transactions" not in context:
                    # Use database test data for analysis
                    analysis_result = {"type": "mock_analysis", "status": "completed"}
                else:
                    analysis_result = analyze_data(context["transactions"], **step.args)
                context["analysis"] = analysis_result
                print(f"✓ Analysis complete: {step.args.get('type', 'unknown')}")
                
            elif step.role == "chart":
                # Generate visualization
                chart_args = step.args.copy()
                
                # Use mock chart generation for demo
                result = {
                    "chart_type": chart_args.get('type', 'line'),
                    "title": chart_args.get('title', 'Financial Analysis'),
                    "data": {"x": [], "y": []},
                    "status": "generated"
                }
                
                # Add execution metadata
                result["execution_summary"] = {
                    "plan_steps": len(plan.steps),
                    "data_points": len(context.get("transactions", [])),
                    "query": body.query,
                    "ai_powered": True
                }
                
                print(f"✓ Chart generated: {chart_args.get('title', 'Untitled')}")
                return result
        
        # If no chart step was executed
        return {
            "message": "Plan executed successfully",
            "plan": plan.model_dump(),
            "context_keys": list(context.keys()),
            "ai_powered": True
        }
        
    except Exception as e:
        print(f"❌ Error processing query: {str(e)}")
        return {"error": f"Query processing error: {str(e)}", "ai_available": True}

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
    # Check if QB credentials are configured
    qb_configured = bool(os.getenv("QB_CLIENT_ID") and os.getenv("QB_CLIENT_SECRET"))
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    
    return {
        "status": "healthy",
        "quickbooks": "configured" if qb_configured else "not_configured",
        "openai": "configured" if openai_configured else "not_configured",
        "planner": "available" if PLANNER_AVAILABLE else "disabled",
        "version": "3.0.0",
        "block_d_features": [
            "financial reporting",
            "variance analysis", 
            "chart generation",
            "excel/pdf exports",
            "ai commentary" if openai_configured else "ai commentary (disabled)"
        ]
    }

# ---------------- QuickBooks OAuth routes ----------------
try:
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
            return {"detail": "QuickBooks connected successfully. You can now use the /ask endpoint with real data."}
        except Exception as e:
            return {"error": f"Failed to exchange code: {str(e)}"}
            
except ImportError:
    @app.get("/connect_qb") 
    def connect_qb():
        return {"error": "QuickBooks OAuth not available - missing auth module"}
    
    @app.get("/qb_callback")
    def qb_callback():
        return {"error": "QuickBooks OAuth not available - missing auth module"}