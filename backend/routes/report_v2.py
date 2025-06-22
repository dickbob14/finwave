"""
Report API routes for PDF and narrative report generation
Handles executive summaries, detailed reports, and custom report generation
"""
import logging
import tempfile
from datetime import datetime, timedelta
from typing import Optional, List
import os
import calendar

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
import io

# Import utilities and check for WeasyPrint
from templates.template_utils import WEASYPRINT_AVAILABLE

# Conditional imports for PDF generation
if WEASYPRINT_AVAILABLE:
    from templates.pdf_reports import generate_executive_pdf, generate_detailed_pdf, save_pdf_report
else:
    # Create stub functions when WeasyPrint is not available
    def generate_executive_pdf(*args, **kwargs):
        raise NotImplementedError("PDF generation is not available. WeasyPrint is not installed.")
    
    def generate_detailed_pdf(*args, **kwargs):
        raise NotImplementedError("PDF generation is not available. WeasyPrint is not installed.")
    
    def save_pdf_report(*args, **kwargs):
        raise NotImplementedError("PDF generation is not available. WeasyPrint is not installed.")

from insights.llm_commentary import generate_commentary, generate_mock_commentary
from database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["reports"])

@router.get("/executive")
async def generate_executive_report(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    include_commentary: bool = Query(True, description="Include AI-generated commentary"),
    filename: Optional[str] = Query(None, description="Custom filename for the report")
):
    """
    Generate executive summary PDF report
    
    Returns a downloadable PDF with key financial metrics and insights
    """
    if not WEASYPRINT_AVAILABLE:
        return JSONResponse(
            status_code=501,
            content={
                "status": "pdf_disabled",
                "message": "PDF generation is not available. WeasyPrint is not installed.",
                "alternatives": ["Use /report/commentary for JSON output", "Export from Excel template"]
            }
        )
    
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Generate filename if not provided
        if not filename:
            filename = f"executive_summary_{start_date}_to_{end_date}.pdf"
        elif not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Generate PDF report
        pdf_content = generate_executive_pdf(start_date, end_date, include_commentary)
        pdf_content.seek(0)
        
        return StreamingResponse(
            io.BytesIO(pdf_content.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Executive report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Executive report generation failed")

@router.get("/detailed")
async def generate_detailed_report(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    include_variance: bool = Query(True, description="Include variance analysis"),
    filename: Optional[str] = Query(None, description="Custom filename for the report")
):
    """
    Generate detailed financial PDF report
    
    Returns a comprehensive PDF with all financial statements and analysis
    """
    if not WEASYPRINT_AVAILABLE:
        return JSONResponse(
            status_code=501,
            content={
                "status": "pdf_disabled",
                "message": "PDF generation is not available. WeasyPrint is not installed.",
                "alternatives": ["Use /report/commentary for JSON output", "Export from Excel template"]
            }
        )
    
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Generate filename if not provided
        if not filename:
            filename = f"detailed_report_{start_date}_to_{end_date}.pdf"
        elif not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Generate PDF report
        pdf_content = generate_detailed_pdf(start_date, end_date, include_variance)
        pdf_content.seek(0)
        
        return StreamingResponse(
            io.BytesIO(pdf_content.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Detailed report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed report generation failed")

@router.get("/board-pack")
async def generate_board_pack(
    period: str = Query(..., description="Period in YYYY-MM format (e.g., 2024-09)"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate comprehensive board pack for the specified month
    
    Returns a board-ready PDF with executive summary, financial statements, and insights
    """
    if not WEASYPRINT_AVAILABLE:
        return JSONResponse(
            status_code=501,
            content={
                "status": "pdf_disabled",
                "message": "PDF generation is not available. WeasyPrint is not installed.",
                "alternatives": ["Use /report/commentary for JSON output", "Export from Excel template"]
            }
        )
    
    try:
        # Parse period
        year, month = period.split('-')
        start_date = f"{year}-{month:0>2}-01"
        
        # Calculate end date (last day of month)
        last_day = calendar.monthrange(int(year), int(month))[1]
        end_date = f"{year}-{month:0>2}-{last_day:0>2}"
        
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        filename = f"board_pack_{period}.pdf"
        
        # Generate comprehensive board pack
        # This combines executive summary with detailed analysis
        pdf_content = generate_detailed_pdf(start_date, end_date, include_variance=True)
        pdf_content.seek(0)
        
        return StreamingResponse(
            io.BytesIO(pdf_content.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid period format. Use YYYY-MM: {str(e)}")
    except Exception as e:
        logger.error(f"Board pack generation failed: {e}")
        raise HTTPException(status_code=500, detail="Board pack generation failed")

@router.post("/commentary")
async def generate_financial_commentary(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    llm_provider: str = Query("openai", description="LLM provider (openai, anthropic, mock)"),
    model: str = Query("gpt-4", description="Model name to use")
):
    """
    Generate AI-powered financial commentary
    
    Returns narrative analysis and insights in JSON format
    """
    try:
        # Validate dates
        datetime.fromisoformat(start_date)
        datetime.fromisoformat(end_date)
        
        # Generate commentary
        if llm_provider.lower() == "mock":
            commentary = generate_mock_commentary(start_date, end_date)
        else:
            try:
                commentary = generate_commentary(start_date, end_date, llm_provider, model)
            except Exception as llm_error:
                logger.warning(f"LLM commentary failed, using mock: {llm_error}")
                commentary = generate_mock_commentary(start_date, end_date)
        
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "executive_summary": commentary.executive_summary,
            "performance_analysis": commentary.performance_analysis,
            "variance_commentary": commentary.variance_commentary,
            "trend_insights": commentary.trend_insights,
            "risk_assessment": commentary.risk_assessment,
            "opportunities": commentary.opportunities,
            "recommendations": commentary.recommendations,
            "confidence_score": commentary.confidence_score,
            "data_sources": commentary.data_sources,
            "generated_at": commentary.generated_at.isoformat(),
            "llm_provider": llm_provider,
            "model": model
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Commentary generation failed: {e}")
        raise HTTPException(status_code=500, detail="Commentary generation failed")

@router.get("/templates")
async def get_report_templates():
    """
    Get available report templates and their descriptions
    """
    return {
        "templates": [
            {
                "name": "executive",
                "title": "Executive Summary",
                "description": "High-level financial overview with key metrics and insights",
                "typical_pages": "2-3",
                "audience": "Board, executives, investors",
                "includes": ["Key metrics", "Performance highlights", "Risk assessment", "Recommendations"],
                "pdf_available": WEASYPRINT_AVAILABLE
            },
            {
                "name": "detailed",
                "title": "Detailed Financial Report",
                "description": "Comprehensive financial analysis with all statements",
                "typical_pages": "8-12",
                "audience": "CFO, finance team, auditors",
                "includes": ["P&L", "Balance Sheet", "Cash Flow", "Trial Balance", "Variance Analysis"],
                "pdf_available": WEASYPRINT_AVAILABLE
            },
            {
                "name": "board_pack",
                "title": "Board Pack",
                "description": "Monthly board-ready package combining executive and operational metrics",
                "typical_pages": "10-15",
                "audience": "Board of directors",
                "includes": ["Executive summary", "Financial statements", "KPIs", "Commentary", "Variance analysis"],
                "pdf_available": WEASYPRINT_AVAILABLE
            }
        ],
        "customization_options": [
            "Date range selection",
            "Include/exclude variance analysis",
            "Include/exclude AI commentary",
            "Custom filename",
            "Logo and branding (coming soon)"
        ],
        "pdf_generation_status": "available" if WEASYPRINT_AVAILABLE else "disabled"
    }

@router.get("/periods")
async def get_available_periods():
    """
    Get available reporting periods based on data in the system
    """
    try:
        with get_db_session() as db:
            from sqlalchemy import func, text
            from models.financial import GeneralLedger
            
            # Get date range of available data
            result = db.query(
                func.min(GeneralLedger.transaction_date).label('earliest'),
                func.max(GeneralLedger.transaction_date).label('latest'),
                func.count().label('total_transactions')
            ).first()
            
            if not result or not result.earliest:
                return {
                    "available_periods": [],
                    "message": "No financial data available",
                    "total_transactions": 0
                }
            
            # Generate suggested periods
            earliest = result.earliest
            latest = result.latest
            total_transactions = result.total_transactions
            
            # Generate monthly periods
            monthly_periods = []
            current = earliest.replace(day=1)
            
            while current <= latest:
                last_day = calendar.monthrange(current.year, current.month)[1]
                period_end = current.replace(day=last_day)
                
                # Check if this period has data
                period_data = db.query(func.count(GeneralLedger.id)).filter(
                    GeneralLedger.transaction_date >= current,
                    GeneralLedger.transaction_date <= period_end
                ).scalar()
                
                if period_data > 0:
                    monthly_periods.append({
                        "period": current.strftime("%Y-%m"),
                        "display_name": current.strftime("%B %Y"),
                        "start_date": current.strftime("%Y-%m-%d"),
                        "end_date": period_end.strftime("%Y-%m-%d"),
                        "transaction_count": period_data,
                        "type": "monthly"
                    })
                
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            
            # Generate quarterly periods
            quarterly_periods = []
            quarters = [
                (1, "Q1"), (4, "Q2"), (7, "Q3"), (10, "Q4")
            ]
            
            for start_month, quarter_name in quarters:
                quarter_start = earliest.replace(month=start_month, day=1)
                if start_month == 10:
                    quarter_end = quarter_start.replace(month=12, day=31)
                else:
                    quarter_end = quarter_start.replace(month=start_month + 2)
                    quarter_end = quarter_end.replace(day=calendar.monthrange(quarter_end.year, quarter_end.month)[1])
                
                if quarter_start <= latest:
                    quarterly_periods.append({
                        "period": f"{quarter_start.year}-{quarter_name}",
                        "display_name": f"{quarter_name} {quarter_start.year}",
                        "start_date": quarter_start.strftime("%Y-%m-%d"),
                        "end_date": min(quarter_end, latest).strftime("%Y-%m-%d"),
                        "type": "quarterly"
                    })
            
            return {
                "data_range": {
                    "earliest_date": earliest.strftime("%Y-%m-%d"),
                    "latest_date": latest.strftime("%Y-%m-%d"),
                    "total_transactions": total_transactions
                },
                "monthly_periods": monthly_periods[-12:],  # Last 12 months
                "quarterly_periods": quarterly_periods[-8:],  # Last 8 quarters
                "suggested_periods": [
                    {
                        "period": "current_month",
                        "display_name": "Current Month",
                        "start_date": datetime.now().replace(day=1).strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d")
                    },
                    {
                        "period": "last_month",
                        "display_name": "Last Month",
                        "start_date": (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d"),
                        "end_date": (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
                    },
                    {
                        "period": "ytd",
                        "display_name": "Year to Date",
                        "start_date": datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d")
                    }
                ]
            }
            
    except Exception as e:
        logger.error(f"Failed to get available periods: {e}")
        return {
            "available_periods": [],
            "error": "Failed to retrieve available periods",
            "total_transactions": 0
        }

@router.get("/status")
async def get_report_status():
    """
    Get report generation system status
    """
    # Check database connectivity
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        db_connected = False
    
    # Check LLM configuration
    llm_configured = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "database_connected": db_connected,
        "pdf_generation_available": WEASYPRINT_AVAILABLE,
        "llm_configured": llm_configured,
        "supported_formats": ["pdf"] if WEASYPRINT_AVAILABLE else ["json", "excel"],
        "available_templates": ["executive", "detailed", "board_pack"],
        "features": {
            "ai_commentary": llm_configured,
            "variance_analysis": True,
            "custom_periods": True,
            "bulk_generation": True,
            "pdf_export": WEASYPRINT_AVAILABLE,
            "excel_export": True,
            "json_export": True
        },
        "checked_at": datetime.now().isoformat()
    }