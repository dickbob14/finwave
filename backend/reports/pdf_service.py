"""
PDF generation service with WeasyPrint
"""

import io
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from reports.report_builder import ReportBuilder
from reports.chart_helpers import ChartGenerator

logger = logging.getLogger(__name__)

# Thread pool for PDF generation
pdf_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='pdf_worker')

class PDFService:
    """Service for generating PDF reports"""
    
    def __init__(self, template_dir: str = None):
        if not template_dir:
            template_dir = Path(__file__).parent.parent / 'pdf_templates'
        
        self.template_dir = Path(template_dir)
        self.static_dir = Path(__file__).parent.parent / 'static'
        
        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_number'] = self._format_number
        self.env.filters['format_currency'] = self._format_currency
        
        # WeasyPrint font config
        self.font_config = FontConfiguration()
        
        # Chart generator
        self.chart_generator = ChartGenerator()
    
    def _format_number(self, value: Optional[float], decimals: int = 0) -> str:
        """Format number for display"""
        if value is None:
            return '-'
        
        if decimals == 0:
            return f"{value:,.0f}"
        else:
            return f"{value:,.{decimals}f}"
    
    def _format_currency(self, value: Optional[float]) -> str:
        """Format currency for display"""
        if value is None:
            return '-'
        
        if value < 0:
            return f"(${abs(value):,.0f})"
        else:
            return f"${value:,.0f}"
    
    def generate_board_report(self, workspace_id: str, period_date: datetime = None,
                            progress_callback: callable = None) -> bytes:
        """
        Generate board report PDF
        
        Args:
            workspace_id: Workspace ID
            period_date: Report period (defaults to current month)
            progress_callback: Optional callback for progress updates
            
        Returns:
            PDF bytes
        """
        try:
            # Progress: Building data
            if progress_callback:
                progress_callback(10, "Building report data...")
            
            # Build report context
            builder = ReportBuilder(workspace_id, period_date)
            context = builder.build_report_context()
            
            # Progress: Generating charts
            if progress_callback:
                progress_callback(30, "Generating charts...")
            
            # Generate charts
            context['charts'] = self.chart_generator.generate_all_charts(context)
            
            # Progress: Rendering HTML
            if progress_callback:
                progress_callback(50, "Rendering report...")
            
            # Render HTML
            template = self.env.get_template('report.html')
            html_content = template.render(**context)
            
            # Progress: Generating PDF
            if progress_callback:
                progress_callback(70, "Generating PDF...")
            
            # Generate PDF
            pdf_bytes = self._render_pdf(html_content)
            
            # Progress: Complete
            if progress_callback:
                progress_callback(100, "Complete")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate board report: {e}")
            raise
    
    def _render_pdf(self, html_content: str) -> bytes:
        """Render HTML to PDF using WeasyPrint"""
        # Create HTML object with base URL for static files
        html = HTML(
            string=html_content,
            base_url=str(self.static_dir),
            encoding='utf-8'
        )
        
        # Custom CSS for print
        print_css = CSS(string="""
            @page {
                size: A4;
                margin: 2cm;
            }
            @media print {
                .page-break {
                    page-break-after: always;
                }
                .no-break {
                    page-break-inside: avoid;
                }
            }
        """)
        
        # Render to bytes
        pdf_document = html.write_pdf(
            stylesheets=[print_css],
            font_config=self.font_config
        )
        
        return pdf_document
    
    def generate_board_report_async(self, workspace_id: str, 
                                  period_date: datetime = None) -> Future:
        """
        Generate board report asynchronously
        
        Returns:
            Future that will contain the PDF bytes
        """
        return pdf_executor.submit(
            self.generate_board_report,
            workspace_id,
            period_date
        )
    
    def generate_custom_report(self, workspace_id: str, template_name: str,
                             custom_context: Dict[str, Any] = None) -> bytes:
        """
        Generate a custom report using a specific template
        
        Args:
            workspace_id: Workspace ID
            template_name: Template file name
            custom_context: Additional context for the template
            
        Returns:
            PDF bytes
        """
        try:
            # Build base context
            builder = ReportBuilder(workspace_id)
            context = builder.build_report_context()
            
            # Add custom context
            if custom_context:
                context.update(custom_context)
            
            # Generate charts if needed
            if 'charts' not in context:
                context['charts'] = self.chart_generator.generate_all_charts(context)
            
            # Render template
            template = self.env.get_template(template_name)
            html_content = template.render(**context)
            
            # Generate PDF
            return self._render_pdf(html_content)
            
        except Exception as e:
            logger.error(f"Failed to generate custom report: {e}")
            raise
    
    def save_to_file(self, pdf_bytes: bytes, output_path: str) -> str:
        """Save PDF bytes to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        return str(output_path)
    
    def upload_to_s3(self, pdf_bytes: bytes, workspace_id: str, 
                    period_date: datetime, report_type: str = 'board-pack') -> str:
        """
        Upload PDF to S3
        
        Returns:
            S3 URL
        """
        # This would integrate with your S3 setup
        # For now, return a mock URL
        key = f"reports/{workspace_id}/{period_date.strftime('%Y-%m')}/{report_type}.pdf"
        
        # In production:
        # s3_client = boto3.client('s3')
        # s3_client.put_object(
        #     Bucket=REPORT_BUCKET,
        #     Key=key,
        #     Body=pdf_bytes,
        #     ContentType='application/pdf'
        # )
        
        return f"s3://finwave-reports/{key}"


# Singleton instance
_pdf_service = None

def get_pdf_service() -> PDFService:
    """Get or create PDF service instance"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service