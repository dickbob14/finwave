"""
FinWave Template Manager
Handles template versioning, storage, and automated population
Following the finance-as-code playbook pattern
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class RefreshFrequency(Enum):
    """Template refresh frequency options"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"
    CLOSE_TRIGGERED = "close_triggered"

class DeliveryMethod(Enum):
    """How templates are delivered to users"""
    GOOGLE_SHEETS = "google_sheets"
    EXCEL_DOWNLOAD = "excel_download"
    EMAIL_ATTACHMENT = "email_attachment"
    S3_ARCHIVE = "s3_archive"
    SLACK_POST = "slack_post"

class TemplateConfig:
    """Configuration for a financial template"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.name = config_dict['name']
        self.title = config_dict['title']
        self.description = config_dict['description']
        self.template_file = config_dict['template_file']
        self.populator_script = config_dict['populator_script']
        self.refresh_frequency = RefreshFrequency(config_dict['refresh_frequency'])
        self.delivery_methods = [DeliveryMethod(m) for m in config_dict['delivery_methods']]
        self.use_case = config_dict['use_case']
        self.version = config_dict.get('version', '1.0.0')
        self.schema = config_dict.get('schema', {})

# Template registry following the playbook patterns
TEMPLATE_REGISTRY = {
    "3_statement_model": TemplateConfig({
        "name": "3_statement_model",
        "title": "Basic 3-Statement Model",
        "description": "Income Statement, Balance Sheet, and Cash Flow with monthly/quarterly views",
        "template_file": "Basic 3-Statement Model-2.xlsx",
        "populator_script": "populate_3statement.py",
        "refresh_frequency": RefreshFrequency.MONTHLY.value,
        "delivery_methods": [DeliveryMethod.EXCEL_DOWNLOAD.value, DeliveryMethod.EMAIL_ATTACHMENT.value],
        "use_case": "Month-end close - 3-statement + board pack",
        "version": "2024.06",
        "schema": {
            "data_sources": ["quickbooks_gl", "quickbooks_tb"],
            "output_sheets": ["Income Statement", "Balance Sheet", "Cash Flow"]
        }
    }),
    
    "kpi_dashboard": TemplateConfig({
        "name": "kpi_dashboard",
        "title": "Executive KPI Dashboard",
        "description": "Multi-dimensional KPIs with entity/department/product breakdowns",
        "template_file": "Cube - KPI Dashboard-1.xlsx",
        "populator_script": "populate_kpi_dashboard.py",
        "refresh_frequency": RefreshFrequency.DAILY.value,
        "delivery_methods": [DeliveryMethod.GOOGLE_SHEETS.value],
        "use_case": "Day-to-day ops - dashboards, tactical variance checks",
        "version": "2024.06",
        "schema": {
            "data_sources": ["quickbooks", "salesforce", "hubspot", "hris"],
            "dimensions": ["Entity", "Department", "Product", "Market"],
            "metrics": ["Revenue", "Orders", "Customers", "OpEx", "Headcount"]
        }
    }),
    
    "budget_vs_actual": TemplateConfig({
        "name": "budget_vs_actual",
        "title": "Budget vs Actual Rolling Forecast",
        "description": "Variance analysis with driver-based forecasting",
        "template_file": "budget_vs_actual_template.xlsx",
        "populator_script": "populate_budget_actual.py",
        "refresh_frequency": RefreshFrequency.DAILY.value,
        "delivery_methods": [DeliveryMethod.GOOGLE_SHEETS.value],
        "use_case": "Budget vs Actual rolling forecast",
        "version": "2024.06"
    }),
    
    "scenario_model": TemplateConfig({
        "name": "scenario_model",
        "title": "Scenario Planning Model",
        "description": "What-if analysis for CapEx, Sales capacity, LTV/CAC",
        "template_file": "scenario_planning_template.xlsx",
        "populator_script": "populate_scenario.py",
        "refresh_frequency": RefreshFrequency.ON_DEMAND.value,
        "delivery_methods": [DeliveryMethod.EXCEL_DOWNLOAD.value],
        "use_case": "Scenario models (CapEx, Sales-capacity, LTV/CAC, etc.)",
        "version": "2024.06"
    })
}

class TemplateManager:
    """
    Manages the lifecycle of financial templates
    Following the s3://finwave-exports/{company_slug}/ structure
    """
    
    def __init__(self, company_slug: str, s3_bucket: str = None):
        self.company_slug = company_slug
        self.s3_bucket = s3_bucket or os.getenv('FINWAVE_S3_BUCKET', 'finwave-exports')
        self.s3_client = None
        
        # Local paths
        self.base_path = Path(__file__).parent
        self.templates_path = self.base_path / 'files'
        self.populated_path = self.base_path / 'populated'
        self.logs_path = self.base_path / 'logs'
        
        # Ensure directories exist
        for path in [self.templates_path, self.populated_path, self.logs_path]:
            path.mkdir(exist_ok=True)
    
    def _get_s3_client(self):
        """Get or create S3 client"""
        if not self.s3_client:
            self.s3_client = boto3.client('s3')
        return self.s3_client
    
    def get_s3_key(self, category: str, filename: str) -> str:
        """Generate S3 key following the playbook structure"""
        return f"{self.company_slug}/{category}/{filename}"
    
    def upload_to_s3(self, local_path: Path, s3_key: str) -> bool:
        """Upload file to S3"""
        try:
            s3 = self._get_s3_client()
            s3.upload_file(str(local_path), self.s3_bucket, s3_key)
            logger.info(f"Uploaded to s3://{self.s3_bucket}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
    
    def download_from_s3(self, s3_key: str, local_path: Path) -> bool:
        """Download file from S3"""
        try:
            s3 = self._get_s3_client()
            s3.download_file(self.s3_bucket, s3_key, str(local_path))
            logger.info(f"Downloaded from s3://{self.s3_bucket}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            return False
    
    def get_latest_template(self, template_name: str) -> Optional[Path]:
        """Get the latest version of a template"""
        config = TEMPLATE_REGISTRY.get(template_name)
        if not config:
            raise ValueError(f"Unknown template: {template_name}")
        
        # Try S3 first
        s3_key = self.get_s3_key('templates', config.template_file)
        local_path = self.templates_path / config.template_file
        
        if self.s3_bucket and self.download_from_s3(s3_key, local_path):
            return local_path
        
        # Fall back to local file
        if local_path.exists():
            return local_path
        
        logger.error(f"Template not found: {config.template_file}")
        return None
    
    def populate_template(self, template_name: str, start_date: str, 
                         end_date: str = None, **kwargs) -> Dict[str, Any]:
        """
        Populate a template with data and handle delivery
        Returns dict with paths and metadata
        """
        config = TEMPLATE_REGISTRY.get(template_name)
        if not config:
            raise ValueError(f"Unknown template: {template_name}")
        
        # Get template
        template_path = self.get_latest_template(template_name)
        if not template_path:
            raise FileNotFoundError(f"Template file not found: {config.template_file}")
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_filename = f"{timestamp}_{config.name}.xlsx"
        output_path = self.populated_path / output_filename
        
        # Import and run the populator
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            f"populator_{template_name}",
            self.base_path / config.populator_script
        )
        populator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(populator_module)
        
        # Create populator instance
        if template_name == "3_statement_model":
            populator = populator_module.ThreeStatementPopulator(str(template_path))
        elif template_name == "kpi_dashboard":
            populator = populator_module.KPIDashboardPopulator(str(template_path))
        else:
            raise NotImplementedError(f"Populator not implemented for {template_name}")
        
        # Run population
        populator.load_template()
        
        if template_name == "3_statement_model":
            data = populator.fetch_quickbooks_data(start_date, end_date or datetime.now().strftime('%Y-%m-%d'))
            populator.populate_income_statement(data['pl'])
            populator.populate_balance_sheet(data['bs'])
        elif template_name == "kpi_dashboard":
            metrics_df = populator.fetch_business_metrics(start_date, end_date or datetime.now().strftime('%Y-%m-%d'))
            populator.populate_drivers_sheet(metrics_df)
        
        # Save populated file
        populated_path = populator.save_populated_file(str(output_path))
        
        # Handle delivery methods
        delivery_results = {}
        
        for delivery_method in config.delivery_methods:
            if delivery_method == DeliveryMethod.S3_ARCHIVE:
                # Always archive to S3
                s3_key = self.get_s3_key('populated', output_filename)
                if self.upload_to_s3(Path(populated_path), s3_key):
                    delivery_results['s3_url'] = f"s3://{self.s3_bucket}/{s3_key}"
            
            elif delivery_method == DeliveryMethod.GOOGLE_SHEETS:
                # Upload to Google Sheets if sheet_id provided
                sheet_id = kwargs.get('sheet_id')
                if sheet_id:
                    try:
                        sheet_url = populator.upload_to_google_sheets(sheet_id)
                        delivery_results['google_sheets_url'] = sheet_url
                        
                        # Save sheet ID reference
                        sheet_ref = {
                            'sheet_id': sheet_id,
                            'sheet_url': sheet_url,
                            'template': template_name,
                            'updated': datetime.now().isoformat()
                        }
                        sheet_ref_path = self.populated_path / f"{timestamp}_{config.name}_google_sheet.json"
                        with open(sheet_ref_path, 'w') as f:
                            json.dump(sheet_ref, f, indent=2)
                        
                        # Archive the reference
                        s3_key = self.get_s3_key('populated', sheet_ref_path.name)
                        self.upload_to_s3(sheet_ref_path, s3_key)
                        
                    except Exception as e:
                        logger.error(f"Google Sheets upload failed: {e}")
                        delivery_results['google_sheets_error'] = str(e)
        
        # Create and save run log
        run_log = {
            'template': template_name,
            'version': config.version,
            'start_date': start_date,
            'end_date': end_date,
            'populated_file': output_filename,
            'delivery_results': delivery_results,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        log_filename = f"{timestamp}_{config.name}_run.log"
        log_path = self.logs_path / log_filename
        with open(log_path, 'w') as f:
            json.dump(run_log, f, indent=2)
        
        # Archive log
        s3_key = self.get_s3_key('logs', log_filename)
        self.upload_to_s3(log_path, s3_key)
        
        return {
            'populated_file': str(populated_path),
            'delivery_results': delivery_results,
            'run_log': run_log
        }
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates with metadata"""
        templates = []
        for name, config in TEMPLATE_REGISTRY.items():
            templates.append({
                'name': name,
                'title': config.title,
                'description': config.description,
                'use_case': config.use_case,
                'refresh_frequency': config.refresh_frequency.value,
                'delivery_methods': [m.value for m in config.delivery_methods],
                'version': config.version
            })
        return templates
    
    def get_populated_files(self, template_name: str = None, 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of populated files from S3"""
        try:
            s3 = self._get_s3_client()
            prefix = f"{self.company_slug}/populated/"
            if template_name:
                prefix += f"*{template_name}*"
            
            response = s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'filename': obj['Key'].split('/')[-1],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': f"s3://{self.s3_bucket}/{obj['Key']}"
                })
            
            return sorted(files, key=lambda x: x['last_modified'], reverse=True)
            
        except ClientError as e:
            logger.error(f"Failed to list populated files: {e}")
            return []


# CLI interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='FinWave Template Manager')
    parser.add_argument('command', choices=['list', 'populate', 'history'],
                        help='Command to execute')
    parser.add_argument('--company', default='demo_corp', help='Company slug')
    parser.add_argument('--template', help='Template name')
    parser.add_argument('--since', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--until', help='End date (YYYY-MM-DD)')
    parser.add_argument('--sheet-id', help='Google Sheets ID')
    
    args = parser.parse_args()
    
    manager = TemplateManager(args.company)
    
    if args.command == 'list':
        templates = manager.list_templates()
        print("\nAvailable Templates:")
        print("-" * 80)
        for tmpl in templates:
            print(f"\n{tmpl['name']}:")
            print(f"  Title: {tmpl['title']}")
            print(f"  Use Case: {tmpl['use_case']}")
            print(f"  Refresh: {tmpl['refresh_frequency']}")
            print(f"  Delivery: {', '.join(tmpl['delivery_methods'])}")
    
    elif args.command == 'populate':
        if not args.template or not args.since:
            print("Error: --template and --since are required for populate command")
            exit(1)
        
        result = manager.populate_template(
            args.template,
            args.since,
            args.until,
            sheet_id=args.sheet_id
        )
        
        print(f"\n✅ Template populated successfully!")
        print(f"📄 File: {result['populated_file']}")
        if 's3_url' in result['delivery_results']:
            print(f"☁️  S3: {result['delivery_results']['s3_url']}")
        if 'google_sheets_url' in result['delivery_results']:
            print(f"📊 Sheets: {result['delivery_results']['google_sheets_url']}")
    
    elif args.command == 'history':
        files = manager.get_populated_files(args.template)
        print(f"\nPopulated Files History:")
        print("-" * 80)
        for f in files:
            print(f"{f['last_modified']}: {f['filename']} ({f['size']} bytes)")