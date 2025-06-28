"""
Dashboard API endpoints for real-time financial data
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from core.database import get_db
from auth import get_current_user
from models.financial_data import (
    FinancialStatement, AccountBalance, Transaction,
    Customer, Vendor, KPIMetric, SyncLog
)
from models.workspace import Workspace
from models.integration import IntegrationCredential
from metrics.kpi_calculator import KPICalculator
from integrations.quickbooks_sync import QuickBooksSyncService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{company_id}/dashboard/summary")
async def get_dashboard_summary(
    company_id: str,
    period: Optional[str] = Query("month", description="Period: day, week, month, quarter, year"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive dashboard summary with KPIs"""
    
    # Verify company access
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Calculate period dates
    end_date = datetime.utcnow()
    if period == "day":
        start_date = end_date - timedelta(days=1)
    elif period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    elif period == "year":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
        
    # Get latest KPIs
    kpi_calc = KPICalculator(company_id)
    latest_kpis = kpi_calc.get_latest_kpis(db)
    
    # Get account balances summary
    account_summary = _get_account_summary(db, company_id)
    
    # Get recent transactions
    recent_transactions = _get_recent_transactions(db, company_id, limit=10)
    
    # Get financial statements summary
    statements_summary = _get_statements_summary(db, company_id, start_date, end_date)
    
    # Get sync status
    sync_status = _get_sync_status(db, company_id)
    
    # Format response
    return {
        "company": {
            "id": company.id,
            "name": company.name
        },
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "type": period
        },
        "kpis": latest_kpis,
        "accounts": account_summary,
        "statements": statements_summary,
        "recent_transactions": recent_transactions,
        "sync_status": sync_status
    }


@router.get("/{company_id}/dashboard/kpis")
async def get_kpis(
    company_id: str,
    metrics: Optional[List[str]] = Query(None, description="Specific metrics to retrieve"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get specific KPI metrics"""
    
    # Verify company access
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Get KPIs
    kpi_calc = KPICalculator(company_id)
    all_kpis = kpi_calc.get_latest_kpis(db)
    
    # Filter specific metrics if requested
    if metrics:
        filtered_kpis = {k: v for k, v in all_kpis.items() if k in metrics}
        return {"kpis": filtered_kpis}
        
    return {"kpis": all_kpis}


@router.get("/{company_id}/dashboard/cash-flow")
async def get_cash_flow(
    company_id: str,
    period: Optional[str] = Query("month", description="Period: day, week, month, quarter, year"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed cash flow analysis"""
    
    # Verify company access
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Calculate period dates
    end_date = datetime.utcnow()
    if period == "day":
        start_date = end_date - timedelta(days=1)
        intervals = 24  # hourly
    elif period == "week":
        start_date = end_date - timedelta(weeks=1)
        intervals = 7  # daily
    elif period == "month":
        start_date = end_date - timedelta(days=30)
        intervals = 30  # daily
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
        intervals = 12  # weekly
    elif period == "year":
        start_date = end_date - timedelta(days=365)
        intervals = 12  # monthly
    else:
        start_date = end_date - timedelta(days=30)
        intervals = 30
        
    # Get cash flow data
    cash_flow_data = _calculate_cash_flow_series(db, company_id, start_date, end_date, intervals)
    
    # Get current cash position
    cash_balance = db.query(func.sum(AccountBalance.balance)).filter(
        AccountBalance.company_id == company_id,
        AccountBalance.account_type == "Asset",
        AccountBalance.account_subtype.in_(["Cash", "Checking", "Savings"])
    ).scalar() or 0
    
    return {
        "current_balance": float(cash_balance),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "type": period
        },
        "series": cash_flow_data
    }


@router.get("/{company_id}/dashboard/revenue-analysis")
async def get_revenue_analysis(
    company_id: str,
    group_by: Optional[str] = Query("customer", description="Group by: customer, product, category"),
    period: Optional[str] = Query("month", description="Period: day, week, month, quarter, year"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed revenue analysis"""
    
    # Verify company access
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Calculate period dates
    end_date = datetime.utcnow()
    if period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    elif period == "year":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
        
    # Get revenue breakdown
    if group_by == "customer":
        revenue_data = _get_revenue_by_customer(db, company_id, start_date, end_date)
    else:
        # Default to customer grouping
        revenue_data = _get_revenue_by_customer(db, company_id, start_date, end_date)
        
    # Get revenue trends
    revenue_trends = _get_revenue_trends(db, company_id, start_date, end_date)
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "type": period
        },
        "breakdown": revenue_data,
        "trends": revenue_trends
    }


@router.get("/{company_id}/dashboard/expense-analysis")
async def get_expense_analysis(
    company_id: str,
    group_by: Optional[str] = Query("vendor", description="Group by: vendor, category, account"),
    period: Optional[str] = Query("month", description="Period: day, week, month, quarter, year"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed expense analysis"""
    
    # Verify company access
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Calculate period dates
    end_date = datetime.utcnow()
    if period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    elif period == "year":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
        
    # Get expense breakdown
    if group_by == "vendor":
        expense_data = _get_expenses_by_vendor(db, company_id, start_date, end_date)
    else:
        # Default to vendor grouping
        expense_data = _get_expenses_by_vendor(db, company_id, start_date, end_date)
        
    # Get expense trends
    expense_trends = _get_expense_trends(db, company_id, start_date, end_date)
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "type": period
        },
        "breakdown": expense_data,
        "trends": expense_trends
    }


@router.post("/{company_id}/dashboard/sync")
async def trigger_sync(
    company_id: str,
    full_sync: bool = Query(False, description="Perform full sync instead of incremental"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Trigger a sync with QuickBooks"""
    
    # Verify company access
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Get QuickBooks integration
    integration = db.query(Integration).filter_by(
        company_id=company_id,
        provider="quickbooks",
        status="active"
    ).first()
    
    if not integration:
        raise HTTPException(status_code=400, detail="No active QuickBooks integration found")
        
    try:
        # Initialize sync service
        sync_service = QuickBooksSyncService(company_id, integration)
        
        # Perform sync
        results = sync_service.sync_all(db, full_sync=full_sync)
        
        # Recalculate KPIs after sync
        kpi_calc = KPICalculator(company_id)
        kpi_calc.calculate_all_kpis(db)
        
        return {
            "status": "success",
            "sync_type": "full" if full_sync else "incremental",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sync failed for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# Helper functions

def _get_account_summary(db: Session, company_id: str) -> Dict[str, Any]:
    """Get summary of account balances by type"""
    
    # Get latest balances grouped by account type
    balances = db.query(
        AccountBalance.account_type,
        func.sum(AccountBalance.balance).label("total")
    ).filter(
        AccountBalance.company_id == company_id
    ).group_by(
        AccountBalance.account_type
    ).all()
    
    summary = {
        "assets": 0,
        "liabilities": 0,
        "equity": 0,
        "revenue": 0,
        "expenses": 0
    }
    
    for balance in balances:
        if balance.account_type == "Asset":
            summary["assets"] = float(balance.total)
        elif balance.account_type == "Liability":
            summary["liabilities"] = float(balance.total)
        elif balance.account_type == "Equity":
            summary["equity"] = float(balance.total)
        elif balance.account_type == "Revenue":
            summary["revenue"] = float(balance.total)
        elif balance.account_type == "Expense":
            summary["expenses"] = float(balance.total)
            
    return summary


def _get_recent_transactions(db: Session, company_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent transactions"""
    
    transactions = db.query(Transaction).filter(
        Transaction.company_id == company_id
    ).order_by(
        Transaction.transaction_date.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": t.id,
            "date": t.transaction_date.isoformat(),
            "type": t.transaction_type,
            "amount": t.amount,
            "currency": t.currency,
            "description": t.description,
            "customer_id": t.customer_id,
            "vendor_id": t.vendor_id
        }
        for t in transactions
    ]


def _get_statements_summary(db: Session, company_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get summary from financial statements"""
    
    # Get latest P&L
    pl_statement = db.query(FinancialStatement).filter(
        FinancialStatement.company_id == company_id,
        FinancialStatement.statement_type == "P&L",
        FinancialStatement.period_end <= end_date
    ).order_by(
        FinancialStatement.period_end.desc()
    ).first()
    
    # Get latest Balance Sheet
    bs_statement = db.query(FinancialStatement).filter(
        FinancialStatement.company_id == company_id,
        FinancialStatement.statement_type == "Balance Sheet",
        FinancialStatement.period_end <= end_date
    ).order_by(
        FinancialStatement.period_end.desc()
    ).first()
    
    summary = {}
    
    if pl_statement and pl_statement.data:
        summary["profit_loss"] = {
            "revenue": pl_statement.data.get("revenue", 0),
            "expenses": pl_statement.data.get("expenses", 0),
            "net_income": pl_statement.data.get("net_income", 0),
            "period": {
                "start": pl_statement.period_start.isoformat(),
                "end": pl_statement.period_end.isoformat()
            }
        }
        
    if bs_statement and bs_statement.data:
        summary["balance_sheet"] = {
            "assets": bs_statement.data.get("assets", 0),
            "liabilities": bs_statement.data.get("liabilities", 0),
            "equity": bs_statement.data.get("equity", 0),
            "as_of": bs_statement.period_end.isoformat()
        }
        
    return summary


def _get_sync_status(db: Session, company_id: str) -> Dict[str, Any]:
    """Get latest sync status"""
    
    latest_sync = db.query(SyncLog).filter(
        SyncLog.company_id == company_id
    ).order_by(
        SyncLog.created_at.desc()
    ).first()
    
    if latest_sync:
        return {
            "last_sync": latest_sync.created_at.isoformat(),
            "status": latest_sync.sync_status,
            "type": latest_sync.sync_type,
            "records_synced": latest_sync.records_synced,
            "duration": (
                (latest_sync.completed_at - latest_sync.started_at).total_seconds()
                if latest_sync.completed_at else None
            )
        }
    else:
        return {
            "last_sync": None,
            "status": "never_synced"
        }


def _calculate_cash_flow_series(
    db: Session, 
    company_id: str, 
    start_date: datetime, 
    end_date: datetime,
    intervals: int
) -> List[Dict[str, Any]]:
    """Calculate cash flow time series"""
    
    # Get all cash transactions in period
    transactions = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).order_by(Transaction.transaction_date).all()
    
    # Calculate interval size
    interval_seconds = (end_date - start_date).total_seconds() / intervals
    
    # Initialize series
    series = []
    current_date = start_date
    
    for i in range(intervals):
        next_date = current_date + timedelta(seconds=interval_seconds)
        
        # Calculate inflows and outflows for this interval
        inflows = sum(
            t.amount for t in transactions
            if current_date <= t.transaction_date < next_date
            and t.transaction_type in ["Payment", "SalesReceipt", "Deposit"]
        )
        
        outflows = sum(
            t.amount for t in transactions
            if current_date <= t.transaction_date < next_date
            and t.transaction_type in ["Bill", "VendorCredit", "Purchase"]
        )
        
        series.append({
            "date": current_date.isoformat(),
            "inflows": float(inflows),
            "outflows": float(outflows),
            "net": float(inflows - outflows)
        })
        
        current_date = next_date
        
    return series


def _get_revenue_by_customer(
    db: Session,
    company_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Get revenue breakdown by customer"""
    
    # Query revenue by customer
    revenue_data = db.query(
        Transaction.customer_id,
        func.sum(Transaction.amount).label("total_revenue"),
        func.count(Transaction.id).label("transaction_count")
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.customer_id.isnot(None)
    ).group_by(
        Transaction.customer_id
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).limit(20).all()
    
    # Get customer details
    results = []
    for row in revenue_data:
        customer = db.query(Customer).filter_by(
            company_id=company_id,
            quickbooks_id=row.customer_id
        ).first()
        
        results.append({
            "customer_id": row.customer_id,
            "customer_name": customer.name if customer else "Unknown",
            "revenue": float(row.total_revenue),
            "transaction_count": row.transaction_count
        })
        
    return results


def _get_revenue_trends(
    db: Session,
    company_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Get revenue trends over time"""
    
    # Calculate daily revenue
    daily_revenue = db.query(
        func.date(Transaction.transaction_date).label("date"),
        func.sum(Transaction.amount).label("revenue")
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by(
        func.date(Transaction.transaction_date)
    ).order_by(
        func.date(Transaction.transaction_date)
    ).all()
    
    return [
        {
            "date": row.date.isoformat(),
            "revenue": float(row.revenue)
        }
        for row in daily_revenue
    ]


def _get_expenses_by_vendor(
    db: Session,
    company_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Get expense breakdown by vendor"""
    
    # Query expenses by vendor
    expense_data = db.query(
        Transaction.vendor_id,
        func.sum(Transaction.amount).label("total_expenses"),
        func.count(Transaction.id).label("transaction_count")
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type.in_(["Bill", "VendorCredit", "Purchase"]),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.vendor_id.isnot(None)
    ).group_by(
        Transaction.vendor_id
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).limit(20).all()
    
    # Get vendor details
    results = []
    for row in expense_data:
        vendor = db.query(Vendor).filter_by(
            company_id=company_id,
            quickbooks_id=row.vendor_id
        ).first()
        
        results.append({
            "vendor_id": row.vendor_id,
            "vendor_name": vendor.name if vendor else "Unknown",
            "expenses": float(row.total_expenses),
            "transaction_count": row.transaction_count
        })
        
    return results


def _get_expense_trends(
    db: Session,
    company_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Get expense trends over time"""
    
    # Calculate daily expenses
    daily_expenses = db.query(
        func.date(Transaction.transaction_date).label("date"),
        func.sum(Transaction.amount).label("expenses")
    ).filter(
        Transaction.company_id == company_id,
        Transaction.transaction_type.in_(["Bill", "VendorCredit", "Purchase"]),
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).group_by(
        func.date(Transaction.transaction_date)
    ).order_by(
        func.date(Transaction.transaction_date)
    ).all()
    
    return [
        {
            "date": row.date.isoformat(),
            "expenses": float(row.expenses)
        }
        for row in daily_expenses
    ]