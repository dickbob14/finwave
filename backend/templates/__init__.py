"""
Templates package for generating financial reports in various formats
"""

from .excel_templates import ExcelTemplateGenerator, GoogleSheetsExporter, generate_financial_excel, export_to_google_sheets

# Try to import PDF functionality, fallback if WeasyPrint is not available
try:
    from .pdf_reports import PDFReportGenerator, generate_executive_pdf, generate_detailed_pdf, save_pdf_report
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    PDFReportGenerator = None
    generate_executive_pdf = None
    generate_detailed_pdf = None
    save_pdf_report = None

__all__ = [
    'ExcelTemplateGenerator', 
    'GoogleSheetsExporter', 
    'generate_financial_excel', 
    'export_to_google_sheets',
    'PDFReportGenerator',
    'generate_executive_pdf',
    'generate_detailed_pdf', 
    'save_pdf_report'
]