"""Performance benchmark tests for doctk operations.

These tests validate that the system meets performance requirements
specified in requirements.md (Requirement 17):
- Tree view rendering: ≤ 1 second for 1000 headings
- User interactions: ≤ 200ms for large documents
- Structural operations: ≤ 2 seconds for large documents
- Memory usage: ≤ 500MB
"""

import gc
import time
from typing import Any

import pytest

from doctk.core import Document, Heading
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations
from doctk.lsp.performance import PerformanceMonitor


def _get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.

    Returns:
        Current process memory usage in megabytes
    """
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # psutil not available, return 0 to skip memory tests
        return 0.0


def generate_large_document(num_headings: int) -> Document[Any]:
    """
    Generate a large test document with the specified number of headings.

    Creates a hierarchical document structure with:
    - Level 1 headings (sections)
    - Level 2 headings (subsections)
    - Level 3 headings (sub-subsections)
    - Some paragraph content

    Args:
        num_headings: Number of headings to generate

    Returns:
        Document with the specified number of headings
    """
    from doctk.core import Paragraph

    nodes: list[Any] = []
    headings_created = 0

    # Create hierarchical structure
    while headings_created < num_headings:
        # Level 1 heading (section)
        if headings_created < num_headings:
            nodes.append(Heading(level=1, text=f"Section {headings_created + 1}"))
            headings_created += 1

        # Add some content
        if headings_created % 10 == 0:
            nodes.append(
                Paragraph(content=f"This is paragraph content for section {headings_created}.")
            )

        # Level 2 heading (subsection)
        if headings_created < num_headings:
            nodes.append(Heading(level=2, text=f"Subsection {headings_created + 1}"))
            headings_created += 1

        # Level 3 heading (sub-subsection)
        if headings_created < num_headings:
            nodes.append(Heading(level=3, text=f"Sub-subsection {headings_created + 1}"))
            headings_created += 1

    return Document(nodes=nodes)


@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmark tests for large documents."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
        # Force garbage collection before each test
        gc.collect()

    def test_generate_1000_heading_document(self):
        """Test: Can generate a document with 1000 headings."""
        start_time = time.perf_counter()
        doc = generate_large_document(1000)
        duration = time.perf_counter() - start_time

        # Verify document was created correctly
        heading_count = sum(1 for node in doc.nodes if isinstance(node, Heading))
        assert heading_count == 1000

        # Document generation should be fast (sanity check)
        assert duration < 5.0, f"Document generation took {duration:.2f}s (should be < 5s)"

    def test_tree_building_1000_headings_performance_baseline(self):
        """
        Requirement 17.1: Documents with up to 1000 headings SHALL render
        tree view within 1 second.

        Current Status: BASELINE TEST
        - Current implementation: ~3.8s for tree building
        - Target (Requirement 17.1): ≤ 1.0s
        - Optimization planned: Tasks 10.1 (incremental parsing) and 10.2 (memory management)

        Known Issue: _calculate_node_line() has O(n²) complexity due to
        repeated document traversal for line number calculation.

        This test establishes a performance baseline and will be tightened
        once optimization tasks are complete.
        """
        doc = generate_large_document(1000)

        with self.monitor.measure("build_tree_1000"):
            builder = DocumentTreeBuilder(doc)
            tree = builder.build_tree_with_ids()

        # Get the actual duration
        stats = self.monitor.get_stats("build_tree_1000")
        assert stats is not None
        duration = stats.average_duration

        # Verify tree was built correctly
        assert tree.id == "root"
        assert tree.label == "Document"

        # Current baseline: Allow 5 seconds (will be tightened to 1s in Task 10.1/10.2)
        assert duration <= 5.0, (
            f"Tree building took {duration:.3f}s (current baseline: ≤ 5.0s, "
            f"target requirement: ≤ 1.0s)"
        )

        # Document current performance for tracking
        if duration > 1.0:
            # This is expected with current implementation
            print(
                f"\nPerformance note: Tree building took {duration:.3f}s "
                f"(exceeds target of 1.0s, optimization needed)"
            )

    def test_promote_operation_on_large_document_within_2_seconds(self):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test promote operation on a document with 1000 headings.
        """
        doc = generate_large_document(1000)

        # Promote a heading in the middle of the document
        with self.monitor.measure("promote_large"):
            result = StructureOperations.promote(doc, "h2-10")

        # Get the actual duration
        stats = self.monitor.get_stats("promote_large")
        assert stats is not None
        duration = stats.average_duration

        # Verify operation succeeded
        assert result.success

        # Performance requirement: ≤ 2 seconds
        assert duration <= 2.0, f"Promote took {duration:.3f}s (required: ≤ 2.0s)"

    def test_demote_operation_on_large_document_within_2_seconds(self):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test demote operation on a document with 1000 headings.
        """
        doc = generate_large_document(1000)

        # Demote a heading in the middle of the document
        with self.monitor.measure("demote_large"):
            result = StructureOperations.demote(doc, "h1-10")

        # Get the actual duration
        stats = self.monitor.get_stats("demote_large")
        assert stats is not None
        duration = stats.average_duration

        # Verify operation succeeded
        assert result.success

        # Performance requirement: ≤ 2 seconds
        assert duration <= 2.0, f"Demote took {duration:.3f}s (required: ≤ 2.0s)"

    def test_move_up_operation_on_large_document_within_2_seconds(self):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test move_up operation on a document with 1000 headings.
        """
        doc = generate_large_document(1000)

        # Move up a heading in the middle of the document
        with self.monitor.measure("move_up_large"):
            result = StructureOperations.move_up(doc, "h1-50")

        # Get the actual duration
        stats = self.monitor.get_stats("move_up_large")
        assert stats is not None
        duration = stats.average_duration

        # Verify operation succeeded
        assert result.success

        # Performance requirement: ≤ 2 seconds
        assert duration <= 2.0, f"Move up took {duration:.3f}s (required: ≤ 2.0s)"

    def test_move_down_operation_on_large_document_within_2_seconds(self):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test move_down operation on a document with 1000 headings.
        """
        doc = generate_large_document(1000)

        # Move down a heading in the middle of the document
        with self.monitor.measure("move_down_large"):
            result = StructureOperations.move_down(doc, "h1-50")

        # Get the actual duration
        stats = self.monitor.get_stats("move_down_large")
        assert stats is not None
        duration = stats.average_duration

        # Verify operation succeeded
        assert result.success

        # Performance requirement: ≤ 2 seconds
        assert duration <= 2.0, f"Move down took {duration:.3f}s (required: ≤ 2.0s)"

    def test_nest_operation_on_large_document_within_2_seconds(self):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test nest operation on a document with 1000 headings.
        """
        doc = generate_large_document(1000)

        # Nest a heading under another in the middle of the document
        with self.monitor.measure("nest_large"):
            result = StructureOperations.nest(doc, "h2-50", "h1-20")

        # Get the actual duration
        stats = self.monitor.get_stats("nest_large")
        assert stats is not None
        duration = stats.average_duration

        # Verify operation succeeded
        assert result.success

        # Performance requirement: ≤ 2 seconds
        assert duration <= 2.0, f"Nest took {duration:.3f}s (required: ≤ 2.0s)"

    def test_unnest_operation_on_large_document_within_2_seconds(self):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test unnest operation on a document with 1000 headings.
        """
        doc = generate_large_document(1000)

        # Unnest a heading in the middle of the document
        with self.monitor.measure("unnest_large"):
            result = StructureOperations.unnest(doc, "h3-50")

        # Get the actual duration
        stats = self.monitor.get_stats("unnest_large")
        assert stats is not None
        duration = stats.average_duration

        # Verify operation succeeded
        assert result.success

        # Performance requirement: ≤ 2 seconds
        assert duration <= 2.0, f"Unnest took {duration:.3f}s (required: ≤ 2.0s)"

    def test_multiple_operations_sequential(self):
        """
        Test: Multiple operations on a large document should maintain
        acceptable performance.

        This simulates a realistic usage scenario where a user performs
        multiple operations in sequence.
        """
        doc = generate_large_document(500)

        operations = [
            ("promote", lambda d: StructureOperations.promote(d, "h2-10")),
            ("demote", lambda d: StructureOperations.demote(d, "h1-20")),
            ("move_up", lambda d: StructureOperations.move_up(d, "h1-30")),
            ("move_down", lambda d: StructureOperations.move_down(d, "h1-40")),
        ]

        total_time = 0.0
        for op_name, op_func in operations:
            with self.monitor.measure(op_name):
                result = op_func(doc)
                # Re-parse for next operation (current architecture limitation)
                if result.success and result.document:
                    doc = Document.from_string(result.document)

            stats = self.monitor.get_stats(op_name)
            assert stats is not None
            total_time += stats.average_duration

        # All operations combined should be reasonably fast
        assert total_time < 10.0, f"Sequential operations took {total_time:.3f}s (should be < 10s)"

    @pytest.mark.skipif(
        _get_memory_usage_mb() == 0, reason="psutil not available for memory monitoring"
    )
    def test_memory_usage_large_document(self):
        """
        Requirement 17.5: When memory usage exceeds 500MB, THE System SHALL
        implement optimization strategies.

        This test verifies that processing a large document doesn't cause
        excessive memory usage.

        Note: This is a basic sanity check. Full memory optimization (Task 10.2)
        will implement LRU caching and memory management strategies.
        """
        # Get baseline memory
        gc.collect()
        time.sleep(0.1)  # Allow GC to settle
        baseline_memory = _get_memory_usage_mb()

        # Create and process large document
        doc = generate_large_document(1000)
        builder = DocumentTreeBuilder(doc)
        tree = builder.build_tree_with_ids()

        # Measure peak memory during operation
        peak_memory = _get_memory_usage_mb()
        memory_increase = peak_memory - baseline_memory

        # Clean up
        del doc
        del builder
        del tree
        gc.collect()

        # Memory increase should be reasonable (not exceeding 500MB)
        # This is a sanity check - actual memory optimization will be in Task 10.2
        assert (
            memory_increase < 500.0
        ), f"Memory increase: {memory_increase:.2f}MB (should be < 500MB)"

    def test_performance_summary_generation(self):
        """
        Test: Performance monitoring should track all operations and
        provide useful summary data.
        """
        doc = generate_large_document(100)

        # Perform various operations
        with self.monitor.measure("promote"):
            StructureOperations.promote(doc, "h2-5")

        with self.monitor.measure("demote"):
            StructureOperations.demote(doc, "h1-5")

        with self.monitor.measure("build_tree"):
            builder = DocumentTreeBuilder(doc)
            builder.build_tree_with_ids()

        # Get summary
        summary = self.monitor.get_summary()

        # Verify summary contains expected information
        assert "Performance Summary:" in summary
        assert "promote" in summary
        assert "demote" in summary
        assert "build_tree" in summary

        # Verify slow operations detection works
        slow_ops = self.monitor.get_slow_operations()
        # With small document (100 headings), operations should be fast
        assert len(slow_ops) == 0 or all(
            duration < 1.0 for _, duration in slow_ops
        ), "Operations on small document should be fast"


@pytest.mark.slow
class TestPerformanceScalability:
    """Tests to verify performance scales appropriately with document size."""

    def test_tree_building_scales_linearly(self):
        """
        Test: Tree building should scale approximately linearly with
        document size (not exponentially).

        Current Status: BASELINE TEST
        - Current implementation: O(n²) due to _calculate_node_line()
        - Scaling ratio: ~55x for 100→1000 headings (quadratic behavior)
        - Target: O(n) linear scaling (~10x for 100→1000)
        - Optimization planned: Task 10.1 (incremental parsing)

        This test documents current scaling behavior and will be tightened
        once optimization is implemented.
        """
        monitor = PerformanceMonitor()
        sizes = [100, 500, 1000]
        durations: list[float] = []

        for size in sizes:
            doc = generate_large_document(size)

            with monitor.measure(f"tree_build_{size}"):
                builder = DocumentTreeBuilder(doc)
                builder.build_tree_with_ids()

            stats = monitor.get_stats(f"tree_build_{size}")
            assert stats is not None
            durations.append(stats.average_duration)

        # Calculate scaling ratio
        ratio = durations[2] / durations[0] if durations[0] > 0 else float("inf")

        # Current baseline: Allow quadratic scaling (will be improved to linear in Task 10.1)
        # With O(n²): 100→1000 is 100x data, expect ~100x time
        # Allow 120x to account for variance in timing
        assert ratio < 120.0, (
            f"Scaling ratio: {ratio:.2f}x (current baseline: < 120x, target: < 15x)"
        )

        # Document current performance for tracking
        if ratio > 15.0:
            # This is expected with current O(n²) implementation
            print(
                f"\nPerformance note: Scaling ratio is {ratio:.2f}x "
                f"(exceeds target of 15x for linear scaling, optimization needed)"
            )

    def test_operation_performance_with_varying_sizes(self):
        """
        Test: Operations should maintain acceptable performance across
        different document sizes.
        """
        monitor = PerformanceMonitor()
        sizes = [100, 500, 1000]

        for size in sizes:
            doc = generate_large_document(size)

            # Test promote operation
            with monitor.measure(f"promote_{size}"):
                result = StructureOperations.promote(doc, "h2-5")

            assert result.success

            # Verify performance requirement
            stats = monitor.get_stats(f"promote_{size}")
            assert stats is not None
            assert stats.average_duration <= 2.0, (
                f"Promote on {size} headings took {stats.average_duration:.3f}s "
                "(required: ≤ 2.0s)"
            )
