"""
Insights API routes for AI-powered financial commentary
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insights.insight_engine import InsightEngine, generate_template_insights
from templates.template_manager import TemplateManager, TEMPLATE_REGISTRY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])

class CompanyContext(BaseModel):
    """Company context for better insights"""
    industry: Optional[str] = None
    stage: Optional[str] = None  # seed, growth, mature
    employee_count: Optional[int] = None
    fiscal_year_end: Optional[str] = None
    key_metrics: Optional[Dict[str, Any]] = None

class InsightResponse(BaseModel):
    """Insight generation response"""
    summary: str
    narrative: str
    findings: list
    recommendations: list
    metrics_summary: Dict[str, Any]
    generated_at: str

@router.get("/{template_name}", response_model=InsightResponse)
async def get_template_insights(
    template_name: str,
    file: Optional[str] = Query(None, description="Specific file to analyze, defaults to latest"),
    include_metrics: bool = Query(True, description="Include detailed metrics in response"),
    company_context: Optional[CompanyContext] = None
):
    """
    Generate AI-powered insights for a template
    
    Returns narrative commentary, key findings, and recommendations
    """
    
    if template_name not in TEMPLATE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_name}")
    
    # Get template manager
    template_manager = TemplateManager(os.getenv('COMPANY_SLUG', 'demo_corp'))
    
    # Find the file to analyze
    if file:
        file_path = template_manager.populated_path / file
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file}")
    else:
        # Get the latest populated file
        files = template_manager.get_populated_files(template_name, limit=1)
        if not files:
            raise HTTPException(
                status_code=404, 
                detail="No populated files found. Please refresh the template first."
            )
        
        file_path = template_manager.populated_path / files[0]['filename']
        
        # Download from S3 if needed
        if not file_path.exists() and template_manager.s3_bucket:
            s3_key = files[0]['key']
            if not template_manager.download_from_s3(s3_key, file_path):
                raise HTTPException(status_code=404, detail="Failed to retrieve file")
    
    try:
        # Generate insights
        engine = InsightEngine()
        
        # Extract metrics
        metrics = engine.extract_metrics_from_template(file_path, template_name)
        
        # Add company context
        context = company_context.dict() if company_context else None
        
        # Generate insights
        insights = engine.generate_insights(metrics, template_name, context)
        
        # Prepare response
        response = InsightResponse(
            summary=insights['summary'],
            narrative=insights['narrative'],
            findings=insights['findings'],
            recommendations=insights['recommendations'],
            metrics_summary=insights['metrics'] if include_metrics else {},
            generated_at=insights['generated_at']
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.post("/{template_name}/generate")
async def generate_fresh_insights(
    template_name: str,
    refresh_data: bool = Query(False, description="Refresh template data before generating insights"),
    start_date: Optional[str] = Query(None, description="Start date for data refresh"),
    end_date: Optional[str] = Query(None, description="End date for data refresh"),
    company_context: Optional[CompanyContext] = None
):
    """
    Generate fresh insights, optionally refreshing the data first
    
    Useful for on-demand insight generation with latest data
    """
    
    if template_name not in TEMPLATE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_name}")
    
    template_manager = TemplateManager(os.getenv('COMPANY_SLUG', 'demo_corp'))
    
    try:
        # Refresh data if requested
        if refresh_data:
            from datetime import datetime
            
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                # Default to YTD
                start_date = datetime.now().replace(month=1, day=1).strftime('%Y-%m-%d')
            
            logger.info(f"Refreshing {template_name} before generating insights")
            
            result = template_manager.populate_template(
                template_name,
                start_date,
                end_date
            )
            
            file_path = Path(result['populated_file'])
        else:
            # Use latest file
            files = template_manager.get_populated_files(template_name, limit=1)
            if not files:
                raise HTTPException(
                    status_code=404,
                    detail="No data available. Set refresh_data=true or refresh template first."
                )
            
            file_path = template_manager.populated_path / files[0]['filename']
        
        # Generate insights
        context = company_context.dict() if company_context else None
        insights_data = generate_template_insights(
            str(file_path),
            template_name,
            context
        )
        
        return {
            "status": "success",
            "insights": InsightResponse(
                summary=insights_data['summary'],
                narrative=insights_data['narrative'],
                findings=insights_data['findings'],
                recommendations=insights_data['recommendations'],
                metrics_summary=insights_data['metrics'],
                generated_at=insights_data['generated_at']
            ),
            "data_file": file_path.name,
            "refreshed": refresh_data
        }
        
    except Exception as e:
        logger.error(f"Fresh insight generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.get("/{template_name}/history")
async def get_insight_history(
    template_name: str,
    limit: int = Query(10, description="Number of historical insights to return")
):
    """
    Get historical insights for a template
    
    Note: This would typically query a database of saved insights
    """
    # TODO: Implement insight history storage
    
    return {
        "template": template_name,
        "message": "Insight history not yet implemented",
        "hint": "Use GET /insights/{template_name} to generate current insights"
    }

@router.post("/compare")
async def compare_periods(
    template_name: str,
    file1: str = Query(..., description="First file to compare"),
    file2: str = Query(..., description="Second file to compare"),
    focus_metrics: Optional[str] = Query(None, description="Comma-separated metrics to focus on")
):
    """
    Compare insights between two periods
    
    Useful for month-over-month or year-over-year analysis
    """
    
    if template_name not in TEMPLATE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_name}")
    
    template_manager = TemplateManager(os.getenv('COMPANY_SLUG', 'demo_corp'))
    engine = InsightEngine()
    
    try:
        # Extract metrics from both files
        file1_path = template_manager.populated_path / file1
        file2_path = template_manager.populated_path / file2
        
        if not file1_path.exists() or not file2_path.exists():
            raise HTTPException(status_code=404, detail="One or both files not found")
        
        metrics1 = engine.extract_metrics_from_template(file1_path, template_name)
        metrics2 = engine.extract_metrics_from_template(file2_path, template_name)
        
        # Generate comparative analysis
        comparison = {
            "period1": file1,
            "period2": file2,
            "changes": {},
            "narrative": "",
            "key_differences": []
        }
        
        # Compare key metrics
        if 'income_statement' in metrics1 and 'income_statement' in metrics2:
            for metric in ['revenue', 'gross_profit', 'ebitda', 'net_income']:
                if metric in metrics1['income_statement'] and metric in metrics2['income_statement']:
                    val1 = metrics1['income_statement'][metric].get('current', 0)
                    val2 = metrics2['income_statement'][metric].get('current', 0)
                    
                    comparison['changes'][metric] = {
                        'period1': val1,
                        'period2': val2,
                        'absolute_change': val2 - val1,
                        'percent_change': ((val2 / val1) - 1) * 100 if val1 else 0
                    }
        
        # Generate comparative narrative
        significant_changes = [
            (metric, data) for metric, data in comparison['changes'].items()
            if abs(data['percent_change']) > 10
        ]
        
        if significant_changes:
            comparison['narrative'] = f"Comparing {file1} to {file2}: "
            narratives = []
            
            for metric, data in significant_changes[:2]:  # Top 2 changes
                direction = "increased" if data['percent_change'] > 0 else "decreased"
                narratives.append(
                    f"{metric.replace('_', ' ').title()} {direction} by {abs(data['percent_change']):.1f}%"
                )
            
            comparison['narrative'] += " and ".join(narratives) + "."
        else:
            comparison['narrative'] = "No significant changes between periods."
        
        return comparison
        
    except Exception as e:
        logger.error(f"Period comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare periods: {str(e)}")

@router.get("/health")
async def insight_engine_health():
    """Check insight engine health and configuration"""
    
    engine = InsightEngine()
    
    return {
        "status": "healthy",
        "openai_configured": bool(engine.api_key),
        "fallback_available": True,
        "supported_templates": list(TEMPLATE_REGISTRY.keys()),
        "features": [
            "variance_analysis",
            "ratio_calculation",
            "narrative_generation",
            "recommendations",
            "period_comparison"
        ]
    }