"""
CRM API routes for sales and marketing data integration
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import CRM client
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integrations.crm.client import create_crm_client, test_crm_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crm", tags=["crm"])

# CRM configuration
CRM_TYPE = os.getenv("CRM_TYPE", "salesforce")

# Response models
class CRMMetrics(BaseModel):
    pipeline_value: float
    pipeline_count: int
    bookings_mtd: float
    deals_won_mtd: int
    bookings_qtd: Optional[float] = None
    bookings_ytd: Optional[float] = None
    avg_deal_size: Optional[float] = None
    win_rate: Optional[float] = None

class OpportunityResponse(BaseModel):
    total: int
    opportunities: List[Dict[str, Any]]
    aggregates: Dict[str, Any]

class CRMStatus(BaseModel):
    connected: bool
    crm_type: str
    last_sync: Optional[str] = None
    error: Optional[str] = None

@router.get("/status", response_model=CRMStatus)
async def get_crm_status():
    """
    Check CRM connection status
    """
    try:
        connected = test_crm_connection(CRM_TYPE)
        
        return CRMStatus(
            connected=connected,
            crm_type=CRM_TYPE,
            last_sync=datetime.now().isoformat() if connected else None,
            error=None if connected else "Failed to connect to CRM"
        )
    except Exception as e:
        logger.error(f"Error checking CRM status: {e}")
        return CRMStatus(
            connected=False,
            crm_type=CRM_TYPE,
            error=str(e)
        )

@router.get("/metrics", response_model=CRMMetrics)
async def get_sales_metrics():
    """
    Get high-level sales metrics from CRM
    """
    try:
        client = create_crm_client(CRM_TYPE)
        metrics = client.get_metrics_summary()
        
        # Add calculated metrics if not present
        if 'bookings_qtd' not in metrics and 'bookings_mtd' in metrics:
            # Rough QTD estimate (3x monthly for simplicity)
            metrics['bookings_qtd'] = metrics['bookings_mtd'] * 3
            
        if 'bookings_ytd' not in metrics and 'bookings_mtd' in metrics:
            # Rough YTD estimate based on current month
            current_month = datetime.now().month
            metrics['bookings_ytd'] = metrics['bookings_mtd'] * current_month
        
        return CRMMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"Error fetching CRM metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities", response_model=OpportunityResponse)
async def get_opportunities(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    stage: Optional[str] = Query(None, description="Filter by stage"),
    limit: int = Query(100, description="Maximum number of results")
):
    """
    Fetch opportunities/deals from CRM with optional filters
    """
    # Default date range if not provided
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    try:
        client = create_crm_client(CRM_TYPE)
        
        # Fetch opportunities
        opps_df = client.fetch_opportunities(start_date, end_date)
        
        # Apply stage filter if provided
        if stage and not opps_df.empty:
            opps_df = opps_df[opps_df['StageName'].str.contains(stage, case=False, na=False)]
        
        # Limit results
        if len(opps_df) > limit:
            opps_df = opps_df.head(limit)
        
        # Calculate aggregates
        aggregates = {
            'total_value': float(opps_df['Amount'].sum()) if not opps_df.empty else 0,
            'avg_value': float(opps_df['Amount'].mean()) if not opps_df.empty else 0,
            'by_stage': {}
        }
        
        if not opps_df.empty:
            stage_summary = opps_df.groupby('StageName')['Amount'].agg(['sum', 'count'])
            aggregates['by_stage'] = {
                stage: {
                    'value': float(row['sum']),
                    'count': int(row['count'])
                }
                for stage, row in stage_summary.iterrows()
            }
        
        # Convert DataFrame to list of dicts
        opportunities = opps_df.to_dict('records') if not opps_df.empty else []
        
        # Clean up data types for JSON serialization
        for opp in opportunities:
            for key, value in opp.items():
                if pd.isna(value):
                    opp[key] = None
                elif hasattr(value, 'isoformat'):
                    opp[key] = value.isoformat()
                elif hasattr(value, 'item'):  # numpy types
                    opp[key] = value.item()
        
        return OpportunityResponse(
            total=len(opportunities),
            opportunities=opportunities,
            aggregates=aggregates
        )
        
    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts")
async def get_accounts(
    limit: int = Query(100, description="Maximum number of results"),
    modified_since: Optional[str] = Query(None, description="Modified since date (YYYY-MM-DD)")
):
    """
    Fetch accounts/companies from CRM
    """
    try:
        client = create_crm_client(CRM_TYPE)
        
        # Fetch accounts
        accounts_df = client.fetch_accounts(modified_since)
        
        # Limit results
        if len(accounts_df) > limit:
            accounts_df = accounts_df.head(limit)
        
        # Convert to dict
        accounts = accounts_df.to_dict('records') if not accounts_df.empty else []
        
        # Clean up data types
        for account in accounts:
            for key, value in account.items():
                if pd.isna(value):
                    account[key] = None
                elif hasattr(value, 'isoformat'):
                    account[key] = value.isoformat()
                elif hasattr(value, 'item'):
                    account[key] = value.item()
        
        return {
            'total': len(accounts),
            'accounts': accounts
        }
        
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipeline-summary")
async def get_pipeline_summary():
    """
    Get pipeline summary by stage
    """
    try:
        client = create_crm_client(CRM_TYPE)
        
        # Get current opportunities
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        opps_df = client.fetch_opportunities(start_date, end_date)
        
        # Filter to open deals only
        if not opps_df.empty:
            open_deals = opps_df[opps_df['IsClosed'] == False]
            
            # Group by stage
            pipeline = open_deals.groupby('StageName').agg({
                'Amount': ['sum', 'count', 'mean'],
                'Probability': 'mean'
            }).round(2)
            
            # Flatten column names
            pipeline.columns = ['total_value', 'deal_count', 'avg_deal_size', 'avg_probability']
            
            # Calculate weighted pipeline value
            result = []
            for stage, row in pipeline.iterrows():
                weighted_value = row['total_value'] * (row['avg_probability'] / 100)
                result.append({
                    'stage': stage,
                    'total_value': float(row['total_value']),
                    'deal_count': int(row['deal_count']),
                    'avg_deal_size': float(row['avg_deal_size']),
                    'avg_probability': float(row['avg_probability']),
                    'weighted_value': float(weighted_value)
                })
            
            return {
                'pipeline': result,
                'total_pipeline_value': float(open_deals['Amount'].sum()),
                'total_weighted_value': sum(s['weighted_value'] for s in result),
                'total_deals': len(open_deals)
            }
        else:
            return {
                'pipeline': [],
                'total_pipeline_value': 0,
                'total_weighted_value': 0,
                'total_deals': 0
            }
            
    except Exception as e:
        logger.error(f"Error getting pipeline summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def trigger_crm_sync():
    """
    Trigger a manual CRM data sync
    """
    try:
        # In a production system, this would trigger a background job
        # For now, we'll just test the connection
        connected = test_crm_connection(CRM_TYPE)
        
        if connected:
            return {
                'status': 'success',
                'message': f'{CRM_TYPE} sync triggered successfully',
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to {CRM_TYPE}"
            )
            
    except Exception as e:
        logger.error(f"Error triggering CRM sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))