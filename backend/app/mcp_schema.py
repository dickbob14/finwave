from pydantic import BaseModel
from typing import Any, Dict, List, Literal

class Step(BaseModel):
    role: Literal["fetch_qb", "chart"]
    args: Dict[str, Any]

class Plan(BaseModel):
    steps: List[Step]