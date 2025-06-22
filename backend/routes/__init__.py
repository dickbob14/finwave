"""
API routes package for FinWave backend
"""

from .export_v2 import router as export_router
from .report import router as report_router
from .insight import router as insight_router
from .charts import router as charts_router
from .crm import router as crm_router

__all__ = ['export_router', 'report_router', 'insight_router', 'charts_router', 'crm_router']