"""End-to-end tests for script execution (REPL, file execution, code blocks).

This test module validates Requirements 12, 13, and 14:
- Requirement 12: DSL Execution in Terminal REPL
- Requirement 13: Script File Execution
- Requirement 14: Code Block Execution in Markdown
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from doctk.core import Document, Heading, Paragraph
from doctk.dsl.codeblock import CodeBlockExecutor
from doctk.dsl.executor import ExecutionError, ScriptExecutor
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
            Paragraph(content="Some content", metadata={}),
        ]
    )


@pytest.fixture
def temp_markdown_file(sample_document):
    """Create a temporary markdown file with sample content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_document.to_string())
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


class TestREPLWorkflow:
    """Test REPL workflow (Requirement 12: DSL Execution in Terminal REPL)."""

    def test_repl_load_document(self, temp_markdown_file):
        """Test loading a document in REPL."""
        repl = REPL()

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {temp_markdown_file}")

        # Verify document was loaded
        assert repl.document is not None
        assert repl.document_path == Path(temp_markdown_file)
        assert len(repl.document.nodes) == 5

    def test_repl_execute_promote_operation(self, temp_markdown_file):
        """Test executing promote operation in REPL."""
        repl = REPL()

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {temp_markdown_file}")

        # Execute promote on h2-0 (Section 1)
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("promote h2-0")

        # Verify the heading was promoted
        assert repl.document is not None
        section_1_nodes = [
            n for n in repl.document.nodes if isinstance(n, Heading) and n.text == "Section 1"
        ]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 1  # Promoted from h2 to h1

    def test_repl_execute_demote_operation(self, temp_markdown_file):
        """Test executing demote operation in REPL."""
        repl = REPL()

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {temp_markdown_file}")

        # Execute demote on h1-0 (Title)
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("demote h1-0")

        # Verify the heading was demoted
        assert repl.document is not None
        title_nodes = [
            n for n in repl.document.nodes if isinstance(n, Heading) and n.text == "Title"
        ]
        assert len(title_nodes) == 1
        assert title_nodes[0].level == 2  # Demoted from h1 to h2

    def test_repl_save_document(self, temp_markdown_file):
        """Test saving document in REPL."""
        repl = REPL()

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {temp_markdown_file}")

        # Make a change
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("promote h2-0")

        # Save document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("save")

        # Verify the file was updated
        saved_doc = Document.from_file(temp_markdown_file)
        section_1_nodes = [
            n for n in saved_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
        ]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 1

    def test_repl_list_nodes(self, temp_markdown_file):
        """Test listing nodes in REPL."""
        repl = REPL()

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {temp_markdown_file}")

        # List nodes (should not raise an error)
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("list")

        # Verify tree builder was created
        assert repl.tree_builder is not None

    def test_repl_show_tree(self, temp_markdown_file):
        """Test showing document tree in REPL."""
        repl = REPL()

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {temp_markdown_file}")

        # Show tree (should not raise an error)
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("tree")

        # Verify tree builder was created
        assert repl.tree_builder is not None

    def test_repl_command_history(self, temp_markdown_file):
        """Test that REPL maintains command history."""
        repl = REPL()

        # Load document
        with patch("doctk.dsl.repl.console"):
            repl.execute_command(f"load {temp_markdown_file}")

        # Execute commands
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("promote h2-0")
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("demote h1-0")

        # Verify history
        assert "promote h2-0" in repl.history
        assert "demote h1-0" in repl.history

    def test_repl_operation_without_loaded_document(self):
        """Test that operations fail gracefully when no document is loaded."""
        repl = REPL()

        # Try to execute operation without loading document
        with patch("doctk.dsl.repl.console") as mock_console:
            repl.execute_command("promote h2-0")

            # Should print warning message
            mock_console.print.assert_called()
            call_args = str(mock_console.print.call_args)
            assert "No document loaded" in call_args

    def test_repl_help_command(self):
        """Test REPL help command."""
        repl = REPL()

        # Execute help command (should not raise an error)
        with patch("doctk.dsl.repl.console"):
            repl.execute_command("help")

        # Should complete without error


class TestScriptFileExecution:
    """Test script file execution (Requirement 13: Script File Execution)."""

    def test_execute_script_with_single_operation(self, sample_document):
        """Test executing a script file with a single operation."""
        # Create script file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as f:
            f.write("doc | promote h2-0")
            script_path = f.name

        # Create document file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_document.to_string())
            doc_path = f.name

        try:
            # Execute script
            executor = ScriptExecutor()
            result_doc = executor.execute_file(script_path, doc_path)

            # Verify operation was applied
            section_1_nodes = [
                n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
            ]
            assert len(section_1_nodes) == 1
            assert section_1_nodes[0].level == 1

        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_script_with_multiple_operations(self, sample_document):
        """Test executing a script file with multiple operations."""
        # Create script file with multiple operations
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as f:
            f.write("doc | promote h2-0\ndoc | demote h1-0")
            script_path = f.name

        # Create document file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_document.to_string())
            doc_path = f.name

        try:
            # Execute script
            executor = ScriptExecutor()
            result_doc = executor.execute_file(script_path, doc_path)

            # Verify both operations were applied
            # Section 1 should be promoted to h1
            section_1_nodes = [
                n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
            ]
            assert len(section_1_nodes) == 1
            assert section_1_nodes[0].level == 1

            # Original Title should be demoted to h2
            title_nodes = [
                n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Title"
            ]
            assert len(title_nodes) == 1
            assert title_nodes[0].level == 2

        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_script_with_comments(self, sample_document):
        """Test executing a script file with comments."""
        # Create script file with comments
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as f:
            f.write("# This is a comment\ndoc | promote h2-0\n# Another comment")
            script_path = f.name

        # Create document file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_document.to_string())
            doc_path = f.name

        try:
            # Execute script
            executor = ScriptExecutor()
            result_doc = executor.execute_file(script_path, doc_path)

            # Verify operation was applied (comments ignored)
            section_1_nodes = [
                n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
            ]
            assert len(section_1_nodes) == 1
            assert section_1_nodes[0].level == 1

        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_script_with_syntax_error(self, sample_document):
        """Test that script execution fails gracefully with syntax errors."""
        # Create script file with syntax error
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as f:
            f.write("doc | invalid syntax here")
            script_path = f.name

        # Create document file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_document.to_string())
            doc_path = f.name

        try:
            # Execute script - should raise an error
            executor = ScriptExecutor()

            with pytest.raises((ExecutionError, Exception)):
                executor.execute_file(script_path, doc_path)

        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)

    def test_execute_script_file_saves_result(self, sample_document):
        """Test that executing a script file can save the result."""
        # Create script file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as f:
            f.write("doc | promote h2-0")
            script_path = f.name

        # Create document file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_document.to_string())
            doc_path = f.name

        try:
            # Execute script and save
            executor = ScriptExecutor()
            result_doc = executor.execute_file_and_save(script_path, doc_path)

            # Verify the saved document was updated
            saved_doc = Document.from_file(doc_path)
            section_1_nodes = [
                n for n in saved_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
            ]
            assert len(section_1_nodes) == 1
            assert section_1_nodes[0].level == 1

        finally:
            Path(script_path).unlink(missing_ok=True)
            Path(doc_path).unlink(missing_ok=True)


class TestCodeBlockExecution:
    """Test code block execution in Markdown (Requirement 14: Code Block Execution)."""

    def test_find_single_code_block(self):
        """Test finding a single doctk code block in Markdown."""
        markdown_text = """# Test Document

Some text before the code block.

```doctk
doc | promote h2-0
```

Some text after the code block.
"""
        executor = CodeBlockExecutor()
        blocks = executor.find_code_blocks(markdown_text)

        assert len(blocks) == 1
        assert blocks[0].language == "doctk"
        assert blocks[0].code.strip() == "doc | promote h2-0"
        assert blocks[0].start_line == 4
        assert blocks[0].end_line == 6

    def test_find_multiple_code_blocks(self):
        """Test finding multiple doctk code blocks in Markdown."""
        markdown_text = """# Test Document

```doctk
doc | promote h2-0
```

Some text in between.

```doctk
doc | demote h1-0
```
"""
        executor = CodeBlockExecutor()
        blocks = executor.find_code_blocks(markdown_text)

        assert len(blocks) == 2
        assert blocks[0].code.strip() == "doc | promote h2-0"
        assert blocks[1].code.strip() == "doc | demote h1-0"

    def test_ignore_non_doctk_code_blocks(self):
        """Test that non-doctk code blocks are ignored."""
        markdown_text = """# Test Document

```python
print("hello")
```

```doctk
doc | promote h2-0
```

```javascript
console.log("world");
```
"""
        executor = CodeBlockExecutor()
        blocks = executor.find_code_blocks(markdown_text)

        # Should only find the doctk block
        assert len(blocks) == 1
        assert blocks[0].code.strip() == "doc | promote h2-0"

    def test_execute_single_code_block(self, sample_document):
        """Test executing a single code block."""
        code_block_text = "doc | promote h2-0"

        # Create markdown with code block
        markdown_text = f"""# Test Document

```doctk
{code_block_text}
```
"""

        executor = CodeBlockExecutor()
        blocks = executor.find_code_blocks(markdown_text)

        # Execute the code block
        result_doc = executor.execute_code_block(blocks[0], sample_document)

        # Verify operation was applied
        section_1_nodes = [
            n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
        ]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 1

    def test_execute_multiple_code_blocks_sequentially(self, sample_document):
        """Test executing multiple code blocks sequentially."""
        markdown_text = """# Test Document

```doctk
doc | promote h2-0
```

```doctk
doc | demote h1-0
```
"""

        executor = CodeBlockExecutor()
        blocks = executor.find_code_blocks(markdown_text)

        # Execute blocks sequentially
        result_doc = sample_document
        for block in blocks:
            result_doc = executor.execute_code_block(block, result_doc)

        # Verify both operations were applied
        section_1_nodes = [
            n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
        ]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 1

        title_nodes = [
            n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Title"
        ]
        assert len(title_nodes) == 1
        assert title_nodes[0].level == 2

    def test_execute_code_blocks_from_file(self, sample_document):
        """Test executing code blocks from a Markdown file."""
        markdown_text = """# Test Document

Apply transformations to the document:

```doctk
doc | promote h2-0
```
"""

        # Create markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_text)
            markdown_path = f.name

        try:
            # Find and execute code blocks
            with open(markdown_path, "r") as f:
                content = f.read()

            executor = CodeBlockExecutor()
            blocks = executor.find_code_blocks(content)

            result_doc = sample_document
            for block in blocks:
                result_doc = executor.execute_code_block(block, result_doc)

            # Verify operation was applied
            section_1_nodes = [
                n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
            ]
            assert len(section_1_nodes) == 1
            assert section_1_nodes[0].level == 1

        finally:
            Path(markdown_path).unlink(missing_ok=True)

    def test_code_block_with_multiple_lines(self, sample_document):
        """Test executing a code block with multiple lines of code."""
        markdown_text = """# Test Document

```doctk
doc | promote h2-0
doc | demote h1-0
```
"""

        executor = CodeBlockExecutor()
        blocks = executor.find_code_blocks(markdown_text)

        assert len(blocks) == 1
        assert "doc | promote h2-0" in blocks[0].code
        assert "doc | demote h1-0" in blocks[0].code

        # Execute the code block
        result_doc = executor.execute_code_block(blocks[0], sample_document)

        # Verify both operations were applied
        section_1_nodes = [
            n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"
        ]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 1

        title_nodes = [
            n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Title"
        ]
        assert len(title_nodes) == 1
        assert title_nodes[0].level == 2
