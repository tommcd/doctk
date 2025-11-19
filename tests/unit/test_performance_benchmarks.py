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

from doctk.core import Document, Heading, Paragraph
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations
from doctk.lsp.performance import PerformanceMonitor

# Performance thresholds from requirements.md (Requirement 17)
STRUCTURAL_OPERATION_THRESHOLD = 2.0  # seconds (Requirement 17.4)
TREE_BUILDING_TARGET_THRESHOLD = 1.0  # seconds (Requirement 17.1)
DOCUMENT_GENERATION_SANITY_THRESHOLD = 5.0  # seconds
SEQUENTIAL_OPERATIONS_THRESHOLD = 10.0  # seconds
MEMORY_THRESHOLD_MB = 500.0  # MB (Requirement 17.5)

# Scalability thresholds (now that Task 10.1 is complete)
SCALING_RATIO_TARGET = 15.0  # Target for linear scaling (100→1000 headings)


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
    nodes: list[Any] = []
    headings_created = 0

    # Create hierarchical structure
    while headings_created < num_headings:
        # Level 1 heading (section)
        nodes.append(Heading(level=1, text=f"Section {headings_created + 1}"))
        headings_created += 1
        if headings_created >= num_headings:
            break

        # Add some content
        if headings_created % 10 == 0:
            nodes.append(
                Paragraph(content=f"This is paragraph content for section {headings_created}.")
            )

        # Level 2 heading (subsection)
        nodes.append(Heading(level=2, text=f"Subsection {headings_created + 1}"))
        headings_created += 1
        if headings_created >= num_headings:
            break

        # Level 3 heading (sub-subsection)
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
        assert duration < DOCUMENT_GENERATION_SANITY_THRESHOLD, (
            f"Document generation took {duration:.2f}s "
            f"(should be < {DOCUMENT_GENERATION_SANITY_THRESHOLD}s)"
        )

    def test_tree_building_1000_headings_performance(self):
        """
        Requirement 17.1: Documents with up to 1000 headings SHALL render
        tree view within 1 second.

        Status: Task 10.1 (incremental parsing) COMPLETE
        - Implemented line position caching to eliminate O(n²) behavior
        - Tree building now uses O(n) cached lookups instead of repeated traversals
        - Target: ≤ 1.0s for 1000 headings

        This test verifies the optimization successfully meets the requirement.
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

        # Requirement 17.1: Must complete within 1 second
        assert duration <= TREE_BUILDING_TARGET_THRESHOLD, (
            f"Tree building took {duration:.3f}s "
            f"(requirement: ≤ {TREE_BUILDING_TARGET_THRESHOLD}s)"
        )

    @pytest.mark.parametrize(
        "operation_name,operation_func,node_args",
        [
            ("promote", lambda doc, node_id: StructureOperations.promote(doc, node_id), ["h2-10"]),
            ("demote", lambda doc, node_id: StructureOperations.demote(doc, node_id), ["h1-10"]),
            (
                "move_up",
                lambda doc, node_id: StructureOperations.move_up(doc, node_id),
                ["h1-50"],
            ),
            (
                "move_down",
                lambda doc, node_id: StructureOperations.move_down(doc, node_id),
                ["h1-50"],
            ),
            (
                "nest",
                lambda doc, node_id, parent_id: StructureOperations.nest(doc, node_id, parent_id),
                ["h2-50", "h1-20"],
            ),
            (
                "unnest",
                lambda doc, node_id: StructureOperations.unnest(doc, node_id),
                ["h3-50"],
            ),
        ],
    )
    def test_structural_operation_on_large_document_within_2_seconds(
        self, operation_name, operation_func, node_args
    ):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Tests all structural operations (promote, demote, move_up, move_down,
        nest, unnest) on a document with 1000 headings.
        """
        doc = generate_large_document(1000)

        # Execute operation with performance monitoring
        with self.monitor.measure(f"{operation_name}_large"):
            result = operation_func(doc, *node_args)

        # Get the actual duration
        stats = self.monitor.get_stats(f"{operation_name}_large")
        assert stats is not None
        duration = stats.average_duration

        # Verify operation succeeded
        assert result.success, f"{operation_name} operation failed: {result.error}"

        # Performance requirement: ≤ 2 seconds
        assert duration <= STRUCTURAL_OPERATION_THRESHOLD, (
            f"{operation_name} took {duration:.3f}s "
            f"(required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
        )

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

            # Verify each operation succeeded
            assert result.success, f"{op_name} operation failed: {result.error}"

            # Re-parse for next operation (current architecture limitation)
            if result.document:
                doc = Document.from_string(result.document)

            stats = self.monitor.get_stats(op_name)
            assert stats is not None
            total_time += stats.average_duration

        # All operations combined should be reasonably fast
        assert total_time < SEQUENTIAL_OPERATIONS_THRESHOLD, (
            f"Sequential operations took {total_time:.3f}s "
            f"(should be < {SEQUENTIAL_OPERATIONS_THRESHOLD}s)"
        )

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
        assert memory_increase < MEMORY_THRESHOLD_MB, (
            f"Memory increase: {memory_increase:.2f}MB (should be < {MEMORY_THRESHOLD_MB}MB)"
        )

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

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
        # Force garbage collection before each test
        gc.collect()

    def test_tree_building_scales_linearly(self):
        """
        Test: Tree building should scale approximately linearly with
        document size (not exponentially).

        Status: Task 10.1 (incremental parsing) COMPLETE
        - Implemented line position caching with O(n) complexity
        - Scaling should now be approximately linear
        - Target: <15x scaling ratio for 100→1000 headings (10x is ideal for perfect O(n))

        This test verifies the optimization achieves linear scaling.
        """
        sizes = [100, 500, 1000]
        durations: list[float] = []

        for size in sizes:
            doc = generate_large_document(size)

            with self.monitor.measure(f"tree_build_{size}"):
                builder = DocumentTreeBuilder(doc)
                builder.build_tree_with_ids()

            stats = self.monitor.get_stats(f"tree_build_{size}")
            assert stats is not None
            durations.append(stats.average_duration)

        # Calculate scaling ratio (100 → 1000 headings)
        ratio = durations[2] / durations[0] if durations[0] > 0 else float("inf")

        # Requirement: Linear scaling (10x data → ~15x time max)
        assert ratio < SCALING_RATIO_TARGET, (
            f"Scaling ratio: {ratio:.2f}x "
            f"(requirement: < {SCALING_RATIO_TARGET}x for linear scaling)"
        )

    def test_operation_performance_with_varying_sizes(self):
        """
        Test: Operations should maintain acceptable performance across
        different document sizes.
        """
        sizes = [100, 500, 1000]

        for size in sizes:
            doc = generate_large_document(size)

            # Test promote operation
            with self.monitor.measure(f"promote_{size}"):
                result = StructureOperations.promote(doc, "h2-5")

            assert result.success, f"Promote on {size} headings failed: {result.error}"

            # Verify performance requirement
            stats = self.monitor.get_stats(f"promote_{size}")
            assert stats is not None
            assert stats.average_duration <= STRUCTURAL_OPERATION_THRESHOLD, (
                f"Promote on {size} headings took {stats.average_duration:.3f}s "
                f"(required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
            )
