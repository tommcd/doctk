"""Tests for performance monitoring functionality."""

import time

import pytest

from doctk.lsp.performance import Metric, OperationStats, PerformanceMonitor


class TestMetric:
    """Tests for Metric dataclass."""

    def test_metric_creation(self):
        """Test creating a Metric instance."""
        metric = Metric(timestamp=1234567890.0, duration=0.5)
        assert metric.timestamp == 1234567890.0
        assert metric.duration == 0.5
        assert metric.metadata == {}

    def test_metric_with_metadata(self):
        """Test creating a Metric with metadata."""
        metadata = {"node_id": "h1-0", "operation": "promote"}
        metric = Metric(timestamp=1234567890.0, duration=0.5, metadata=metadata)
        assert metric.metadata == metadata


class TestOperationStats:
    """Tests for OperationStats dataclass."""

    def test_stats_initialization(self):
        """Test creating OperationStats instance."""
        stats = OperationStats(operation_name="promote")
        assert stats.operation_name == "promote"
        assert stats.total_calls == 0
        assert stats.total_duration == 0.0
        assert stats.min_duration == float("inf")
        assert stats.max_duration == float("-inf")
        assert stats.metrics == []

    def test_average_duration_empty(self):
        """Test average duration with no metrics."""
        stats = OperationStats(operation_name="promote")
        assert stats.average_duration == 0.0

    def test_add_metric(self):
        """Test adding a metric to stats."""
        stats = OperationStats(operation_name="promote")
        metric = Metric(timestamp=time.time(), duration=0.5)
        stats.add_metric(metric)

        assert stats.total_calls == 1
        assert stats.total_duration == 0.5
        assert stats.min_duration == 0.5
        assert stats.max_duration == 0.5
        assert stats.average_duration == 0.5
        assert len(stats.metrics) == 1

    def test_add_multiple_metrics(self):
        """Test adding multiple metrics to stats."""
        stats = OperationStats(operation_name="promote")
        metrics = [
            Metric(timestamp=time.time(), duration=0.1),
            Metric(timestamp=time.time(), duration=0.5),
            Metric(timestamp=time.time(), duration=0.3),
        ]

        for metric in metrics:
            stats.add_metric(metric)

        assert stats.total_calls == 3
        assert stats.total_duration == pytest.approx(0.9)
        assert stats.min_duration == 0.1
        assert stats.max_duration == 0.5
        assert stats.average_duration == pytest.approx(0.3)


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""

    def test_monitor_initialization(self):
        """Test creating a PerformanceMonitor instance."""
        monitor = PerformanceMonitor()
        assert monitor.slow_operation_threshold == 0.5
        assert monitor.stats == {}

    def test_monitor_custom_threshold(self):
        """Test creating a monitor with custom threshold."""
        monitor = PerformanceMonitor(slow_operation_threshold=1.0)
        assert monitor.slow_operation_threshold == 1.0

    def test_record_operation(self):
        """Test recording a single operation."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)

        stats = monitor.get_stats("promote")
        assert stats is not None
        assert stats.operation_name == "promote"
        assert stats.total_calls == 1
        assert stats.total_duration == 0.1

    def test_record_operation_with_metadata(self):
        """Test recording operation with metadata."""
        monitor = PerformanceMonitor()
        metadata = {"node_id": "h1-0"}
        monitor.record_operation("promote", 0.1, metadata=metadata)

        stats = monitor.get_stats("promote")
        assert stats is not None
        assert len(stats.metrics) == 1
        assert stats.metrics[0].metadata == metadata

    def test_record_multiple_operations(self):
        """Test recording multiple operations of the same type."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("promote", 0.2)
        monitor.record_operation("promote", 0.3)

        stats = monitor.get_stats("promote")
        assert stats is not None
        assert stats.total_calls == 3
        assert stats.total_duration == pytest.approx(0.6)
        assert stats.average_duration == pytest.approx(0.2)

    def test_record_different_operations(self):
        """Test recording different operation types."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("demote", 0.2)

        promote_stats = monitor.get_stats("promote")
        demote_stats = monitor.get_stats("demote")

        assert promote_stats is not None
        assert demote_stats is not None
        assert promote_stats.total_calls == 1
        assert demote_stats.total_calls == 1

    def test_measure_context_manager(self):
        """Test the measure context manager."""
        monitor = PerformanceMonitor()

        with monitor.measure("test_operation"):
            time.sleep(0.01)  # Small delay

        stats = monitor.get_stats("test_operation")
        assert stats is not None
        assert stats.total_calls == 1
        assert stats.average_duration >= 0.01  # At least the sleep duration

    def test_measure_with_metadata(self):
        """Test measure context manager with metadata."""
        monitor = PerformanceMonitor()
        metadata = {"test": "value"}

        with monitor.measure("test_operation", metadata=metadata):
            time.sleep(0.01)

        stats = monitor.get_stats("test_operation")
        assert stats is not None
        assert stats.metrics[0].metadata == metadata

    def test_measure_with_exception(self):
        """Test that measure records even when exception occurs."""
        monitor = PerformanceMonitor()

        with pytest.raises(ValueError):
            with monitor.measure("test_operation"):
                raise ValueError("Test error")

        stats = monitor.get_stats("test_operation")
        assert stats is not None
        assert stats.total_calls == 1

    def test_get_stats_not_found(self):
        """Test getting stats for non-existent operation."""
        monitor = PerformanceMonitor()
        stats = monitor.get_stats("nonexistent")
        assert stats is None

    def test_get_average_time(self):
        """Test getting average time for an operation."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("promote", 0.3)

        avg = monitor.get_average_time("promote")
        assert avg == 0.2

    def test_get_average_time_not_found(self):
        """Test getting average time for non-existent operation."""
        monitor = PerformanceMonitor()
        avg = monitor.get_average_time("nonexistent")
        assert avg == 0.0

    def test_get_all_stats(self):
        """Test getting all operation statistics."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("demote", 0.2)

        all_stats = monitor.get_all_stats()
        assert len(all_stats) == 2
        assert "promote" in all_stats
        assert "demote" in all_stats

    def test_get_slow_operations_none(self):
        """Test getting slow operations when none exist."""
        monitor = PerformanceMonitor(slow_operation_threshold=1.0)
        monitor.record_operation("promote", 0.1)

        slow_ops = monitor.get_slow_operations()
        assert slow_ops == []

    def test_get_slow_operations_single(self):
        """Test getting slow operations with one slow operation."""
        monitor = PerformanceMonitor(slow_operation_threshold=0.2)
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("demote", 0.5)

        slow_ops = monitor.get_slow_operations()
        assert len(slow_ops) == 1
        assert slow_ops[0][0] == "demote"
        assert slow_ops[0][1] == 0.5

    def test_get_slow_operations_multiple(self):
        """Test getting multiple slow operations."""
        monitor = PerformanceMonitor(slow_operation_threshold=0.2)
        monitor.record_operation("promote", 0.6)
        monitor.record_operation("demote", 0.3)
        monitor.record_operation("move_up", 0.1)

        slow_ops = monitor.get_slow_operations()
        assert len(slow_ops) == 2
        # Should be sorted by duration (slowest first)
        assert slow_ops[0][0] == "promote"
        assert slow_ops[0][1] == 0.6
        assert slow_ops[1][0] == "demote"
        assert slow_ops[1][1] == 0.3

    def test_report_slow_operations_none(self):
        """Test slow operations report when none exist."""
        monitor = PerformanceMonitor(slow_operation_threshold=1.0)
        monitor.record_operation("promote", 0.1)

        report = monitor.report_slow_operations()
        assert report == "No slow operations detected."

    def test_report_slow_operations_single(self):
        """Test slow operations report with one slow operation."""
        monitor = PerformanceMonitor(slow_operation_threshold=0.2)
        monitor.record_operation("demote", 0.5)
        monitor.record_operation("demote", 0.7)

        report = monitor.report_slow_operations()
        assert "Slow operations detected" in report
        assert "demote" in report
        assert "avg=600ms" in report
        assert "calls=2" in report

    def test_report_slow_operations_multiple(self):
        """Test slow operations report with multiple slow operations."""
        monitor = PerformanceMonitor(slow_operation_threshold=0.2)
        monitor.record_operation("promote", 0.6)
        monitor.record_operation("demote", 0.3)

        report = monitor.report_slow_operations()
        assert "Slow operations detected" in report
        assert "promote" in report
        assert "demote" in report

    def test_get_summary_empty(self):
        """Test summary report with no metrics."""
        monitor = PerformanceMonitor()
        summary = monitor.get_summary()
        assert summary == "No performance metrics recorded."

    def test_get_summary_single_operation(self):
        """Test summary report with single operation."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)

        summary = monitor.get_summary()
        assert "Performance Summary:" in summary
        assert "promote" in summary
        assert "avg=100.00ms" in summary
        assert "calls=1" in summary

    def test_get_summary_multiple_operations(self):
        """Test summary report with multiple operations."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("demote", 0.2)

        summary = monitor.get_summary()
        assert "Performance Summary:" in summary
        assert "promote" in summary
        assert "demote" in summary

    def test_get_summary_includes_slow_operations(self):
        """Test that summary includes slow operations section."""
        monitor = PerformanceMonitor(slow_operation_threshold=0.1)
        monitor.record_operation("promote", 0.5)

        summary = monitor.get_summary()
        assert "Performance Summary:" in summary
        assert "Slow operations detected" in summary

    def test_clear_metrics(self):
        """Test clearing all metrics."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("demote", 0.2)

        assert len(monitor.stats) == 2

        monitor.clear()

        assert len(monitor.stats) == 0
        assert monitor.get_stats("promote") is None
        assert monitor.get_stats("demote") is None

    def test_get_total_operations(self):
        """Test getting total operation count."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("promote", 0.2)
        monitor.record_operation("demote", 0.3)

        total = monitor.get_total_operations()
        assert total == 3

    def test_get_total_operations_empty(self):
        """Test getting total operations when empty."""
        monitor = PerformanceMonitor()
        total = monitor.get_total_operations()
        assert total == 0

    def test_get_total_time(self):
        """Test getting total time spent in operations."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("promote", 0.2)
        monitor.record_operation("demote", 0.3)

        total_time = monitor.get_total_time()
        assert total_time == pytest.approx(0.6)

    def test_get_total_time_empty(self):
        """Test getting total time when empty."""
        monitor = PerformanceMonitor()
        total_time = monitor.get_total_time()
        assert total_time == 0.0

    def test_min_max_duration_tracking(self):
        """Test that min and max durations are tracked correctly."""
        monitor = PerformanceMonitor()
        monitor.record_operation("promote", 0.1)
        monitor.record_operation("promote", 0.5)
        monitor.record_operation("promote", 0.3)

        stats = monitor.get_stats("promote")
        assert stats is not None
        assert stats.min_duration == 0.1
        assert stats.max_duration == 0.5

    def test_performance_requirement_500ms(self):
        """Test that slow operation threshold matches requirement (500ms)."""
        monitor = PerformanceMonitor()  # Default threshold is 0.5s (500ms)

        # Fast operation (under threshold)
        monitor.record_operation("fast_op", 0.2)
        # Slow operation (over threshold)
        monitor.record_operation("slow_op", 0.6)

        slow_ops = monitor.get_slow_operations()
        assert len(slow_ops) == 1
        assert slow_ops[0][0] == "slow_op"

    def test_concurrent_operation_tracking(self):
        """Test tracking multiple different operations concurrently."""
        monitor = PerformanceMonitor()

        # Simulate various operations being called
        operations = ["promote", "demote", "move_up", "move_down", "nest", "unnest"]
        for op in operations:
            monitor.record_operation(op, 0.1)

        assert len(monitor.get_all_stats()) == 6
        assert monitor.get_total_operations() == 6

    def test_measure_preserves_return_value(self):
        """Test that measure context manager doesn't interfere with code execution."""
        monitor = PerformanceMonitor()

        def operation_with_return():
            with monitor.measure("test"):
                return 42

        result = operation_with_return()
        assert result == 42
        assert monitor.get_stats("test") is not None

    def test_metric_retention_limit(self):
        """Test that metrics are limited to prevent unbounded growth."""
        # Set low limit for testing
        monitor = PerformanceMonitor(max_metrics_per_operation=5)

        # Record more metrics than the limit
        for i in range(10):
            monitor.record_operation("test_op", 0.1 * i)

        stats = monitor.get_stats("test_op")
        assert stats is not None
        # Should only retain max_metrics_per_operation metrics
        assert len(stats.metrics) == 5
        # Should keep the most recent metrics (oldest evicted)
        assert stats.metrics[0].duration == pytest.approx(0.5)  # 6th metric
        assert stats.metrics[-1].duration == pytest.approx(0.9)  # 10th metric

    def test_metric_retention_default_limit(self):
        """Test that default retention limit is 1000."""
        monitor = PerformanceMonitor()
        assert monitor.max_metrics_per_operation == 1000

    def test_metric_retention_preserves_stats(self):
        """Test that stats remain accurate after metric eviction."""
        monitor = PerformanceMonitor(max_metrics_per_operation=3)

        # Record 5 metrics
        durations = [0.1, 0.2, 0.3, 0.4, 0.5]
        for duration in durations:
            monitor.record_operation("test_op", duration)

        stats = monitor.get_stats("test_op")
        assert stats is not None
        # Should have recorded all 5 calls
        assert stats.total_calls == 5
        # Total duration should include all metrics
        assert stats.total_duration == pytest.approx(1.5)
        # Average should be correct
        assert stats.average_duration == pytest.approx(0.3)
        # But only 3 metrics retained
        assert len(stats.metrics) == 3

    def test_get_all_stats_returns_deep_copy(self):
        """Test that get_all_stats returns deep copy to prevent external mutation."""
        monitor = PerformanceMonitor()
        monitor.record_operation("test_op", 0.1)

        # Get stats and try to modify
        stats_copy = monitor.get_all_stats()
        stats_copy["test_op"].total_calls = 999

        # Original should be unchanged
        original_stats = monitor.get_stats("test_op")
        assert original_stats is not None
        assert original_stats.total_calls == 1  # Not 999
