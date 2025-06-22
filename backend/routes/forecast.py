"""
Forecast API routes for scenario planning and driver modeling
"""

import logging
import os
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from auth import get_current_user, require_workspace
from templates.populate_forecast_drivers import ForecastDriverPopulator
from forecast.engine import ForecastEngine, forecast_metrics_task
from core.database import get_db_session
from metrics.models import Metric

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["forecast"])


# Request/Response models
class ForecastRequest(BaseModel):
    metric_ids: Optional[List[str]] = None
    periods_ahead: int = 12
    method: str = 'auto'  # auto, arima, linear, cagr, seasonal

class DriverUpdate(BaseModel):
    driver_id: str
    value: float
    period_start: Optional[date] = None
    period_end: Optional[date] = None

class ScenarioRequest(BaseModel):
    scenario_name: str
    drivers: List[DriverUpdate]
    regenerate_forecast: bool = True

class ForecastResponse(BaseModel):
    metric_id: str
    forecast_values: Dict[str, float]
    method_used: str
    confidence_interval: Optional[Dict[str, float]] = None

class DriverResponse(BaseModel):
    driver_id: str
    current_value: float
    unit: Optional[str] = None
    description: Optional[str] = None
    last_updated: datetime


@router.post("/upload")
async def upload_forecast_workbook(
    file: UploadFile = File(...),
    scenario: Optional[str] = Form(None),
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Upload a forecast workbook with driver assumptions
    Extracts drivers and updates forecasts
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xlsm')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xlsm) are supported"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process the workbook
            populator = ForecastDriverPopulator(tmp_path)
            populator.load_template()
            
            # Extract drivers
            driver_sheets = populator.extract_driver_sheets()
            all_drivers = {}
            for sheet_drivers in driver_sheets.values():
                all_drivers.update(sheet_drivers)
            
            # Extract scenarios
            scenarios = populator.extract_scenario_assumptions()
            
            # Apply scenario if specified
            if scenario and scenarios:
                for scenario_data in scenarios.values():
                    if scenario.lower() in scenario_data:
                        all_drivers.update(scenario_data[scenario.lower()])
                        break
            
            # Store drivers
            period_start = date.today().replace(day=1)
            period_end = date(period_start.year + 1, period_start.month, 1)
            
            driver_results = populator.create_driver_metrics(
                workspace_id, all_drivers, period_start, period_end
            )
            
            # Update forecasts
            forecast_results = populator.update_forecasts_with_drivers(
                workspace_id, all_drivers
            )
            
            # Check variances
            variance_results = populator.trigger_variance_refresh(workspace_id)
            
            return {
                'status': 'success',
                'filename': file.filename,
                'drivers_extracted': len(all_drivers),
                'drivers': {k: v for k, v in list(all_drivers.items())[:10]},  # First 10
                'forecasts_updated': forecast_results['total_saved'],
                'alerts_generated': variance_results['alerts_generated'],
                'scenario': scenario
            }
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Error processing forecast workbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drivers", response_model=List[DriverResponse])
async def get_forecast_drivers(
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Get current forecast driver assumptions
    """
    try:
        with get_db_session() as db:
            # Get all driver metrics
            driver_metrics = db.query(Metric).filter(
                Metric.workspace_id == workspace_id,
                Metric.metric_id.like('driver_%')
            ).order_by(Metric.metric_id, Metric.period_date.desc()).all()
            
            # Group by driver and get latest value
            drivers = {}
            for metric in driver_metrics:
                driver_id = metric.metric_id.replace('driver_', '')
                if driver_id not in drivers or metric.period_date > drivers[driver_id].period_date:
                    drivers[driver_id] = metric
            
            # Format response
            response = []
            for driver_id, metric in drivers.items():
                # Get description based on driver ID
                descriptions = {
                    'new_customer_growth': 'Monthly new customer growth rate',
                    'churn_rate': 'Monthly customer churn rate',
                    'arpu': 'Average revenue per user',
                    'gross_margin_target': 'Target gross margin percentage',
                    'headcount_growth': 'Monthly headcount growth rate',
                    'salary_inflation': 'Annual salary inflation rate',
                    'cac_target': 'Target customer acquisition cost',
                    'burn_rate': 'Monthly cash burn rate'
                }
                
                response.append(DriverResponse(
                    driver_id=driver_id,
                    current_value=metric.value,
                    unit=metric.unit or ('percentage' if 'rate' in driver_id else None),
                    description=descriptions.get(driver_id),
                    last_updated=metric.updated_at
                ))
            
            return response
            
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/drivers/{driver_id}")
async def update_forecast_driver(
    driver_id: str,
    update: DriverUpdate,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Update a single forecast driver
    """
    try:
        with get_db_session() as db:
            # Create or update driver metric
            metric_id = f"driver_{driver_id}"
            period_start = update.period_start or date.today().replace(day=1)
            period_end = update.period_end or date(period_start.year + 1, period_start.month, 1)
            
            updated_count = 0
            
            # Update for each period
            current_date = period_start
            while current_date <= period_end:
                existing = db.query(Metric).filter_by(
                    workspace_id=workspace_id,
                    metric_id=metric_id,
                    period_date=current_date
                ).first()
                
                if existing:
                    existing.value = update.value
                    existing.updated_at = datetime.utcnow()
                else:
                    metric = Metric(
                        workspace_id=workspace_id,
                        metric_id=metric_id,
                        period_date=current_date,
                        value=update.value,
                        source_template='api_update',
                        unit='percentage' if 'rate' in driver_id else None
                    )
                    db.add(metric)
                
                updated_count += 1
                current_date = date(current_date.year, current_date.month + 1, 1)
            
            db.commit()
        
        # Regenerate forecasts if requested
        if update.regenerate_forecast:
            engine = ForecastEngine(workspace_id)
            forecast_results = forecast_metrics_task(workspace_id)
        else:
            forecast_results = None
        
        return {
            'driver_id': driver_id,
            'value': update.value,
            'periods_updated': updated_count,
            'forecast_regenerated': forecast_results is not None
        }
        
    except Exception as e:
        logger.error(f"Error updating driver: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenarios")
async def create_forecast_scenario(
    scenario: ScenarioRequest,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Create a forecast scenario with multiple driver changes
    """
    try:
        # Apply all driver updates
        updated_drivers = []
        
        with get_db_session() as db:
            for driver_update in scenario.drivers:
                metric_id = f"driver_{driver_update.driver_id}"
                period_start = driver_update.period_start or date.today().replace(day=1)
                
                # Update driver value
                existing = db.query(Metric).filter_by(
                    workspace_id=workspace_id,
                    metric_id=metric_id,
                    period_date=period_start
                ).first()
                
                if existing:
                    existing.value = driver_update.value
                    existing.updated_at = datetime.utcnow()
                else:
                    metric = Metric(
                        workspace_id=workspace_id,
                        metric_id=metric_id,
                        period_date=period_start,
                        value=driver_update.value,
                        source_template=f'scenario_{scenario.scenario_name}'
                    )
                    db.add(metric)
                
                updated_drivers.append(driver_update.driver_id)
            
            db.commit()
        
        # Regenerate forecasts
        forecast_results = None
        if scenario.regenerate_forecast:
            forecast_results = forecast_metrics_task(workspace_id, periods_ahead=12)
        
        return {
            'scenario_name': scenario.scenario_name,
            'drivers_updated': updated_drivers,
            'forecast_regenerated': forecast_results is not None,
            'forecast_results': forecast_results
        }
        
    except Exception as e:
        logger.error(f"Error creating scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenarios/compare")
async def compare_scenarios(
    base_scenario: str = Query('current', description="Base scenario name"),
    compare_scenarios: List[str] = Query(..., description="Scenarios to compare"),
    metrics: List[str] = Query(['revenue', 'burn_rate', 'runway_months'], description="Metrics to compare"),
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Compare multiple forecast scenarios
    """
    try:
        comparison = {
            'base_scenario': base_scenario,
            'scenarios': {},
            'metrics': metrics
        }
        
        # For each scenario, get forecast values
        for scenario_name in [base_scenario] + compare_scenarios:
            scenario_data = {}
            
            with get_db_session() as db:
                for metric_id in metrics:
                    # Get forecast values
                    forecast_metric_id = f"forecast_{metric_id}"
                    
                    forecasts = db.query(Metric).filter(
                        Metric.workspace_id == workspace_id,
                        Metric.metric_id == forecast_metric_id,
                        Metric.source_template.like(f'%{scenario_name}%') if scenario_name != 'current' else True
                    ).order_by(Metric.period_date).all()
                    
                    if forecasts:
                        scenario_data[metric_id] = {
                            str(f.period_date): f.value
                            for f in forecasts
                        }
                
            comparison['scenarios'][scenario_name] = scenario_data
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_forecast(
    request: ForecastRequest,
    workspace_id: str = Depends(require_workspace),
    user: dict = Depends(get_current_user)
):
    """
    Generate forecast for specific metrics
    """
    try:
        engine = ForecastEngine(workspace_id)
        
        # Generate forecasts
        if request.metric_ids:
            forecasts = {}
            for metric_id in request.metric_ids:
                forecast = engine.forecast_metric(
                    metric_id,
                    periods_ahead=request.periods_ahead,
                    method=request.method
                )
                if forecast:
                    forecasts[metric_id] = forecast
        else:
            # Forecast all standard metrics
            all_forecasts = engine.forecast_all_metrics(
                periods_ahead=request.periods_ahead
            )
            forecasts = all_forecasts
        
        # Save forecasts
        saved_count = engine.save_forecasts(forecasts)
        
        # Format response
        response = []
        for metric_id, forecast_data in forecasts.items():
            response.append(ForecastResponse(
                metric_id=metric_id,
                forecast_values={
                    str(k): v for k, v in forecast_data.items()
                },
                method_used=request.method
            ))
        
        return {
            'forecasts': response,
            'metrics_forecasted': len(forecasts),
            'data_points_saved': saved_count
        }
        
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-template")
async def download_forecast_template():
    """
    Download the forecast driver template
    """
    template_path = Path("assets/templates/registered/Rolling 12-Month Forecast Template.xlsx")
    
    if not template_path.exists():
        # Provide a basic template
        template_path = Path("assets/templates/forecast_driver_template.xlsx")
    
    if not template_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Forecast template not found"
        )
    
    return FileResponse(
        path=str(template_path),
        filename="forecast_driver_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )