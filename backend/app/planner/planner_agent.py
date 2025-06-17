import os, json
from openai import OpenAI
from ..mcp_schema import Plan

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

_SYSTEM = """You are a planner that converts user finance questions
into JSON Plans. Roles allowed: fetch_qb, chart.
Return ONLY valid JSON."""
_FEWSHOT = '''
User: show cash trend
Assistant: {"steps":[
  {"role":"fetch_qb","args":{"days":365}},
  {"role":"chart","args":{"type":"line","title":"Operating cash"}}
]}'''

def create_plan(user_query: str) -> Plan:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content":_SYSTEM},
            {"role":"assistant","content":_FEWSHOT},
            {"role":"user","content":user_query}
        ],
    )
    return Plan.model_validate_json(resp.choices[0].message.content)