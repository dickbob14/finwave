from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .planner.planner_agent import create_plan
from .mcp_schema import Plan
from .executors.fetch_qb import fetch_qb
from .executors.chart import make_chart

app = FastAPI()

class Ask(BaseModel):
    query: str

@app.post("/ask")
def ask(body: Ask):
    plan: Plan = create_plan(body.query)
    payload = {}
    for step in plan.steps:
        if step.role == "fetch_qb":
            payload["transactions"] = fetch_qb(**step.args)["transactions"]
        elif step.role == "chart":
            if "transactions" not in payload:
                raise HTTPException(status_code=500, detail="No data fetched")
            return make_chart(payload["transactions"], **step.args)
    return {"error":"Plan produced no chart"}

@app.get("/")
def ping():
    return {"status":"FinWave Day-1 ready"}

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