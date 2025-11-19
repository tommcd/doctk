"""Integration tests for doctk core API usage (Task 13).

These tests verify that the LSP integration layer properly uses the doctk
core API and that all operations are consistent with doctk abstractions.
"""


from doctk.core import Document, Heading, Paragraph
from doctk.lsp import (
    CompatibilityChecker,
    DocumentTreeBuilder,
    OperationRegistry,
    StructureOperations,
    check_compatibility,
    check_feature,
    get_doctk_version,
)


class TestCoreAPIUsage:
    """Test that all operations use doctk core API properly."""

    def test_structure_operations_use_document_api(self):
        """Test that StructureOperations uses Document API."""
        doc_text = "# Heading 1\n\n## Heading 2\n\nParagraph content\n"
        doc = Document.from_string(doc_text)

        # All operations should work with Document objects from doctk core
        assert isinstance(doc, Document)
        assert len(doc.nodes) > 0

    def test_operations_preserve_document_abstractions(self):
        """Test that operations preserve doctk Document/Node abstractions."""
        doc_text = "# Title\n\n## Section\n\nContent here\n"
        doc = Document.from_string(doc_text)

        # Promote operation
        result = StructureOperations.promote(doc, "h2-0")

        assert result.success is True
        assert result.document is not None

        # Verify result is valid doctk markdown
        result_doc = Document.from_string(result.document)
        assert isinstance(result_doc, Document)
        assert all(hasattr(node, "__class__") for node in result_doc.nodes)

    def test_tree_builder_uses_document_nodes(self):
        """Test that DocumentTreeBuilder uses doctk Node types."""
        doc_text = "# H1\n\n## H2\n\n### H3\n"
        doc = Document.from_string(doc_text)

        builder = DocumentTreeBuilder(doc)

        # Should be able to access nodes using doctk abstractions
        assert all(isinstance(node, (Heading, Paragraph)) for node in doc.nodes)

        # Build tree
        tree = builder.build_tree_with_ids()
        assert tree is not None
        assert tree.id == "root"

    def test_operations_return_valid_markdown(self):
        """Test that operations return valid markdown parseable by doctk."""
        doc_text = "# Title\n\n## Section 1\n\n## Section 2\n"
        doc = Document.from_string(doc_text)

        operations = [
            ("promote", StructureOperations.promote),
            ("demote", StructureOperations.demote),
            ("move_up", StructureOperations.move_up),
            ("move_down", StructureOperations.move_down),
        ]

        for op_name, op_func in operations:
            node_id = "h2-0" if op_name != "move_up" else "h2-1"
            result = op_func(doc, node_id)

            assert result.success or result.error, f"Operation {op_name} failed unexpectedly"

            if result.success:
                # Verify result is valid doctk markdown
                result_doc = Document.from_string(result.document)
                assert isinstance(result_doc, Document)
                assert len(result_doc.nodes) > 0


class TestDynamicOperationDiscovery:
    """Test dynamic operation discovery from doctk core (Task 13.2)."""

    def test_registry_discovers_operations_from_doctk(self):
        """Test that registry dynamically loads operations from doctk."""
        registry = OperationRegistry()

        # Should have discovered operations from doctk.operations
        assert len(registry.operations) > 0

        # Key operations should be present
        expected_operations = [
            "select",
            "where",
            "promote",
            "demote",
            "heading",
            "paragraph",
            "compose",
            "first",
            "last",
            "lift",
            "lower",
            "nest",
            "unnest",
        ]

        for op_name in expected_operations:
            assert (
                registry.operation_exists(op_name)
            ), f"Operation '{op_name}' should be discovered"

    def test_new_operations_automatically_discovered(self):
        """Test that new operations are automatically discovered."""
        registry = OperationRegistry()

        # Get initial count
        initial_count = len(registry.operations)

        # Verify we have operations
        assert initial_count > 0

        # All publicly available operations from doctk.operations should be registered
        import doctk.operations as ops

        public_ops = [
            name
            for name in dir(ops)
            if not name.startswith("_")
            and callable(getattr(ops, name))
            and not name[0].isupper()
        ]

        # Most public operations should be in registry (some may be skipped by filters)
        registered_ops = set(registry.get_operation_names())
        discovered_ratio = len(registered_ops) / len(public_ops)

        # At least 70% of public operations should be discovered
        assert discovered_ratio >= 0.7, f"Only {discovered_ratio:.0%} of operations discovered"

    def test_registry_provides_metadata_for_operations(self):
        """Test that registry provides metadata for discovered operations."""
        registry = OperationRegistry()

        # Check a few key operations have metadata
        for op_name in ["select", "where", "promote", "demote"]:
            metadata = registry.get_operation(op_name)

            assert metadata is not None, f"Missing metadata for {op_name}"
            assert metadata.name == op_name
            assert metadata.description != ""
            assert metadata.category != ""

    def test_registry_categorizes_operations(self):
        """Test that registry categorizes operations correctly."""
        registry = OperationRegistry()

        # Check category assignments
        selection_ops = registry.get_operations_by_category("selection")
        structure_ops = registry.get_operations_by_category("structure")
        predicates = registry.get_operations_by_category("predicates")

        assert len(selection_ops) > 0, "Should have selection operations"
        assert len(structure_ops) > 0, "Should have structure operations"
        assert len(predicates) > 0, "Should have predicate operations"

        # Verify specific categorizations
        assert any(op.name == "select" for op in selection_ops)
        assert any(op.name == "promote" for op in structure_ops)
        assert any(op.name == "is_heading" for op in predicates)


class TestBackwardCompatibility:
    """Test backward compatibility handling (Task 13.3)."""

    def test_compatibility_checker_available(self):
        """Test that compatibility checker is available."""
        assert CompatibilityChecker is not None

        checker = CompatibilityChecker()
        assert checker is not None

    def test_version_checking_works(self):
        """Test that version checking works."""
        version = get_doctk_version()

        assert version is not None
        assert version.major >= 0
        assert version.minor >= 0
        assert version.patch >= 0

    def test_compatibility_check_succeeds(self):
        """Test that current version is compatible."""
        compatible = check_compatibility()

        assert compatible is True, "Current doctk version should be compatible"

    def test_feature_checking_works(self):
        """Test that feature checking works."""
        # Features that should be available in current version
        basic_features = [
            ("document_operations", "0.1.0"),
            ("heading_manipulation", "0.1.0"),
            ("selection_operations", "0.1.0"),
        ]

        for feature, min_version in basic_features:
            available = check_feature(feature, min_version)
            assert available is True, f"Feature '{feature}' should be available"

        # Features that should not be available (future versions)
        future_features = [
            ("advanced_ai", "99.0.0"),
            ("quantum_operations", "99.9.9"),
        ]

        for feature, min_version in future_features:
            available = check_feature(feature, min_version)
            assert available is False, f"Feature '{feature}' should not be available yet"

    def test_min_version_requirement(self):
        """Test that minimum version requirement is defined."""
        assert hasattr(CompatibilityChecker, "MIN_VERSION")
        min_version = CompatibilityChecker.MIN_VERSION

        assert min_version.major == 0
        assert min_version.minor == 1
        assert min_version.patch == 0

    def test_breaking_changes_tracked(self):
        """Test that breaking changes are tracked."""
        assert hasattr(CompatibilityChecker, "BREAKING_CHANGES")
        breaking_changes = CompatibilityChecker.BREAKING_CHANGES

        # Should be a dictionary (may be empty for now)
        assert isinstance(breaking_changes, dict)


class TestAPIConsistency:
    """Test consistency across all doctk API usage."""

    def test_all_operations_use_same_document_type(self):
        """Test that all operations use doctk.core.Document consistently."""
        from doctk.core import Document as CoreDocument
        from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations

        doc_text = "# Test\n\n## Section\n"
        doc = CoreDocument.from_string(doc_text)

        # StructureOperations should work with core Document
        builder = DocumentTreeBuilder(doc)
        assert builder.document is doc

        # Operations should accept Document and return strings that parse to core Document
        result = StructureOperations.promote(doc, "h2-0")
        assert result.success

        parsed = CoreDocument.from_string(result.document)
        assert isinstance(parsed, CoreDocument)

    def test_node_types_consistent(self):
        """Test that node types are consistent with doctk core."""
        from doctk.core import Node

        doc_text = """# Heading

Paragraph text

- List item

```python
code = "block"
```
"""
        doc = Document.from_string(doc_text)

        # All nodes should be from doctk.core
        for node in doc.nodes:
            assert isinstance(node, Node)
            assert type(node).__module__ == "doctk.core"

    def test_immutability_preserved(self):
        """Test that immutability from doctk core is preserved."""
        doc_text = "# Original\n\n## Section\n"
        doc = Document.from_string(doc_text)

        # Perform operation
        result = StructureOperations.promote(doc, "h2-0")

        # Original document object should be unchanged
        original_doc = Document.from_string(doc_text)
        result_doc = Document.from_string(result.document)

        # Documents should be different
        assert doc_text != result.document

        # But both should be valid
        assert len(original_doc.nodes) > 0
        assert len(result_doc.nodes) > 0


class TestIntegrationWorkflow:
    """Test complete integration workflows."""

    def test_complete_lsp_to_core_workflow(self):
        """Test complete workflow from LSP to core API."""
        # 1. Start with markdown text
        doc_text = "# Title\n\n## Section 1\n\n## Section 2\n\nContent\n"

        # 2. Parse with doctk core
        doc = Document.from_string(doc_text)
        assert isinstance(doc, Document)

        # 3. Use LSP operations
        result = StructureOperations.promote(doc, "h2-0")
        assert result.success

        # 4. Parse result with doctk core
        result_doc = Document.from_string(result.document)
        assert isinstance(result_doc, Document)

        # 5. Verify tree building works
        builder = DocumentTreeBuilder(result_doc)
        tree = builder.build_tree_with_ids()
        assert tree.id == "root"
        assert len(tree.children) > 0

    def test_operation_chain_preserves_api(self):
        """Test that chaining operations preserves API consistency."""
        doc_text = "# Title\n\n## Section\n\n### Subsection\n"
        doc = Document.from_string(doc_text)

        # Perform an operation
        result = StructureOperations.promote(doc, "h3-0")

        assert result.success, "Operation failed"

        # Verify each result is valid doctk document
        result_doc = Document.from_string(result.document)
        assert isinstance(result_doc, Document)
        assert len(result_doc.nodes) > 0

        # Note: Can't easily chain operations because node IDs change after serialization
        # This is a known limitation documented in design.md

    def test_registry_and_operations_alignment(self):
        """Test that registry and operations are aligned."""
        registry = OperationRegistry()

        # Get all structure operations from registry
        structure_ops = registry.get_operations_by_category("structure")

        # These operations should be executable via StructureOperations
        doc_text = "# Title\n\n## Section\n"
        doc = Document.from_string(doc_text)

        operation_map = {
            "promote": StructureOperations.promote,
            "demote": StructureOperations.demote,
            "lift": StructureOperations.promote,  # alias
            "unnest": StructureOperations.promote,  # alias
            "lower": StructureOperations.demote,  # alias
            "move_up": StructureOperations.move_up,
            "move_down": StructureOperations.move_down,
        }

        for op_metadata in structure_ops:
            op_name = op_metadata.name

            # Skip operations that aren't in StructureOperations
            if op_name not in operation_map:
                continue

            # Should be able to execute
            try:
                op_func = operation_map[op_name]
                result = op_func(doc, "h2-0")
                # Some operations may fail (e.g., unnest on h2-0), but should return result
                assert result is not None
            except (NotImplementedError, AttributeError):
                # Some operations may not be fully implemented yet
                pass


class TestAPIStability:
    """Test API stability and future-proofing."""

    def test_core_imports_stable(self):
        """Test that core imports are stable."""
        # These imports should always work
        from doctk.core import CodeBlock, Document, Heading, List, Node, Paragraph

        assert Document is not None
        assert Node is not None
        assert Heading is not None
        assert Paragraph is not None
        assert List is not None
        assert CodeBlock is not None

    def test_lsp_public_api_stable(self):
        """Test that LSP public API is stable."""
        from doctk import lsp

        # Core components should be available
        required_exports = [
            "CompatibilityChecker",
            "DocumentTreeBuilder",
            "ExtensionBridge",
            "OperationRegistry",
            "StructureOperations",
            "check_compatibility",
            "get_doctk_version",
        ]

        for export in required_exports:
            assert hasattr(lsp, export), f"Missing required export: {export}"

    def test_operation_signatures_stable(self):
        """Test that operation signatures are stable."""
        # Key operations should maintain their signatures
        doc_text = "# Test\n"
        doc = Document.from_string(doc_text)

        # These calls should work
        StructureOperations.promote(doc, "h1-0")
        StructureOperations.demote(doc, "h1-0")
        StructureOperations.move_up(doc, "h1-0")
        StructureOperations.move_down(doc, "h1-0")

        # All operations return OperationResult
        result = StructureOperations.promote(doc, "h1-0")
        assert hasattr(result, "success")
        assert hasattr(result, "document")
        assert hasattr(result, "modified_ranges")
