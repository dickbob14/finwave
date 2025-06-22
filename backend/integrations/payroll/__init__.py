"""
Payroll integration module
"""

from .client import (
    PayrollClient,
    GustoClient,
    ADPClient,
    create_payroll_client,
    test_payroll_connection
)

__all__ = [
    'PayrollClient',
    'GustoClient', 
    'ADPClient',
    'create_payroll_client',
    'test_payroll_connection'
]