"""
Metric ingestion from Excel templates
Extracts named ranges and persists to metric store
"""

import argparse
import logging
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.workbook.defined_name import DefinedName
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.models import Metric, ALL_METRICS, METRIC_METADATA
from metrics.utils import normalize_period
from core.database import get_db_session, engine

logger = logging.getLogger(__name__)

# Metric store configuration - now unified via DATABASE_URL
def get_metric_engine():
    """Get appropriate engine based on DATABASE_URL"""
    # Just use the main engine from core.database
    return engine

def extract_named_ranges(workbook: Workbook) -> Dict[str, Tuple[str, Any]]:
    """
    Extract named ranges from Excel workbook
    Returns dict of {range_name: (sheet_name, cell_reference)}
    """
    named_ranges = {}
    
    for defined_name in workbook.defined_names.definedName:
        # Skip print areas and other special ranges
        if defined_name.name.startswith('_xlnm'):
            continue
            
        # Parse the range reference
        # Format: 'SheetName'!$A$1 or SheetName!$A$1:$B$2
        destinations = list(defined_name.destinations)
        
        if destinations:
            sheet_name, cell_ref = destinations[0]
            # Remove absolute references
            cell_ref = cell_ref.replace('$', '')
            named_ranges[defined_name.name] = (sheet_name, cell_ref)
            logger.debug(f"Found named range: {defined_name.name} -> {sheet_name}!{cell_ref}")
    
    return named_ranges

def get_cell_value(workbook: Workbook, sheet_name: str, cell_ref: str) -> Optional[float]:
    """
    Get numeric value from a cell or range
    For ranges, returns the sum of all numeric values
    """
    try:
        sheet = workbook[sheet_name]
        
        # Check if it's a single cell or range
        if ':' in cell_ref:
            # It's a range - sum all numeric values
            total = 0.0
            for row in sheet[cell_ref]:
                for cell in row:
                    if isinstance(cell.value, (int, float)):
                        total += float(cell.value)
            return total
        else:
            # Single cell
            cell = sheet[cell_ref]
            if isinstance(cell.value, (int, float)):
                return float(cell.value)
            else:
                logger.warning(f"Non-numeric value in {sheet_name}!{cell_ref}: {cell.value}")
                return None
                
    except Exception as e:
        logger.error(f"Error reading {sheet_name}!{cell_ref}: {e}")
        return None

def extract_period_from_workbook(workbook: Workbook) -> Optional[date]:
    """
    Extract period date from workbook
    Looks for named ranges or metadata cells
    """
    # Try common named ranges first
    period_names = ['period_date', 'report_date', 'as_of_date', 'month_end']
    named_ranges = extract_named_ranges(workbook)
    
    for period_name in period_names:
        if period_name in named_ranges:
            sheet_name, cell_ref = named_ranges[period_name]
            try:
                sheet = workbook[sheet_name]
                cell_value = sheet[cell_ref].value
                if isinstance(cell_value, datetime):
                    return cell_value.date()
                elif isinstance(cell_value, date):
                    return cell_value
            except:
                pass
    
    # Fallback: look for date in specific cells
    try:
        # Common locations for report dates
        for sheet_name in ['Summary', 'Dashboard', 'P&L', 'Income Statement']:
            if sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                # Check cells like B1, B2, etc.
                for row in range(1, 5):
                    for col in ['A', 'B', 'C']:
                        cell = sheet[f'{col}{row}']
                        if isinstance(cell.value, (datetime, date)):
                            return cell.value if isinstance(cell.value, date) else cell.value.date()
    except:
        pass
    
    # Default to month-end of current month
    today = datetime.now()
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    
    # Last day of current month
    period_date = date(next_month.year, next_month.month, 1) - timedelta(days=1)
    logger.warning(f"Could not extract period date, using month-end: {period_date}")
    
    return period_date

def ingest_metrics(workspace_id: str, excel_path: str, period_date: Optional[date] = None) -> Dict[str, int]:
    """
    Ingest metrics from Excel file into metric store
    
    Returns dict with counts: {'extracted': n, 'inserted': n, 'updated': n}
    """
    logger.info(f"Ingesting metrics from {excel_path} for workspace {workspace_id}")
    
    # Load workbook
    workbook = openpyxl.load_workbook(excel_path, data_only=True)
    
    # Extract period if not provided
    if not period_date:
        period_date = extract_period_from_workbook(workbook)
    
    # Normalize period to month-end
    period_date = normalize_period(period_date)
    logger.info(f"Using normalized period date: {period_date}")
    
    # Extract named ranges
    named_ranges = extract_named_ranges(workbook)
    
    # Map of expected range names to metric IDs
    range_to_metric = {
        'rng_revenue': 'revenue',
        'rng_cogs': 'cogs',
        'rng_gross_profit': 'gross_profit',
        'rng_opex': 'opex',
        'rng_ebitda': 'ebitda',
        'rng_net_income': 'net_income',
        'rng_cash': 'cash',
        'rng_total_assets': 'total_assets',
        'rng_total_liabilities': 'total_liabilities',
        'rng_total_equity': 'total_equity',
        'rng_mrr': 'mrr',
        'rng_arr': 'arr',
        'rng_new_customers': 'new_customers',
        'rng_churn_rate': 'churn_rate',
        'rng_headcount': 'headcount',
        'rng_burn_rate': 'burn_rate'
    }
    
    # Also try without prefix
    for metric_id in ALL_METRICS:
        if metric_id not in range_to_metric.values():
            range_to_metric[metric_id] = metric_id
    
    # Extract metrics
    metrics_data = []
    extracted_count = 0
    
    for range_name, metric_id in range_to_metric.items():
        if range_name in named_ranges:
            sheet_name, cell_ref = named_ranges[range_name]
            value = get_cell_value(workbook, sheet_name, cell_ref)
            
            if value is not None:
                # Get metadata
                metadata = METRIC_METADATA.get(metric_id, {})
                
                metrics_data.append({
                    'workspace_id': workspace_id,
                    'metric_id': metric_id,
                    'period_date': period_date,
                    'value': value,
                    'source_template': Path(excel_path).name,
                    'unit': metadata.get('unit', None)
                })
                extracted_count += 1
                logger.debug(f"Extracted {metric_id}: {value}")
    
    # Get database session
    metric_engine = get_metric_engine()
    SessionLocal = sessionmaker(bind=metric_engine)
    
    inserted_count = 0
    updated_count = 0
    
    with SessionLocal() as session:
        try:
            if METRIC_STORE == "postgres":
                # PostgreSQL: Use INSERT ... ON CONFLICT
                for data in metrics_data:
                    stmt = pg_insert(Metric).values(**data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['workspace_id', 'metric_id', 'period_date'],
                        set_={
                            'value': stmt.excluded.value,
                            'source_template': stmt.excluded.source_template,
                            'updated_at': datetime.utcnow()
                        }
                    )
                    
                    result = session.execute(stmt)
                    if result.rowcount > 0:
                        inserted_count += 1
                    
            else:
                # DuckDB or SQLite: Manual upsert
                for data in metrics_data:
                    existing = session.query(Metric).filter_by(
                        workspace_id=data['workspace_id'],
                        metric_id=data['metric_id'],
                        period_date=data['period_date']
                    ).first()
                    
                    if existing:
                        # Update
                        existing.value = data['value']
                        existing.source_template = data['source_template']
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Insert
                        metric = Metric(**data)
                        session.add(metric)
                        inserted_count += 1
            
            session.commit()
            logger.info(f"Successfully ingested {extracted_count} metrics ({inserted_count} new, {updated_count} updated)")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to ingest metrics: {e}")
            raise
    
    return {
        'extracted': extracted_count,
        'inserted': inserted_count,
        'updated': updated_count
    }

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Ingest metrics from Excel templates')
    parser.add_argument('--workspace', required=True, help='Workspace ID')
    parser.add_argument('--file', required=True, help='Path to Excel file')
    parser.add_argument('--period', help='Period date (YYYY-MM-DD), defaults to auto-detect')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse period date if provided
    period_date = None
    if args.period:
        try:
            period_date = datetime.strptime(args.period, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.period}. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Check if file exists
    if not Path(args.file).exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    try:
        # Run ingestion
        results = ingest_metrics(args.workspace, args.file, period_date)
        
        logger.info(f"Metric ingestion complete: extracted={results['extracted']}, inserted={results['inserted']}, updated={results['updated']}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()