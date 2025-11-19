"""End-to-end tests for pluggable architecture (Requirement 15).

This test module validates Requirement 15: Pluggable Interface Architecture
- Interface abstraction: Multiple implementations can be swapped
- VS Code interface implementation: ExtensionBridge works end-to-end
- Shared operations: All interfaces use the same StructureOperations
- Future extensibility: New interfaces can be added easily
"""

from typing import Any

import pytest

from doctk.core import Document, Heading, Paragraph
from doctk.integration.bridge import ExtensionBridge
from doctk.integration.operations import DocumentTreeBuilder, StructureOperations
from doctk.integration.protocols import DocumentInterface, OperationResult, TreeNode


# Mock interface for testing (simpler than the one in unit tests)
class SimpleInterface(DocumentInterface):
    """Simple implementation of DocumentInterface for testing pluggability."""

    def __init__(self):
        """Initialize simple interface."""
        self.operations = StructureOperations()
        self.displayed_trees: list[TreeNode] = []
        self.errors: list[str] = []

    def display_tree(self, tree: TreeNode) -> None:
        """Record displayed tree."""
        self.displayed_trees.append(tree)

    def get_user_selection(self) -> str | None:
        """Not implemented for simple interface."""
        return None

    def apply_operation(self, operation: str) -> OperationResult:
        """Not implemented for simple interface."""
        return OperationResult(success=False, error="Not implemented")

    def show_error(self, message: str) -> None:
        """Record error message."""
        self.errors.append(message)


# Alternative CLI-like interface for demonstrating pluggability
class CLIInterface(DocumentInterface):
    """CLI-style implementation of DocumentInterface."""

    def __init__(self):
        """Initialize CLI interface."""
        self.operations = StructureOperations()
        self.output_lines: list[str] = []

    def display_tree(self, tree: TreeNode) -> None:
        """Display tree as text output."""
        self.output_lines.append(f"Tree: {tree.label}")
        for child in tree.children:
            self.output_lines.append(f"  - {child.label}")

    def get_user_selection(self) -> str | None:
        """Get selection from CLI input (simulated)."""
        return None

    def apply_operation(self, operation: str) -> OperationResult:
        """Apply operation via CLI."""
        return OperationResult(success=False, error="CLI operations not implemented in test")

    def show_error(self, message: str) -> None:
        """Show error to CLI."""
        self.output_lines.append(f"ERROR: {message}")


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        [
            Heading(level=1, text="Title", children=[], metadata={}),
            Heading(level=2, text="Section 1", children=[], metadata={}),
            Paragraph(content="Content for section 1", metadata={}),
            Heading(level=2, text="Section 2", children=[], metadata={}),
            Heading(level=3, text="Subsection", children=[], metadata={}),
        ]
    )


class TestInterfacePluggability:
    """Test that multiple interface implementations can be swapped."""

    def test_multiple_interfaces_all_implement_protocol(self):
        """Test that all interface implementations conform to the protocol."""
        # Create different interface implementations
        simple = SimpleInterface()
        cli = CLIInterface()

        # All should implement the protocol methods
        assert isinstance(simple, DocumentInterface)
        assert isinstance(cli, DocumentInterface)

        # All should have the required methods
        for interface in [simple, cli]:
            assert hasattr(interface, "display_tree")
            assert hasattr(interface, "get_user_selection")
            assert hasattr(interface, "apply_operation")
            assert hasattr(interface, "show_error")

    def test_interfaces_use_shared_operations(self):
        """Test that all interfaces use the same StructureOperations."""
        simple = SimpleInterface()
        cli = CLIInterface()

        # Both should use StructureOperations
        assert isinstance(simple.operations, StructureOperations)
        assert isinstance(cli.operations, StructureOperations)

        # Operations should be the same type (same class, different instances)
        assert type(simple.operations) == type(cli.operations)

    def test_interfaces_can_be_swapped(self, sample_document):
        """Test that interfaces can be swapped without changing core logic."""

        def use_interface(interface: DocumentInterface, doc: Document) -> None:
            """Generic function that works with any DocumentInterface."""
            # Build tree
            builder = DocumentTreeBuilder(doc)
            tree = builder.build_tree_with_ids()

            # Display via interface
            interface.display_tree(tree)

            # This function works regardless of which interface is used

        # Use with different interfaces
        simple = SimpleInterface()
        cli = CLIInterface()

        # Both should work
        use_interface(simple, sample_document)
        use_interface(cli, sample_document)

        # Verify both recorded output (in their own ways)
        assert len(simple.displayed_trees) == 1
        assert len(cli.output_lines) > 0

    def test_new_interface_can_be_added_easily(self):
        """Test that new interface implementations are easy to add."""

        class NewInterface(DocumentInterface):
            """Hypothetical new interface (e.g., JupyterLab)."""

            def __init__(self):
                """Initialize new interface."""
                self.operations = StructureOperations()
                self.notebook_cells: list[str] = []

            def display_tree(self, tree: TreeNode) -> None:
                """Display tree in notebook cell."""
                self.notebook_cells.append(f"# Tree View\n{tree.label}")

            def get_user_selection(self) -> str | None:
                """Get selection from notebook UI."""
                return None

            def apply_operation(self, operation: str) -> OperationResult:
                """Apply operation in notebook."""
                return OperationResult(success=True, document="")

            def show_error(self, message: str) -> None:
                """Show error in notebook."""
                self.notebook_cells.append(f"**Error**: {message}")

        # New interface should work immediately
        new_interface = NewInterface()
        assert isinstance(new_interface, DocumentInterface)
        assert isinstance(new_interface.operations, StructureOperations)

        # Can use it just like any other interface
        new_interface.show_error("Test error")
        assert len(new_interface.notebook_cells) == 1


class TestVSCodeInterfaceImplementation:
    """Test VS Code interface implementation via ExtensionBridge."""

    def test_extension_bridge_handles_json_rpc_requests(self, sample_document):
        """Test that ExtensionBridge correctly handles JSON-RPC requests."""
        bridge = ExtensionBridge()

        # Create a JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": sample_document.to_string(), "node_id": "h2-0"},
        }

        # Handle request
        response = bridge.handle_request(request)

        # Verify response
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["success"] is True

    def test_extension_bridge_promote_operation(self, sample_document):
        """Test promote operation through ExtensionBridge."""
        bridge = ExtensionBridge()

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": sample_document.to_string(), "node_id": "h2-0"},
        }

        response = bridge.handle_request(request)

        # Verify operation succeeded
        assert response["result"]["success"] is True
        assert "# Section 1" in response["result"]["document"]

    def test_extension_bridge_demote_operation(self, sample_document):
        """Test demote operation through ExtensionBridge."""
        bridge = ExtensionBridge()

        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "demote",
            "params": {"document": sample_document.to_string(), "node_id": "h1-0"},
        }

        response = bridge.handle_request(request)

        # Verify operation succeeded
        assert response["result"]["success"] is True
        assert "## Title" in response["result"]["document"]

    def test_extension_bridge_move_up_operation(self, sample_document):
        """Test move_up operation through ExtensionBridge."""
        bridge = ExtensionBridge()

        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "move_up",
            "params": {"document": sample_document.to_string(), "node_id": "h2-1"},
        }

        response = bridge.handle_request(request)

        # Verify operation succeeded
        assert response["result"]["success"] is True
        # Section 2 should now be before Section 1
        result_doc = response["result"]["document"]
        assert result_doc.index("Section 2") < result_doc.index("Section 1")

    def test_extension_bridge_move_down_operation(self, sample_document):
        """Test move_down operation through ExtensionBridge."""
        bridge = ExtensionBridge()

        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "move_down",
            "params": {"document": sample_document.to_string(), "node_id": "h2-0"},
        }

        response = bridge.handle_request(request)

        # Verify operation succeeded
        assert response["result"]["success"] is True
        # Section 1 should now be after Section 2
        result_doc = response["result"]["document"]
        assert result_doc.index("Section 1") > result_doc.index("Section 2")

    def test_extension_bridge_get_document_tree(self, sample_document):
        """Test get_document_tree method through ExtensionBridge."""
        bridge = ExtensionBridge()

        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "get_document_tree",
            "params": {"document": sample_document.to_string()},
        }

        response = bridge.handle_request(request)

        # Verify tree structure
        assert "result" in response
        result = response["result"]
        assert "root" in result
        tree = result["root"]
        assert tree["id"] == "root"
        assert len(tree["children"]) > 0
        assert tree["children"][0]["label"] == "Title"

    def test_extension_bridge_error_handling(self):
        """Test that ExtensionBridge handles errors correctly."""
        bridge = ExtensionBridge()

        # Invalid JSON-RPC version
        request = {"jsonrpc": "1.0", "id": 1, "method": "promote", "params": {}}

        response = bridge.handle_request(request)

        # Should return error
        assert "error" in response
        assert response["error"]["code"] == -32600

    def test_extension_bridge_unknown_method(self, sample_document):
        """Test that unknown methods return appropriate errors."""
        bridge = ExtensionBridge()

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown_operation",
            "params": {"document": sample_document.to_string(), "node_id": "h1-0"},
        }

        response = bridge.handle_request(request)

        # Should return error
        assert "error" in response
        assert "Unknown method" in response["error"]["message"]

    def test_extension_bridge_missing_parameters(self):
        """Test that missing parameters return appropriate errors."""
        bridge = ExtensionBridge()

        request = {"jsonrpc": "2.0", "id": 1, "method": "promote", "params": {}}

        response = bridge.handle_request(request)

        # Should return error
        assert "error" in response

    def test_extension_bridge_full_workflow(self, sample_document):
        """Test full workflow through ExtensionBridge."""
        bridge = ExtensionBridge()

        # Step 1: Get document tree
        tree_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": sample_document.to_string()},
        }
        tree_response = bridge.handle_request(tree_request)
        assert tree_response["result"]["root"]["id"] == "root"

        # Step 2: Promote a heading
        promote_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "promote",
            "params": {"document": sample_document.to_string(), "node_id": "h2-0"},
        }
        promote_response = bridge.handle_request(promote_request)
        assert promote_response["result"]["success"] is True

        # Step 3: Validate the change
        new_doc_text = promote_response["result"]["document"]
        assert "# Section 1" in new_doc_text


class TestSharedOperationsLayer:
    """Test that all interfaces share the same operations layer."""

    def test_all_interfaces_use_structure_operations(self):
        """Test that all interface types use StructureOperations."""
        simple = SimpleInterface()
        cli = CLIInterface()
        bridge = ExtensionBridge()

        # All should have operations instance
        assert hasattr(simple, "operations")
        assert hasattr(cli, "operations")
        assert hasattr(bridge, "operations")

        # All should be StructureOperations
        assert isinstance(simple.operations, StructureOperations)
        assert isinstance(cli.operations, StructureOperations)
        assert isinstance(bridge.operations, StructureOperations)

    def test_operations_produce_consistent_results(self, sample_document):
        """Test that all interfaces produce the same operation results."""
        simple = SimpleInterface()
        bridge = ExtensionBridge()

        # Promote via bridge (JSON-RPC)
        bridge_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": sample_document.to_string(), "node_id": "h2-0"},
        }
        bridge_response = bridge.handle_request(bridge_request)
        bridge_result = bridge_response["result"]["document"]

        # Promote via direct operations call (what simple interface would do)
        direct_result = simple.operations.promote(sample_document, "h2-0")

        # Results should be equivalent
        assert direct_result.success is True
        assert bridge_result == direct_result.document

    def test_interfaces_can_share_operation_instance(self):
        """Test that interfaces can share a single StructureOperations instance."""
        # Create shared operations instance
        shared_ops = StructureOperations()

        class InterfaceA(DocumentInterface):
            def __init__(self, operations: StructureOperations):
                self.operations = operations

            def display_tree(self, tree: TreeNode) -> None:
                pass

            def get_user_selection(self) -> str | None:
                return None

            def apply_operation(self, operation: str) -> OperationResult:
                return OperationResult(success=False, error="")

            def show_error(self, message: str) -> None:
                pass

        class InterfaceB(DocumentInterface):
            def __init__(self, operations: StructureOperations):
                self.operations = operations

            def display_tree(self, tree: TreeNode) -> None:
                pass

            def get_user_selection(self) -> str | None:
                return None

            def apply_operation(self, operation: str) -> OperationResult:
                return OperationResult(success=False, error="")

            def show_error(self, message: str) -> None:
                pass

        # Both interfaces can share the same operations instance
        interface_a = InterfaceA(shared_ops)
        interface_b = InterfaceB(shared_ops)

        assert interface_a.operations is interface_b.operations


class TestArchitecturalSeparation:
    """Test clear separation between interface and core layers."""

    def test_interfaces_dont_depend_on_each_other(self):
        """Test that interface implementations are independent."""
        # SimpleInterface should work without ExtensionBridge
        simple = SimpleInterface()
        assert isinstance(simple, DocumentInterface)

        # CLIInterface should work without either
        cli = CLIInterface()
        assert isinstance(cli, DocumentInterface)

        # ExtensionBridge should work independently
        bridge = ExtensionBridge()
        assert hasattr(bridge, "handle_request")

    def test_core_operations_independent_of_interfaces(self, sample_document):
        """Test that core operations work without any interface."""
        # StructureOperations should work independently
        ops = StructureOperations()

        # Can use directly without any interface
        result = ops.promote(sample_document, "h2-0")

        assert result.success is True
        assert "# Section 1" in result.document

    def test_document_tree_builder_independent(self, sample_document):
        """Test that DocumentTreeBuilder works independently."""
        # Can build tree without any interface
        builder = DocumentTreeBuilder(sample_document)
        tree = builder.build_tree_with_ids()

        assert tree.id == "root"
        assert len(tree.children) > 0

    def test_interfaces_reuse_core_without_modification(self, sample_document):
        """Test that adding new interfaces doesn't modify core."""
        # Take snapshot of StructureOperations methods
        ops = StructureOperations()
        original_methods = set(dir(ops))

        # Create a new interface (shouldn't modify StructureOperations)
        class FutureInterface(DocumentInterface):
            def __init__(self):
                self.operations = StructureOperations()

            def display_tree(self, tree: TreeNode) -> None:
                pass

            def get_user_selection(self) -> str | None:
                return None

            def apply_operation(self, operation: str) -> OperationResult:
                return OperationResult(success=False, error="")

            def show_error(self, message: str) -> None:
                pass

        future = FutureInterface()

        # StructureOperations should be unchanged
        new_methods = set(dir(future.operations))
        assert original_methods == new_methods


class TestRealWorldScenarios:
    """Test real-world usage scenarios of the pluggable architecture."""

    def test_vs_code_extension_scenario(self, sample_document):
        """Simulate VS Code extension workflow."""
        bridge = ExtensionBridge()

        # 1. Extension requests document tree
        tree_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": sample_document.to_string()},
        }
        tree_resp = bridge.handle_request(tree_req)
        assert "result" in tree_resp

        # 2. User clicks "promote" in tree view
        promote_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "promote",
            "params": {"document": sample_document.to_string(), "node_id": "h3-0"},
        }
        promote_resp = bridge.handle_request(promote_req)
        assert promote_resp["result"]["success"] is True

        # 3. Extension applies granular edits
        modified_ranges = promote_resp["result"]["modified_ranges"]
        assert modified_ranges is not None
        assert len(modified_ranges) > 0

    def test_cli_tool_scenario(self, sample_document):
        """Simulate CLI tool workflow."""
        cli = CLIInterface()
        ops = StructureOperations()

        # 1. Load and display document
        builder = DocumentTreeBuilder(sample_document)
        tree = builder.build_tree_with_ids()
        cli.display_tree(tree)

        assert len(cli.output_lines) > 0

        # 2. Execute operation directly
        result = ops.promote(sample_document, "h2-0")

        # 3. Display result or error
        if result.success:
            cli.output_lines.append(f"Success: {result.document[:50]}...")
        else:
            cli.show_error(result.error)

        assert len(cli.output_lines) > 1

    def test_future_jupyter_scenario(self, sample_document):
        """Simulate future JupyterLab integration."""

        class JupyterInterface(DocumentInterface):
            """Hypothetical Jupyter interface."""

            def __init__(self):
                self.operations = StructureOperations()
                self.outputs: list[dict[str, Any]] = []

            def display_tree(self, tree: TreeNode) -> None:
                """Display as Jupyter notebook cell output."""
                self.outputs.append({"type": "tree", "data": tree.label})

            def get_user_selection(self) -> str | None:
                return None

            def apply_operation(self, operation: str) -> OperationResult:
                return OperationResult(success=False, error="")

            def show_error(self, message: str) -> None:
                """Display error in Jupyter."""
                self.outputs.append({"type": "error", "message": message})

        jupyter = JupyterInterface()

        # Can use same StructureOperations
        result = jupyter.operations.promote(sample_document, "h2-0")
        assert result.success is True

        # Can display tree
        builder = DocumentTreeBuilder(sample_document)
        tree = builder.build_tree_with_ids()
        jupyter.display_tree(tree)

        assert len(jupyter.outputs) == 1
        assert jupyter.outputs[0]["type"] == "tree"
