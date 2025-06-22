"""
Field Mapper - Loads and applies field mappings from YAML configuration
Allows changing QuickBooks->Template mappings without code changes
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

logger = logging.getLogger(__name__)

class FieldMapper:
    """Manages field mappings between QuickBooks and templates"""
    
    def __init__(self, config_file: str = 'quickbooks.yml'):
        self.config_path = Path(__file__).parent / 'field_maps' / config_file
        self.mappings = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, Any]:
        """Load field mappings from YAML file"""
        if not self.config_path.exists():
            logger.warning(f"Field mapping file not found: {self.config_path}")
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                mappings = yaml.safe_load(f)
                logger.info(f"Loaded field mappings from {self.config_path}")
                return mappings
        except Exception as e:
            logger.error(f"Error loading field mappings: {e}")
            return {}
    
    def map_gl_fields(self, qb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map QuickBooks GL fields to template fields"""
        gl_mapping = self.mappings.get('gl_fields', {})
        
        result = {}
        for qb_field, template_field in gl_mapping.items():
            # Handle nested fields (e.g., AccountRef.name)
            if '.' in qb_field:
                parts = qb_field.split('.')
                value = qb_data
                for part in parts:
                    value = value.get(part, {}) if isinstance(value, dict) else None
                    if value is None:
                        break
                result[template_field] = value
            else:
                result[template_field] = qb_data.get(qb_field)
        
        return result
    
    def get_account_type(self, account_number: str, account_name: str = '') -> str:
        """Determine account type based on number and name"""
        account_types = self.mappings.get('account_types', {})
        
        # Try to parse account number
        try:
            acct_num = int(str(account_number).split('-')[0])
        except:
            acct_num = 0
        
        # Check each account type
        for acct_type, config in account_types.items():
            # Check number ranges
            for range_def in config.get('ranges', []):
                if range_def['start'] <= acct_num <= range_def['end']:
                    return acct_type
            
            # Check keywords in account name
            for keyword in config.get('keywords', []):
                if keyword.lower() in account_name.lower():
                    return acct_type
        
        return 'unknown'
    
    def map_to_coa_category(self, account_number: str) -> str:
        """Map account number to COA category for reporting"""
        coa_mapping = self.mappings.get('coa_mapping', {}).get('categories', {})
        
        # Try to parse account number
        try:
            acct_num = int(str(account_number).split('-')[0])
        except:
            return 'Other'
        
        # Check each category
        for category, config in coa_mapping.items():
            for account_range in config.get('accounts', []):
                if '-' in account_range:
                    start, end = account_range.split('-')
                    try:
                        if int(start) <= acct_num <= int(end):
                            return category
                    except:
                        continue
        
        return 'Other'
    
    def map_department(self, qb_class: str) -> str:
        """Map QuickBooks class/location to template department"""
        dept_mapping = self.mappings.get('departments', {})
        return dept_mapping.get(qb_class, 'Unassigned')
    
    def map_entity(self, qb_location: str) -> str:
        """Map QuickBooks location to template entity"""
        entity_mapping = self.mappings.get('entities', {})
        return entity_mapping.get(qb_location, entity_mapping.get('', 'Main'))
    
    def get_transaction_gl_impact(self, transaction_type: str) -> List[Dict[str, str]]:
        """Get GL impact rules for transaction type"""
        tx_types = self.mappings.get('transaction_types', {})
        tx_config = tx_types.get(transaction_type, {})
        return tx_config.get('gl_impact', [])
    
    def get_template_specific_mappings(self, template_name: str) -> Dict[str, Any]:
        """Get mappings specific to a template"""
        return self.mappings.get('template_specific', {}).get(template_name, {})
    
    def calculate_signed_amount(self, debit: float, credit: float, 
                               account_number: str, account_name: str = '') -> float:
        """
        Calculate signed amount based on account type
        Uses the mapping configuration to determine sign convention
        """
        account_type = self.get_account_type(account_number, account_name)
        
        # Apply sign conventions
        if account_type == 'assets':
            # Assets: Debit positive, Credit negative
            return debit - credit
        elif account_type == 'expenses':
            # Expenses: Show as negative (outflows)
            return -(debit - credit)
        elif account_type in ['liabilities', 'equity', 'revenue']:
            # Liabilities/Equity/Revenue: Credit positive, Debit negative
            return credit - debit
        else:
            # Default: Natural sign
            return debit - credit
    
    def reload(self):
        """Reload mappings from file"""
        self.mappings = self._load_mappings()
        logger.info("Reloaded field mappings")


# Singleton instance
_mapper_instance = None

def get_field_mapper() -> FieldMapper:
    """Get or create the field mapper instance"""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = FieldMapper()
    return _mapper_instance


# Integration test
if __name__ == '__main__':
    mapper = get_field_mapper()
    
    # Test GL field mapping
    qb_transaction = {
        'TxnDate': '2024-01-15',
        'AccountRef': {'value': '4000', 'name': 'Sales Revenue'},
        'Amount': 1000.00,
        'Description': 'Product sale',
        'ClassRef': {'name': 'Sales - US'},
        'EntityRef': {'name': 'United States'}
    }
    
    mapped = mapper.map_gl_fields(qb_transaction)
    print("GL Field Mapping Test:")
    print(f"  QuickBooks: {qb_transaction}")
    print(f"  Mapped to: {mapped}")
    
    # Test account type detection
    print("\nAccount Type Tests:")
    test_accounts = [
        ('1000', 'Cash'),
        ('2000', 'Accounts Payable'),
        ('3000', 'Retained Earnings'),
        ('4000', 'Sales Revenue'),
        ('5000', 'Cost of Goods Sold')
    ]
    
    for acct_num, acct_name in test_accounts:
        acct_type = mapper.get_account_type(acct_num, acct_name)
        print(f"  {acct_num} {acct_name}: {acct_type}")
    
    # Test signed amount calculation
    print("\nSigned Amount Tests:")
    test_amounts = [
        ('1000', 'Cash', 1000, 0),           # Asset debit
        ('4000', 'Revenue', 0, 1000),        # Revenue credit
        ('5000', 'Expense', 1000, 0),        # Expense debit
    ]
    
    for acct_num, acct_name, debit, credit in test_amounts:
        signed = mapper.calculate_signed_amount(debit, credit, acct_num, acct_name)
        print(f"  {acct_name}: Dr {debit} Cr {credit} = {signed:+.2f}")