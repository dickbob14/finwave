"""
Background scheduler for automated template refresh
Can be run as a standalone process or integrated with FastAPI
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import time

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from templates.template_manager import TemplateManager, TEMPLATE_REGISTRY
from integrations.quickbooks.client import test_connection

logger = logging.getLogger(__name__)

class TemplateScheduler:
    """Manages scheduled template refreshes"""
    
    def __init__(self):
        self.template_manager = TemplateManager(os.getenv('COMPANY_SLUG', 'demo_corp'))
        self.jobs = []
        
    def refresh_template(self, template_name: str, **kwargs):
        """Refresh a single template"""
        try:
            logger.info(f"Starting scheduled refresh for {template_name}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=kwargs.get('days_back', 30))
            
            # Include prior year for variance templates
            include_py = kwargs.get('include_prior_year', True)
            
            # Run population
            result = self.template_manager.populate_template(
                template_name,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                sheet_id=kwargs.get('sheet_id')
            )
            
            logger.info(f"✅ Successfully refreshed {template_name}")
            
            # Optional: Send notification
            if kwargs.get('notify_slack'):
                self._send_slack_notification(template_name, result)
                
        except Exception as e:
            logger.error(f"❌ Failed to refresh {template_name}: {e}")
            # Optional: Send error notification
    
    def _send_slack_notification(self, template_name: str, result: Dict):
        """Send Slack notification (implement based on your Slack setup)"""
        # Example implementation
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if webhook_url:
            import requests
            config = TEMPLATE_REGISTRY.get(template_name)
            
            message = {
                "text": f"✅ {config.title} refreshed successfully",
                "attachments": [{
                    "color": "good",
                    "fields": [
                        {"title": "Template", "value": config.title, "short": True},
                        {"title": "Generated", "value": datetime.now().strftime('%Y-%m-%d %H:%M'), "short": True}
                    ]
                }]
            }
            
            try:
                requests.post(webhook_url, json=message)
            except:
                logger.warning("Failed to send Slack notification")
    
    def schedule_all_templates(self):
        """Schedule all templates based on their refresh frequency"""
        
        for name, config in TEMPLATE_REGISTRY.items():
            frequency = config.refresh_frequency.value
            
            if frequency == 'hourly':
                schedule.every().hour.do(self.refresh_template, name)
                logger.info(f"Scheduled {name} to run hourly")
                
            elif frequency == 'daily':
                # Run at 6 AM
                schedule.every().day.at("06:00").do(self.refresh_template, name)
                logger.info(f"Scheduled {name} to run daily at 6 AM")
                
            elif frequency == 'weekly':
                # Run on Mondays at 6 AM
                schedule.every().monday.at("06:00").do(self.refresh_template, name)
                logger.info(f"Scheduled {name} to run weekly on Mondays")
                
            elif frequency == 'monthly':
                # For monthly, we'll check daily and run on the 1st
                def monthly_check(template_name):
                    if datetime.now().day == 1:
                        self.refresh_template(template_name)
                
                schedule.every().day.at("06:00").do(monthly_check, name)
                logger.info(f"Scheduled {name} to run monthly on the 1st")
    
    def run_forever(self):
        """Run the scheduler forever"""
        logger.info("🕐 Template scheduler started")
        
        # Test QuickBooks connection first
        if not test_connection():
            logger.error("QuickBooks connection failed. Please check credentials.")
            return
        
        # Schedule all templates
        self.schedule_all_templates()
        
        # Run the schedule
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


# FastAPI Background Task Integration
async def refresh_template_async(template_name: str, **kwargs):
    """Async version for FastAPI background tasks"""
    scheduler = TemplateScheduler()
    
    # Run in thread pool to avoid blocking
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(scheduler.refresh_template, template_name, **kwargs)
        return future.result()


# Standalone CLI
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='FinWave Template Scheduler')
    parser.add_argument('command', choices=['run', 'once', 'list'],
                        help='Command to execute')
    parser.add_argument('--template', help='Template name for once command')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scheduler = TemplateScheduler()
    
    if args.command == 'run':
        # Run forever
        scheduler.run_forever()
        
    elif args.command == 'once':
        # Run single template once
        if not args.template:
            print("Error: --template required for once command")
            exit(1)
            
        scheduler.refresh_template(args.template)
        
    elif args.command == 'list':
        # List scheduled templates
        print("\n📅 Scheduled Templates:")
        print("=" * 60)
        
        for name, config in TEMPLATE_REGISTRY.items():
            print(f"\n{config.title}")
            print(f"  Name: {name}")
            print(f"  Frequency: {config.refresh_frequency.value}")
            print(f"  Delivery: {', '.join([m.value for m in config.delivery_methods])}")