#!/usr/bin/env python3
"""
Test Stage 4: Forecasting & Variance Alerts
"""

import unittest
import os
import sys
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.engine import ForecastEngine
from scheduler.variance_watcher import VarianceWatcher
from scheduler.models import Alert, AlertSeverity, AlertStatus
from metrics.models import Metric
from core.database import get_db_session, init_db


class TestStage4(unittest.TestCase):
    """Test forecasting and variance alert functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test database"""
        os.environ['DATABASE_URL'] = 'sqlite:///test_stage4.db'
        init_db()
        
    def setUp(self):
        """Setup for each test"""
        self.workspace_id = "test-workspace"
        self.setup_test_metrics()
        
    def setup_test_metrics(self):
        """Create test metrics in database"""
        with get_db_session() as db:
            # Clean up existing test data
            db.query(Metric).filter_by(workspace_id=self.workspace_id).delete()
            db.query(Alert).filter_by(workspace_id=self.workspace_id).delete()
            
            # Create historical revenue data
            base_date = date(2024, 1, 1)
            revenue_values = [100000, 105000, 110000, 108000, 115000, 120000,
                            125000, 130000, 128000, 135000, 140000, 145000]
            
            for i, value in enumerate(revenue_values):
                metric = Metric(
                    workspace_id=self.workspace_id,
                    metric_id='revenue',
                    period_date=base_date.replace(month=i+1),
                    value=value,
                    source_template='test'
                )
                db.add(metric)
            
            # Create budget data
            budget_values = [105000, 110000, 115000, 120000, 125000, 130000,
                           135000, 140000, 145000, 150000, 155000, 160000]
            
            for i, value in enumerate(budget_values):
                metric = Metric(
                    workspace_id=self.workspace_id,
                    metric_id='budget_revenue',
                    period_date=base_date.replace(month=i+1),
                    value=value,
                    source_template='test'
                )
                db.add(metric)
            
            # Create burn rate data
            burn_values = [50000, 52000, 54000, 56000, 58000, 60000]
            
            for i, value in enumerate(burn_values):
                metric = Metric(
                    workspace_id=self.workspace_id,
                    metric_id='burn_rate',
                    period_date=base_date.replace(month=i+1),
                    value=value,
                    source_template='test'
                )
                db.add(metric)
            
            # Add cash balance
            metric = Metric(
                workspace_id=self.workspace_id,
                metric_id='cash',
                period_date=date(2024, 12, 1),
                value=1000000,
                source_template='test'
            )
            db.add(metric)
            
            db.commit()
    
    def test_forecast_engine_initialization(self):
        """Test forecast engine can be initialized"""
        engine = ForecastEngine(self.workspace_id)
        self.assertEqual(engine.workspace_id, self.workspace_id)
        self.assertEqual(engine.min_history_points, 6)
    
    def test_forecast_revenue(self):
        """Test revenue forecasting"""
        engine = ForecastEngine(self.workspace_id)
        
        # Generate 6-month forecast
        forecast = engine.forecast_metric('revenue', periods_ahead=6)
        
        # Should have 6 forecast points
        self.assertEqual(len(forecast), 6)
        
        # Values should be reasonable (growing trend)
        values = list(forecast.values())
        self.assertTrue(all(v > 100000 for v in values))
        self.assertTrue(values[-1] > values[0])  # Growing trend
        
        # Dates should be future months
        dates = list(forecast.keys())
        self.assertTrue(all(d > date(2024, 12, 1) for d in dates))
    
    def test_forecast_methods(self):
        """Test different forecasting methods"""
        engine = ForecastEngine(self.workspace_id)
        
        # Test each method
        methods = ['linear', 'cagr', 'arima']
        
        for method in methods:
            forecast = engine.forecast_metric('revenue', periods_ahead=3, method=method)
            self.assertGreater(len(forecast), 0, f"{method} should produce forecast")
    
    def test_runway_calculation(self):
        """Test runway calculation"""
        engine = ForecastEngine(self.workspace_id)
        
        # Calculate runway
        runway = engine.calculate_runway()
        
        # Should have runway based on cash and burn rate
        self.assertIsNotNone(runway)
        self.assertGreater(runway, 0)
        
        # With 1M cash and ~60k burn, should be ~16 months
        self.assertGreater(runway, 10)
        self.assertLess(runway, 20)
    
    def test_variance_watcher_initialization(self):
        """Test variance watcher can be initialized"""
        watcher = VarianceWatcher("config/variance_rules.yml")
        
        # Should load rules
        self.assertGreater(len(watcher.rules), 0)
        self.assertTrue(watcher.settings['enabled'])
    
    def test_variance_detection(self):
        """Test variance detection for revenue below budget"""
        # Create a recent metric below budget
        with get_db_session() as db:
            metric = Metric(
                workspace_id=self.workspace_id,
                metric_id='revenue',
                period_date=date(2024, 12, 31),
                value=150000,  # Actual
                source_template='test'
            )
            db.add(metric)
            
            budget = Metric(
                workspace_id=self.workspace_id,
                metric_id='budget_revenue',
                period_date=date(2024, 12, 31),
                value=165000,  # Budget (10% higher)
                source_template='test'
            )
            db.add(budget)
            db.commit()
        
        # Check variance
        watcher = VarianceWatcher()
        
        # Find revenue below budget rule
        revenue_rule = None
        for rule in watcher.rules:
            if (rule['metric_id'] == 'revenue' and 
                rule['comparison'] == 'budget' and
                rule['direction'] == 'below'):
                revenue_rule = rule
                break
        
        self.assertIsNotNone(revenue_rule)
        
        # Check the rule
        alert = watcher.check_rule(self.workspace_id, revenue_rule)
        
        # Should trigger alert (revenue is ~9% below budget)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.metric_id, 'revenue')
        self.assertIn('below budget', alert.message)
    
    def test_alert_cooldown(self):
        """Test alert cooldown period"""
        watcher = VarianceWatcher()
        
        # Create an existing alert
        with get_db_session() as db:
            alert = Alert(
                workspace_id=self.workspace_id,
                metric_id='revenue',
                rule_name='revenue_budget_below',
                severity=AlertSeverity.WARNING.value,
                message='Test alert',
                triggered_at=datetime.utcnow() - timedelta(hours=12)
            )
            db.add(alert)
            db.commit()
        
        # Check if on cooldown (24 hour cooldown)
        is_cooldown = watcher.is_on_cooldown(
            self.workspace_id,
            'revenue_budget_below',
            cooldown_hours=24
        )
        
        self.assertTrue(is_cooldown)
        
        # Check with shorter cooldown
        is_cooldown = watcher.is_on_cooldown(
            self.workspace_id,
            'revenue_budget_below',
            cooldown_hours=6
        )
        
        self.assertFalse(is_cooldown)
    
    def test_forecast_save_and_retrieve(self):
        """Test saving forecasts to metric store"""
        engine = ForecastEngine(self.workspace_id)
        
        # Generate and save forecasts
        forecasts = engine.forecast_all_metrics(metric_ids=['revenue'], periods_ahead=3)
        saved_count = engine.save_forecasts(forecasts)
        
        self.assertGreater(saved_count, 0)
        
        # Retrieve forecast metrics
        with get_db_session() as db:
            forecast_metrics = db.query(Metric).filter(
                Metric.workspace_id == self.workspace_id,
                Metric.metric_id == 'forecast_revenue'
            ).all()
            
            self.assertEqual(len(forecast_metrics), 3)
            self.assertTrue(all(m.source_template == 'forecast_engine' for m in forecast_metrics))
    
    def test_populate_forecast_data(self):
        """Test budget/forecast data population"""
        from templates.populate_forecast import ForecastPopulator
        
        # Create test template
        template_path = 'test_budget_template.xlsx'
        
        # Mock the template loading and extraction
        populator = ForecastPopulator(template_path)
        populator.budget_metrics = {
            'budget_revenue': {
                date(2025, 1, 1): 170000,
                date(2025, 2, 1): 175000,
                date(2025, 3, 1): 180000
            },
            'budget_opex': {
                date(2025, 1, 1): 120000,
                date(2025, 2, 1): 125000,
                date(2025, 3, 1): 130000
            }
        }
        
        # Ingest budget metrics
        results = populator.ingest_budget_metrics(self.workspace_id, populator.budget_metrics)
        
        self.assertEqual(results['ingested'], 6)
        
        # Verify metrics were saved
        with get_db_session() as db:
            budget_revenue = db.query(Metric).filter(
                Metric.workspace_id == self.workspace_id,
                Metric.metric_id == 'budget_revenue',
                Metric.period_date == date(2025, 1, 1)
            ).first()
            
            self.assertIsNotNone(budget_revenue)
            self.assertEqual(budget_revenue.value, 170000)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup test database"""
        if os.path.exists('test_stage4.db'):
            os.remove('test_stage4.db')


if __name__ == '__main__':
    unittest.main()