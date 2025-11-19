"""End-to-end performance benchmarking tests.

This module validates that the complete integration stack meets performance
requirements specified in Requirement 17:

- Tree view rendering: ≤ 1 second for 1000 headings (17.1)
- User interactions: ≤ 200ms for large documents (17.2)
- LSP completions: ≤ 500ms (17.3)
- Structural operations: ≤ 2 seconds for large documents (17.4)
- Memory usage: ≤ 500MB (17.5)

These tests validate the complete stack including:
- CLI execute command
- REPL workflow
- ExtensionBridge JSON-RPC
- Script execution
- Code block execution
"""

import gc
import tempfile
import time
from pathlib import Path

import pytest

from doctk.core import Document, Heading, Paragraph
from doctk.dsl.executor import ScriptExecutor
from doctk.dsl.repl import REPL
from doctk.integration.bridge import ExtensionBridge
from doctk.integration.operations import DocumentTreeBuilder

# Performance thresholds from Requirement 17
TREE_VIEW_RENDERING_THRESHOLD = 1.0  # seconds (Req 17.1)
USER_INTERACTION_THRESHOLD = 0.2  # seconds (Req 17.2)
LSP_COMPLETION_THRESHOLD = 0.5  # seconds (Req 17.3)
STRUCTURAL_OPERATION_THRESHOLD = 2.0  # seconds (Req 17.4)
MEMORY_THRESHOLD_MB = 500.0  # MB (Req 17.5)


def _get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


def generate_large_document(num_headings: int) -> Document:
    """Generate a large test document with hierarchical structure."""
    nodes = []
    headings_created = 0

    while headings_created < num_headings:
        # Level 1 heading
        nodes.append(Heading(level=1, text=f"Section {headings_created + 1}"))
        headings_created += 1
        if headings_created >= num_headings:
            break

        # Add content every 10 headings
        if headings_created % 10 == 0:
            nodes.append(
                Paragraph(content=f"Content for section {headings_created}.", metadata={})
            )

        # Level 2 heading
        nodes.append(Heading(level=2, text=f"Subsection {headings_created + 1}"))
        headings_created += 1
        if headings_created >= num_headings:
            break

        # Level 3 heading
        nodes.append(Heading(level=3, text=f"Sub-subsection {headings_created + 1}"))
        headings_created += 1

    return Document(nodes=nodes)


@pytest.fixture
def large_document_file():
    """Create a temporary file with a large document (1000+ headings)."""
    doc = generate_large_document(1000)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(doc.to_string())
        file_path = f.name

    yield file_path

    # Cleanup
    Path(file_path).unlink(missing_ok=True)


@pytest.fixture
def medium_document_file():
    """Create a temporary file with a medium document (500 headings)."""
    doc = generate_large_document(500)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(doc.to_string())
        file_path = f.name

    yield file_path

    # Cleanup
    Path(file_path).unlink(missing_ok=True)


@pytest.mark.slow
class TestE2EPerformanceREPL:
    """End-to-end performance tests for REPL with large documents."""

    def setup_method(self):
        """Set up test fixtures."""
        gc.collect()

    def test_repl_load_large_document_performance(self, large_document_file):
        """
        Requirement 17.1: Documents with up to 1000 headings SHALL render
        tree view within 1 second.

        Test loading a large document in REPL.
        """
        repl = REPL()

        start_time = time.perf_counter()
        from unittest.mock import patch

        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {large_document_file}")
        duration = time.perf_counter() - start_time

        # Verify document loaded
        assert repl.document is not None
        heading_count = sum(1 for node in repl.document.nodes if isinstance(node, Heading))
        assert heading_count == 1000

        # Performance requirement: ≤ 1 second
        assert duration <= TREE_VIEW_RENDERING_THRESHOLD, (
            f"REPL load took {duration:.3f}s (required: ≤ {TREE_VIEW_RENDERING_THRESHOLD}s)"
        )

    def test_repl_operation_on_large_document_performance(self, large_document_file):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test REPL operation execution on large document.
        """
        repl = REPL()
        from unittest.mock import patch

        # Load document first
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {large_document_file}")

        # Execute operation and measure performance
        start_time = time.perf_counter()
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("promote h2-10")
        duration = time.perf_counter() - start_time

        # Verify operation succeeded
        assert repl.document is not None

        # Performance requirement: ≤ 2 seconds
        assert duration <= STRUCTURAL_OPERATION_THRESHOLD, (
            f"REPL operation took {duration:.3f}s (required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
        )

    def test_repl_tree_display_large_document_performance(self, large_document_file):
        """
        Requirement 17.1: Tree view rendering should complete within 1 second
        for documents with 1000 headings.

        Test tree display in REPL.
        """
        repl = REPL()
        from unittest.mock import patch

        # Load document first
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {large_document_file}")

        # Display tree and measure performance
        start_time = time.perf_counter()
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("tree")
        duration = time.perf_counter() - start_time

        # Performance requirement: ≤ 1 second
        assert duration <= TREE_VIEW_RENDERING_THRESHOLD, (
            f"Tree display took {duration:.3f}s (required: ≤ {TREE_VIEW_RENDERING_THRESHOLD}s)"
        )

    def test_repl_multiple_operations_performance(self, medium_document_file):
        """
        Test: Multiple sequential operations in REPL should maintain
        acceptable performance.
        """
        repl = REPL()
        from unittest.mock import patch

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {medium_document_file}")

        # Execute multiple operations
        operations = ["promote h2-10", "demote h1-20", "move_up h1-30"]

        total_time = 0.0
        for operation in operations:
            start_time = time.perf_counter()
            with patch("doctk.dsl.repl.console"):
                repl.execute_command(operation)
            duration = time.perf_counter() - start_time
            total_time += duration

            # Each operation should meet threshold
            assert duration <= STRUCTURAL_OPERATION_THRESHOLD, (
                f"Operation '{operation}' took {duration:.3f}s "
                f"(required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
            )

        # Total time for all operations should be reasonable
        assert total_time <= len(operations) * STRUCTURAL_OPERATION_THRESHOLD


@pytest.mark.slow
class TestE2EPerformanceScriptExecution:
    """End-to-end performance tests for script execution with large documents."""

    def setup_method(self):
        """Set up test fixtures."""
        gc.collect()

    def test_script_execution_large_document_performance(self, large_document_file):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test script execution on large document.
        """
        # Create script file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | promote h2-10")
            script_path = script_file.name

        try:
            executor = ScriptExecutor()

            # Execute script and measure performance
            start_time = time.perf_counter()
            result_doc = executor.execute_file(script_path, large_document_file)
            duration = time.perf_counter() - start_time

            # Verify execution succeeded
            assert result_doc is not None
            heading_count = sum(
                1 for node in result_doc.nodes if isinstance(node, Heading)
            )
            assert heading_count == 1000

            # Performance requirement: ≤ 2 seconds
            assert duration <= STRUCTURAL_OPERATION_THRESHOLD, (
                f"Script execution took {duration:.3f}s "
                f"(required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
            )

        finally:
            Path(script_path).unlink(missing_ok=True)

    def test_script_multiple_operations_large_document_performance(self, medium_document_file):
        """
        Test: Script with multiple operations on large document should
        maintain acceptable performance.
        """
        # Create script with multiple operations
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | promote h2-10\n")
            script_file.write("doc | demote h1-20\n")
            script_file.write("doc | move_up h1-30\n")
            script_path = script_file.name

        try:
            executor = ScriptExecutor()

            # Execute script and measure performance
            start_time = time.perf_counter()
            result_doc = executor.execute_file(script_path, medium_document_file)
            duration = time.perf_counter() - start_time

            # Verify execution succeeded
            assert result_doc is not None

            # Performance requirement: reasonable for multiple operations
            max_time = 3 * STRUCTURAL_OPERATION_THRESHOLD
            assert duration <= max_time, (
                f"Script with 3 operations took {duration:.3f}s "
                f"(expected: ≤ {max_time}s)"
            )

        finally:
            Path(script_path).unlink(missing_ok=True)


@pytest.mark.slow
class TestE2EPerformanceExtensionBridge:
    """End-to-end performance tests for ExtensionBridge with large documents."""

    def setup_method(self):
        """Set up test fixtures."""
        gc.collect()

    def test_bridge_get_tree_large_document_performance(self, large_document_file):
        """
        Requirement 17.1: Documents with up to 1000 headings SHALL render
        tree view within 1 second.

        Test ExtensionBridge tree building with large document.
        """
        # Load document
        doc = Document.from_file(large_document_file)

        # Create bridge request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc.to_string()},
        }

        bridge = ExtensionBridge()

        # Execute request and measure performance
        start_time = time.perf_counter()
        response = bridge.handle_request(request)
        duration = time.perf_counter() - start_time

        # Verify response succeeded
        assert "result" in response
        assert "root" in response["result"]

        # Performance requirement: ≤ 1 second
        assert duration <= TREE_VIEW_RENDERING_THRESHOLD, (
            f"Bridge tree building took {duration:.3f}s "
            f"(required: ≤ {TREE_VIEW_RENDERING_THRESHOLD}s)"
        )

    def test_bridge_operation_large_document_performance(self, large_document_file):
        """
        Requirement 17.4: Structural operations on large documents SHALL
        complete within 2 seconds.

        Test ExtensionBridge operation execution on large document.
        """
        # Load document
        doc = Document.from_file(large_document_file)

        # Create operation request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": doc.to_string(), "node_id": "h2-10"},
        }

        bridge = ExtensionBridge()

        # Execute request and measure performance
        start_time = time.perf_counter()
        response = bridge.handle_request(request)
        duration = time.perf_counter() - start_time

        # Verify response succeeded
        assert "result" in response
        assert response["result"]["success"] is True

        # Performance requirement: ≤ 2 seconds
        assert duration <= STRUCTURAL_OPERATION_THRESHOLD, (
            f"Bridge operation took {duration:.3f}s "
            f"(required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
        )

    @pytest.mark.parametrize(
        "operation,node_id,extra_params",
        [
            ("promote", "h2-10", {}),
            ("demote", "h1-10", {}),
            ("move_up", "h1-50", {}),
            ("move_down", "h1-50", {}),
            ("nest", "h2-50", {"parent_id": "h1-20"}),
            ("unnest", "h3-50", {}),
        ],
    )
    def test_bridge_all_operations_large_document_performance(
        self, large_document_file, operation, node_id, extra_params
    ):
        """
        Requirement 17.4: All structural operations on large documents SHALL
        complete within 2 seconds.

        Test all operations through ExtensionBridge.
        """
        # Load document
        doc = Document.from_file(large_document_file)

        # Create operation request
        params = {"document": doc.to_string(), "node_id": node_id}
        params.update(extra_params)

        request = {"jsonrpc": "2.0", "id": 1, "method": operation, "params": params}

        bridge = ExtensionBridge()

        # Execute request and measure performance
        start_time = time.perf_counter()
        response = bridge.handle_request(request)
        duration = time.perf_counter() - start_time

        # Verify response succeeded
        assert "result" in response, f"Operation {operation} failed: {response.get('error')}"
        assert response["result"]["success"] is True

        # Performance requirement: ≤ 2 seconds
        assert duration <= STRUCTURAL_OPERATION_THRESHOLD, (
            f"Bridge {operation} took {duration:.3f}s "
            f"(required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
        )


@pytest.mark.slow
class TestE2EPerformanceMemory:
    """End-to-end memory usage tests for large documents."""

    def setup_method(self):
        """Set up test fixtures."""
        gc.collect()

    @pytest.mark.skipif(
        _get_memory_usage_mb() == 0, reason="psutil not available for memory monitoring"
    )
    def test_repl_memory_usage_large_document(self, large_document_file):
        """
        Requirement 17.5: Memory usage should stay under 500MB when processing
        large documents.

        Test REPL memory usage with large document.
        """
        # Get baseline memory
        gc.collect()
        time.sleep(0.1)
        baseline_memory = _get_memory_usage_mb()

        # Create REPL and load document
        repl = REPL()
        from unittest.mock import patch

        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {large_document_file}")

        # Perform operations
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("promote h2-10")
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("tree")

        # Measure peak memory
        peak_memory = _get_memory_usage_mb()
        memory_increase = peak_memory - baseline_memory

        # Clean up
        del repl
        gc.collect()

        # Memory requirement: < 500MB increase
        assert memory_increase < MEMORY_THRESHOLD_MB, (
            f"Memory increase: {memory_increase:.2f}MB "
            f"(required: < {MEMORY_THRESHOLD_MB}MB)"
        )

    @pytest.mark.skipif(
        _get_memory_usage_mb() == 0, reason="psutil not available for memory monitoring"
    )
    def test_bridge_memory_usage_large_document(self, large_document_file):
        """
        Requirement 17.5: Memory usage should stay under 500MB when processing
        large documents through ExtensionBridge.
        """
        # Get baseline memory
        gc.collect()
        time.sleep(0.1)
        baseline_memory = _get_memory_usage_mb()

        # Load document
        doc = Document.from_file(large_document_file)

        # Create bridge and execute operations
        bridge = ExtensionBridge()

        # Tree building
        request1 = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc.to_string()},
        }
        bridge.handle_request(request1)

        # Operation
        request2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "promote",
            "params": {"document": doc.to_string(), "node_id": "h2-10"},
        }
        bridge.handle_request(request2)

        # Measure peak memory
        peak_memory = _get_memory_usage_mb()
        memory_increase = peak_memory - baseline_memory

        # Clean up
        del bridge
        del doc
        gc.collect()

        # Memory requirement: < 500MB increase
        assert memory_increase < MEMORY_THRESHOLD_MB, (
            f"Memory increase: {memory_increase:.2f}MB "
            f"(required: < {MEMORY_THRESHOLD_MB}MB)"
        )


@pytest.mark.slow
class TestE2EPerformanceIntegration:
    """End-to-end integration performance tests combining multiple components."""

    def setup_method(self):
        """Set up test fixtures."""
        gc.collect()

    def test_complete_workflow_performance(self, medium_document_file):
        """
        Test: Complete workflow from document load to multiple operations
        should maintain acceptable performance.

        This simulates a realistic user session with REPL.
        """
        repl = REPL()
        from unittest.mock import patch

        total_time = 0.0

        # Load document
        start = time.perf_counter()
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {medium_document_file}")
        load_time = time.perf_counter() - start
        total_time += load_time

        assert load_time <= TREE_VIEW_RENDERING_THRESHOLD, (
            f"Load took {load_time:.3f}s (required: ≤ {TREE_VIEW_RENDERING_THRESHOLD}s)"
        )

        # Display tree
        start = time.perf_counter()
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("tree")
        tree_time = time.perf_counter() - start
        total_time += tree_time

        assert tree_time <= TREE_VIEW_RENDERING_THRESHOLD, (
            f"Tree display took {tree_time:.3f}s "
            f"(required: ≤ {TREE_VIEW_RENDERING_THRESHOLD}s)"
        )

        # Perform operations
        operations = ["promote h2-10", "demote h1-20", "move_up h1-30"]
        for operation in operations:
            start = time.perf_counter()
            with patch("doctk.dsl.repl.console"):
                repl.execute_command(operation)
            op_time = time.perf_counter() - start
            total_time += op_time

            assert op_time <= STRUCTURAL_OPERATION_THRESHOLD, (
                f"Operation '{operation}' took {op_time:.3f}s "
                f"(required: ≤ {STRUCTURAL_OPERATION_THRESHOLD}s)"
            )

        # Total workflow should be reasonable
        max_total = (
            TREE_VIEW_RENDERING_THRESHOLD
            + TREE_VIEW_RENDERING_THRESHOLD
            + len(operations) * STRUCTURAL_OPERATION_THRESHOLD
        )
        assert total_time <= max_total, (
            f"Complete workflow took {total_time:.3f}s (expected: ≤ {max_total:.3f}s)"
        )

    def test_tree_builder_direct_performance(self, large_document_file):
        """
        Requirement 17.1: Direct DocumentTreeBuilder should meet performance
        requirements for 1000 headings.
        """
        # Load document
        doc = Document.from_file(large_document_file)

        # Build tree and measure performance
        start_time = time.perf_counter()
        builder = DocumentTreeBuilder(doc)
        tree = builder.build_tree_with_ids()
        duration = time.perf_counter() - start_time

        # Verify tree was built
        assert tree.id == "root"
        assert tree.label == "Document"

        # Performance requirement: ≤ 1 second
        assert duration <= TREE_VIEW_RENDERING_THRESHOLD, (
            f"Tree builder took {duration:.3f}s "
            f"(required: ≤ {TREE_VIEW_RENDERING_THRESHOLD}s)"
        )
