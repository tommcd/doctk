"""Tests for the doctk REPL."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from doctk.core import Document, Heading
from doctk.dsl.repl import REPL


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        [
            Heading(level=1, text="Title", children=[], metadata={}),
            Heading(level=2, text="Section 1", children=[], metadata={}),
            Heading(level=3, text="Subsection 1.1", children=[], metadata={}),
            Heading(level=2, text="Section 2", children=[], metadata={}),
        ]
    )


@pytest.fixture
def temp_markdown_file(sample_document):
    """Create a temporary markdown file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_document.to_string())
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestREPLBasics:
    """Test basic REPL functionality."""

    def test_repl_initialization(self):
        """Test REPL initializes correctly."""
        repl = REPL()
        assert repl.document is None
        assert repl.document_path is None
        assert repl.history == []
        assert repl.operations is not None

    def test_load_document_success(self, repl_instance, temp_markdown_file):
        """Test loading a document successfully."""
        repl_instance.load_document(temp_markdown_file)

        assert repl_instance.document is not None
        assert repl_instance.document_path is not None
        assert repl_instance.tree_builder is not None
        assert len(repl_instance.document.nodes) == 4

    def test_load_document_nonexistent_file(self, repl_instance, capsys):
        """Test loading a nonexistent file."""
        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.load_document("/nonexistent/file.md")

            # Verify error message was printed
            assert mock_console.print.called
            call_args = str(mock_console.print.call_args)
            assert "not found" in call_args.lower() or "error" in call_args.lower()

    def test_save_document_success(self, repl_instance, temp_markdown_file, sample_document):
        """Test saving a document successfully."""
        # Load the document first
        repl_instance.load_document(temp_markdown_file)

        # Modify the document
        repl_instance.document = sample_document

        # Save it
        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.save_document()

            # Verify success message
            assert mock_console.print.called

        # Verify file was written
        saved_doc = Document.from_file(temp_markdown_file)
        assert len(saved_doc.nodes) == len(sample_document.nodes)

    def test_save_document_no_document_loaded(self, repl_instance):
        """Test saving when no document is loaded."""
        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.save_document()

            # Verify warning message
            assert mock_console.print.called
            call_args = str(mock_console.print.call_args)
            assert "no document" in call_args.lower()


class TestREPLCommands:
    """Test REPL command execution."""

    def test_execute_command_help(self, repl_instance):
        """Test help command."""
        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.execute_command("help")

            # Verify help was displayed
            assert mock_console.print.called
            call_args = str(mock_console.print.call_args)
            assert "commands" in call_args.lower() or "operations" in call_args.lower()

    def test_execute_command_exit(self, repl_instance):
        """Test exit command."""
        with pytest.raises(EOFError):
            repl_instance.execute_command("exit")

    def test_execute_command_load(self, repl_instance, temp_markdown_file):
        """Test load command."""
        repl_instance.execute_command(f"load {temp_markdown_file}")

        assert repl_instance.document is not None
        assert len(repl_instance.document.nodes) == 4

    def test_execute_command_save(self, repl_instance, temp_markdown_file):
        """Test save command."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("save")

        # Document should still be loaded
        assert repl_instance.document is not None

    def test_execute_command_tree(self, repl_instance, temp_markdown_file):
        """Test tree command."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.execute_command("tree")

            # Verify tree was printed
            assert mock_console.print.called

    def test_execute_command_list(self, repl_instance, temp_markdown_file):
        """Test list command."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.execute_command("list")

            # Verify list was printed
            assert mock_console.print.called


class TestREPLOperations:
    """Test REPL operations execution."""

    def test_operation_without_document(self, repl_instance):
        """Test executing operation without loaded document."""
        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.execute_command("promote h1-0")

            # Verify warning message
            assert mock_console.print.called
            call_args = str(mock_console.print.call_args)
            assert "no document" in call_args.lower()

    def test_operation_promote(self, repl_instance, temp_markdown_file):
        """Test promote operation."""
        repl_instance.load_document(temp_markdown_file)

        # Get the original heading level
        from doctk.lsp.operations import DocumentTreeBuilder
        original_builder = DocumentTreeBuilder(repl_instance.document)
        original_node = original_builder.find_node("h2-0")
        assert original_node is not None
        assert isinstance(original_node, Heading)
        original_level = original_node.level

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("promote h2-0")

        # Verify document was updated
        assert repl_instance.document is not None
        assert "promote h2-0" in repl_instance.history

        # Verify the heading level actually decreased
        new_builder = DocumentTreeBuilder(repl_instance.document)
        new_node = new_builder.find_node("h1-0")  # After promotion, h2-0 becomes h1-0
        assert new_node is not None
        assert isinstance(new_node, Heading)
        assert new_node.level == original_level - 1

    def test_operation_demote(self, repl_instance, temp_markdown_file):
        """Test demote operation."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("demote h2-0")

        # Verify operation was executed
        assert "demote h2-0" in repl_instance.history

    def test_operation_move_up(self, repl_instance, temp_markdown_file):
        """Test move_up operation."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("move_up h2-1")

        # Verify operation was executed
        assert "move_up h2-1" in repl_instance.history

    def test_operation_move_down(self, repl_instance, temp_markdown_file):
        """Test move_down operation."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("move_down h2-0")

        # Verify operation was executed
        assert "move_down h2-0" in repl_instance.history

    def test_operation_unnest(self, repl_instance, temp_markdown_file):
        """Test unnest operation."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("unnest h3-0")

        # Verify operation was executed
        assert "unnest h3-0" in repl_instance.history

    def test_operation_nest(self, repl_instance, temp_markdown_file):
        """Test nest operation."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("nest h2-1 h1-0")

        # Verify operation was executed
        assert "nest h2-1 h1-0" in repl_instance.history

    def test_operation_nest_missing_parent(self, repl_instance, temp_markdown_file):
        """Test nest operation with missing parent_id."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.execute_command("nest h2-0")

            # Verify error message
            assert mock_console.print.called
            call_args = str(mock_console.print.call_args)
            assert "parent_id" in call_args.lower() or "requires" in call_args.lower()

    def test_operation_unknown(self, repl_instance, temp_markdown_file):
        """Test unknown operation."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.execute_command("invalid_op h1-0")

            # Verify error message
            assert mock_console.print.called
            # Check all print calls for the error message
            all_calls = " ".join([str(call) for call in mock_console.print.call_args_list])
            assert "unknown" in all_calls.lower() or "available" in all_calls.lower()

    def test_operation_invalid_format(self, repl_instance, temp_markdown_file):
        """Test operation with invalid format."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console") as mock_console:
            repl_instance.execute_command("promote")

            # Verify error message
            assert mock_console.print.called
            call_args = str(mock_console.print.call_args)
            assert "invalid" in call_args.lower() or "format" in call_args.lower()


class TestREPLStateManagement:
    """Test REPL state management."""

    def test_history_tracking(self, repl_instance, temp_markdown_file):
        """Test that commands are added to history."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("promote h2-0")
            repl_instance.execute_command("demote h3-0")

        assert len(repl_instance.history) == 2
        assert "promote h2-0" in repl_instance.history
        assert "demote h3-0" in repl_instance.history

    def test_document_state_persistence(self, repl_instance, temp_markdown_file):
        """Test that document state persists across commands."""
        repl_instance.load_document(temp_markdown_file)
        original_nodes = len(repl_instance.document.nodes)

        with patch("doctk.dsl.repl.console"):
            repl_instance.execute_command("promote h2-0")

        # Document should still be loaded
        assert repl_instance.document is not None
        assert len(repl_instance.document.nodes) == original_nodes


class TestREPLErrorHandling:
    """Test REPL error handling."""

    def test_operation_failure_handling(self, repl_instance, temp_markdown_file):
        """Test handling of operation failures."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console") as mock_console:
            # Try to operate on non-existent node
            repl_instance.execute_command("promote h99-99")

            # Verify error was handled
            assert mock_console.print.called

    def test_exception_during_operation(self, repl_instance, temp_markdown_file):
        """Test handling of exceptions during operation execution."""
        repl_instance.load_document(temp_markdown_file)

        with patch("doctk.dsl.repl.console") as mock_console:
            with patch.object(repl_instance.operations, "promote", side_effect=Exception("Test error")):
                repl_instance.execute_command("promote h2-0")

                # Verify error message was printed
                assert mock_console.print.called
                call_args = str(mock_console.print.call_args)
                assert "error" in call_args.lower()


# Fixtures
@pytest.fixture
def repl_instance():
    """Create a REPL instance for testing."""
    return REPL()
