"""
Utility functions for metric store
"""

import calendar
from datetime import date, datetime
from typing import Union

def normalize_period(period: Union[date, datetime, str]) -> date:
    """
    Normalize period to last day of month at 00:00 UTC
    This ensures consistent period dates regardless of timezone
    
    Examples:
        2024-01-15 -> 2024-01-31
        2024-02-01 -> 2024-02-29 (leap year)
        2024-12-25 -> 2024-12-31
    """
    # Convert to date if needed
    if isinstance(period, str):
        # Try to parse ISO format
        if 'T' in period:
            period = datetime.fromisoformat(period.replace('Z', '+00:00')).date()
        else:
            period = date.fromisoformat(period)
    elif isinstance(period, datetime):
        period = period.date()
    
    # Get last day of month
    last_day = calendar.monthrange(period.year, period.month)[1]
    
    # Return normalized date
    return date(period.year, period.month, last_day)

def get_period_range(end_date: date, months: int) -> tuple[date, date]:
    """
    Get start and end dates for a period range
    Returns (start_date, end_date) both normalized to month-end
    
    Example:
        get_period_range(date(2024, 3, 15), 3) -> (date(2023, 12, 31), date(2024, 3, 31))
    """
    end_normalized = normalize_period(end_date)
    
    # Calculate start month
    start_year = end_normalized.year
    start_month = end_normalized.month - months + 1
    
    # Handle year boundary
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    
    # Get last day of start month
    start_day = calendar.monthrange(start_year, start_month)[1]
    start_normalized = date(start_year, start_month, start_day)
    
    return start_normalized, end_normalized

def format_period(period: date) -> str:
    """
    Format period date for display
    Example: 2024-01-31 -> "Jan 2024"
    """
    return period.strftime("%b %Y")

def parse_metric_value(value: Union[str, int, float]) -> float:
    """
    Parse metric value from various formats
    Handles currency symbols, percentages, etc.
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Remove common symbols
        cleaned = value.replace('$', '').replace(',', '').replace('%', '').strip()
        
        # Handle parentheses for negative numbers
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    return 0.0