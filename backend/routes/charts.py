"""
Charts API routes for serving Plotly JSON data
Provides REST endpoints for financial chart data to be consumed by Next.js frontend
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract

from database import get_db_session
from models.financial import GeneralLedger, Account, Customer, Vendor
from templates.excel_templates import ExcelTemplateGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/charts", tags=["charts"])

@router.get("/revenue-trend")
async def get_revenue_trend_chart(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    grouping: str = Query("monthly", description="Grouping period (daily, weekly, monthly, quarterly)")
):
    """
    Get revenue trend chart data in Plotly JSON format
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        with get_db_session() as db:
            chart_data = _get_revenue_trend_data(db, start_date, end_date, grouping)
            
            # Convert to Plotly format
            plotly_data = {
                "data": [
                    {
                        "x": [point["period"] for point in chart_data],
                        "y": [point["revenue"] for point in chart_data],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "name": "Revenue",
                        "line": {"color": "#2E86AB", "width": 3},
                        "marker": {"size": 8, "color": "#2E86AB"}
                    }
                ],
                "layout": {
                    "title": {"text": f"Revenue Trend ({grouping.title()})", "font": {"size": 20}},
                    "xaxis": {"title": "Period", "type": "category"},
                    "yaxis": {"title": "Revenue ($)", "tickformat": "$,.0f"},
                    "hovermode": "x unified",
                    "template": "plotly_white"
                }
            }
            
            return {
                "chart_type": "revenue_trend",
                "period": {"start_date": start_date, "end_date": end_date},
                "grouping": grouping,
                "plotly_data": plotly_data,
                "data_points": len(chart_data),
                "generated_at": datetime.now().isoformat()
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Revenue trend chart failed: {e}")
        raise HTTPException(status_code=500, detail="Chart generation failed")

@router.get("/expense-breakdown")
async def get_expense_breakdown_chart(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    chart_type: str = Query("pie", description="Chart type (pie, bar, treemap)")
):
    """
    Get expense breakdown chart data in Plotly JSON format
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        with get_db_session() as db:
            expense_data = _get_expense_breakdown_data(db, start_date, end_date)
            
            # Generate Plotly data based on chart type
            if chart_type == "pie":
                plotly_data = {
                    "data": [
                        {
                            "labels": [item["account_name"] for item in expense_data],
                            "values": [item["amount"] for item in expense_data],
                            "type": "pie",
                            "textinfo": "label+percent",
                            "hovertemplate": "<b>%{label}</b><br>Amount: $%{value:,.0f}<br>Percentage: %{percent}<extra></extra>"
                        }
                    ],
                    "layout": {
                        "title": {"text": "Expense Breakdown", "font": {"size": 20}},
                        "template": "plotly_white"
                    }
                }
            elif chart_type == "bar":
                plotly_data = {
                    "data": [
                        {
                            "x": [item["account_name"] for item in expense_data],
                            "y": [item["amount"] for item in expense_data],
                            "type": "bar",
                            "marker": {"color": "#F18F01"},
                            "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.0f}<extra></extra>"
                        }
                    ],
                    "layout": {
                        "title": {"text": "Expense Breakdown", "font": {"size": 20}},
                        "xaxis": {"title": "Expense Account", "tickangle": -45},
                        "yaxis": {"title": "Amount ($)", "tickformat": "$,.0f"},
                        "template": "plotly_white"
                    }
                }
            elif chart_type == "treemap":
                plotly_data = {
                    "data": [
                        {
                            "labels": [item["account_name"] for item in expense_data],
                            "values": [item["amount"] for item in expense_data],
                            "parents": [""] * len(expense_data),
                            "type": "treemap",
                            "textinfo": "label+value",
                            "hovertemplate": "<b>%{label}</b><br>Amount: $%{value:,.0f}<extra></extra>"
                        }
                    ],
                    "layout": {
                        "title": {"text": "Expense Breakdown (Treemap)", "font": {"size": 20}},
                        "template": "plotly_white"
                    }
                }
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported chart type: {chart_type}")
            
            return {
                "chart_type": "expense_breakdown",
                "period": {"start_date": start_date, "end_date": end_date},
                "display_type": chart_type,
                "plotly_data": plotly_data,
                "data_points": len(expense_data),
                "generated_at": datetime.now().isoformat()
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Expense breakdown chart failed: {e}")
        raise HTTPException(status_code=500, detail="Chart generation failed")

@router.get("/profit-margin")
async def get_profit_margin_chart(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    grouping: str = Query("monthly", description="Grouping period (monthly, quarterly)")
):
    """
    Get profit margin trend chart data in Plotly JSON format
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        with get_db_session() as db:
            margin_data = _get_profit_margin_data(db, start_date, end_date, grouping)
            
            plotly_data = {
                "data": [
                    {
                        "x": [point["period"] for point in margin_data],
                        "y": [point["profit_margin"] for point in margin_data],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "name": "Profit Margin %",
                        "line": {"color": "#A23B72", "width": 3},
                        "marker": {"size": 8, "color": "#A23B72"},
                        "hovertemplate": "<b>%{x}</b><br>Profit Margin: %{y:.1f}%<extra></extra>"
                    },
                    {
                        "x": [point["period"] for point in margin_data],
                        "y": [15] * len(margin_data),  # Target line at 15%
                        "type": "scatter",
                        "mode": "lines",
                        "name": "Target (15%)",
                        "line": {"color": "#666666", "width": 2, "dash": "dash"},
                        "hoverinfo": "skip"
                    }
                ],
                "layout": {
                    "title": {"text": f"Profit Margin Trend ({grouping.title()})", "font": {"size": 20}},
                    "xaxis": {"title": "Period", "type": "category"},
                    "yaxis": {"title": "Profit Margin (%)", "tickformat": ".1f"},
                    "hovermode": "x unified",
                    "template": "plotly_white"
                }
            }
            
            return {
                "chart_type": "profit_margin",
                "period": {"start_date": start_date, "end_date": end_date},
                "grouping": grouping,
                "plotly_data": plotly_data,
                "data_points": len(margin_data),
                "generated_at": datetime.now().isoformat()
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Profit margin chart failed: {e}")
        raise HTTPException(status_code=500, detail="Chart generation failed")

@router.get("/cash-flow")
async def get_cash_flow_chart(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    grouping: str = Query("monthly", description="Grouping period (weekly, monthly)")
):
    """
    Get cash flow chart data in Plotly JSON format
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        with get_db_session() as db:
            cash_flow_data = _get_cash_flow_data(db, start_date, end_date, grouping)
            
            plotly_data = {
                "data": [
                    {
                        "x": [point["period"] for point in cash_flow_data],
                        "y": [point["cash_in"] for point in cash_flow_data],
                        "type": "bar",
                        "name": "Cash In",
                        "marker": {"color": "#2E86AB"},
                        "hovertemplate": "<b>%{x}</b><br>Cash In: $%{y:,.0f}<extra></extra>"
                    },
                    {
                        "x": [point["period"] for point in cash_flow_data],
                        "y": [-point["cash_out"] for point in cash_flow_data],  # Negative for visual effect
                        "type": "bar",
                        "name": "Cash Out",
                        "marker": {"color": "#F18F01"},
                        "hovertemplate": "<b>%{x}</b><br>Cash Out: $%{y:,.0f}<extra></extra>"
                    },
                    {
                        "x": [point["period"] for point in cash_flow_data],
                        "y": [point["net_cash_flow"] for point in cash_flow_data],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "name": "Net Cash Flow",
                        "line": {"color": "#A23B72", "width": 3},
                        "marker": {"size": 8},
                        "yaxis": "y2",
                        "hovertemplate": "<b>%{x}</b><br>Net Cash Flow: $%{y:,.0f}<extra></extra>"
                    }
                ],
                "layout": {
                    "title": {"text": f"Cash Flow Analysis ({grouping.title()})", "font": {"size": 20}},
                    "xaxis": {"title": "Period", "type": "category"},
                    "yaxis": {"title": "Cash In/Out ($)", "tickformat": "$,.0f"},
                    "yaxis2": {
                        "title": "Net Cash Flow ($)",
                        "overlaying": "y",
                        "side": "right",
                        "tickformat": "$,.0f"
                    },
                    "hovermode": "x unified",
                    "template": "plotly_white",
                    "barmode": "relative"
                }
            }
            
            return {
                "chart_type": "cash_flow",
                "period": {"start_date": start_date, "end_date": end_date},
                "grouping": grouping,
                "plotly_data": plotly_data,
                "data_points": len(cash_flow_data),
                "generated_at": datetime.now().isoformat()
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Cash flow chart failed: {e}")
        raise HTTPException(status_code=500, detail="Chart generation failed")

@router.get("/account-balance")
async def get_account_balance_chart(
    account_id: str = Query(..., description="Account ID to chart"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    grouping: str = Query("daily", description="Grouping period (daily, weekly, monthly)")
):
    """
    Get account balance trend chart data in Plotly JSON format
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        with get_db_session() as db:
            balance_data = _get_account_balance_data(db, account_id, start_date, end_date, grouping)
            
            if not balance_data:
                raise HTTPException(status_code=404, detail=f"No data found for account {account_id}")
            
            account_name = balance_data[0].get("account_name", account_id)
            
            plotly_data = {
                "data": [
                    {
                        "x": [point["period"] for point in balance_data],
                        "y": [point["running_balance"] for point in balance_data],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "name": f"{account_name} Balance",
                        "line": {"color": "#2E86AB", "width": 3},
                        "marker": {"size": 6},
                        "hovertemplate": "<b>%{x}</b><br>Balance: $%{y:,.2f}<extra></extra>"
                    }
                ],
                "layout": {
                    "title": {"text": f"{account_name} Balance Trend", "font": {"size": 20}},
                    "xaxis": {"title": "Date", "type": "category"},
                    "yaxis": {"title": "Balance ($)", "tickformat": "$,.0f"},
                    "hovermode": "x unified",
                    "template": "plotly_white"
                }
            }
            
            return {
                "chart_type": "account_balance",
                "account_id": account_id,
                "account_name": account_name,
                "period": {"start_date": start_date, "end_date": end_date},
                "grouping": grouping,
                "plotly_data": plotly_data,
                "data_points": len(balance_data),
                "generated_at": datetime.now().isoformat()
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Account balance chart failed: {e}")
        raise HTTPException(status_code=500, detail="Chart generation failed")

@router.get("/kpi-dashboard")
async def get_kpi_dashboard_chart(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    """
    Get KPI dashboard with multiple metrics in Plotly JSON format
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        with get_db_session() as db:
            kpi_data = _get_kpi_dashboard_data(db, start_date, end_date)
            
            # Create subplot layout with multiple KPIs
            plotly_data = {
                "data": [
                    # Revenue gauge
                    {
                        "type": "indicator",
                        "mode": "gauge+number",
                        "value": kpi_data["current_revenue"],
                        "domain": {"x": [0, 0.5], "y": [0.5, 1]},
                        "title": {"text": "Revenue"},
                        "gauge": {
                            "axis": {"range": [None, kpi_data["revenue_target"]]},
                            "bar": {"color": "#2E86AB"},
                            "steps": [
                                {"range": [0, kpi_data["revenue_target"] * 0.5], "color": "lightgray"},
                                {"range": [kpi_data["revenue_target"] * 0.5, kpi_data["revenue_target"] * 0.8], "color": "gray"}
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": kpi_data["revenue_target"]
                            }
                        }
                    },
                    # Profit margin gauge
                    {
                        "type": "indicator",
                        "mode": "gauge+number",
                        "value": kpi_data["profit_margin"],
                        "domain": {"x": [0.5, 1], "y": [0.5, 1]},
                        "title": {"text": "Profit Margin %"},
                        "gauge": {
                            "axis": {"range": [0, 30]},
                            "bar": {"color": "#A23B72"},
                            "steps": [
                                {"range": [0, 10], "color": "lightgray"},
                                {"range": [10, 20], "color": "gray"}
                            ],
                            "threshold": {
                                "line": {"color": "green", "width": 4},
                                "thickness": 0.75,
                                "value": 15
                            }
                        }
                    },
                    # Cash flow indicator
                    {
                        "type": "indicator",
                        "mode": "number+delta",
                        "value": kpi_data["current_cash"],
                        "delta": {"reference": kpi_data["previous_cash"]},
                        "domain": {"x": [0, 0.5], "y": [0, 0.5]},
                        "title": {"text": "Cash Position"}
                    },
                    # Expense ratio indicator  
                    {
                        "type": "indicator",
                        "mode": "number+delta",
                        "value": kpi_data["expense_ratio"],
                        "delta": {"reference": kpi_data["previous_expense_ratio"]},
                        "domain": {"x": [0.5, 1], "y": [0, 0.5]},
                        "title": {"text": "Expense Ratio %"}
                    }
                ],
                "layout": {
                    "title": {"text": "Financial KPI Dashboard", "font": {"size": 24}},
                    "template": "plotly_white",
                    "height": 600
                }
            }
            
            return {
                "chart_type": "kpi_dashboard",
                "period": {"start_date": start_date, "end_date": end_date},
                "plotly_data": plotly_data,
                "kpi_values": kpi_data,
                "generated_at": datetime.now().isoformat()
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"KPI dashboard chart failed: {e}")
        raise HTTPException(status_code=500, detail="Chart generation failed")

@router.get("/available-charts")
async def get_available_charts():
    """
    Get list of available chart types and their descriptions
    """
    return {
        "charts": [
            {
                "endpoint": "/charts/revenue-trend",
                "name": "Revenue Trend",
                "description": "Time series chart showing revenue over time",
                "parameters": ["start_date", "end_date", "grouping"],
                "chart_types": ["line"]
            },
            {
                "endpoint": "/charts/expense-breakdown",
                "name": "Expense Breakdown",
                "description": "Breakdown of expenses by account",
                "parameters": ["start_date", "end_date", "chart_type"],
                "chart_types": ["pie", "bar", "treemap"]
            },
            {
                "endpoint": "/charts/profit-margin",
                "name": "Profit Margin Trend",
                "description": "Profit margin percentage over time",
                "parameters": ["start_date", "end_date", "grouping"],
                "chart_types": ["line"]
            },
            {
                "endpoint": "/charts/cash-flow",
                "name": "Cash Flow Analysis",
                "description": "Cash inflow, outflow, and net cash flow",
                "parameters": ["start_date", "end_date", "grouping"],
                "chart_types": ["bar", "line"]
            },
            {
                "endpoint": "/charts/account-balance",
                "name": "Account Balance Trend",
                "description": "Balance trend for a specific account",
                "parameters": ["account_id", "start_date", "end_date", "grouping"],
                "chart_types": ["line"]
            },
            {
                "endpoint": "/charts/kpi-dashboard",
                "name": "KPI Dashboard",
                "description": "Multiple KPI gauges and indicators",
                "parameters": ["start_date", "end_date"],
                "chart_types": ["gauge", "indicator"]
            }
        ],
        "grouping_options": ["daily", "weekly", "monthly", "quarterly"],
        "supported_formats": ["plotly_json"],
        "features": [
            "Interactive charts via Plotly",
            "Customizable date ranges",
            "Multiple chart types",
            "Real-time data",
            "Responsive design"
        ]
    }

# Helper functions for data retrieval
def _get_revenue_trend_data(db: Session, start_date: str, end_date: str, grouping: str) -> List[Dict]:
    """Get revenue trend data grouped by period"""
    if grouping == "daily":
        date_trunc = func.date(GeneralLedger.transaction_date)
    elif grouping == "weekly":
        date_trunc = func.date_trunc('week', GeneralLedger.transaction_date)
    elif grouping == "monthly":
        date_trunc = func.date_trunc('month', GeneralLedger.transaction_date)
    elif grouping == "quarterly":
        date_trunc = func.date_trunc('quarter', GeneralLedger.transaction_date)
    else:
        date_trunc = func.date(GeneralLedger.transaction_date)
    
    results = db.query(
        date_trunc.label('period'),
        func.sum(GeneralLedger.credit_amount).label('revenue')
    ).filter(
        and_(
            GeneralLedger.transaction_date >= start_date,
            GeneralLedger.transaction_date <= end_date,
            GeneralLedger.account_type.in_(['Income', 'Revenue'])
        )
    ).group_by(date_trunc).order_by(date_trunc).all()
    
    return [
        {
            "period": r.period.strftime("%Y-%m-%d") if hasattr(r.period, 'strftime') else str(r.period),
            "revenue": float(r.revenue or 0)
        }
        for r in results
    ]

def _get_expense_breakdown_data(db: Session, start_date: str, end_date: str) -> List[Dict]:
    """Get expense breakdown data by account"""
    results = db.query(
        GeneralLedger.account_name,
        func.sum(GeneralLedger.debit_amount).label('amount')
    ).filter(
        and_(
            GeneralLedger.transaction_date >= start_date,
            GeneralLedger.transaction_date <= end_date,
            GeneralLedger.account_type == 'Expense'
        )
    ).group_by(GeneralLedger.account_name).order_by(func.sum(GeneralLedger.debit_amount).desc()).all()
    
    return [
        {
            "account_name": r.account_name,
            "amount": float(r.amount or 0)
        }
        for r in results
    ]

def _get_profit_margin_data(db: Session, start_date: str, end_date: str, grouping: str) -> List[Dict]:
    """Get profit margin data by period"""
    if grouping == "monthly":
        date_trunc = func.date_trunc('month', GeneralLedger.transaction_date)
    elif grouping == "quarterly":
        date_trunc = func.date_trunc('quarter', GeneralLedger.transaction_date)
    else:
        date_trunc = func.date_trunc('month', GeneralLedger.transaction_date)
    
    # Get revenue by period
    revenue_data = db.query(
        date_trunc.label('period'),
        func.sum(GeneralLedger.credit_amount).label('revenue')
    ).filter(
        and_(
            GeneralLedger.transaction_date >= start_date,
            GeneralLedger.transaction_date <= end_date,
            GeneralLedger.account_type.in_(['Income', 'Revenue'])
        )
    ).group_by(date_trunc).subquery()
    
    # Get expenses by period
    expense_data = db.query(
        date_trunc.label('period'),
        func.sum(GeneralLedger.debit_amount).label('expenses')
    ).filter(
        and_(
            GeneralLedger.transaction_date >= start_date,
            GeneralLedger.transaction_date <= end_date,
            GeneralLedger.account_type == 'Expense'
        )
    ).group_by(date_trunc).subquery()
    
    # Join and calculate profit margin
    results = db.query(
        revenue_data.c.period,
        revenue_data.c.revenue,
        expense_data.c.expenses
    ).join(
        expense_data, revenue_data.c.period == expense_data.c.period
    ).order_by(revenue_data.c.period).all()
    
    return [
        {
            "period": r.period.strftime("%Y-%m") if hasattr(r.period, 'strftime') else str(r.period),
            "revenue": float(r.revenue or 0),
            "expenses": float(r.expenses or 0),
            "profit_margin": ((float(r.revenue or 0) - float(r.expenses or 0)) / float(r.revenue or 1) * 100) if r.revenue else 0
        }
        for r in results
    ]

def _get_cash_flow_data(db: Session, start_date: str, end_date: str, grouping: str) -> List[Dict]:
    """Get cash flow data by period"""
    if grouping == "weekly":
        date_trunc = func.date_trunc('week', GeneralLedger.transaction_date)
    elif grouping == "monthly":
        date_trunc = func.date_trunc('month', GeneralLedger.transaction_date)
    else:
        date_trunc = func.date_trunc('month', GeneralLedger.transaction_date)
    
    # Get cash inflows (revenue)
    cash_in = db.query(
        date_trunc.label('period'),
        func.sum(GeneralLedger.credit_amount).label('cash_in')
    ).filter(
        and_(
            GeneralLedger.transaction_date >= start_date,
            GeneralLedger.transaction_date <= end_date,
            GeneralLedger.account_type.in_(['Income', 'Revenue'])
        )
    ).group_by(date_trunc).subquery()
    
    # Get cash outflows (expenses)
    cash_out = db.query(
        date_trunc.label('period'),
        func.sum(GeneralLedger.debit_amount).label('cash_out')
    ).filter(
        and_(
            GeneralLedger.transaction_date >= start_date,
            GeneralLedger.transaction_date <= end_date,
            GeneralLedger.account_type == 'Expense'
        )
    ).group_by(date_trunc).subquery()
    
    # Join data
    results = db.query(
        cash_in.c.period,
        cash_in.c.cash_in,
        cash_out.c.cash_out
    ).join(
        cash_out, cash_in.c.period == cash_out.c.period
    ).order_by(cash_in.c.period).all()
    
    return [
        {
            "period": r.period.strftime("%Y-%m") if hasattr(r.period, 'strftime') else str(r.period),
            "cash_in": float(r.cash_in or 0),
            "cash_out": float(r.cash_out or 0),
            "net_cash_flow": float(r.cash_in or 0) - float(r.cash_out or 0)
        }
        for r in results
    ]

def _get_account_balance_data(db: Session, account_id: str, start_date: str, end_date: str, grouping: str) -> List[Dict]:
    """Get account balance trend data"""
    if grouping == "daily":
        date_trunc = func.date(GeneralLedger.transaction_date)
    elif grouping == "weekly":
        date_trunc = func.date_trunc('week', GeneralLedger.transaction_date)
    elif grouping == "monthly":
        date_trunc = func.date_trunc('month', GeneralLedger.transaction_date)
    else:
        date_trunc = func.date(GeneralLedger.transaction_date)
    
    results = db.query(
        date_trunc.label('period'),
        GeneralLedger.account_name,
        func.sum(GeneralLedger.amount).label('period_change')
    ).filter(
        and_(
            GeneralLedger.account_id == account_id,
            GeneralLedger.transaction_date >= start_date,
            GeneralLedger.transaction_date <= end_date
        )
    ).group_by(date_trunc, GeneralLedger.account_name).order_by(date_trunc).all()
    
    # Calculate running balance
    running_balance = 0
    balance_data = []
    
    for r in results:
        running_balance += float(r.period_change or 0)
        balance_data.append({
            "period": r.period.strftime("%Y-%m-%d") if hasattr(r.period, 'strftime') else str(r.period),
            "account_name": r.account_name,
            "period_change": float(r.period_change or 0),
            "running_balance": running_balance
        })
    
    return balance_data

def _get_kpi_dashboard_data(db: Session, start_date: str, end_date: str) -> Dict[str, float]:
    """Get KPI dashboard data"""
    excel_gen = ExcelTemplateGenerator()
    
    # Current period metrics
    current_revenue = float(excel_gen._get_revenue(db, start_date, end_date))
    current_expenses = float(excel_gen._get_expenses(db, start_date, end_date))
    current_cash = float(excel_gen._get_cash_balance(db, end_date))
    
    # Previous period for comparison
    period_days = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
    prev_start = (datetime.fromisoformat(start_date) - timedelta(days=period_days)).date().isoformat()
    prev_end = (datetime.fromisoformat(end_date) - timedelta(days=period_days)).date().isoformat()
    
    previous_revenue = float(excel_gen._get_revenue(db, prev_start, prev_end))
    previous_expenses = float(excel_gen._get_expenses(db, prev_start, prev_end))
    previous_cash = float(excel_gen._get_cash_balance(db, prev_end))
    
    # Calculate KPIs
    profit_margin = ((current_revenue - current_expenses) / current_revenue * 100) if current_revenue > 0 else 0
    expense_ratio = (current_expenses / current_revenue * 100) if current_revenue > 0 else 0
    previous_expense_ratio = (previous_expenses / previous_revenue * 100) if previous_revenue > 0 else 0
    
    return {
        "current_revenue": current_revenue,
        "revenue_target": current_revenue * 1.2,  # 20% target increase
        "profit_margin": profit_margin,
        "current_cash": current_cash,
        "previous_cash": previous_cash,
        "expense_ratio": expense_ratio,
        "previous_expense_ratio": previous_expense_ratio
    }

@router.get("/status")
async def get_charts_status():
    """
    Get charts system status
    """
    # Check database connectivity
    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
            db_connected = True
    except Exception:
        db_connected = False
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "database_connected": db_connected,
        "available_charts": 6,
        "supported_formats": ["plotly_json"],
        "chart_types": ["line", "bar", "pie", "gauge", "indicator", "treemap"],
        "grouping_options": ["daily", "weekly", "monthly", "quarterly"],
        "features": [
            "Real-time data",
            "Interactive charts", 
            "Custom date ranges",
            "Multiple visualization types"
        ],
        "checked_at": datetime.now().isoformat()
    }