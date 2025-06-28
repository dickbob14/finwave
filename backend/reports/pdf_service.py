"""
FinWave PDF Service

WeasyPrint renderer with thread-pool support for generating
board-ready financial reports
"""

import asyncio
import base64
import io
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("WeasyPrint not installed. PDF generation will fail.")

from reports.report_builder import build_board_pack
from reports.chart_helpers import build_base64_chart

logger = logging.getLogger(__name__)

# Thread pool for PDF generation (WeasyPrint is CPU-intensive)
pdf_thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix='pdf-gen')


class PDFService:
    """
    Handles PDF generation for financial reports
    """
    
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / 'pdf_templates'
        self.static_dir = Path(__file__).parent.parent / 'static'
        self.fonts_dir = self.static_dir / 'fonts'
        
        # Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # WeasyPrint font configuration
        self.font_config = FontConfiguration() if WEASYPRINT_AVAILABLE else None
        
        # S3 client (lazy loaded)
        self._s3_client = None
    
    def _get_s3_client(self):
        """Get or create S3 client"""
        if not self._s3_client and os.getenv('AWS_S3_BUCKET'):
            self._s3_client = boto3.client('s3')
        return self._s3_client
    
    async def build_pdf(self, workspace_id: str, period: str, 
                       template: str = 'report',
                       attach_variance: bool = True) -> Dict[str, Any]:
        """
        Build PDF report asynchronously
        
        Args:
            workspace_id: Workspace identifier
            period: YYYY-MM format
            template: Template name
            attach_variance: Include variance appendix
            
        Returns:
            Dictionary with file path, S3 URL, etc.
        """
        loop = asyncio.get_event_loop()
        
        # Run CPU-intensive work in thread pool
        result = await loop.run_in_executor(
            pdf_thread_pool,
            self._build_pdf_sync,
            workspace_id, period, template, attach_variance
        )
        
        return result
    
    def _build_pdf_sync(self, workspace_id: str, period: str, 
                       template: str, attach_variance: bool) -> Dict[str, Any]:
        """
        Synchronous PDF builder (runs in thread pool)
        """
        try:
            # Step 1: Build report context
            logger.info(f"Building report context for {workspace_id}/{period}")
            context = build_board_pack(
                workspace_id, 
                period,
                include_variance=attach_variance
            )
            
            # Step 2: Generate charts
            logger.info("Generating charts")
            context['charts'] = self._generate_charts(context)
            
            # Step 3: Add additional context
            context['fonts_path'] = str(self.fonts_dir)
            context['generated_at'] = datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')
            
            # Step 4: Render HTML
            logger.info(f"Rendering template: {template}.html")
            html_template = self.jinja_env.get_template(f"{template}.html")
            html_content = html_template.render(**context)
            
            # Step 5: Generate PDF
            logger.info("Generating PDF with WeasyPrint")
            pdf_bytes = self._render_pdf(html_content)
            
            # Step 6: Save locally
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"{workspace_id}_{period}_board_pack_{timestamp}.pdf"
            local_path = self._save_locally(pdf_bytes, filename)
            
            result = {
                'filename': filename,
                'local_path': str(local_path),
                'size_bytes': len(pdf_bytes),
                'pages': self._estimate_pages(len(pdf_bytes))
            }
            
            # Step 7: Upload to S3 if configured
            if os.getenv('AWS_S3_BUCKET'):
                try:
                    s3_url = self._upload_to_s3(pdf_bytes, workspace_id, period, filename)
                    result['s3_url'] = s3_url
                    result['download_url'] = self._generate_presigned_url(s3_url)
                except Exception as e:
                    logger.error(f"S3 upload failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise
    
    def _generate_charts(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate all charts for the report
        """
        charts = {}
        
        try:
            # Revenue trend chart
            if 'revenue_trend' in context['charts']:
                charts['revenue_trend'] = build_base64_chart(
                    'line',
                    context['charts']['revenue_trend'],
                    palette_key='secondary'
                )
            
            # Cash runway projection
            if 'runway_projection' in context['charts']:
                charts['runway_projection'] = build_base64_chart(
                    'area',
                    context['charts']['runway_projection'],
                    palette_key='accent'
                )
            
            # Scenario analysis
            if context.get('forecast'):
                charts['scenario'] = build_base64_chart(
                    'scenario',
                    context['forecast']
                )
            
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
        
        return charts
    
    def _render_pdf(self, html_content: str) -> bytes:
        """
        Render HTML to PDF using WeasyPrint
        """
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint not installed. Run: pip install weasyprint")
        
        # Create HTML object
        html = HTML(
            string=html_content,
            base_url=str(self.static_dir)
        )
        
        # Custom CSS for print optimization
        print_css = CSS(string="""
            @media print {
                * {
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
            }
        """)
        
        # Generate PDF
        pdf_document = html.write_pdf(
            stylesheets=[print_css],
            font_config=self.font_config
        )
        
        return pdf_document
    
    def _save_locally(self, pdf_bytes: bytes, filename: str) -> Path:
        """
        Save PDF to local reports directory
        """
        reports_dir = Path(__file__).parent.parent / 'generated_reports'
        reports_dir.mkdir(exist_ok=True)
        
        file_path = reports_dir / filename
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"PDF saved locally: {file_path}")
        return file_path
    
    def _upload_to_s3(self, pdf_bytes: bytes, workspace_id: str, 
                     period: str, filename: str) -> str:
        """
        Upload PDF to S3 bucket
        """
        s3_client = self._get_s3_client()
        if not s3_client:
            raise ValueError("S3 not configured")
        
        bucket = os.getenv('AWS_S3_BUCKET')
        key = f"reports/{workspace_id}/{period}/{filename}"
        
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=pdf_bytes,
            ContentType='application/pdf',
            ServerSideEncryption='AES256',
            Metadata={
                'workspace_id': workspace_id,
                'period': period,
                'generated_at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"PDF uploaded to S3: s3://{bucket}/{key}")
        return f"s3://{bucket}/{key}"
    
    def _generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for S3 object
        """
        s3_client = self._get_s3_client()
        if not s3_client:
            return ""
        
        # Parse S3 URL
        parts = s3_url.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]
        
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ""
    
    def _estimate_pages(self, pdf_size: int) -> int:
        """
        Estimate page count based on PDF size
        """
        # Rough estimate: ~50KB per page
        return max(1, pdf_size // 50000)


# Global instance
_pdf_service = None

def get_pdf_service() -> PDFService:
    """Get or create PDF service instance"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service


# Convenience functions
async def build_board_pack_pdf(workspace_id: str, period: str, **kwargs) -> Dict[str, Any]:
    """
    Build board pack PDF
    
    Args:
        workspace_id: Workspace ID
        period: YYYY-MM format
        **kwargs: Additional options
        
    Returns:
        Dictionary with PDF metadata
    """
    service = get_pdf_service()
    return await service.build_pdf(workspace_id, period, 'report', **kwargs)
