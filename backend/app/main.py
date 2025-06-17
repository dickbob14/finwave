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