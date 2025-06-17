import pandas as pd, plotly.graph_objects as go
from typing import Dict, List

def make_chart(transactions: List[dict], type: str="line", title: str="Cash") -> Dict:
    df = pd.DataFrame(transactions)
    df["balance"] = df["amount"].cumsum()
    fig = go.Figure(go.Scatter(x=df["date"], y=df["balance"]))
    fig.update_layout(title=title)
    return {"chart_spec": fig.to_json(), "citations": df["id"].tolist()}