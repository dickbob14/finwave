"""
Report Builder - Serializes metric data for PDF generation
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional
from dateutil.relativedelta import relativedelta

from core.database import get_db_session
from metrics.models import Metric
from models.workspace import Workspace
from models.integration import list_workspace_integrations
from scheduler.models import Alert, AlertSeverity
from insights import InsightEngine
from forecast.engine import ForecastEngine

logger = logging.getLogger(__name__)

class ReportBuilder:
    """Builds context data for PDF report generation"""
    
    def __init__(self, workspace_id: str, period_date: date = None):
        self.workspace_id = workspace_id
        self.period_date = period_date or date.today().replace(day=1)
        self.theme = self._load_theme()
        
    def _load_theme(self) -> Dict[str, Any]:
        """Load theme configuration"""
        theme_path = Path(__file__).parent.parent / 'static' / 'theme.json'
        with open(theme_path) as f:
            return json.load(f)
    
    def build_report_context(self) -> Dict[str, Any]:
        """Build complete context for report template"""
        logger.info(f"Building report context for {self.workspace_id} - {self.period_date}")
        
        # Get workspace info
        workspace = self._get_workspace()
        
        # Get periods for analysis
        periods = self._get_periods()
        
        # Build context sections
        context = {
            # Metadata
            'company_name': workspace.name,
            'report_period': self.period_date.strftime('%B %Y'),
            'report_date': datetime.now().strftime('%B %d, %Y'),
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'logo_url': self.theme['brand'].get('logo_url'),
            'contact_email': self.theme['brand'].get('contact_email'),
            'theme': self.theme['colors'],
            
            # Period data
            'periods': [p.strftime('%b %Y') for p in periods],
            'current_period': self.period_date,
            
            # Content sections
            'key_metrics': self._build_key_metrics(),
            'executive_summary': self._build_executive_summary(),
            'kpi_dashboard': self._build_kpi_dashboard(periods),
            'income_statement': self._build_income_statement(periods),
            'balance_sheet': self._build_balance_sheet(),
            'cash_flow': self._build_cash_flow(periods),
            'variance_alerts': self._build_variance_alerts(),
            'variance_insights': self._build_variance_insights(),
            'forecast_data': self._build_forecast_data(),
            'runway_analysis': self._build_runway_analysis(),
            'scenarios': self._build_scenario_analysis(),
            'data_sources': self._build_data_sources(),
            'metric_definitions': self._build_metric_definitions(),
            
            # Charts (will be populated by chart helpers)
            'charts': {}
        }
        
        return context
    
    def _get_workspace(self) -> Workspace:
        """Get workspace details"""
        with get_db_session() as db:
            workspace = db.query(Workspace).filter_by(id=self.workspace_id).first()
            if not workspace:
                raise ValueError(f"Workspace not found: {self.workspace_id}")
            return workspace
    
    def _get_periods(self, months: int = 12) -> List[date]:
        """Get period dates for analysis"""
        periods = []
        current = self.period_date
        
        for _ in range(months):
            periods.append(current)
            current = current - relativedelta(months=1)
        
        return sorted(periods)
    
    def _get_metric_value(self, metric_id: str, period: date = None) -> Optional[float]:
        """Get single metric value"""
        period = period or self.period_date
        
        with get_db_session() as db:
            metric = db.query(Metric).filter_by(
                workspace_id=self.workspace_id,
                metric_id=metric_id,
                period_date=period
            ).first()
            
            return metric.value if metric else None
    
    def _get_metric_series(self, metric_id: str, periods: List[date]) -> List[Optional[float]]:
        """Get metric values for multiple periods"""
        with get_db_session() as db:
            metrics = db.query(Metric).filter(
                Metric.workspace_id == self.workspace_id,
                Metric.metric_id == metric_id,
                Metric.period_date.in_(periods)
            ).all()
            
            # Create lookup
            values_by_period = {m.period_date: m.value for m in metrics}
            
            # Return ordered list
            return [values_by_period.get(p) for p in periods]
    
    def _calculate_change(self, current: Optional[float], prior: Optional[float]) -> Optional[float]:
        """Calculate percentage change"""
        if current is None or prior is None or prior == 0:
            return None
        return ((current - prior) / abs(prior)) * 100
    
    def _build_key_metrics(self) -> List[Dict[str, Any]]:
        """Build key metrics for executive summary"""
        metrics = []
        
        # Revenue
        revenue = self._get_metric_value('revenue')
        revenue_prior = self._get_metric_value('revenue', 
                                             self.period_date - relativedelta(months=1))
        
        if revenue:
            metrics.append({
                'label': 'Revenue',
                'value': revenue,
                'formatted_value': f"${revenue/1000:.0f}K",
                'change': self._calculate_change(revenue, revenue_prior)
            })
        
        # Gross Margin
        gross_margin = self._get_metric_value('gross_margin')
        if gross_margin:
            metrics.append({
                'label': 'Gross Margin',
                'value': gross_margin,
                'formatted_value': f"{gross_margin:.1f}%",
                'change': None  # Could calculate pp change
            })
        
        # EBITDA
        ebitda = self._get_metric_value('ebitda')
        ebitda_prior = self._get_metric_value('ebitda',
                                            self.period_date - relativedelta(months=1))
        
        if ebitda is not None:
            metrics.append({
                'label': 'EBITDA',
                'value': ebitda,
                'formatted_value': f"${ebitda/1000:.0f}K" if ebitda >= 0 else f"(${abs(ebitda)/1000:.0f}K)",
                'change': self._calculate_change(ebitda, ebitda_prior)
            })
        
        # Cash
        cash = self._get_metric_value('cash')
        if cash:
            metrics.append({
                'label': 'Cash Balance',
                'value': cash,
                'formatted_value': f"${cash/1000000:.1f}M",
                'change': None
            })
        
        # Runway
        runway = self._get_metric_value('runway_months')
        if runway:
            metrics.append({
                'label': 'Runway',
                'value': runway,
                'formatted_value': f"{runway:.0f} months",
                'change': None
            })
        
        return metrics
    
    def _build_executive_summary(self) -> str:
        """Generate executive summary narrative"""
        try:
            engine = InsightEngine(self.workspace_id)
            result = engine.generate_insights(
                template_name='executive_summary',
                custom_context={'period': self.period_date.isoformat()}
            )
            return result.get('insight', 'Executive summary pending.')
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return "Executive summary generation in progress."
    
    def _build_kpi_dashboard(self, periods: List[date]) -> Dict[str, List[Dict[str, Any]]]:
        """Build KPI dashboard data"""
        dashboard = {
            'Financial': [],
            'SaaS Metrics': [],
            'Operational': []
        }
        
        # Financial KPIs
        financial_metrics = [
            ('revenue', 'Revenue', 'dollars'),
            ('gross_margin', 'Gross Margin %', 'percentage'),
            ('ebitda_margin', 'EBITDA Margin %', 'percentage'),
            ('burn_rate', 'Burn Rate', 'dollars')
        ]

        
        for metric_id, name, unit in financial_metrics:
            values = self._get_metric_series(metric_id, periods[-3:])
            if any(values):
                current = values[-1]
                prior = values[-2] if len(values) > 1 else None
                target = self._get_metric_value(f"budget_{metric_id}")
                
                dashboard['Financial'].append({
                    'name': name,
                    'values': values,
                    'trend': self._calculate_change(current, prior) or 0,
                    'target': target,
                    'variance': self._calculate_change(current, target) if target else 0,
                    'unit': unit
                })
        
        # SaaS Metrics
        saas_metrics = [
            ('mrr', 'MRR', 'dollars'),
            ('customer_count', 'Customers', 'count'),
            ('churn_rate', 'Churn Rate %', 'percentage'),
            ('ltv_to_cac_ratio', 'LTV:CAC', 'ratio')
        ]
        
        for metric_id, name, unit in saas_metrics:
            values = self._get_metric_series(metric_id, periods[-3:])
            if any(values):
                current = values[-1]
                prior = values[-2] if len(values) > 1 else None
                
                dashboard['SaaS Metrics'].append({
                    'name': name,
                    'values': values,
                    'trend': self._calculate_change(current, prior) or 0,
                    'target': None,
                    'variance': 0,
                    'unit': unit
                })
        
        return dashboard
    
    def _build_income_statement(self, periods: List[date]) -> List[Dict[str, Any]]:
        """Build income statement data"""
        statement = []
        
        # Revenue
        revenue_values = self._get_metric_series('revenue', periods[-6:])
        statement.append({
            'label': 'Revenue',
            'values': revenue_values,
            'indent': 0,
            'is_total': False
        })
        
        # COGS
        cogs_values = self._get_metric_series('cogs', periods[-6:])
        statement.append({
            'label': 'Cost of Goods Sold',
            'values': cogs_values,
            'indent': 0,
            'is_total': False
        })
        
        # Gross Profit
        gross_profit_values = []
        for i in range(len(periods[-6:])):
            rev = revenue_values[i] if i < len(revenue_values) else None
            cogs = cogs_values[i] if i < len(cogs_values) else None
            if rev is not None and cogs is not None:
                gross_profit_values.append(rev - cogs)
            else:
                gross_profit_values.append(None)
        
        statement.append({
            'label': 'Gross Profit',
            'values': gross_profit_values,
            'indent': 0,
            'is_total': True
        })
        
        # Operating Expenses
        opex_values = self._get_metric_series('opex', periods[-6:])
        statement.append({
            'label': 'Operating Expenses',
            'values': opex_values,
            'indent': 0,
            'is_total': False
        })
        
        # EBITDA
        ebitda_values = []
        for i in range(len(periods[-6:])):
            gp = gross_profit_values[i] if i < len(gross_profit_values) else None
            opex = opex_values[i] if i < len(opex_values) else None
            if gp is not None and opex is not None:
                ebitda_values.append(gp - opex)
            else:
                ebitda_values.append(None)
        
        statement.append({
            'label': 'EBITDA',
            'values': ebitda_values,
            'indent': 0,
            'is_total': True
        })
        
        # Net Income
        net_income_values = self._get_metric_series('net_income', periods[-6:])
        if any(net_income_values):
            statement.append({
                'label': 'Net Income',
                'values': net_income_values,
                'indent': 0,
                'is_total': True
            })
        
        return statement
    
    def _build_balance_sheet(self) -> List[Dict[str, Any]]:
        """Build balance sheet data"""
        sheet = []
        current_period = self.period_date
        prior_period = self.period_date - relativedelta(months=1)
        
        # Assets
        sheet.append({
            'label': 'ASSETS',
            'prior': None,
            'current': None,
            'change': None,
            'indent': 0,
            'is_total': False
        })
        
        # Current Assets
        cash_current = self._get_metric_value('cash', current_period)
        cash_prior = self._get_metric_value('cash', prior_period)
        
        if cash_current:
            sheet.append({
                'label': 'Cash and Cash Equivalents',
                'prior': cash_prior,
                'current': cash_current,
                'change': self._calculate_change(cash_current, cash_prior),
                'indent': 1,
                'is_total': False
            })
        
        ar_current = self._get_metric_value('accounts_receivable', current_period)
        ar_prior = self._get_metric_value('accounts_receivable', prior_period)
        
        if ar_current:
            sheet.append({
                'label': 'Accounts Receivable',
                'prior': ar_prior,
                'current': ar_current,
                'change': self._calculate_change(ar_current, ar_prior),
                'indent': 1,
                'is_total': False
            })
        
        # Total Current Assets
        current_assets = (cash_current or 0) + (ar_current or 0)
        prior_assets = (cash_prior or 0) + (ar_prior or 0)
        
        sheet.append({
            'label': 'Total Current Assets',
            'prior': prior_assets,
            'current': current_assets,
            'change': self._calculate_change(current_assets, prior_assets),
            'indent': 1,
            'is_total': True
        })
        
        return sheet
    
    def _build_cash_flow(self, periods: List[date]) -> List[Dict[str, Any]]:
        """Build cash flow statement data"""
        statement = []
        
        # Operating Activities
        statement.append({
            'label': 'OPERATING ACTIVITIES',
            'values': [None] * 3,
            'indent': 0,
            'is_total': False
        })
        
        # Net Income
        net_income = self._get_metric_series('net_income', periods[-3:])
        statement.append({
            'label': 'Net Income',
            'values': net_income,
            'indent': 1,
            'is_total': False
        })
        
        # Changes in Working Capital (simplified)
        statement.append({
            'label': 'Changes in Working Capital',
            'values': [0] * 3,  # Placeholder
            'indent': 1,
            'is_total': False
        })
        
        # Net Cash from Operations
        cash_ops = net_income  # Simplified
        statement.append({
            'label': 'Net Cash from Operating Activities',
            'values': cash_ops,
            'indent': 1,
            'is_total': True
        })
        
        return statement
    
    def _build_variance_alerts(self) -> List[Dict[str, Any]]:
        """Build variance alerts data"""
        alerts = []
        
        with get_db_session() as db:
            # Get recent critical/warning alerts
            db_alerts = db.query(Alert).filter(
                Alert.workspace_id == self.workspace_id,
                Alert.status == 'active',
                Alert.severity.in_([AlertSeverity.CRITICAL.value, AlertSeverity.WARNING.value])
            ).order_by(Alert.severity.desc(), Alert.triggered_at.desc()).limit(5).all()
            
            for alert in db_alerts:
                # Get metric name
                metric_name = alert.metric_id.replace('_', ' ').title()
                
                alerts.append({
                    'metric_name': metric_name,
                    'severity': alert.severity,
                    'message': alert.message,
                    'current_value': alert.current_value,
                    'expected_value': alert.comparison_value or alert.threshold_value,
                    'variance_pct': self._calculate_change(
                        alert.current_value,
                        alert.comparison_value or alert.threshold_value
                    ) or 0
                })
        
        return alerts
    
    def _build_variance_insights(self) -> str:
        """Generate variance analysis narrative"""
        if not self._build_variance_alerts():
            return ""
        
        try:
            engine = InsightEngine(self.workspace_id)
            result = engine.generate_insights(
                template_name='variance_analysis',
                custom_context={'period': self.period_date.isoformat()}
            )
            return result.get('insight', '')
        except Exception as e:
            logger.error(f"Failed to generate variance insights: {e}")
            return ""
    
    def _build_forecast_data(self) -> bool:
        """Check if forecast data exists"""
        with get_db_session() as db:
            forecast_count = db.query(Metric).filter(
                Metric.workspace_id == self.workspace_id,
                Metric.metric_id.like('forecast_%')
            ).count()
            
        return forecast_count > 0
    
    def _build_runway_analysis(self) -> Optional[Dict[str, Any]]:
        """Build runway analysis"""
        runway = self._get_metric_value('runway_months')
        burn_rate = self._get_metric_value('burn_rate')
        cash = self._get_metric_value('cash')
        
        if not runway:
            return None
        
        narrative = f"At the current burn rate of ${burn_rate/1000:.0f}K per month, "
        narrative += f"the company has {runway:.0f} months of runway remaining. "
        
        if runway < 12:
            narrative += "Management should consider fundraising or cost reduction measures."
        elif runway < 18:
            narrative += "The company has adequate runway but should monitor burn rate closely."
        else:
            narrative += "The company has strong cash position with extended runway."
        
        return {
            'months': runway,
            'burn_rate': burn_rate,
            'cash': cash,
            'narrative': narrative
        }
    
    def _build_scenario_analysis(self) -> List[Dict[str, Any]]:
        """Build scenario analysis if available"""
        # Placeholder - would pull from forecast scenarios
        return []
    
    def _build_data_sources(self) -> Dict[str, str]:
        """Build data source information"""
        integrations = list_workspace_integrations(self.workspace_id)
        
        sources = {
            'accounting': 'QuickBooks',
            'crm': 'Salesforce',
            'payroll': 'Gusto',
            'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        for integration in integrations:
            if 'quickbooks' in integration.source:
                sources['accounting'] = 'QuickBooks'
                if integration.last_synced_at:
                    sources['last_sync'] = integration.last_synced_at.strftime('%Y-%m-%d %H:%M')
            elif 'salesforce' in integration.source:
                sources['crm'] = 'Salesforce'
            elif 'hubspot' in integration.source:
                sources['crm'] = 'HubSpot'
            elif 'gusto' in integration.source:
                sources['payroll'] = 'Gusto'
        
        return sources
    
    def _build_metric_definitions(self) -> List[Dict[str, str]]:
        """Build metric definitions for appendix"""
        return [
            {
                'name': 'MRR',
                'definition': 'Monthly Recurring Revenue - Total recurring revenue normalized to a monthly amount'
            },
            {
                'name': 'Gross Margin',
                'definition': 'Revenue minus Cost of Goods Sold, expressed as a percentage of revenue'
            },
            {
                'name': 'EBITDA',
                'definition': 'Earnings Before Interest, Taxes, Depreciation and Amortization'
            },
            {
                'name': 'Burn Rate',
                'definition': 'Net cash outflow per month, calculated as cash used in operations'
            },
            {
                'name': 'Runway',
                'definition': 'Number of months until cash reaches zero at current burn rate'
            },
            {
                'name': 'LTV:CAC',
                'definition': 'Customer Lifetime Value divided by Customer Acquisition Cost'
            }
        ]

def build_board_pack(workspace_id: str, period: str, include_variance: bool = True) -> Dict[str, Any]:
    """Build and return context for a board pack PDF report."""
    # Parse period YYYY-MM to date (first of month)
    try:
        period_date = datetime.strptime(period, '%Y-%m').date()
    except Exception as e:
        raise ValueError(f"Invalid period format '{period}', expected 'YYYY-MM'.") from e
    # Instantiate builder and build report context
    builder = ReportBuilder(workspace_id, period_date)
    context = builder.build_report_context()
    # Optionally remove variance sections
    if not include_variance:
        context.pop('variance_alerts', None)
        context.pop('variance_insights', None)
    # Prepare raw chart data container
    context['charts'] = {}
    # Revenue trend (last 12 months)
    periods = builder._get_periods(12)
    labels = [p.strftime('%b %Y') for p in periods]
    revenue_values = builder._get_metric_series('revenue', periods)
    context['charts']['revenue_trend'] = {
        'labels': labels,
        'values': revenue_values,
        'title': 'Revenue Trend',
        'y_label': 'Revenue ($)'
    }
    # Cash runway projection
    runway_info = context.get('runway_analysis') or {}
    runway_months = runway_info.get('months')
    burn_rate = runway_info.get('burn_rate')
    cash_balance = runway_info.get('cash')
    if runway_months and burn_rate is not None and cash_balance is not None:
        project_months = int(runway_months) if runway_months <= 12 else 12
        proj_labels = []
        proj_values = []
        for i in range(project_months + 1):
            dt = builder.period_date + relativedelta(months=i)
            proj_labels.append(dt.strftime('%b %Y'))
            proj_values.append(cash_balance - burn_rate * i)
        context['charts']['runway_projection'] = {
            'labels': proj_labels,
            'values': proj_values,
            'title': 'Cash Runway Projection',
            'y_label': 'Cash Balance ($)'
        }
    # Scenario analysis (if provided)
    scenarios = context.get('scenarios')
    if scenarios:
        context['forecast'] = scenarios
    return context
