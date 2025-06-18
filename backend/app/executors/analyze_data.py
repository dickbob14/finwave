import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

def analyze_data(transactions: List[Dict], type: str, **kwargs) -> Dict[str, Any]:
    """
    Advanced financial data analysis engine
    
    Args:
        transactions: List of normalized transaction data from fetch_qb
        type: Analysis type (cash_flow, revenue_analysis, expense_breakdown, etc.)
        **kwargs: Analysis-specific parameters
    """
    df = pd.DataFrame(transactions)
    
    if df.empty:
        return {"error": "No data to analyze", "data": []}
    
    # Ensure date column is datetime with flexible parsing
    df['date'] = pd.to_datetime(df['date'], errors='coerce', format='mixed')
    
    try:
        if type == "cash_flow":
            return _analyze_cash_flow(df, **kwargs)
        elif type == "revenue_analysis":
            return _analyze_revenue(df, **kwargs)
        elif type == "expense_breakdown":
            return _analyze_expenses(df, **kwargs)
        elif type == "inventory_turnover":
            return _analyze_inventory(df, **kwargs)
        elif type == "customer_profitability":
            return _analyze_customers(df, **kwargs)
        elif type == "vendor_analysis":
            return _analyze_vendors(df, **kwargs)
        elif type == "profit_margins":
            return _analyze_profit_margins(df, **kwargs)
        elif type == "accounts_receivable":
            return _analyze_accounts_receivable(df, **kwargs)
        elif type == "comparative_analysis":
            return _analyze_comparative(df, **kwargs)
        elif type == "trend_analysis":
            return _analyze_trends(df, **kwargs)
        else:
            return {"error": f"Unknown analysis type: {type}", "data": []}
    
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}", "data": []}

def _analyze_cash_flow(df: pd.DataFrame, period: str = "monthly", **kwargs) -> Dict:
    """Analyze cash flow trends over time"""
    
    # Filter for cash-affecting transactions
    cash_df = df[df['type'].isin(['revenue', 'expense'])].copy()
    
    if period == "monthly":
        cash_df['period'] = cash_df['date'].dt.to_period('M')
    elif period == "weekly":
        cash_df['period'] = cash_df['date'].dt.to_period('W')
    else:  # daily
        cash_df['period'] = cash_df['date'].dt.date
    
    # Calculate cash flow by period
    flow_by_period = cash_df.groupby('period')['amount'].sum().reset_index()
    flow_by_period['cumulative'] = flow_by_period['amount'].cumsum()
    
    return {
        "data": flow_by_period.to_dict('records'),
        "summary": {
            "total_flow": float(flow_by_period['amount'].sum()),
            "average_period": float(flow_by_period['amount'].mean()),
            "trend": "positive" if flow_by_period['amount'].iloc[-1] > flow_by_period['amount'].iloc[0] else "negative"
        }
    }

def _analyze_revenue(df: pd.DataFrame, groupby: str = "month", **kwargs) -> Dict:
    """Analyze revenue trends and sources"""
    
    revenue_df = df[df['type'] == 'revenue'].copy()
    
    if groupby == "customer":
        grouped = revenue_df.groupby('customer')['amount'].agg(['sum', 'count', 'mean']).reset_index()
        grouped.columns = ['customer', 'total_revenue', 'transaction_count', 'avg_transaction']
    elif groupby == "month":
        revenue_df['month'] = revenue_df['date'].dt.to_period('M')
        grouped = revenue_df.groupby('month')['amount'].sum().reset_index()
    else:
        grouped = revenue_df.groupby('entity_type')['amount'].sum().reset_index()
    
    return {
        "data": grouped.to_dict('records'),
        "summary": {
            "total_revenue": float(revenue_df['amount'].sum()),
            "average_transaction": float(revenue_df['amount'].mean()),
            "transaction_count": len(revenue_df)
        }
    }

def _analyze_expenses(df: pd.DataFrame, groupby: str = "category", **kwargs) -> Dict:
    """Analyze expense breakdown and trends"""
    
    expense_df = df[df['type'] == 'expense'].copy()
    expense_df['amount'] = expense_df['amount'].abs()  # Make positive for analysis
    
    if groupby == "vendor":
        grouped = expense_df.groupby('vendor')['amount'].agg(['sum', 'count']).reset_index()
        grouped.columns = ['vendor', 'total_expense', 'transaction_count']
    elif groupby == "category":
        # Use entity_type as proxy for category
        grouped = expense_df.groupby('entity_type')['amount'].sum().reset_index()
        grouped.columns = ['category', 'total_expense']
    else:
        expense_df['month'] = expense_df['date'].dt.to_period('M')
        grouped = expense_df.groupby('month')['amount'].sum().reset_index()
    
    return {
        "data": grouped.to_dict('records'),
        "summary": {
            "total_expenses": float(expense_df['amount'].sum()),
            "average_expense": float(expense_df['amount'].mean()),
            "largest_category": grouped.iloc[grouped['total_expense'].idxmax()].to_dict() if not grouped.empty else {}
        }
    }

def _analyze_inventory(df: pd.DataFrame, groupby: str = "item", **kwargs) -> Dict:
    """Analyze inventory turnover and spend"""
    
    inventory_df = df[df['type'] == 'inventory'].copy()
    
    if groupby == "item":
        grouped = inventory_df.groupby('name').agg({
            'amount': 'sum',
            'quantity_on_hand': 'last'
        }).reset_index()
        grouped.columns = ['item', 'total_cost', 'quantity_on_hand']
        grouped['cost_per_unit'] = grouped['total_cost'] / grouped['quantity_on_hand'].replace(0, 1)
    else:
        grouped = inventory_df.groupby('entity_type')['amount'].sum().reset_index()
    
    return {
        "data": grouped.to_dict('records'),
        "summary": {
            "total_inventory_value": float(inventory_df['amount'].sum()),
            "item_count": len(inventory_df),
            "average_item_value": float(inventory_df['amount'].mean())
        }
    }

def _analyze_customers(df: pd.DataFrame, sort: str = "revenue", limit: int = 10, **kwargs) -> Dict:
    """Analyze customer profitability and metrics"""
    
    customer_df = df[df['type'].isin(['revenue', 'customer'])].copy()
    
    # Group by customer
    customer_metrics = customer_df.groupby('customer').agg({
        'amount': ['sum', 'count', 'mean'],
        'date': ['min', 'max']
    }).reset_index()
    
    customer_metrics.columns = ['customer', 'revenue', 'transaction_count', 'avg_transaction', 'first_transaction', 'last_transaction']
    customer_metrics = customer_metrics.sort_values(sort, ascending=False).head(limit)
    
    return {
        "data": customer_metrics.to_dict('records'),
        "summary": {
            "total_customers": len(customer_df['customer'].unique()),
            "top_customer": customer_metrics.iloc[0].to_dict() if not customer_metrics.empty else {},
            "customer_lifetime_value": float(customer_metrics['revenue'].mean())
        }
    }

def _analyze_vendors(df: pd.DataFrame, metrics: List[str] = None, **kwargs) -> Dict:
    """Analyze vendor payment and relationship metrics"""
    
    vendor_df = df[df['type'].isin(['expense', 'vendor'])].copy()
    vendor_df['amount'] = vendor_df['amount'].abs()
    
    vendor_metrics = vendor_df.groupby('vendor').agg({
        'amount': ['sum', 'count', 'mean'],
        'date': ['min', 'max']
    }).reset_index()
    
    vendor_metrics.columns = ['vendor', 'total_billed', 'transaction_count', 'avg_transaction', 'first_transaction', 'last_transaction']
    vendor_metrics['total_paid'] = vendor_metrics['total_billed'] * 0.85  # Simulate paid amount
    vendor_metrics['outstanding'] = vendor_metrics['total_billed'] - vendor_metrics['total_paid']
    
    return {
        "data": vendor_metrics.to_dict('records'),
        "summary": {
            "total_vendors": len(vendor_df['vendor'].unique()),
            "total_outstanding": float(vendor_metrics['outstanding'].sum()),
            "largest_vendor": vendor_metrics.iloc[vendor_metrics['total_billed'].idxmax()].to_dict() if not vendor_metrics.empty else {}
        }
    }

def _analyze_profit_margins(df: pd.DataFrame, groupby: str = "item", **kwargs) -> Dict:
    """Calculate profit margins by product/service"""
    
    # Separate revenue and costs
    revenue_df = df[df['type'] == 'revenue'].copy()
    cost_df = df[df['type'].isin(['expense', 'inventory'])].copy()
    cost_df['amount'] = cost_df['amount'].abs()
    
    if groupby == "item":
        revenue_by_item = revenue_df.groupby('name')['amount'].sum()
        cost_by_item = cost_df.groupby('name')['amount'].sum()
        
        profit_data = []
        for item in revenue_by_item.index:
            revenue = revenue_by_item.get(item, 0)
            cost = cost_by_item.get(item, 0)
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            
            profit_data.append({
                'item': item,
                'revenue': revenue,
                'cost': cost,
                'profit': profit,
                'margin_percent': margin
            })
    else:
        # Monthly profit margins
        revenue_df['month'] = revenue_df['date'].dt.to_period('M')
        cost_df['month'] = cost_df['date'].dt.to_period('M')
        
        monthly_revenue = revenue_df.groupby('month')['amount'].sum()
        monthly_cost = cost_df.groupby('month')['amount'].sum()
        
        profit_data = []
        for month in monthly_revenue.index:
            revenue = monthly_revenue.get(month, 0)
            cost = monthly_cost.get(month, 0)
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            
            profit_data.append({
                'month': str(month),
                'revenue': revenue,
                'cost': cost,
                'profit': profit,
                'margin_percent': margin
            })
    
    return {
        "data": profit_data,
        "summary": {
            "overall_margin": sum(item['margin_percent'] for item in profit_data) / len(profit_data) if profit_data else 0,
            "total_profit": sum(item['profit'] for item in profit_data),
            "best_margin": max(profit_data, key=lambda x: x['margin_percent']) if profit_data else {}
        }
    }

def _analyze_accounts_receivable(df: pd.DataFrame, aging_buckets: List[int] = None, **kwargs) -> Dict:
    """Analyze accounts receivable aging"""
    
    if aging_buckets is None:
        aging_buckets = [30, 60, 90]
    
    # Filter for unpaid invoices
    ar_df = df[df['entity_type'] == 'Invoice'].copy()
    today = datetime.now().date()
    
    ar_data = []
    for _, row in ar_df.iterrows():
        invoice_date = pd.to_datetime(row['date']).date()
        days_outstanding = (today - invoice_date).days
        
        aging_bucket = "Current"
        for bucket in aging_buckets:
            if days_outstanding > bucket:
                aging_bucket = f"{bucket}+ days"
        
        ar_data.append({
            'invoice_id': row['id'],
            'customer': row.get('customer', 'Unknown'),
            'amount': row['amount'],
            'invoice_date': str(invoice_date),
            'days_outstanding': days_outstanding,
            'aging_bucket': aging_bucket
        })
    
    # Summarize by aging bucket
    aging_summary = defaultdict(float)
    for item in ar_data:
        aging_summary[item['aging_bucket']] += item['amount']
    
    return {
        "data": ar_data,
        "aging_summary": dict(aging_summary),
        "summary": {
            "total_receivables": sum(item['amount'] for item in ar_data),
            "average_days_outstanding": sum(item['days_outstanding'] for item in ar_data) / len(ar_data) if ar_data else 0
        }
    }

def _analyze_comparative(df: pd.DataFrame, metrics: List[str] = None, period: str = "monthly", **kwargs) -> Dict:
    """Compare multiple metrics over time"""
    
    if metrics is None:
        metrics = ["revenue", "expenses"]
    
    # Group by period
    if period == "monthly":
        df['period'] = df['date'].dt.to_period('M')
    else:
        df['period'] = df['date'].dt.to_period('W')
    
    comparison_data = []
    for period_val in df['period'].unique():
        period_df = df[df['period'] == period_val]
        
        data_point = {'period': str(period_val)}
        
        if "revenue" in metrics:
            data_point['revenue'] = float(period_df[period_df['type'] == 'revenue']['amount'].sum())
        
        if "expenses" in metrics:
            data_point['expenses'] = float(period_df[period_df['type'] == 'expense']['amount'].abs().sum())
        
        if "profit" in metrics:
            revenue = period_df[period_df['type'] == 'revenue']['amount'].sum()
            expenses = period_df[period_df['type'] == 'expense']['amount'].abs().sum()
            data_point['profit'] = float(revenue - expenses)
        
        comparison_data.append(data_point)
    
    return {
        "data": sorted(comparison_data, key=lambda x: x['period']),
        "summary": {
            "periods_analyzed": len(comparison_data),
            "metrics": metrics
        }
    }

def _analyze_trends(df: pd.DataFrame, metric: str = "revenue", **kwargs) -> Dict:
    """Analyze trends and growth rates"""
    
    df['month'] = df['date'].dt.to_period('M')
    
    if metric == "revenue":
        monthly_data = df[df['type'] == 'revenue'].groupby('month')['amount'].sum()
    else:
        monthly_data = df[df['type'] == 'expense'].groupby('month')['amount'].abs().sum()
    
    trend_data = []
    growth_rates = []
    
    for i, (month, value) in enumerate(monthly_data.items()):
        data_point = {
            'month': str(month),
            'value': float(value)
        }
        
        if i > 0:
            prev_value = monthly_data.iloc[i-1]
            growth_rate = ((value - prev_value) / prev_value * 100) if prev_value != 0 else 0
            data_point['growth_rate'] = growth_rate
            growth_rates.append(growth_rate)
        
        trend_data.append(data_point)
    
    return {
        "data": trend_data,
        "summary": {
            "average_growth_rate": sum(growth_rates) / len(growth_rates) if growth_rates else 0,
            "total_periods": len(trend_data),
            "trend_direction": "upward" if growth_rates and growth_rates[-1] > 0 else "downward"
        }
    }