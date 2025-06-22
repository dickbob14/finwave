#!/usr/bin/env python3
"""
Variance Watcher Service
Monitors metrics against configured rules and generates alerts
Runs periodically to check for threshold breaches
"""

import logging
import os
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db_session
from metrics.models import Metric
from models.workspace import Workspace
from scheduler.models import Alert, AlertSeverity, AlertStatus
from metrics.utils import normalize_period, get_period_range
from insights.client import InsightEngine

logger = logging.getLogger(__name__)

class VarianceWatcher:
    """Monitor metrics and generate alerts based on variance rules"""
    
    def __init__(self, config_path: str = "config/variance_rules.yml"):
        self.config_path = config_path
        self.rules = []
        self.compound_rules = []
        self.alert_channels = []
        self.settings = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load variance rules from YAML configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            self.rules = config.get('variance_rules', [])
            self.compound_rules = config.get('compound_rules', [])
            self.alert_channels = config.get('alert_channels', [])
            self.settings = config.get('settings', {
                'enabled': True,
                'check_frequency_minutes': 60,
                'lookback_periods': 3,
                'forecast_confidence_interval': 0.8
            })
            
            logger.info(f"Loaded {len(self.rules)} variance rules and "
                       f"{len(self.compound_rules)} compound rules")
            
        except Exception as e:
            logger.error(f"Failed to load variance config: {e}")
            raise
    
    def check_all_workspaces(self) -> Dict[str, List[Alert]]:
        """Check variance rules for all active workspaces"""
        if not self.settings.get('enabled', True):
            logger.info("Variance checking is disabled")
            return {}
        
        results = {}
        
        with get_db_session() as db:
            # Get all active workspaces
            workspaces = db.query(Workspace).filter(
                Workspace.billing_status.in_(['trial', 'active'])
            ).all()
            
            logger.info(f"Checking {len(workspaces)} active workspaces")
            
            for workspace in workspaces:
                try:
                    alerts = self.check_workspace(workspace.id)
                    if alerts:
                        results[workspace.id] = alerts
                        logger.info(f"Generated {len(alerts)} alerts for {workspace.id}")
                except Exception as e:
                    logger.error(f"Error checking workspace {workspace.id}: {e}")
        
        return results
    
    def check_workspace(self, workspace_id: str) -> List[Alert]:
        """Check variance rules for a single workspace"""
        alerts = []
        
        # Check simple rules
        for rule in self.rules:
            alert = self.check_rule(workspace_id, rule)
            if alert:
                alerts.append(alert)
        
        # Check compound rules
        for compound_rule in self.compound_rules:
            alert = self.check_compound_rule(workspace_id, compound_rule)
            if alert:
                alerts.append(alert)
        
        # Save alerts and trigger actions
        if alerts:
            self.save_and_notify_alerts(workspace_id, alerts)
        
        return alerts
    
    def check_rule(self, workspace_id: str, rule: Dict[str, Any]) -> Optional[Alert]:
        """Check a single variance rule"""
        metric_id = rule['metric_id']
        comparison = rule['comparison']
        threshold_type = rule['threshold_type']
        threshold_value = rule['threshold_value']
        direction = rule['direction']
        severity = rule.get('severity', 'warning')
        cooldown_hours = rule.get('cooldown_hours', 24)
        
        # Check if rule is on cooldown
        if self.is_on_cooldown(workspace_id, metric_id, cooldown_hours):
            return None
        
        # Get current metric value
        current = self.get_latest_metric(workspace_id, metric_id)
        if not current:
            logger.debug(f"No current value for {metric_id}")
            return None
        
        # Get comparison value
        if comparison == 'budget':
            comparison_value = self.get_latest_metric(workspace_id, f"budget_{metric_id}")
        elif comparison == 'forecast':
            comparison_value = self.get_latest_metric(workspace_id, f"forecast_{metric_id}")
        elif comparison == 'prior_period':
            comparison_value = self.get_prior_period_metric(workspace_id, metric_id, current.period_date)
        elif comparison == 'absolute':
            comparison_value = None  # Will compare against threshold directly
        else:
            logger.warning(f"Unknown comparison type: {comparison}")
            return None
        
        # Calculate variance
        if comparison == 'absolute':
            # Direct comparison against threshold
            actual_value = current.value
            if direction == 'below' and actual_value < threshold_value:
                variance_triggered = True
            elif direction == 'above' and actual_value > threshold_value:
                variance_triggered = True
            else:
                variance_triggered = False
        else:
            # Compare against another value
            if not comparison_value:
                logger.debug(f"No comparison value for {metric_id} ({comparison})")
                return None
            
            # Calculate variance based on threshold type
            if threshold_type == 'percentage':
                if comparison_value.value == 0:
                    variance_pct = 0
                else:
                    variance_pct = ((current.value - comparison_value.value) / 
                                   abs(comparison_value.value) * 100)
                
                if direction == 'below' and variance_pct < threshold_value:
                    variance_triggered = True
                elif direction == 'above' and variance_pct > threshold_value:
                    variance_triggered = True
                else:
                    variance_triggered = False
                    
            elif threshold_type == 'absolute':
                variance_abs = current.value - comparison_value.value
                
                if direction == 'below' and variance_abs < threshold_value:
                    variance_triggered = True
                elif direction == 'above' and variance_abs > threshold_value:
                    variance_triggered = True
                else:
                    variance_triggered = False
            else:
                logger.warning(f"Unknown threshold type: {threshold_type}")
                return None
        
        # Generate alert if triggered
        if variance_triggered:
            # Format message
            message = rule.get('message', f"{metric_id} variance detected")
            
            # Replace placeholders
            replacements = {
                'current_value': current.value,
                'metric_id': metric_id
            }
            
            if comparison != 'absolute' and comparison_value:
                replacements['comparison_value'] = comparison_value.value
                replacements['variance_pct'] = variance_pct if threshold_type == 'percentage' else 0
                replacements['variance_abs'] = current.value - comparison_value.value
            elif comparison == 'absolute':
                replacements['variance_pct'] = 0
                replacements['variance_abs'] = current.value - threshold_value
            
            try:
                message = message.format(**replacements)
            except:
                pass  # Use default message if formatting fails
            
            # Create alert
            alert = Alert(
                workspace_id=workspace_id,
                metric_id=metric_id,
                rule_name=f"{metric_id}_{comparison}_{direction}",
                severity=AlertSeverity[severity.upper()],
                message=message,
                current_value=current.value,
                threshold_value=threshold_value,
                comparison_value=comparison_value.value if comparison_value else None,
                triggered_at=datetime.utcnow()
            )
            
            return alert
        
        return None
    
    def check_compound_rule(self, workspace_id: str, compound_rule: Dict[str, Any]) -> Optional[Alert]:
        """Check a compound rule with multiple conditions"""
        name = compound_rule['name']
        conditions = compound_rule['conditions']
        severity = compound_rule.get('severity', 'warning')
        cooldown_hours = compound_rule.get('cooldown_hours', 48)
        
        # Check if rule is on cooldown
        if self.is_on_cooldown(workspace_id, name, cooldown_hours):
            return None
        
        # Check all conditions
        all_triggered = True
        condition_results = []
        
        for condition in conditions:
            # Create a temporary rule from the condition
            temp_rule = condition.copy()
            temp_rule['severity'] = 'info'  # Don't create individual alerts
            temp_rule['cooldown_hours'] = 0  # No cooldown for sub-conditions
            
            result = self.check_rule(workspace_id, temp_rule)
            if result:
                condition_results.append({
                    'metric_id': condition['metric_id'],
                    'triggered': True,
                    'value': result.current_value
                })
            else:
                all_triggered = False
                condition_results.append({
                    'metric_id': condition['metric_id'],
                    'triggered': False
                })
        
        # Generate alert if all conditions triggered
        if all_triggered:
            # Format message
            message = compound_rule.get('message', f"Compound rule {name} triggered")
            
            # Create replacements dict with all metric values
            replacements = {}
            for result in condition_results:
                if result['triggered']:
                    replacements[result['metric_id']] = result['value']
            
            try:
                message = message.format(**replacements)
            except:
                pass  # Use default message if formatting fails
            
            # Create alert
            alert = Alert(
                workspace_id=workspace_id,
                metric_id='compound',
                rule_name=name,
                severity=AlertSeverity[severity.upper()],
                message=message,
                triggered_at=datetime.utcnow()
            )
            
            return alert
        
        return None
    
    def get_latest_metric(self, workspace_id: str, metric_id: str) -> Optional[Metric]:
        """Get the latest value for a metric"""
        with get_db_session() as db:
            metric = db.query(Metric).filter(
                Metric.workspace_id == workspace_id,
                Metric.metric_id == metric_id
            ).order_by(Metric.period_date.desc()).first()
            
        return metric
    
    def get_prior_period_metric(self, workspace_id: str, metric_id: str, 
                               current_period: date) -> Optional[Metric]:
        """Get the metric value from the prior period"""
        # Calculate prior period (usually prior month)
        prior_period = current_period - timedelta(days=30)  # Approximate
        prior_period = normalize_period(prior_period)
        
        with get_db_session() as db:
            metric = db.query(Metric).filter(
                Metric.workspace_id == workspace_id,
                Metric.metric_id == metric_id,
                Metric.period_date <= prior_period
            ).order_by(Metric.period_date.desc()).first()
            
        return metric
    
    def is_on_cooldown(self, workspace_id: str, rule_name: str, 
                      cooldown_hours: int) -> bool:
        """Check if a rule is on cooldown"""
        if cooldown_hours <= 0:
            return False
        
        with get_db_session() as db:
            # Check for recent alerts from this rule
            cutoff_time = datetime.utcnow() - timedelta(hours=cooldown_hours)
            
            recent_alert = db.query(Alert).filter(
                Alert.workspace_id == workspace_id,
                Alert.rule_name == rule_name,
                Alert.triggered_at >= cutoff_time
            ).first()
            
            return recent_alert is not None
    
    def save_and_notify_alerts(self, workspace_id: str, alerts: List[Alert]) -> None:
        """Save alerts to database and trigger notifications"""
        with get_db_session() as db:
            for alert in alerts:
                db.add(alert)
            db.commit()
        
        # Send to enabled channels
        for channel in self.alert_channels:
            if channel.get('enabled', False):
                self.send_to_channel(workspace_id, alerts, channel)
        
        # Trigger insight regeneration for critical alerts
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            self.trigger_insight_update(workspace_id, critical_alerts)
    
    def send_to_channel(self, workspace_id: str, alerts: List[Alert], 
                       channel: Dict[str, Any]) -> None:
        """Send alerts to a specific channel"""
        channel_type = channel['type']
        
        if channel_type == 'database':
            # Already saved
            pass
        elif channel_type == 'email':
            # TODO: Implement email notifications
            logger.info(f"Would send {len(alerts)} alerts via email")
        elif channel_type == 'slack':
            # TODO: Implement Slack notifications
            logger.info(f"Would send {len(alerts)} alerts to Slack")
        elif channel_type == 'webhook':
            # TODO: Implement webhook notifications
            logger.info(f"Would send {len(alerts)} alerts to webhook")
    
    def trigger_insight_update(self, workspace_id: str, alerts: List[Alert]) -> None:
        """Trigger insight engine to regenerate commentary"""
        try:
            engine = InsightEngine(workspace_id)
            
            # Generate alert-specific context
            alert_context = []
            for alert in alerts:
                alert_context.append({
                    'metric': alert.metric_id,
                    'message': alert.message,
                    'severity': alert.severity.value,
                    'timestamp': alert.triggered_at.isoformat()
                })
            
            # Request insight update with alert context
            result = engine.generate_insights(
                template_name='alerts',
                custom_context={'alerts': alert_context}
            )
            
            logger.info(f"Triggered insight update for {len(alerts)} critical alerts")
            
        except Exception as e:
            logger.error(f"Failed to trigger insight update: {e}")


def run_variance_check():
    """Main entry point for variance checking"""
    logger.info("Starting variance check run")
    
    try:
        watcher = VarianceWatcher()
        results = watcher.check_all_workspaces()
        
        # Log summary
        total_alerts = sum(len(alerts) for alerts in results.values())
        logger.info(f"Variance check complete: {total_alerts} alerts across "
                   f"{len(results)} workspaces")
        
        return results
        
    except Exception as e:
        logger.error(f"Variance check failed: {e}")
        raise


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run check
    results = run_variance_check()
    
    # Print summary
    for workspace_id, alerts in results.items():
        print(f"\n{workspace_id}:")
        for alert in alerts:
            print(f"  - [{alert.severity.value}] {alert.message}")