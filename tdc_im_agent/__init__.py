"""
TDC - IM Performance Tracking Agent
Enterprise AI-Assisted Analytics Application for The Derma Co (Honasa Consumer Ltd.)
"""

from .config import APP_NAME, APP_VERSION
from .orchestrator import TDCOrchestrator
from .models import CanonicalRow, QAValidationReport, ProcessingState

__version__ = APP_VERSION
__all__ = ["TDCOrchestrator", "CanonicalRow", "QAValidationReport", "ProcessingState"]
