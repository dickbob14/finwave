"""
PDF report generation pipeline using Jinja2 templates and WeasyPrint
Generates narrative financial reports with auto-commentary using LLM
"""
import io
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, BinaryIO
from decimal import Decimal
import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

try:
    import weasyprint
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    weasyprint = None
    HTML = None
    CSS = None
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database import get_db_session
from models.financial import GeneralLedger, Account, Customer, Vendor
from templates.excel_templates import ExcelTemplateGenerator

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """Generate narrative PDF reports with financial data and commentary"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize PDF generator
        
        Args:
            template_dir: Directory containing Jinja2 templates. Defaults to templates/pdf/
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "pdf"
            template_dir.mkdir(exist_ok=True)
        
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Add custom filters
        self.env.filters['currency'] = self._format_currency
        self.env.filters['percentage'] = self._format_percentage
        self.env.filters['date'] = self._format_date
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def _format_currency(self, value: Decimal) -> str:
        """Format decimal as currency"""
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"
    
    def _format_percentage(self, value: float) -> str:
        """Format float as percentage"""
        if value is None:
            return "0.00%"
        return f"{value:.2%}"
    
    def _format_date(self, value: datetime) -> str:
        """Format datetime as readable date"""
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime("%B %d, %Y")
    
    def generate_executive_summary(self, start_date: str, end_date: str, include_commentary: bool = True) -> BinaryIO:
        """
        Generate executive summary PDF report
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            include_commentary: Whether to include LLM-generated commentary
            
        Returns:
            BinaryIO object containing PDF
        """
        with get_db_session() as db:
            # Gather financial data
            financial_data = self._gather_financial_data(db, start_date, end_date)
            
            # Generate commentary if requested
            commentary = {}
            if include_commentary:
                commentary = self._generate_commentary(financial_data, start_date, end_date)
            
            # Prepare template context
            context = {
                'report_title': 'Executive Financial Summary',
                'period_start': start_date,
                'period_end': end_date,
                'generated_date': datetime.now(),
                'financial_data': financial_data,
                'commentary': commentary,
                'charts': self._prepare_chart_data(financial_data)
            }
            
            # Render template
            template = self.env.get_template('executive_summary.html')
            html_content = template.render(**context)
            
            # Generate PDF
            return self._html_to_pdf(html_content)
    
    def generate_detailed_report(self, start_date: str, end_date: str, include_variance: bool = True) -> BinaryIO:
        """
        Generate detailed financial report with variance analysis
        
        Args:
            start_date: YYYY-MM-DD format
            end_date: YYYY-MM-DD format
            include_variance: Whether to include variance analysis
            
        Returns:
            BinaryIO object containing PDF
        """
        with get_db_session() as db:
            # Gather comprehensive data
            financial_data = self._gather_financial_data(db, start_date, end_date)
            trial_balance = self._get_trial_balance_data(db, start_date, end_date)
            pl_data = self._get_pl_detailed_data(db, start_date, end_date)
            balance_sheet = self._get_balance_sheet_data(db, end_date)
            
            # Variance analysis if requested
            variance_data = {}
            if include_variance:
                variance_data = self._calculate_variance_analysis(db, start_date, end_date)
            
            context = {
                'report_title': 'Detailed Financial Report',
                'period_start': start_date,
                'period_end': end_date,
                'generated_date': datetime.now(),
                'financial_data': financial_data,
                'trial_balance': trial_balance,
                'profit_loss': pl_data,
                'balance_sheet': balance_sheet,
                'variance_analysis': variance_data,
                'charts': self._prepare_detailed_charts(financial_data, pl_data, balance_sheet)
            }
            
            template = self.env.get_template('detailed_report.html')
            html_content = template.render(**context)
            
            return self._html_to_pdf(html_content)
    
    def generate_custom_report(self, template_name: str, context_data: Dict) -> BinaryIO:
        """
        Generate custom report using specified template
        
        Args:
            template_name: Name of template file (e.g., 'custom_report.html')
            context_data: Dictionary of data to pass to template
            
        Returns:
            BinaryIO object containing PDF
        """
        template = self.env.get_template(template_name)
        html_content = template.render(**context_data)
        return self._html_to_pdf(html_content)
    
    def _gather_financial_data(self, db: Session, start_date: str, end_date: str) -> Dict:
        """Gather key financial metrics"""
        # Use Excel template generator for consistency
        excel_gen = ExcelTemplateGenerator()
        
        revenue = excel_gen._get_revenue(db, start_date, end_date)
        expenses = excel_gen._get_expenses(db, start_date, end_date)
        net_income = revenue - expenses
        
        # Additional metrics
        cash_balance = excel_gen._get_cash_balance(db, end_date)
        ar_balance = excel_gen._get_ar_balance(db, end_date)
        ap_balance = excel_gen._get_ap_balance(db, end_date)
        
        # Calculate ratios
        profit_margin = (net_income / revenue * 100) if revenue != 0 else 0
        
        # Previous period comparison
        prev_start = (datetime.fromisoformat(start_date) - timedelta(days=30)).date().isoformat()
        prev_end = (datetime.fromisoformat(end_date) - timedelta(days=30)).date().isoformat()
        
        prev_revenue = excel_gen._get_revenue(db, prev_start, prev_end)
        prev_expenses = excel_gen._get_expenses(db, prev_start, prev_end)
        prev_net_income = prev_revenue - prev_expenses
        
        # Growth calculations
        revenue_growth = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue != 0 else 0
        expense_growth = ((expenses - prev_expenses) / prev_expenses * 100) if prev_expenses != 0 else 0
        
        return {
            'current_period': {
                'revenue': revenue,
                'expenses': expenses,
                'net_income': net_income,
                'profit_margin': profit_margin,
                'cash_balance': cash_balance,
                'ar_balance': ar_balance,
                'ap_balance': ap_balance
            },
            'previous_period': {
                'revenue': prev_revenue,
                'expenses': prev_expenses,
                'net_income': prev_net_income
            },
            'growth_metrics': {
                'revenue_growth': revenue_growth,
                'expense_growth': expense_growth,
                'net_income_change': net_income - prev_net_income
            }
        }
    
    def _generate_commentary(self, financial_data: Dict, start_date: str, end_date: str) -> Dict:
        """
        Generate AI commentary on financial performance
        This is a simplified version - in production, you'd use an LLM API
        """
        current = financial_data['current_period']
        growth = financial_data['growth_metrics']
        
        # Performance assessment
        performance_summary = []
        
        if growth['revenue_growth'] > 10:
            performance_summary.append("Strong revenue growth indicates healthy business expansion.")
        elif growth['revenue_growth'] > 0:
            performance_summary.append("Moderate revenue growth shows steady business performance.")
        else:
            performance_summary.append("Revenue decline warrants attention to sales and marketing strategies.")
        
        if current['profit_margin'] > 20:
            performance_summary.append("Excellent profit margins demonstrate strong operational efficiency.")
        elif current['profit_margin'] > 10:
            performance_summary.append("Healthy profit margins indicate good cost management.")
        else:
            performance_summary.append("Profit margins could be improved through cost optimization.")
        
        # Cash flow insights
        cash_insights = []
        if current['cash_balance'] > current['expenses']:
            cash_insights.append("Strong cash position provides good operational flexibility.")
        else:
            cash_insights.append("Cash position relative to expenses suggests monitoring liquidity.")
        
        # Recommendations
        recommendations = []
        
        if growth['expense_growth'] > growth['revenue_growth']:
            recommendations.append("Consider reviewing expense categories that are growing faster than revenue.")
        
        if current['ar_balance'] > current['revenue'] * 0.3:
            recommendations.append("High accounts receivable relative to revenue may indicate collection issues.")
        
        if not recommendations:
            recommendations.append("Continue current operational strategies while monitoring key metrics.")
        
        return {
            'performance_summary': performance_summary,
            'cash_insights': cash_insights,
            'recommendations': recommendations,
            'key_highlights': [
                f"Revenue {growth['revenue_growth']:+.1f}% vs prior period",
                f"Net income ${growth['net_income_change']:,.2f} change",
                f"Profit margin of {current['profit_margin']:.1f}%"
            ]
        }
    
    def _get_trial_balance_data(self, db: Session, start_date: str, end_date: str) -> List[Dict]:
        """Get trial balance data for detailed report"""
        excel_gen = ExcelTemplateGenerator()
        return excel_gen._get_trial_balance_data(db, start_date, end_date)
    
    def _get_pl_detailed_data(self, db: Session, start_date: str, end_date: str) -> Dict:
        """Get detailed P&L data"""
        excel_gen = ExcelTemplateGenerator()
        return excel_gen._get_pl_data(db, start_date, end_date)
    
    def _get_balance_sheet_data(self, db: Session, end_date: str) -> Dict:
        """Get balance sheet data"""
        excel_gen = ExcelTemplateGenerator()
        return excel_gen._get_balance_sheet_data(db, end_date)
    
    def _calculate_variance_analysis(self, db: Session, start_date: str, end_date: str) -> Dict:
        """Calculate variance analysis (simplified - assumes budget data exists)"""
        pl_data = self._get_pl_detailed_data(db, start_date, end_date)
        
        # In a real implementation, you'd have budget data in the database
        # For now, we'll create simplified variance analysis
        revenue_variance = []
        for item in pl_data['revenue']:
            # Assume budget is 10% higher than actual for demo
            budget = item['amount'] * Decimal('1.1')
            variance = item['amount'] - budget
            variance_pct = (variance / budget * 100) if budget != 0 else 0
            
            revenue_variance.append({
                'account': item['account_name'],
                'budget': budget,
                'actual': item['amount'],
                'variance': variance,
                'variance_pct': variance_pct,
                'status': 'favorable' if variance > 0 else 'unfavorable'
            })
        
        expense_variance = []
        for item in pl_data['expenses']:
            # Assume budget is 10% lower than actual for demo
            budget = item['amount'] * Decimal('0.9')
            variance = budget - item['amount']  # For expenses, lower actual is favorable
            variance_pct = (variance / budget * 100) if budget != 0 else 0
            
            expense_variance.append({
                'account': item['account_name'],
                'budget': budget,
                'actual': item['amount'],
                'variance': variance,
                'variance_pct': variance_pct,
                'status': 'favorable' if variance > 0 else 'unfavorable'
            })
        
        return {
            'revenue_variance': revenue_variance,
            'expense_variance': expense_variance
        }
    
    def _prepare_chart_data(self, financial_data: Dict) -> Dict:
        """Prepare data for charts (simplified for PDF)"""
        current = financial_data['current_period']
        
        # Revenue vs Expenses pie chart data
        pie_data = [
            {'label': 'Net Income', 'value': float(current['net_income'])},
            {'label': 'Expenses', 'value': float(current['expenses'])}
        ]
        
        # Growth trend data
        growth = financial_data['growth_metrics']
        trend_data = [
            {'metric': 'Revenue Growth', 'value': float(growth['revenue_growth'])},
            {'metric': 'Expense Growth', 'value': float(growth['expense_growth'])}
        ]
        
        return {
            'revenue_breakdown': pie_data,
            'growth_trends': trend_data
        }
    
    def _prepare_detailed_charts(self, financial_data: Dict, pl_data: Dict, balance_sheet: Dict) -> Dict:
        """Prepare detailed chart data"""
        # Revenue by account
        revenue_chart = [
            {'account': item['account_name'], 'amount': float(item['amount'])}
            for item in pl_data['revenue'][:10]  # Top 10
        ]
        
        # Expenses by account
        expense_chart = [
            {'account': item['account_name'], 'amount': float(item['amount'])}
            for item in pl_data['expenses'][:10]  # Top 10
        ]
        
        # Assets breakdown
        assets_chart = []
        for item in balance_sheet['current_assets'][:5]:
            assets_chart.append({'account': item['account_name'], 'amount': float(item['balance'])})
        
        return {
            'revenue_by_account': revenue_chart,
            'expenses_by_account': expense_chart,
            'assets_breakdown': assets_chart
        }
    
    def _html_to_pdf(self, html_content: str) -> BinaryIO:
        """Convert HTML to PDF using WeasyPrint"""
        if not WEASYPRINT_AVAILABLE:
            # Return HTML content as fallback when WeasyPrint is not available
            html_io = io.BytesIO(html_content.encode('utf-8'))
            html_io.seek(0)
            return html_io
            
        try:
            # Create PDF
            html_doc = HTML(string=html_content)
            pdf_bytes = html_doc.write_pdf()
            
            # Return as BytesIO
            pdf_io = io.BytesIO(pdf_bytes)
            pdf_io.seek(0)
            return pdf_io
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise
    
    def _create_default_templates(self):
        """Create default HTML templates if they don't exist"""
        templates = {
            'base.html': self._base_template(),
            'executive_summary.html': self._executive_summary_template(),
            'detailed_report.html': self._detailed_report_template(),
            'styles.css': self._default_styles()
        }
        
        for filename, content in templates.items():
            filepath = self.template_dir / filename
            if not filepath.exists():
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Created default template: {filepath}")
    
    def _base_template(self) -> str:
        """Base HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Financial Report{% endblock %}</title>
    <style>
        {{ css_content | safe }}
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    
    <div class="footer">
        <p>Generated on {{ generated_date | date }} | Page <span class="page-counter"></span></p>
    </div>
</body>
</html>"""
    
    def _executive_summary_template(self) -> str:
        """Executive summary template"""
        return """{% extends "base.html" %}
{% set css_content = self.load_css() %}

{% block title %}{{ report_title }}{% endblock %}

{% block content %}
<div class="header">
    <h1>{{ report_title }}</h1>
    <h2>{{ period_start | date }} - {{ period_end | date }}</h2>
</div>

<div class="executive-summary">
    <div class="key-metrics">
        <h3>Key Financial Metrics</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <h4>Revenue</h4>
                <p class="metric-value">{{ financial_data.current_period.revenue | currency }}</p>
                <p class="metric-change {% if financial_data.growth_metrics.revenue_growth > 0 %}positive{% else %}negative{% endif %}">
                    {{ financial_data.growth_metrics.revenue_growth | percentage }} vs prior period
                </p>
            </div>
            
            <div class="metric-card">
                <h4>Net Income</h4>
                <p class="metric-value">{{ financial_data.current_period.net_income | currency }}</p>
                <p class="metric-change">
                    {{ financial_data.current_period.profit_margin | percentage }} profit margin
                </p>
            </div>
            
            <div class="metric-card">
                <h4>Cash Balance</h4>
                <p class="metric-value">{{ financial_data.current_period.cash_balance | currency }}</p>
            </div>
            
            <div class="metric-card">
                <h4>Accounts Receivable</h4>
                <p class="metric-value">{{ financial_data.current_period.ar_balance | currency }}</p>
            </div>
        </div>
    </div>
    
    {% if commentary %}
    <div class="commentary">
        <h3>Executive Commentary</h3>
        
        <div class="commentary-section">
            <h4>Performance Highlights</h4>
            <ul>
                {% for highlight in commentary.key_highlights %}
                <li>{{ highlight }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="commentary-section">
            <h4>Performance Analysis</h4>
            {% for insight in commentary.performance_summary %}
            <p>{{ insight }}</p>
            {% endfor %}
        </div>
        
        <div class="commentary-section">
            <h4>Cash Flow Insights</h4>
            {% for insight in commentary.cash_insights %}
            <p>{{ insight }}</p>
            {% endfor %}
        </div>
        
        <div class="commentary-section">
            <h4>Recommendations</h4>
            <ul>
                {% for rec in commentary.recommendations %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
        </div>
    </div>
    {% endif %}
</div>

<div class="page-break"></div>

<div class="financial-summary">
    <h3>Financial Summary</h3>
    <table class="summary-table">
        <thead>
            <tr>
                <th>Metric</th>
                <th>Current Period</th>
                <th>Previous Period</th>
                <th>Change</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Revenue</td>
                <td>{{ financial_data.current_period.revenue | currency }}</td>
                <td>{{ financial_data.previous_period.revenue | currency }}</td>
                <td class="{% if financial_data.growth_metrics.revenue_growth > 0 %}positive{% else %}negative{% endif %}">
                    {{ financial_data.growth_metrics.revenue_growth | percentage }}
                </td>
            </tr>
            <tr>
                <td>Expenses</td>
                <td>{{ financial_data.current_period.expenses | currency }}</td>
                <td>{{ financial_data.previous_period.expenses | currency }}</td>
                <td class="{% if financial_data.growth_metrics.expense_growth < 0 %}positive{% else %}negative{% endif %}">
                    {{ financial_data.growth_metrics.expense_growth | percentage }}
                </td>
            </tr>
            <tr class="total-row">
                <td>Net Income</td>
                <td>{{ financial_data.current_period.net_income | currency }}</td>
                <td>{{ financial_data.previous_period.net_income | currency }}</td>
                <td class="{% if financial_data.growth_metrics.net_income_change > 0 %}positive{% else %}negative{% endif %}">
                    {{ financial_data.growth_metrics.net_income_change | currency }}
                </td>
            </tr>
        </tbody>
    </table>
</div>
{% endblock %}

{% macro load_css() %}
    {% include 'styles.css' %}
{% endmacro %}"""
    
    def _detailed_report_template(self) -> str:
        """Detailed report template"""
        return """{% extends "base.html" %}
{% set css_content = self.load_css() %}

{% block title %}{{ report_title }}{% endblock %}

{% block content %}
<div class="header">
    <h1>{{ report_title }}</h1>
    <h2>{{ period_start | date }} - {{ period_end | date }}</h2>
</div>

<!-- Executive Summary Section -->
<div class="section">
    <h3>Executive Summary</h3>
    <div class="metrics-grid">
        <div class="metric-card">
            <h4>Total Revenue</h4>
            <p class="metric-value">{{ financial_data.current_period.revenue | currency }}</p>
        </div>
        <div class="metric-card">
            <h4>Total Expenses</h4>
            <p class="metric-value">{{ financial_data.current_period.expenses | currency }}</p>
        </div>
        <div class="metric-card">
            <h4>Net Income</h4>
            <p class="metric-value">{{ financial_data.current_period.net_income | currency }}</p>
        </div>
        <div class="metric-card">
            <h4>Profit Margin</h4>
            <p class="metric-value">{{ financial_data.current_period.profit_margin | percentage }}</p>
        </div>
    </div>
</div>

<div class="page-break"></div>

<!-- Profit & Loss Statement -->
<div class="section">
    <h3>Profit & Loss Statement</h3>
    <table class="financial-table">
        <thead>
            <tr>
                <th>Account</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>
            <tr class="section-header">
                <td colspan="2"><strong>REVENUE</strong></td>
            </tr>
            {% for item in profit_loss.revenue %}
            <tr>
                <td>{{ item.account_name }}</td>
                <td class="currency">{{ item.amount | currency }}</td>
            </tr>
            {% endfor %}
            <tr class="subtotal">
                <td><strong>Total Revenue</strong></td>
                <td class="currency"><strong>{{ profit_loss.revenue | sum(attribute='amount') | currency }}</strong></td>
            </tr>
            
            <tr class="section-header">
                <td colspan="2"><strong>EXPENSES</strong></td>
            </tr>
            {% for item in profit_loss.expenses %}
            <tr>
                <td>{{ item.account_name }}</td>
                <td class="currency">{{ item.amount | currency }}</td>
            </tr>
            {% endfor %}
            <tr class="subtotal">
                <td><strong>Total Expenses</strong></td>
                <td class="currency"><strong>{{ profit_loss.expenses | sum(attribute='amount') | currency }}</strong></td>
            </tr>
            
            <tr class="total-row">
                <td><strong>NET INCOME</strong></td>
                <td class="currency"><strong>{{ financial_data.current_period.net_income | currency }}</strong></td>
            </tr>
        </tbody>
    </table>
</div>

<div class="page-break"></div>

<!-- Balance Sheet -->
<div class="section">
    <h3>Balance Sheet</h3>
    <h4>As of {{ period_end | date }}</h4>
    
    <table class="financial-table">
        <thead>
            <tr>
                <th>Account</th>
                <th>Balance</th>
            </tr>
        </thead>
        <tbody>
            <tr class="section-header">
                <td colspan="2"><strong>ASSETS</strong></td>
            </tr>
            <tr class="subsection-header">
                <td colspan="2"><em>Current Assets</em></td>
            </tr>
            {% for item in balance_sheet.current_assets %}
            <tr>
                <td>{{ item.account_name }}</td>
                <td class="currency">{{ item.balance | currency }}</td>
            </tr>
            {% endfor %}
            <tr class="subtotal">
                <td><strong>Total Current Assets</strong></td>
                <td class="currency"><strong>{{ balance_sheet.current_assets | sum(attribute='balance') | currency }}</strong></td>
            </tr>
            
            <tr class="subsection-header">
                <td colspan="2"><em>Fixed Assets</em></td>
            </tr>
            {% for item in balance_sheet.fixed_assets %}
            <tr>
                <td>{{ item.account_name }}</td>
                <td class="currency">{{ item.balance | currency }}</td>
            </tr>
            {% endfor %}
            <tr class="subtotal">
                <td><strong>Total Fixed Assets</strong></td>
                <td class="currency"><strong>{{ balance_sheet.fixed_assets | sum(attribute='balance') | currency }}</strong></td>
            </tr>
            
            <tr class="total-row">
                <td><strong>TOTAL ASSETS</strong></td>
                <td class="currency"><strong>{{ (balance_sheet.current_assets | sum(attribute='balance')) + (balance_sheet.fixed_assets | sum(attribute='balance')) | currency }}</strong></td>
            </tr>
            
            <tr class="section-header">
                <td colspan="2"><strong>LIABILITIES & EQUITY</strong></td>
            </tr>
            <tr class="subsection-header">
                <td colspan="2"><em>Current Liabilities</em></td>
            </tr>
            {% for item in balance_sheet.current_liabilities %}
            <tr>
                <td>{{ item.account_name }}</td>
                <td class="currency">{{ item.balance | currency }}</td>
            </tr>
            {% endfor %}
            <tr class="subtotal">
                <td><strong>Total Current Liabilities</strong></td>
                <td class="currency"><strong>{{ balance_sheet.current_liabilities | sum(attribute='balance') | currency }}</strong></td>
            </tr>
            
            <tr class="subsection-header">
                <td colspan="2"><em>Equity</em></td>
            </tr>
            {% for item in balance_sheet.equity %}
            <tr>
                <td>{{ item.account_name }}</td>
                <td class="currency">{{ item.balance | currency }}</td>
            </tr>
            {% endfor %}
            <tr class="subtotal">
                <td><strong>Total Equity</strong></td>
                <td class="currency"><strong>{{ balance_sheet.equity | sum(attribute='balance') | currency }}</strong></td>
            </tr>
            
            <tr class="total-row">
                <td><strong>TOTAL LIABILITIES & EQUITY</strong></td>
                <td class="currency"><strong>{{ (balance_sheet.current_liabilities | sum(attribute='balance')) + (balance_sheet.equity | sum(attribute='balance')) | currency }}</strong></td>
            </tr>
        </tbody>
    </table>
</div>

{% if variance_analysis %}
<div class="page-break"></div>

<!-- Variance Analysis -->
<div class="section">
    <h3>Variance Analysis</h3>
    
    <h4>Revenue Variance</h4>
    <table class="variance-table">
        <thead>
            <tr>
                <th>Account</th>
                <th>Budget</th>
                <th>Actual</th>
                <th>Variance</th>
                <th>Variance %</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for item in variance_analysis.revenue_variance %}
            <tr>
                <td>{{ item.account }}</td>
                <td class="currency">{{ item.budget | currency }}</td>
                <td class="currency">{{ item.actual | currency }}</td>
                <td class="currency {% if item.variance > 0 %}positive{% else %}negative{% endif %}">{{ item.variance | currency }}</td>
                <td class="percentage {% if item.variance > 0 %}positive{% else %}negative{% endif %}">{{ item.variance_pct | percentage }}</td>
                <td class="status {{ item.status }}">{{ item.status | title }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <h4>Expense Variance</h4>
    <table class="variance-table">
        <thead>
            <tr>
                <th>Account</th>
                <th>Budget</th>
                <th>Actual</th>
                <th>Variance</th>
                <th>Variance %</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for item in variance_analysis.expense_variance %}
            <tr>
                <td>{{ item.account }}</td>
                <td class="currency">{{ item.budget | currency }}</td>
                <td class="currency">{{ item.actual | currency }}</td>
                <td class="currency {% if item.variance > 0 %}positive{% else %}negative{% endif %}">{{ item.variance | currency }}</td>
                <td class="percentage {% if item.variance > 0 %}positive{% else %}negative{% endif %}">{{ item.variance_pct | percentage }}</td>
                <td class="status {{ item.status }}">{{ item.status | title }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% endblock %}

{% macro load_css() %}
    {% include 'styles.css' %}
{% endmacro %}"""
    
    def _default_styles(self) -> str:
        """Default CSS styles for PDF reports"""
        return """
/* Base Styles */
body {
    font-family: 'Arial', sans-serif;
    font-size: 12px;
    line-height: 1.4;
    color: #333;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

/* Headers */
.header {
    text-align: center;
    margin-bottom: 30px;
    border-bottom: 2px solid #366092;
    padding-bottom: 20px;
}

.header h1 {
    font-size: 24px;
    color: #366092;
    margin: 0;
}

.header h2 {
    font-size: 16px;
    color: #666;
    margin: 10px 0 0 0;
    font-weight: normal;
}

/* Sections */
.section {
    margin-bottom: 40px;
}

.section h3 {
    font-size: 18px;
    color: #366092;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.section h4 {
    font-size: 14px;
    color: #444;
    margin-bottom: 15px;
}

/* Metrics Grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.metric-card h4 {
    font-size: 12px;
    color: #666;
    margin: 0 0 10px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 20px;
    font-weight: bold;
    color: #366092;
    margin: 0 0 5px 0;
}

.metric-change {
    font-size: 11px;
    margin: 0;
}

.metric-change.positive {
    color: #28a745;
}

.metric-change.negative {
    color: #dc3545;
}

/* Tables */
.financial-table, .summary-table, .variance-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    font-size: 11px;
}

.financial-table th, .summary-table th, .variance-table th {
    background-color: #366092;
    color: white;
    padding: 12px 8px;
    text-align: left;
    font-weight: bold;
}

.financial-table td, .summary-table td, .variance-table td {
    padding: 8px;
    border-bottom: 1px solid #ddd;
}

.financial-table .currency, .summary-table .currency, .variance-table .currency {
    text-align: right;
}

.financial-table .percentage, .variance-table .percentage {
    text-align: right;
}

/* Table Row Styles */
.section-header td {
    background-color: #f1f3f4;
    font-weight: bold;
    color: #366092;
    padding: 10px 8px;
}

.subsection-header td {
    background-color: #f8f9fa;
    font-style: italic;
    padding: 8px;
}

.subtotal td {
    border-top: 1px solid #366092;
    font-weight: bold;
    background-color: #f8f9fa;
}

.total-row td {
    border-top: 2px solid #366092;
    border-bottom: 2px solid #366092;
    font-weight: bold;
    background-color: #e9ecef;
    font-size: 12px;
}

/* Commentary */
.commentary {
    background: #f8f9fa;
    border-left: 4px solid #366092;
    padding: 20px;
    margin-bottom: 30px;
}

.commentary-section {
    margin-bottom: 20px;
}

.commentary-section:last-child {
    margin-bottom: 0;
}

.commentary-section h4 {
    color: #366092;
    margin-bottom: 10px;
}

.commentary-section ul {
    margin: 0;
    padding-left: 20px;
}

.commentary-section li {
    margin-bottom: 5px;
}

/* Variance Analysis */
.status.favorable {
    color: #28a745;
    font-weight: bold;
}

.status.unfavorable {
    color: #dc3545;
    font-weight: bold;
}

.positive {
    color: #28a745;
}

.negative {
    color: #dc3545;
}

/* Page Breaks */
.page-break {
    page-break-before: always;
}

/* Footer */
.footer {
    position: fixed;
    bottom: 20px;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 10px;
    color: #666;
}

/* Print Optimizations */
@media print {
    body {
        font-size: 11px;
    }
    
    .metric-value {
        font-size: 16px;
    }
    
    .header h1 {
        font-size: 20px;
    }
    
    .section h3 {
        font-size: 16px;
    }
}

/* WeasyPrint specific styles */
@page {
    size: A4;
    margin: 1in;
    
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 10px;
        color: #666;
    }
}
"""


# Convenience functions
def generate_executive_pdf(start_date: str, end_date: str, include_commentary: bool = True) -> BinaryIO:
    """Generate executive summary PDF"""
    generator = PDFReportGenerator()
    return generator.generate_executive_summary(start_date, end_date, include_commentary)

def generate_detailed_pdf(start_date: str, end_date: str, include_variance: bool = True) -> BinaryIO:
    """Generate detailed financial report PDF"""
    generator = PDFReportGenerator()
    return generator.generate_detailed_report(start_date, end_date, include_variance)

def save_pdf_report(pdf_content: BinaryIO, output_path: str):
    """Save PDF content to file"""
    with open(output_path, 'wb') as f:
        pdf_content.seek(0)
        f.write(pdf_content.read())
    logger.info(f"PDF report saved to: {output_path}")


if __name__ == "__main__":
    # Example usage
    import tempfile
    from datetime import datetime, timedelta
    
    # Generate reports for last 30 days
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    
    print(f"Generating PDF reports for {start_date} to {end_date}")
    
    # Executive summary
    exec_pdf = generate_executive_pdf(start_date, end_date)
    with tempfile.NamedTemporaryFile(suffix='_executive.pdf', delete=False) as f:
        save_pdf_report(exec_pdf, f.name)
        print(f"Executive summary saved: {f.name}")
    
    # Detailed report
    detailed_pdf = generate_detailed_pdf(start_date, end_date)
    with tempfile.NamedTemporaryFile(suffix='_detailed.pdf', delete=False) as f:
        save_pdf_report(detailed_pdf, f.name)
        print(f"Detailed report saved: {f.name}")