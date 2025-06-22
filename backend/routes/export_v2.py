"""
Export API routes for financial reports (Enhanced Version)
Handles Excel, Google Sheets, and other export formats
"""
import logging
import tempfile
from datetime import datetime, timedelta
from typing import Optional
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
import io

# Import the new ETL
from templates.etl_qb_to_excel import QuickBooksToExcelETL
from templates.template_utils import copy_to_google_sheets, get_template_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/excel")
async def export_excel(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    filename: Optional[str] = Query(None, description="Custom filename for the export"),
    include_prior_year: bool = Query(True, description="Include prior year data for variance analysis")
):
    """
    Export financial data to Excel format using board pack template
    
    Returns a downloadable Excel file with comprehensive financial reports
    """
    try:
        # If dates not provided, use current fiscal year from settings
        if not start_date or not end_date:
            # Default to last complete month
            today = datetime.now()
            if today.day < 15:  # If early in month, use last complete month
                end_date = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                end_date = today.strftime('%Y-%m-%d')
            
            # Default to YTD
            start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Generate filename if not provided
        if not filename:
            filename = f"finwave_board_pack_{start_date}_to_{end_date}.xlsx"
        elif not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        # Create ETL instance
        etl = QuickBooksToExcelETL()
        
        # Run ETL to populate template
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        populated_file = etl.run_etl(output_path)
        
        if not populated_file or not Path(populated_file).exists():
            raise HTTPException(status_code=500, detail="Failed to generate Excel file")
        
        # Return as file response
        return FileResponse(
            path=populated_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")

@router.get("/google-sheets")
async def export_google_sheets(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    sheet_title: Optional[str] = Query(None, description="Title for the Google Sheet")
):
    """
    Export financial data to Google Sheets
    
    Returns a URL to the created Google Sheet
    """
    try:
        # Check if Google Sheets credentials are configured
        credentials_path = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON")
        if not credentials_path or not os.path.exists(credentials_path):
            raise HTTPException(
                status_code=400, 
                detail="Google Sheets credentials not configured. Set GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON environment variable."
            )
        
        # If dates not provided, use defaults
        if not start_date or not end_date:
            today = datetime.now()
            end_date = today.strftime('%Y-%m-%d')
            start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Generate sheet title if not provided
        if not sheet_title:
            sheet_title = f"FinWave Board Pack {start_date} to {end_date}"
        
        # First generate populated Excel file
        etl = QuickBooksToExcelETL()
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        populated_file = etl.run_etl(output_path)
        
        if not populated_file:
            raise HTTPException(status_code=500, detail="Failed to generate Excel file")
        
        # Export to Google Sheets
        sheet_url = copy_to_google_sheets(populated_file, sheet_title)
        
        # Clean up temp file
        try:
            Path(populated_file).unlink()
        except:
            pass
        
        if not sheet_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload to Google Sheets. Check credentials and permissions."
            )
        
        return {
            "status": "success",
            "sheet_url": sheet_url,
            "sheet_title": sheet_title,
            "period": {"start_date": start_date, "end_date": end_date},
            "created_at": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Google Sheets export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Google Sheets export failed: {str(e)}")

@router.get("/templates")
async def get_export_templates():
    """
    Get available export templates and their descriptions
    """
    return {
        "templates": [
            {
                "name": "board_pack",
                "title": "Board Pack Template",
                "description": "Professional financial reporting template with dynamic periods and COA mapping",
                "sheets": [
                    "DATA_GL - General ledger transactions",
                    "DATA_GL_PY - Prior year transactions",
                    "REPORT_P&L - Income statement with monthly columns",
                    "REPORT_BS - Balance sheet with variance",
                    "DASH_KPI - Executive KPI dashboard"
                ],
                "features": [
                    "Dynamic month columns based on fiscal year",
                    "Automatic prior year comparison",
                    "COA mapping for flexible account structures",
                    "Professional formatting and conditional formatting",
                    "Ready for PDF export from Excel"
                ]
            }
        ],
        "export_formats": [
            {
                "format": "excel",
                "endpoint": "/export/excel",
                "description": "Download populated Excel workbook",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
            {
                "format": "google_sheets",
                "endpoint": "/export/google-sheets",
                "description": "Create Google Sheets document",
                "requires": "GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON environment variable"
            }
        ]
    }

@router.get("/status")
async def get_export_status():
    """
    Get export system status
    """
    # Check template existence
    template_path = get_template_path() / "finwave_board_pack.xlsx"
    template_exists = template_path.exists()
    
    # Check Google Sheets availability
    google_sheets_configured = bool(os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON"))
    
    # Check QuickBooks connection
    try:
        etl = QuickBooksToExcelETL()
        # This will fail if QB not connected
        qb_connected = True
    except:
        qb_connected = False
    
    return {
        "status": "healthy" if template_exists and qb_connected else "degraded",
        "template_exists": template_exists,
        "template_path": str(template_path) if template_exists else None,
        "quickbooks_connected": qb_connected,
        "google_sheets_configured": google_sheets_configured,
        "capabilities": {
            "excel_export": template_exists and qb_connected,
            "google_sheets_export": template_exists and qb_connected and google_sheets_configured,
            "prior_year_variance": True,
            "dynamic_periods": True,
            "coa_mapping": True
        },
        "checked_at": datetime.now().isoformat()
    }