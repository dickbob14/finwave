"""
Simple forecast engine using ARIMA and CAGR extrapolation
Generates forward-looking metrics based on historical trends
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dateutil.relativedelta import relativedelta

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

from core.database import get_db_session
from metrics.models import Metric
from metrics.utils import normalize_period, get_period_range

logger = logging.getLogger(__name__)

class ForecastEngine:
    """Generate forecasts for financial metrics"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.min_history_points = 6  # Minimum historical points needed
        
    def forecast_metric(self, metric_id: str, periods_ahead: int = 12, 
                       method: str = 'auto') -> Dict[date, float]:
        """
        Forecast a single metric forward
        
        Args:
            metric_id: Metric to forecast
            periods_ahead: Number of periods to forecast (default 12 months)
            method: 'auto', 'arima', 'linear', 'cagr', 'seasonal'
        
        Returns:
            Dict of {period_date: forecasted_value}
        """
        # Fetch historical data
        historical = self._fetch_historical_data(metric_id)
        
        if len(historical) < self.min_history_points:
            logger.warning(f"Insufficient history for {metric_id}: {len(historical)} points")
            return {}
        
        # Convert to series
        dates = [h.period_date for h in historical]
        values = [h.value for h in historical]
        ts = pd.Series(values, index=pd.DatetimeIndex(dates))
        ts = ts.sort_index()
        
        # Choose forecasting method
        if method == 'auto':
            method = self._select_best_method(ts)
        
        # Generate forecast
        if method == 'arima':
            forecast = self._forecast_arima(ts, periods_ahead)
        elif method == 'cagr':
            forecast = self._forecast_cagr(ts, periods_ahead)
        elif method == 'seasonal':
            forecast = self._forecast_seasonal(ts, periods_ahead)
        else:  # linear
            forecast = self._forecast_linear(ts, periods_ahead)
        
        # Convert to period dates
        result = {}
        for i, value in enumerate(forecast):
            # Calculate future period
            last_date = dates[-1]
            future_date = last_date + relativedelta(months=i+1)
            period_date = normalize_period(future_date)
            result[period_date] = value
        
        return result
    
    def _fetch_historical_data(self, metric_id: str) -> List[Metric]:
        """Fetch historical metric data"""
        with get_db_session() as db:
            metrics = db.query(Metric).filter(
                Metric.workspace_id == self.workspace_id,
                Metric.metric_id == metric_id
            ).order_by(Metric.period_date).all()
            
        return metrics
    
    def _select_best_method(self, ts: pd.Series) -> str:
        """Select best forecasting method based on data characteristics"""
        
        # Check for seasonality
        if len(ts) >= 24:  # Need 2+ years for seasonal
            seasonal_strength = self._measure_seasonality(ts)
            if seasonal_strength > 0.5:
                return 'seasonal'
        
        # Check stationarity for ARIMA
        try:
            adf_result = adfuller(ts.values)
            if adf_result[1] < 0.05:  # Stationary
                return 'arima'
        except:
            pass
        
        # Check growth pattern
        if len(ts) >= 12:
            growth_rate = (ts.iloc[-1] / ts.iloc[0]) ** (1/len(ts)) - 1
            if abs(growth_rate) > 0.05:  # Strong growth
                return 'cagr'
        
        # Default to linear
        return 'linear'
    
    def _measure_seasonality(self, ts: pd.Series) -> float:
        """Measure strength of seasonality (0-1)"""
        try:
            # Simple seasonality test using autocorrelation at lag 12
            from statsmodels.tsa.stattools import acf
            acf_values = acf(ts.values, nlags=12)
            return abs(acf_values[12]) if len(acf_values) > 12 else 0
        except:
            return 0
    
    def _forecast_arima(self, ts: pd.Series, periods_ahead: int) -> np.ndarray:
        """ARIMA forecast"""
        try:
            # Fit ARIMA model with auto-selection
            model = ARIMA(ts, order=(1, 1, 1))
            model_fit = model.fit()
            
            # Generate forecast
            forecast = model_fit.forecast(steps=periods_ahead)
            return forecast.values
            
        except Exception as e:
            logger.warning(f"ARIMA failed, falling back to linear: {e}")
            return self._forecast_linear(ts, periods_ahead)
    
    def _forecast_linear(self, ts: pd.Series, periods_ahead: int) -> np.ndarray:
        """Simple linear regression forecast"""
        # Create time index
        x = np.arange(len(ts))
        y = ts.values
        
        # Fit linear regression
        slope, intercept, _, _, _ = stats.linregress(x, y)
        
        # Generate forecast
        future_x = np.arange(len(ts), len(ts) + periods_ahead)
        forecast = slope * future_x + intercept
        
        # Ensure non-negative for certain metrics
        if all(v >= 0 for v in y):
            forecast = np.maximum(forecast, 0)
        
        return forecast
    
    def _forecast_cagr(self, ts: pd.Series, periods_ahead: int) -> np.ndarray:
        """Compound Annual Growth Rate forecast"""
        # Calculate CAGR
        start_value = ts.iloc[0]
        end_value = ts.iloc[-1]
        periods = len(ts) - 1
        
        if start_value <= 0 or end_value <= 0:
            # Fall back to linear for non-positive values
            return self._forecast_linear(ts, periods_ahead)
        
        cagr = (end_value / start_value) ** (1 / periods) - 1
        
        # Apply CAGR forward
        last_value = end_value
        forecast = []
        
        for i in range(periods_ahead):
            next_value = last_value * (1 + cagr)
            forecast.append(next_value)
            last_value = next_value
        
        return np.array(forecast)
    
    def _forecast_seasonal(self, ts: pd.Series, periods_ahead: int) -> np.ndarray:
        """Seasonal decomposition forecast"""
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            
            # Decompose
            decomposition = seasonal_decompose(ts, model='additive', period=12)
            
            # Extract trend and seasonal components
            trend = decomposition.trend.dropna()
            seasonal = decomposition.seasonal
            
            # Forecast trend using linear regression
            x = np.arange(len(trend))
            slope, intercept, _, _, _ = stats.linregress(x, trend.values)
            
            # Generate forecast
            forecast = []
            for i in range(periods_ahead):
                # Trend component
                trend_value = slope * (len(trend) + i) + intercept
                
                # Seasonal component (cycle through historical seasonal pattern)
                seasonal_idx = i % 12
                seasonal_value = seasonal.iloc[seasonal_idx]
                
                forecast_value = trend_value + seasonal_value
                forecast.append(forecast_value)
            
            return np.array(forecast)
            
        except Exception as e:
            logger.warning(f"Seasonal forecast failed, falling back to CAGR: {e}")
            return self._forecast_cagr(ts, periods_ahead)
    
    def forecast_all_metrics(self, metric_ids: Optional[List[str]] = None, 
                           periods_ahead: int = 12) -> Dict[str, Dict[date, float]]:
        """
        Forecast multiple metrics
        
        Returns:
            Dict of {metric_id: {period_date: value}}
        """
        if metric_ids is None:
            # Default to common financial metrics
            metric_ids = [
                'revenue', 'cogs', 'gross_profit', 'opex', 'ebitda', 'net_income',
                'mrr', 'arr', 'new_customers', 'churn_rate', 'burn_rate', 'cash'
            ]
        
        results = {}
        
        for metric_id in metric_ids:
            logger.info(f"Forecasting {metric_id}...")
            forecast = self.forecast_metric(metric_id, periods_ahead)
            
            if forecast:
                # Store with forecast_ prefix
                forecast_metric_id = f"forecast_{metric_id}"
                results[forecast_metric_id] = forecast
                
                # Log summary
                values = list(forecast.values())
                logger.info(f"  Generated {len(values)} periods, "
                          f"range: ${min(values):,.0f} - ${max(values):,.0f}")
        
        return results
    
    def save_forecasts(self, forecasts: Dict[str, Dict[date, float]]) -> int:
        """Save forecasts to metric store"""
        saved_count = 0
        
        with get_db_session() as db:
            for metric_id, period_values in forecasts.items():
                for period_date, value in period_values.items():
                    # Check if exists
                    existing = db.query(Metric).filter_by(
                        workspace_id=self.workspace_id,
                        metric_id=metric_id,
                        period_date=period_date
                    ).first()
                    
                    if existing:
                        existing.value = value
                        existing.source_template = 'forecast_engine'
                        existing.updated_at = datetime.utcnow()
                    else:
                        metric = Metric(
                            workspace_id=self.workspace_id,
                            metric_id=metric_id,
                            period_date=period_date,
                            value=value,
                            source_template='forecast_engine',
                            unit='dollars' if any(x in metric_id for x in ['revenue', 'cost', 'profit']) else None
                        )
                        db.add(metric)
                    
                    saved_count += 1
            
            db.commit()
        
        logger.info(f"Saved {saved_count} forecast data points")
        return saved_count
    
    def calculate_runway(self, burn_rate_override: Optional[float] = None) -> Optional[float]:
        """Calculate months of runway based on cash and burn rate"""
        
        with get_db_session() as db:
            # Get latest cash balance
            cash_metric = db.query(Metric).filter(
                Metric.workspace_id == self.workspace_id,
                Metric.metric_id == 'cash'
            ).order_by(Metric.period_date.desc()).first()
            
            if not cash_metric:
                return None
            
            cash = cash_metric.value
            
            # Get burn rate
            if burn_rate_override:
                burn_rate = burn_rate_override
            else:
                burn_metric = db.query(Metric).filter(
                    Metric.workspace_id == self.workspace_id,
                    Metric.metric_id == 'burn_rate'
                ).order_by(Metric.period_date.desc()).first()
                
                if not burn_metric:
                    # Calculate from net income
                    net_income_metric = db.query(Metric).filter(
                        Metric.workspace_id == self.workspace_id,
                        Metric.metric_id == 'net_income'
                    ).order_by(Metric.period_date.desc()).first()
                    
                    if net_income_metric and net_income_metric.value < 0:
                        burn_rate = abs(net_income_metric.value)
                    else:
                        return None
                else:
                    burn_rate = abs(burn_metric.value)
            
            # Calculate runway
            if burn_rate > 0:
                runway_months = cash / burn_rate
                return runway_months
            
            return None


def forecast_metrics_task(workspace_id: str, periods_ahead: int = 12) -> Dict[str, Any]:
    """
    Task to run metric forecasting
    Can be called by scheduler or API
    """
    engine = ForecastEngine(workspace_id)
    
    # Generate forecasts
    forecasts = engine.forecast_all_metrics(periods_ahead=periods_ahead)
    
    # Save to metric store
    saved_count = engine.save_forecasts(forecasts)
    
    # Calculate runway
    runway = engine.calculate_runway()
    
    result = {
        'workspace_id': workspace_id,
        'metrics_forecasted': len(forecasts),
        'periods_ahead': periods_ahead,
        'data_points_saved': saved_count,
        'runway_months': runway,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Forecast complete for {workspace_id}: {result}")
    return result