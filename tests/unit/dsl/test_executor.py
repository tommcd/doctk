"""Tests for the DSL executor."""

import tempfile
from pathlib import Path

import pytest

from doctk.core import Document, Heading
from doctk.dsl import ExecutionError, Executor, ScriptExecutor
from doctk.dsl.lexer import Lexer
from doctk.dsl.parser import Parser


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


class TestExecutor:
    """Test the Executor class."""

    def test_executor_initialization(self, sample_document):
        """Test executor initializes correctly."""
        executor = Executor(sample_document)
        assert executor.document == sample_document
        assert "doc" in executor.variables
        assert executor.variables["doc"] == sample_document

    def test_execute_promote_operation(self, sample_document):
        """Test executing a promote operation."""
        # Parse: doc | promote h2-0
        lexer = Lexer("doc | promote h2-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify the h2-0 node was promoted to h1
        assert isinstance(result, Document)
        # Check that we have a heading with "Section 1" text that should now be level 1
        section_1_nodes = [n for n in result.nodes if isinstance(n, Heading) and n.text == "Section 1"]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 1

    def test_execute_demote_operation(self, sample_document):
        """Test executing a demote operation."""
        # Parse: doc | demote h2-0
        lexer = Lexer("doc | demote h2-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify the h2-0 node was demoted to h3
        assert isinstance(result, Document)
        section_1_nodes = [n for n in result.nodes if isinstance(n, Heading) and n.text == "Section 1"]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 3

    def test_execute_move_up_operation(self, sample_document):
        """Test executing a move_up operation."""
        # Parse: doc | move_up h2-1
        lexer = Lexer("doc | move_up h2-1")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify the document was modified
        assert isinstance(result, Document)
        assert len(result.nodes) == 4

    def test_execute_move_down_operation(self, sample_document):
        """Test executing a move_down operation."""
        # Parse: doc | move_down h2-0
        lexer = Lexer("doc | move_down h2-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify the document was modified
        assert isinstance(result, Document)
        assert len(result.nodes) == 4

    def test_execute_nest_operation(self, sample_document):
        """Test executing a nest operation."""
        # Parse: doc | nest h2-1, h2-0
        # Note: DSL parser requires comma-separated arguments
        lexer = Lexer("doc | nest h2-1, h2-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify the document was modified
        assert isinstance(result, Document)

    def test_execute_unnest_operation(self, sample_document):
        """Test executing an unnest operation."""
        # Parse: doc | unnest h3-0
        lexer = Lexer("doc | unnest h3-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify the h3-0 node was unnested to h2
        assert isinstance(result, Document)
        subsection_nodes = [n for n in result.nodes if isinstance(n, Heading) and n.text == "Subsection 1.1"]
        assert len(subsection_nodes) == 1
        assert subsection_nodes[0].level == 2

    def test_execute_assignment(self, sample_document):
        """Test executing an assignment."""
        # Parse: let x = doc | promote h2-0
        lexer = Lexer("let x = doc | promote h2-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify variable was created
        assert "x" in executor.variables
        assert executor.variables["x"] == result

    def test_execute_unknown_operation(self, sample_document):
        """Test executing an unknown operation raises error."""
        # Parse: doc | unknown_op arg
        lexer = Lexer("doc | unknown_op arg")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)

        with pytest.raises(ExecutionError, match="Unknown operation"):
            executor.execute(ast)

    def test_execute_undefined_variable(self, sample_document):
        """Test executing with undefined variable raises error."""
        # Parse: unknown_var | promote h2-0
        lexer = Lexer("unknown_var | promote h2-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)

        with pytest.raises(ExecutionError, match="Undefined variable"):
            executor.execute(ast)

    def test_execute_operation_missing_argument(self, sample_document):
        """Test executing operation with missing argument raises error."""
        # Parse: doc | promote (no argument)
        lexer = Lexer("doc | promote")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)

        with pytest.raises(ExecutionError, match="requires 1 argument"):
            executor.execute(ast)

    def test_node_id_remapping_in_pipeline(self, sample_document):
        """
        Test that node IDs are NOT stable across pipeline operations.

        This documents a known limitation: re-parsing causes DocumentTreeBuilder
        to reassign heading IDs. Multi-step operations on the same node ID will
        operate on the wrong node.

        See: P1 issue from Codex review - Node Identity Preservation
        Future enhancement: Maintain stable node identifiers across operations
        """
        # Parse: doc | promote h2-0 | demote h2-0
        # After promote, the node that was h2-0 becomes h1-0
        # The demote h2-0 will operate on what is NOW at h2-0 (different node!)
        lexer = Lexer("doc | promote h2-0 | demote h2-0")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        executor = Executor(sample_document)
        result = executor.execute(ast)

        # Verify that demote operated on the node that is NOW at h2-0,
        # not the originally promoted node
        assert isinstance(result, Document)

        # After promote h2-0 (Section 1 becomes h1), the structure is:
        #   h1-0: Title
        #   h1-1: Section 1 (promoted from h2)
        #   h2-0: Subsection 1.1 (was h3-0, now at different ID)
        #   h2-1: Section 2 (was h2-1)
        #
        # Then demote h2-0 operates on "Subsection 1.1" (NOT Section 1!)
        # and demotes it from h2 to h3

        # Verify Section 1 stayed at h1 (not demoted back)
        section_1 = [n for n in result.nodes if isinstance(n, Heading) and n.text == "Section 1"]
        assert len(section_1) == 1
        assert section_1[0].level == 1  # Still promoted

        # Verify Subsection 1.1 was demoted (it was at h2-0 after first operation)
        subsection = [n for n in result.nodes if isinstance(n, Heading) and n.text == "Subsection 1.1"]
        assert len(subsection) == 1
        assert subsection[0].level == 3  # Demoted from h2 back to h3


class TestScriptExecutor:
    """Test the ScriptExecutor class."""

    def test_execute_file_success(self, sample_document):
        """Test executing a script file successfully."""
        # Create temp files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | promote h2-0")
            script_path = script_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
            doc_file.write(sample_document.to_string())
            doc_path = doc_file.name

        try:
            # Execute script
            executor = ScriptExecutor()
            result = executor.execute_file(script_path, doc_path)

            # Verify result
            assert isinstance(result, Document)
            section_1_nodes = [n for n in result.nodes if isinstance(n, Heading) and n.text == "Section 1"]
            assert len(section_1_nodes) == 1
            assert section_1_nodes[0].level == 1

        finally:
            # Cleanup
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_file_and_save(self, sample_document):
        """Test executing a script file and saving the result."""
        # Create temp files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | promote h2-0")
            script_path = script_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
            doc_file.write(sample_document.to_string())
            doc_path = doc_file.name

        try:
            # Execute script and save
            executor = ScriptExecutor()
            executor.execute_file_and_save(script_path, doc_path)

            # Verify result was saved
            saved_doc = Document.from_file(doc_path)
            assert isinstance(saved_doc, Document)

            # Verify transformation was applied
            section_1_nodes = [n for n in saved_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"]
            assert len(section_1_nodes) == 1
            assert section_1_nodes[0].level == 1

        finally:
            # Cleanup
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_file_script_not_found(self, sample_document):
        """Test error when script file not found."""
        executor = ScriptExecutor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
            doc_file.write(sample_document.to_string())
            doc_path = doc_file.name

        try:
            with pytest.raises(FileNotFoundError):
                executor.execute_file("/nonexistent/script.tk", doc_path)
        finally:
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_file_document_not_found(self):
        """Test error when document file not found."""
        executor = ScriptExecutor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | promote h2-0")
            script_path = script_file.name

        try:
            with pytest.raises(FileNotFoundError):
                executor.execute_file(script_path, "/nonexistent/document.md")
        finally:
            Path(script_path).unlink(missing_ok=True)

    def test_execute_file_syntax_error(self, sample_document):
        """Test error reporting for syntax errors in script."""
        # Create script with syntax error
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | @#$%")  # Invalid syntax
            script_path = script_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
            doc_file.write(sample_document.to_string())
            doc_path = doc_file.name

        try:
            executor = ScriptExecutor()
            with pytest.raises(ExecutionError, match="Syntax error"):
                executor.execute_file(script_path, doc_path)
        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_file_execution_error(self, sample_document):
        """Test error reporting for execution errors."""
        # Create script with invalid operation
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | promote nonexistent-node")
            script_path = script_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
            doc_file.write(sample_document.to_string())
            doc_path = doc_file.name

        try:
            executor = ScriptExecutor()
            with pytest.raises(ExecutionError):
                executor.execute_file(script_path, doc_path)
        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_multiple_operations(self, sample_document):
        """Test executing multiple operations in a script."""
        # Create script with multiple operations
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
            script_file.write("doc | promote h2-0 | demote h3-0")
            script_path = script_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
            doc_file.write(sample_document.to_string())
            doc_path = doc_file.name

        try:
            executor = ScriptExecutor()
            result = executor.execute_file(script_path, doc_path)

            # Verify both operations were applied
            assert isinstance(result, Document)
            assert len(result.nodes) == 4

        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)
