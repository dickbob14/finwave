"""
KPI Calculator for deriving financial metrics from synced data
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from models.financial_data import (
    FinancialStatement, AccountBalance, Transaction,
    Customer, Vendor, KPIMetric
)
from models.workspace import Workspace

logger = logging.getLogger(__name__)


class KPICalculator:
    """Calculate and store KPI metrics from financial data"""
    
    def __init__(self, company_id: str):
        self.company_id = company_id
        
    def calculate_all_kpis(self, db: Session, period_end: Optional[datetime] = None) -> Dict[str, float]:
        """Calculate all KPIs for the company"""
        if not period_end:
            period_end = datetime.utcnow()
            
        period_start = datetime(period_end.year, period_end.month, 1)
        
        logger.info(f"Calculating KPIs for company {self.company_id} for period {period_start} to {period_end}")
        
        kpis = {}
        
        # Revenue metrics
        kpis.update(self._calculate_revenue_metrics(db, period_start, period_end))
        
        # Cash metrics
        kpis.update(self._calculate_cash_metrics(db, period_start, period_end))
        
        # Customer metrics
        kpis.update(self._calculate_customer_metrics(db, period_start, period_end))
        
        # Profitability metrics
        kpis.update(self._calculate_profitability_metrics(db, period_start, period_end))
        
        # Liquidity metrics
        kpis.update(self._calculate_liquidity_metrics(db, period_end))
        
        # Efficiency metrics
        kpis.update(self._calculate_efficiency_metrics(db, period_start, period_end))
        
        # Store KPIs in database
        self._store_kpis(db, kpis, period_start, period_end)
        
        return kpis
        
    def _calculate_revenue_metrics(self, db: Session, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Calculate revenue-related KPIs"""
        metrics = {}
        
        # Current period revenue
        current_revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).scalar() or 0
        
        metrics["revenue"] = float(current_revenue)
        
        # Previous period revenue for growth calculation
        prev_period_start = period_start - timedelta(days=30)
        prev_period_end = period_start - timedelta(days=1)
        
        prev_revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
            Transaction.transaction_date >= prev_period_start,
            Transaction.transaction_date <= prev_period_end
        ).scalar() or 0
        
        # Revenue growth rate
        if prev_revenue > 0:
            metrics["revenue_growth_rate"] = ((current_revenue - prev_revenue) / prev_revenue) * 100
        else:
            metrics["revenue_growth_rate"] = 0
            
        # Monthly Recurring Revenue (MRR) - simplified calculation
        # Count unique customers with transactions this month
        active_customers = db.query(func.count(func.distinct(Transaction.customer_id))).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end,
            Transaction.customer_id.isnot(None)
        ).scalar() or 0
        
        if active_customers > 0:
            metrics["mrr"] = current_revenue  # Simplified - assumes all revenue is recurring
            metrics["arr"] = metrics["mrr"] * 12
        else:
            metrics["mrr"] = 0
            metrics["arr"] = 0
            
        return metrics
        
    def _calculate_cash_metrics(self, db: Session, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Calculate cash-related KPIs"""
        metrics = {}
        
        # Get cash balance from accounts
        cash_accounts = db.query(func.sum(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_type == "Asset",
            AccountBalance.account_subtype.in_(["Cash", "Checking", "Savings", "MoneyMarket"])
        ).scalar() or 0
        
        metrics["cash_balance"] = float(cash_accounts)
        
        # Calculate burn rate (monthly expenses)
        monthly_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Bill", "VendorCredit", "Purchase"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).scalar() or 0
        
        metrics["burn_rate"] = float(monthly_expenses)
        
        # Cash runway (months of cash left)
        if metrics["burn_rate"] > 0:
            metrics["cash_runway"] = metrics["cash_balance"] / metrics["burn_rate"]
        else:
            metrics["cash_runway"] = float('inf')  # Infinite runway if no burn
            
        # Net cash flow
        cash_inflows = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Payment", "SalesReceipt", "Deposit"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).scalar() or 0
        
        cash_outflows = monthly_expenses
        metrics["net_cash_flow"] = float(cash_inflows - cash_outflows)
        
        return metrics
        
    def _calculate_customer_metrics(self, db: Session, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Calculate customer-related KPIs"""
        metrics = {}
        
        # Total customers
        total_customers = db.query(func.count(Customer.id)).filter(
            Customer.company_id == self.company_id
        ).scalar() or 0
        
        # Active customers (with transactions in current period)
        active_customers = db.query(func.count(func.distinct(Transaction.customer_id))).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end,
            Transaction.customer_id.isnot(None)
        ).scalar() or 0
        
        metrics["total_customers"] = total_customers
        metrics["active_customers"] = active_customers
        
        # Customer churn rate
        churned_customers = db.query(func.count(Customer.id)).filter(
            Customer.company_id == self.company_id,
            Customer.status == "churned",
            Customer.churn_date >= period_start,
            Customer.churn_date <= period_end
        ).scalar() or 0
        
        if total_customers > 0:
            metrics["customer_churn_rate"] = (churned_customers / total_customers) * 100
        else:
            metrics["customer_churn_rate"] = 0
            
        # Average revenue per customer (ARPC)
        if active_customers > 0:
            total_revenue = metrics.get("revenue", 0)
            metrics["arpc"] = total_revenue / active_customers
        else:
            metrics["arpc"] = 0
            
        # Customer Acquisition Cost (CAC) - simplified
        # Look for marketing/sales expenses
        sales_marketing_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Bill", "VendorCredit"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end,
            Transaction.description.ilike("%marketing%") | Transaction.description.ilike("%sales%")
        ).scalar() or 0
        
        # New customers this period
        new_customers = db.query(func.count(Customer.id)).filter(
            Customer.company_id == self.company_id,
            Customer.created_at >= period_start,
            Customer.created_at <= period_end
        ).scalar() or 0
        
        if new_customers > 0:
            metrics["cac"] = float(sales_marketing_expenses) / new_customers
        else:
            metrics["cac"] = 0
            
        # Lifetime Value (LTV) - simplified
        # Average customer lifespan in months
        if metrics["customer_churn_rate"] > 0:
            avg_lifespan_months = 100 / metrics["customer_churn_rate"]
            metrics["ltv"] = metrics["arpc"] * avg_lifespan_months
        else:
            metrics["ltv"] = metrics["arpc"] * 24  # Assume 2 year lifespan if no churn
            
        # LTV:CAC ratio
        if metrics["cac"] > 0:
            metrics["ltv_cac_ratio"] = metrics["ltv"] / metrics["cac"]
        else:
            metrics["ltv_cac_ratio"] = float('inf')
            
        return metrics
        
    def _calculate_profitability_metrics(self, db: Session, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Calculate profitability KPIs"""
        metrics = {}
        
        # Get revenue
        revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).scalar() or 0
        
        # Get COGS (Cost of Goods Sold)
        cogs = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Bill", "VendorCredit"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end,
            Transaction.description.ilike("%cost of goods%") | Transaction.description.ilike("%inventory%")
        ).scalar() or 0
        
        # Gross profit and margin
        gross_profit = float(revenue - cogs)
        metrics["gross_profit"] = gross_profit
        
        if revenue > 0:
            metrics["gross_margin"] = (gross_profit / revenue) * 100
        else:
            metrics["gross_margin"] = 0
            
        # Operating expenses
        opex = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Bill", "VendorCredit"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end,
            ~(Transaction.description.ilike("%cost of goods%") | Transaction.description.ilike("%inventory%"))
        ).scalar() or 0
        
        # EBITDA (simplified - excluding interest, tax, depreciation, amortization)
        ebitda = gross_profit - float(opex)
        metrics["ebitda"] = ebitda
        
        if revenue > 0:
            metrics["ebitda_margin"] = (ebitda / revenue) * 100
        else:
            metrics["ebitda_margin"] = 0
            
        # Net profit (simplified)
        metrics["net_profit"] = ebitda  # Simplified - not including tax, interest
        
        if revenue > 0:
            metrics["net_profit_margin"] = (metrics["net_profit"] / revenue) * 100
        else:
            metrics["net_profit_margin"] = 0
            
        return metrics
        
    def _calculate_liquidity_metrics(self, db: Session, as_of_date: datetime) -> Dict[str, float]:
        """Calculate liquidity KPIs"""
        metrics = {}
        
        # Current assets
        current_assets = db.query(func.sum(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_type == "Asset",
            AccountBalance.account_subtype.in_(["Cash", "Checking", "Savings", "AccountsReceivable", "Inventory"])
        ).scalar() or 0
        
        # Current liabilities
        current_liabilities = db.query(func.sum(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_type == "Liability",
            AccountBalance.account_subtype.in_(["AccountsPayable", "CreditCard", "ShortTermDebt"])
        ).scalar() or 0
        
        # Working capital
        metrics["working_capital"] = float(current_assets - current_liabilities)
        
        # Current ratio
        if current_liabilities > 0:
            metrics["current_ratio"] = float(current_assets) / float(current_liabilities)
        else:
            metrics["current_ratio"] = float('inf')
            
        # Quick ratio (excluding inventory)
        quick_assets = db.query(func.sum(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_type == "Asset",
            AccountBalance.account_subtype.in_(["Cash", "Checking", "Savings", "AccountsReceivable"])
        ).scalar() or 0
        
        if current_liabilities > 0:
            metrics["quick_ratio"] = float(quick_assets) / float(current_liabilities)
        else:
            metrics["quick_ratio"] = float('inf')
            
        # Debt-to-equity ratio
        total_debt = db.query(func.sum(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_type == "Liability"
        ).scalar() or 0
        
        total_equity = db.query(func.sum(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_type == "Equity"
        ).scalar() or 0
        
        if total_equity > 0:
            metrics["debt_to_equity_ratio"] = float(total_debt) / float(total_equity)
        else:
            metrics["debt_to_equity_ratio"] = float('inf')
            
        return metrics
        
    def _calculate_efficiency_metrics(self, db: Session, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """Calculate efficiency KPIs"""
        metrics = {}
        
        # Accounts Receivable Turnover
        revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Invoice", "SalesReceipt"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).scalar() or 0
        
        avg_ar = db.query(func.avg(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_subtype == "AccountsReceivable"
        ).scalar() or 0
        
        if avg_ar > 0:
            metrics["ar_turnover"] = float(revenue) / float(avg_ar)
            metrics["days_sales_outstanding"] = 30 / metrics["ar_turnover"]  # Monthly DSO
        else:
            metrics["ar_turnover"] = 0
            metrics["days_sales_outstanding"] = 0
            
        # Accounts Payable Turnover
        purchases = db.query(func.sum(Transaction.amount)).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_type.in_(["Bill", "VendorCredit"]),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).scalar() or 0
        
        avg_ap = db.query(func.avg(AccountBalance.balance)).filter(
            AccountBalance.company_id == self.company_id,
            AccountBalance.account_subtype == "AccountsPayable"
        ).scalar() or 0
        
        if avg_ap > 0:
            metrics["ap_turnover"] = float(purchases) / float(avg_ap)
            metrics["days_payable_outstanding"] = 30 / metrics["ap_turnover"]  # Monthly DPO
        else:
            metrics["ap_turnover"] = 0
            metrics["days_payable_outstanding"] = 0
            
        # Cash conversion cycle
        metrics["cash_conversion_cycle"] = (
            metrics["days_sales_outstanding"] - 
            metrics["days_payable_outstanding"]
        )
        
        return metrics
        
    def _store_kpis(self, db: Session, kpis: Dict[str, float], period_start: datetime, period_end: datetime):
        """Store calculated KPIs in the database"""
        for metric_name, metric_value in kpis.items():
            # Skip infinite values
            if metric_value == float('inf'):
                continue
                
            # Check if KPI already exists for this period
            existing = db.query(KPIMetric).filter(
                KPIMetric.company_id == self.company_id,
                KPIMetric.metric_name == metric_name,
                KPIMetric.period_start == period_start,
                KPIMetric.period_end == period_end
            ).first()
            
            if existing:
                # Update existing KPI
                existing.metric_value = metric_value
                existing.created_at = datetime.utcnow()
            else:
                # Create new KPI
                kpi = KPIMetric(
                    id=str(uuid.uuid4()),
                    company_id=self.company_id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    metric_unit=self._get_metric_unit(metric_name),
                    period_start=period_start,
                    period_end=period_end,
                    calculation_method="automated",
                    metadata={}
                )
                db.add(kpi)
                
        db.commit()
        logger.info(f"Stored {len(kpis)} KPIs for company {self.company_id}")
        
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get the unit for a metric"""
        if metric_name.endswith("_rate") or metric_name.endswith("_margin"):
            return "percentage"
        elif metric_name.endswith("_ratio"):
            return "ratio"
        elif metric_name in ["cash_runway", "days_sales_outstanding", "days_payable_outstanding", "cash_conversion_cycle"]:
            return "days"
        elif metric_name in ["total_customers", "active_customers"]:
            return "count"
        else:
            return "currency"
            
    def get_latest_kpis(self, db: Session) -> Dict[str, Any]:
        """Get the latest calculated KPIs for the company"""
        # Get the most recent period
        latest_period = db.query(
            func.max(KPIMetric.period_end)
        ).filter(
            KPIMetric.company_id == self.company_id
        ).scalar()
        
        if not latest_period:
            return {}
            
        # Get all KPIs for the latest period
        kpis = db.query(KPIMetric).filter(
            KPIMetric.company_id == self.company_id,
            KPIMetric.period_end == latest_period
        ).all()
        
        return {
            kpi.metric_name: {
                "value": kpi.metric_value,
                "unit": kpi.metric_unit,
                "period_start": kpi.period_start.isoformat(),
                "period_end": kpi.period_end.isoformat()
            }
            for kpi in kpis
        }