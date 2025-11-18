"""End-to-end tests for the CLI execute command."""

import tempfile
from pathlib import Path

import pytest

from doctk.core import Document, Heading


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


def test_cli_execute_command_success(sample_document):
    """Test the execute command via CLI."""
    # Create temp files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
        script_file.write("doc | promote h2-0")
        script_path = script_file.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
        doc_file.write(sample_document.to_string())
        doc_path = doc_file.name

    try:
        # Execute via CLI
        from doctk.cli import run_execute
        from rich.console import Console

        console = Console()
        run_execute(console, [script_path, doc_path])

        # Verify the document was transformed and saved
        result_doc = Document.from_file(doc_path)
        section_1_nodes = [n for n in result_doc.nodes if isinstance(n, Heading) and n.text == "Section 1"]
        assert len(section_1_nodes) == 1
        assert section_1_nodes[0].level == 1

    finally:
        # Cleanup
        Path(script_path).unlink(missing_ok=True)
        Path(doc_path).unlink(missing_ok=True)


def test_cli_execute_missing_arguments():
    """Test execute command with missing arguments."""
    import sys

    from doctk.cli import run_execute
    from rich.console import Console

    console = Console()

    with pytest.raises(SystemExit) as exc_info:
        run_execute(console, [])

    assert exc_info.value.code == 1


def test_cli_execute_script_not_found(sample_document):
    """Test execute command with nonexistent script file."""
    import sys

    from doctk.cli import run_execute
    from rich.console import Console

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
        doc_file.write(sample_document.to_string())
        doc_path = doc_file.name

    try:
        console = Console()

        with pytest.raises(SystemExit) as exc_info:
            run_execute(console, ["/nonexistent/script.tk", doc_path])

        assert exc_info.value.code == 1

    finally:
        Path(doc_path).unlink(missing_ok=True)


def test_cli_execute_document_not_found():
    """Test execute command with nonexistent document file."""
    import sys

    from doctk.cli import run_execute
    from rich.console import Console

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
        script_file.write("doc | promote h2-0")
        script_path = script_file.name

    try:
        console = Console()

        with pytest.raises(SystemExit) as exc_info:
            run_execute(console, [script_path, "/nonexistent/document.md"])

        assert exc_info.value.code == 1

    finally:
        Path(script_path).unlink(missing_ok=True)


def test_cli_execute_with_execution_error(sample_document):
    """Test execute command with script that causes execution error."""
    import sys

    from doctk.cli import run_execute
    from rich.console import Console

    # Create script with invalid operation
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tk", delete=False) as script_file:
        script_file.write("doc | promote nonexistent-node")
        script_path = script_file.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as doc_file:
        doc_file.write(sample_document.to_string())
        doc_path = doc_file.name

    try:
        console = Console()

        with pytest.raises(SystemExit) as exc_info:
            run_execute(console, [script_path, doc_path])

        assert exc_info.value.code == 1

    finally:
        Path(script_path).unlink(missing_ok=True)
        Path(doc_path).unlink(missing_ok=True)
