"""Performance monitoring for doctk operations.

This module provides performance monitoring capabilities to track operation
durations, identify bottlenecks, and ensure the system meets performance
requirements.
"""

import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Metric:
    """A single performance metric."""

    timestamp: float
    duration: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationStats:
    """Statistics for a specific operation."""

    operation_name: str
    total_calls: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    metrics: list[Metric] = field(default_factory=list)

    @property
    def average_duration(self) -> float:
        """Calculate average duration."""
        if self.total_calls == 0:
            return 0.0
        return self.total_duration / self.total_calls

    def add_metric(self, metric: Metric) -> None:
        """Add a metric and update statistics."""
        self.metrics.append(metric)
        self.total_calls += 1
        self.total_duration += metric.duration
        self.min_duration = min(self.min_duration, metric.duration)
        self.max_duration = max(self.max_duration, metric.duration)


class PerformanceMonitor:
    """Monitor and track performance metrics for doctk operations.

    This class provides functionality to:
    - Record operation durations
    - Calculate statistics (average, min, max)
    - Identify slow operations
    - Report performance metrics

    Example:
        >>> monitor = PerformanceMonitor()
        >>> with monitor.measure("promote"):
        ...     # Perform operation
        ...     pass
        >>> stats = monitor.get_stats("promote")
        >>> print(f"Average time: {stats.average_duration * 1000:.2f}ms")
    """

    def __init__(self, slow_operation_threshold: float = 0.5):
        """Initialize performance monitor.

        Args:
            slow_operation_threshold: Threshold in seconds for slow operations (default: 0.5s)
        """
        self.stats: dict[str, OperationStats] = {}
        self.slow_operation_threshold = slow_operation_threshold

    def record_operation(
        self, operation: str, duration: float, metadata: dict[str, Any] | None = None
    ) -> None:
        """Record an operation's execution time.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            metadata: Optional metadata about the operation
        """
        if operation not in self.stats:
            self.stats[operation] = OperationStats(operation_name=operation)

        metric = Metric(
            timestamp=time.time(), duration=duration, metadata=metadata or {}
        )
        self.stats[operation].add_metric(metric)

    @contextmanager
    def measure(
        self, operation: str, metadata: dict[str, Any] | None = None
    ) -> Generator[None, None, None]:
        """Context manager to measure operation duration.

        Args:
            operation: Name of the operation to measure
            metadata: Optional metadata about the operation

        Example:
            >>> monitor = PerformanceMonitor()
            >>> with monitor.measure("promote", {"node_id": "h1-0"}):
            ...     # Perform operation
            ...     pass
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.record_operation(operation, duration, metadata)

    def get_stats(self, operation: str) -> OperationStats | None:
        """Get statistics for a specific operation.

        Args:
            operation: Name of the operation

        Returns:
            OperationStats if operation has been recorded, None otherwise
        """
        return self.stats.get(operation)

    def get_average_time(self, operation: str) -> float:
        """Get average execution time for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Average duration in seconds, or 0.0 if operation not found
        """
        stats = self.get_stats(operation)
        return stats.average_duration if stats else 0.0

    def get_all_stats(self) -> dict[str, OperationStats]:
        """Get statistics for all operations.

        Returns:
            Dictionary mapping operation names to their statistics
        """
        return dict(self.stats)

    def get_slow_operations(self) -> list[tuple[str, float]]:
        """Identify operations exceeding the slow threshold.

        Returns:
            List of tuples (operation_name, average_duration) for slow operations,
            sorted by duration (slowest first)
        """
        slow_ops = [
            (name, stats.average_duration)
            for name, stats in self.stats.items()
            if stats.average_duration > self.slow_operation_threshold
        ]
        return sorted(slow_ops, key=lambda x: x[1], reverse=True)

    def report_slow_operations(self) -> str:
        """Generate a report of slow operations.

        Returns:
            Human-readable report string
        """
        slow_ops = self.get_slow_operations()
        if not slow_ops:
            return "No slow operations detected."

        threshold_ms = int(self.slow_operation_threshold * 1000)
        lines = [f"Slow operations detected (threshold: {threshold_ms}ms):"]
        for operation, avg_duration in slow_ops:
            stats = self.stats[operation]
            lines.append(
                f"  - {operation}: avg={avg_duration*1000:.0f}ms, "
                f"min={stats.min_duration*1000:.0f}ms, "
                f"max={stats.max_duration*1000:.0f}ms, "
                f"calls={stats.total_calls}"
            )
        return "\n".join(lines)

    def get_summary(self) -> str:
        """Generate a summary report of all operations.

        Returns:
            Human-readable summary string
        """
        if not self.stats:
            return "No performance metrics recorded."

        lines = ["Performance Summary:"]
        for name, stats in sorted(self.stats.items()):
            lines.append(
                f"  {name}: avg={stats.average_duration*1000:.2f}ms, "
                f"min={stats.min_duration*1000:.2f}ms, "
                f"max={stats.max_duration*1000:.2f}ms, "
                f"calls={stats.total_calls}"
            )

        slow_ops = self.get_slow_operations()
        if slow_ops:
            lines.append("")
            lines.append(self.report_slow_operations())

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all recorded metrics."""
        self.stats.clear()

    def get_total_operations(self) -> int:
        """Get total number of operations recorded.

        Returns:
            Total count of all operation calls
        """
        return sum(stats.total_calls for stats in self.stats.values())

    def get_total_time(self) -> float:
        """Get total time spent in all operations.

        Returns:
            Total duration in seconds
        """
        return sum(stats.total_duration for stats in self.stats.values())
