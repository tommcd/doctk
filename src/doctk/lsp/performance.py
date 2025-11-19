"""Backward compatibility wrapper for doctk.integration.performance.

DEPRECATED: Import from doctk.integration.performance instead.

This module exists solely for backward compatibility with code that imported
from doctk.lsp.performance. All functionality has moved to doctk.integration.performance.
"""

from doctk.integration.performance import PerformanceMonitor

__all__ = ["PerformanceMonitor"]
