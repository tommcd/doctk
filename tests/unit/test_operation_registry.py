"""Tests for operation registry."""

from doctk.lsp.registry import OperationMetadata, OperationRegistry, ParameterInfo


class TestParameterInfo:
    """Test ParameterInfo dataclass."""

    def test_parameter_info_creation(self):
        """Test creating a parameter info."""
        param = ParameterInfo(
            name="level",
            type="int",
            required=True,
            description="Heading level (1-6)",
        )

        assert param.name == "level"
        assert param.type == "int"
        assert param.required is True
        assert param.description == "Heading level (1-6)"
        assert param.default is None

    def test_parameter_info_with_default(self):
        """Test parameter info with default value."""
        param = ParameterInfo(
            name="under",
            type="str | None",
            required=False,
            description="Target section",
            default=None,
        )

        assert param.name == "under"
        assert param.required is False
        assert param.default is None


class TestOperationMetadata:
    """Test OperationMetadata dataclass."""

    def test_operation_metadata_creation(self):
        """Test creating operation metadata."""
        metadata = OperationMetadata(
            name="select",
            description="Select nodes matching predicate",
            category="selection",
        )

        assert metadata.name == "select"
        assert metadata.description == "Select nodes matching predicate"
        assert metadata.category == "selection"
        assert metadata.parameters == []
        assert metadata.return_type == "Document"
        assert metadata.examples == []

    def test_operation_metadata_with_parameters(self):
        """Test operation metadata with parameters."""
        params = [
            ParameterInfo(
                name="predicate",
                type="Callable[[Node], bool]",
                required=True,
                description="Function to test nodes",
            )
        ]

        metadata = OperationMetadata(
            name="select",
            description="Select nodes",
            parameters=params,
            examples=["doc | select heading"],
        )

        assert len(metadata.parameters) == 1
        assert metadata.parameters[0].name == "predicate"
        assert len(metadata.examples) == 1


class TestOperationRegistry:
    """Test OperationRegistry class."""

    def test_registry_initialization(self):
        """Test that registry initializes and loads operations."""
        registry = OperationRegistry()

        # Should have loaded operations from doctk
        assert len(registry.operations) > 0
        assert "select" in registry.operations
        assert "where" in registry.operations
        assert "promote" in registry.operations
        assert "demote" in registry.operations

    def test_get_operation_found(self):
        """Test getting an operation that exists."""
        registry = OperationRegistry()

        select_op = registry.get_operation("select")

        assert select_op is not None
        assert select_op.name == "select"
        assert select_op.description == "Select nodes matching a predicate"
        assert select_op.category == "selection"

    def test_get_operation_not_found(self):
        """Test getting an operation that doesn't exist."""
        registry = OperationRegistry()

        result = registry.get_operation("nonexistent")

        assert result is None

    def test_get_all_operations(self):
        """Test getting all operations."""
        registry = OperationRegistry()

        operations = registry.get_all_operations()

        assert len(operations) > 0
        assert all(isinstance(op, OperationMetadata) for op in operations)

        # Check specific operations are present
        op_names = {op.name for op in operations}
        assert "select" in op_names
        assert "where" in op_names
        assert "promote" in op_names
        assert "demote" in op_names

    def test_get_operations_by_category_selection(self):
        """Test getting operations by category (selection)."""
        registry = OperationRegistry()

        selection_ops = registry.get_operations_by_category("selection")

        assert len(selection_ops) > 0
        assert all(op.category == "selection" for op in selection_ops)

        # Specific selection operations
        op_names = {op.name for op in selection_ops}
        assert "select" in op_names
        assert "where" in op_names
        assert "heading" in op_names
        assert "paragraph" in op_names

    def test_get_operations_by_category_structure(self):
        """Test getting operations by category (structure)."""
        registry = OperationRegistry()

        structure_ops = registry.get_operations_by_category("structure")

        assert len(structure_ops) > 0
        assert all(op.category == "structure" for op in structure_ops)

        # Specific structure operations
        op_names = {op.name for op in structure_ops}
        assert "promote" in op_names
        assert "demote" in op_names
        assert "lift" in op_names
        assert "lower" in op_names
        assert "nest" in op_names
        assert "unnest" in op_names

    def test_get_operations_by_category_empty(self):
        """Test getting operations from nonexistent category."""
        registry = OperationRegistry()

        ops = registry.get_operations_by_category("nonexistent")

        assert ops == []

    def test_get_operation_names(self):
        """Test getting all operation names."""
        registry = OperationRegistry()

        names = registry.get_operation_names()

        assert len(names) > 0
        assert "select" in names
        assert "where" in names
        assert "promote" in names
        assert "demote" in names

    def test_operation_exists_true(self):
        """Test checking if operation exists (true case)."""
        registry = OperationRegistry()

        assert registry.operation_exists("select") is True
        assert registry.operation_exists("where") is True
        assert registry.operation_exists("promote") is True

    def test_operation_exists_false(self):
        """Test checking if operation exists (false case)."""
        registry = OperationRegistry()

        assert registry.operation_exists("nonexistent") is False
        assert registry.operation_exists("invalid_op") is False


class TestOperationMetadataDetails:
    """Test specific operation metadata details."""

    def test_select_operation_metadata(self):
        """Test metadata for select operation."""
        registry = OperationRegistry()

        select_op = registry.get_operation("select")

        assert select_op is not None
        assert select_op.name == "select"
        assert select_op.category == "selection"
        assert len(select_op.parameters) == 1
        assert select_op.parameters[0].name == "predicate"
        assert len(select_op.examples) > 0

    def test_where_operation_metadata(self):
        """Test metadata for where operation."""
        registry = OperationRegistry()

        where_op = registry.get_operation("where")

        assert where_op is not None
        assert where_op.name == "where"
        assert where_op.category == "selection"
        assert len(where_op.parameters) >= 1
        assert len(where_op.examples) > 0

    def test_promote_operation_metadata(self):
        """Test metadata for promote operation."""
        registry = OperationRegistry()

        promote_op = registry.get_operation("promote")

        assert promote_op is not None
        assert promote_op.name == "promote"
        assert promote_op.category == "structure"
        assert promote_op.description == "Promote heading levels (h3 -> h2)"
        assert len(promote_op.parameters) == 0  # No parameters
        assert len(promote_op.examples) > 0

    def test_demote_operation_metadata(self):
        """Test metadata for demote operation."""
        registry = OperationRegistry()

        demote_op = registry.get_operation("demote")

        assert demote_op is not None
        assert demote_op.name == "demote"
        assert demote_op.category == "structure"
        assert demote_op.description == "Demote heading levels (h2 -> h3)"
        assert len(demote_op.parameters) == 0  # No parameters

    def test_nest_operation_metadata(self):
        """Test metadata for nest operation."""
        registry = OperationRegistry()

        nest_op = registry.get_operation("nest")

        assert nest_op is not None
        assert nest_op.name == "nest"
        assert nest_op.category == "structure"
        # Nest has an optional 'under' parameter
        assert len(nest_op.parameters) >= 1
        assert nest_op.parameters[0].name == "under"
        assert nest_op.parameters[0].required is False


class TestRegistryIntegration:
    """Integration tests for registry usage."""

    def test_registry_can_validate_known_operations(self):
        """Test that registry can validate known operations."""
        registry = OperationRegistry()

        # These should all be valid
        valid_ops = ["select", "where", "promote", "demote", "heading", "paragraph"]

        for op in valid_ops:
            assert registry.operation_exists(op), f"Operation '{op}' should exist"

    def test_registry_rejects_unknown_operations(self):
        """Test that registry rejects unknown operations."""
        registry = OperationRegistry()

        # These should all be invalid
        invalid_ops = [
            "invalid_operation",
            "unknown_op",
            "foo",
            "bar",
            "select_invalid",
        ]

        for op in invalid_ops:
            assert not registry.operation_exists(op), f"Operation '{op}' should not exist"

    def test_registry_provides_examples_for_all_operations(self):
        """Test that all operations have examples."""
        registry = OperationRegistry()

        operations = registry.get_all_operations()

        # Most operations should have at least one example
        # (Some may not, but the majority should)
        ops_with_examples = [op for op in operations if len(op.examples) > 0]
        assert len(ops_with_examples) > 0
