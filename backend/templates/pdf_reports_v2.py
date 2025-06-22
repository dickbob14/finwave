"""
PDF Report Generation Module (Enhanced Version)
Generates professional financial reports using WeasyPrint with proper dependency guards
"""

import os
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import utilities and check for WeasyPrint
from template_utils import WEASYPRINT_AVAILABLE

# Conditional imports
if WEASYPRINT_AVAILABLE:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
else:
    # Create placeholder classes when WeasyPrint is not available
    class HTML:
        def __init__(self, *args, **kwargs):
            raise ImportError("WeasyPrint is not installed. PDF generation is disabled.")
    
    class CSS:
        def __init__(self, *args, **kwargs):
            raise ImportError("WeasyPrint is not installed. PDF generation is disabled.")
    
    class FontConfiguration:
        def __init__(self, *args, **kwargs):
            raise ImportError("WeasyPrint is not installed. PDF generation is disabled.")

from jinja2 import Environment, FileSystemLoader, select_autoescape
from database import get_db_session
from models.financial import GeneralLedger, TrialBalance
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

# Report configuration
REPORT_CONFIG = {
    'company_name': os.getenv('COMPANY_NAME', 'FinWave Inc.'),
    'logo_path': Path(__file__).parent / 'assets' / 'logo.png',
    'primary_color': '#002B49',
    'accent_color': '#00A6A6',
    'font_family': 'Helvetica, Arial, sans-serif'
}

class PDFReportGenerator:
    """Enhanced PDF report generator with proper error handling"""
    
    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is not installed. Cannot create PDFReportGenerator.")
        
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / 'report_templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Font configuration
        self.font_config = FontConfiguration()
        
    def get_financial_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch financial data from database"""
        with get_db_session() as db:
            # Get P&L data
            revenue = db.query(
                func.sum(GeneralLedger.amount)
            ).filter(
                and_(
                    GeneralLedger.transaction_date >= start_date,
                    GeneralLedger.transaction_date <= end_date,
                    GeneralLedger.account_code.like('4%')  # Revenue accounts
                )
            ).scalar() or 0
            
            expenses = db.query(
                func.sum(GeneralLedger.amount)
            ).filter(
                and_(
                    GeneralLedger.transaction_date >= start_date,
                    GeneralLedger.transaction_date <= end_date,
                    GeneralLedger.account_code.like('6%')  # Expense accounts
                )
            ).scalar() or 0
            
            # Get trial balance
            trial_balance = db.query(TrialBalance).filter(
                TrialBalance.period_end == end_date
            ).all()
            
            # Calculate key metrics
            gross_profit = revenue - expenses
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
            
            return {
                'period': {
                    'start': start_date,
                    'end': end_date
                },
                'metrics': {
                    'revenue': revenue,
                    'expenses': abs(expenses),
                    'gross_profit': gross_profit,
                    'gross_margin': gross_margin,
                    'net_income': gross_profit  # Simplified
                },
                'trial_balance': trial_balance
            }
    
    def generate_executive_summary(self, start_date: str, end_date: str, include_commentary: bool = True) -> io.BytesIO:
        """Generate executive summary PDF"""
        # Get financial data
        data = self.get_financial_data(start_date, end_date)
        
        # Add company info
        data['company'] = REPORT_CONFIG
        data['generated_at'] = datetime.now().strftime('%B %d, %Y')
        data['include_commentary'] = include_commentary
        
        # Render HTML template
        template = self.env.get_template('executive_summary.html')
        html_content = template.render(**data)
        
        # Convert to PDF
        pdf_buffer = io.BytesIO()
        
        # Base CSS
        base_css = CSS(string=self._get_base_css())
        
        # Generate PDF
        HTML(
            string=html_content,
            base_url=str(Path(__file__).parent)
        ).write_pdf(
            pdf_buffer,
            stylesheets=[base_css],
            font_config=self.font_config
        )
        
        pdf_buffer.seek(0)
        return pdf_buffer
    
    def generate_detailed_report(self, start_date: str, end_date: str, include_variance: bool = True) -> io.BytesIO:
        """Generate detailed financial report PDF"""
        # Get financial data
        data = self.get_financial_data(start_date, end_date)
        
        # Add additional details
        data['company'] = REPORT_CONFIG
        data['generated_at'] = datetime.now().strftime('%B %d, %Y')
        data['include_variance'] = include_variance
        
        # Get prior period data if variance requested
        if include_variance:
            # Calculate prior period
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            period_days = (end_dt - start_dt).days
            
            prior_start = (start_dt - timedelta(days=period_days + 1)).isoformat()[:10]
            prior_end = (start_dt - timedelta(days=1)).isoformat()[:10]
            
            data['prior_period'] = self.get_financial_data(prior_start, prior_end)
        
        # Render HTML template
        template = self.env.get_template('detailed_report.html')
        html_content = template.render(**data)
        
        # Convert to PDF
        pdf_buffer = io.BytesIO()
        
        # Base CSS
        base_css = CSS(string=self._get_base_css())
        
        # Generate PDF
        HTML(
            string=html_content,
            base_url=str(Path(__file__).parent)
        ).write_pdf(
            pdf_buffer,
            stylesheets=[base_css],
            font_config=self.font_config
        )
        
        pdf_buffer.seek(0)
        return pdf_buffer
    
    def _get_base_css(self) -> str:
        """Get base CSS for PDF styling"""
        return f"""
        @page {{
            size: letter;
            margin: 1in 0.75in;
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}
        
        body {{
            font-family: {REPORT_CONFIG['font_family']};
            font-size: 10pt;
            line-height: 1.5;
            color: #333;
        }}
        
        h1 {{
            color: {REPORT_CONFIG['primary_color']};
            font-size: 24pt;
            margin-bottom: 20px;
        }}
        
        h2 {{
            color: {REPORT_CONFIG['primary_color']};
            font-size: 18pt;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        h3 {{
            color: {REPORT_CONFIG['accent_color']};
            font-size: 14pt;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th {{
            background-color: {REPORT_CONFIG['primary_color']};
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
        }}
        
        td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        .metric-box {{
            background-color: #f5f5f5;
            border-left: 4px solid {REPORT_CONFIG['accent_color']};
            padding: 15px;
            margin: 10px 0;
        }}
        
        .metric-value {{
            font-size: 24pt;
            font-weight: bold;
            color: {REPORT_CONFIG['primary_color']};
        }}
        
        .metric-label {{
            font-size: 10pt;
            color: #666;
            text-transform: uppercase;
        }}
        
        .positive {{
            color: #00B050;
        }}
        
        .negative {{
            color: #FF0000;
        }}
        
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 9pt;
            color: #666;
        }}
        """

# Module-level functions for backward compatibility
def generate_executive_pdf(start_date: str, end_date: str, include_commentary: bool = True) -> io.BytesIO:
    """Generate executive summary PDF (wrapper function)"""
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint is not installed. PDF generation is disabled.")
    
    try:
        generator = PDFReportGenerator()
        return generator.generate_executive_summary(start_date, end_date, include_commentary)
    except Exception as e:
        logger.error(f"Failed to generate executive PDF: {e}")
        raise

def generate_detailed_pdf(start_date: str, end_date: str, include_variance: bool = True) -> io.BytesIO:
    """Generate detailed report PDF (wrapper function)"""
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint is not installed. PDF generation is disabled.")
    
    try:
        generator = PDFReportGenerator()
        return generator.generate_detailed_report(start_date, end_date, include_variance)
    except Exception as e:
        logger.error(f"Failed to generate detailed PDF: {e}")
        raise

def save_pdf_report(pdf_buffer: io.BytesIO, filename: str) -> str:
    """Save PDF report to file"""
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint is not installed. PDF generation is disabled.")
    
    try:
        output_dir = Path(__file__).parent.parent / 'generated_reports'
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        logger.info(f"PDF report saved to: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Failed to save PDF report: {e}")
        raise

# Create placeholder HTML templates if they don't exist
def create_default_templates():
    """Create default HTML templates for reports"""
    template_dir = Path(__file__).parent / 'report_templates'
    template_dir.mkdir(exist_ok=True)
    
    # Executive summary template
    executive_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Executive Summary - {{ period.start }} to {{ period.end }}</title>
</head>
<body>
    <h1>{{ company.company_name }}</h1>
    <h2>Executive Summary</h2>
    <p>Period: {{ period.start }} to {{ period.end }}</p>
    
    <div class="metric-box">
        <div class="metric-label">Revenue</div>
        <div class="metric-value">${{ "{:,.0f}".format(metrics.revenue) }}</div>
    </div>
    
    <div class="metric-box">
        <div class="metric-label">Expenses</div>
        <div class="metric-value">${{ "{:,.0f}".format(metrics.expenses) }}</div>
    </div>
    
    <div class="metric-box">
        <div class="metric-label">Net Income</div>
        <div class="metric-value {% if metrics.net_income >= 0 %}positive{% else %}negative{% endif %}">
            ${{ "{:,.0f}".format(metrics.net_income) }}
        </div>
    </div>
    
    <div class="metric-box">
        <div class="metric-label">Gross Margin</div>
        <div class="metric-value">{{ "{:.1f}".format(metrics.gross_margin) }}%</div>
    </div>
    
    <div class="footer">
        Generated on {{ generated_at }}
    </div>
</body>
</html>
"""
    
    # Detailed report template
    detailed_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Financial Report - {{ period.start }} to {{ period.end }}</title>
</head>
<body>
    <h1>{{ company.company_name }}</h1>
    <h2>Detailed Financial Report</h2>
    <p>Period: {{ period.start }} to {{ period.end }}</p>
    
    <h3>Income Statement</h3>
    <table>
        <tr>
            <th>Item</th>
            <th>Amount</th>
            {% if include_variance and prior_period %}
            <th>Prior Period</th>
            <th>Variance</th>
            {% endif %}
        </tr>
        <tr>
            <td>Revenue</td>
            <td>${{ "{:,.0f}".format(metrics.revenue) }}</td>
            {% if include_variance and prior_period %}
            <td>${{ "{:,.0f}".format(prior_period.metrics.revenue) }}</td>
            <td>{{ "{:.1f}".format(((metrics.revenue - prior_period.metrics.revenue) / prior_period.metrics.revenue * 100) if prior_period.metrics.revenue else 0) }}%</td>
            {% endif %}
        </tr>
        <tr>
            <td>Expenses</td>
            <td>${{ "{:,.0f}".format(metrics.expenses) }}</td>
            {% if include_variance and prior_period %}
            <td>${{ "{:,.0f}".format(prior_period.metrics.expenses) }}</td>
            <td>{{ "{:.1f}".format(((metrics.expenses - prior_period.metrics.expenses) / prior_period.metrics.expenses * 100) if prior_period.metrics.expenses else 0) }}%</td>
            {% endif %}
        </tr>
        <tr>
            <td><strong>Net Income</strong></td>
            <td><strong>${{ "{:,.0f}".format(metrics.net_income) }}</strong></td>
            {% if include_variance and prior_period %}
            <td><strong>${{ "{:,.0f}".format(prior_period.metrics.net_income) }}</strong></td>
            <td><strong>{{ "{:.1f}".format(((metrics.net_income - prior_period.metrics.net_income) / abs(prior_period.metrics.net_income) * 100) if prior_period.metrics.net_income else 0) }}%</strong></td>
            {% endif %}
        </tr>
    </table>
    
    <h3>Key Metrics</h3>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Gross Profit</td>
            <td>${{ "{:,.0f}".format(metrics.gross_profit) }}</td>
        </tr>
        <tr>
            <td>Gross Margin %</td>
            <td>{{ "{:.1f}".format(metrics.gross_margin) }}%</td>
        </tr>
    </table>
    
    <div class="footer">
        Generated on {{ generated_at }}
    </div>
</body>
</html>
"""
    
    # Save templates
    with open(template_dir / 'executive_summary.html', 'w') as f:
        f.write(executive_template)
    
    with open(template_dir / 'detailed_report.html', 'w') as f:
        f.write(detailed_template)
    
    logger.info("Created default report templates")

# Create templates on module load if needed
if WEASYPRINT_AVAILABLE:
    template_dir = Path(__file__).parent / 'report_templates'
    if not template_dir.exists() or not (template_dir / 'executive_summary.html').exists():
        create_default_templates()