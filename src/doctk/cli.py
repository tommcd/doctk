"""
Command-line interface for doctk.

Provides Unix-style pipeline operations for document manipulation.
"""

import sys
from pathlib import Path

from rich.console import Console

from doctk.core import Document
from doctk.operations import (
    heading,
    promote,
    select,
    where,
)
from doctk.outliner import outline, outline_headings_only


def main() -> None:
    """Main CLI entry point."""
    console = Console()

    if len(sys.argv) < 2:
        show_help(console)
        sys.exit(0)

    command = sys.argv[1]

    if command == "help" or command == "--help" or command == "-h":
        show_help(console)
        sys.exit(0)

    if command == "version" or command == "--version" or command == "-v":
        from doctk import __version__

        console.print(f"doctk version {__version__}")
        sys.exit(0)

    if command == "outline":
        run_outline(console, sys.argv[2:])
    elif command == "demo":
        run_demo(console)
    elif command == "repl":
        run_repl()
    elif command == "execute":
        run_execute(console, sys.argv[2:])
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("\nRun 'doctk help' for usage information.")
        sys.exit(1)


def show_help(console: Console) -> None:
    """Show help information."""
    help_text = """
[bold cyan]doctk[/bold cyan] - A composable toolkit for structured document manipulation

[bold]Usage:[/bold]
    doctk <command> [arguments]

[bold]Commands:[/bold]
    [cyan]outline[/cyan] <file>           Show document structure
    [cyan]demo[/cyan]                    Run interactive demo
    [cyan]repl[/cyan]                    Start interactive REPL
    [cyan]execute[/cyan] <script> <doc>  Execute .tk script on document
    [cyan]help[/cyan]                    Show this help message
    [cyan]version[/cyan]                 Show version information

[bold]Outline Options:[/bold]
    doctk outline <file>                    Full outline
    doctk outline <file> --headings-only    Headings only (hierarchical)
    doctk outline <file> --depth N          Limit depth to N levels
    doctk outline <file> --content          Show content preview

[bold]Examples:[/bold]
    # View document structure
    doctk outline README.md

    # Show only headings in hierarchical view
    doctk outline guide.md --headings-only

    # Limit outline depth
    doctk outline docs.md --depth 2

    # Show with content preview
    doctk outline article.md --content

    # Execute a script file
    doctk execute transform.tk document.md

[bold]Python API:[/bold]
    from doctk import Document
    from doctk.operations import select, where, promote

    # Load and transform
    doc = Document.from_file("guide.md")
    result = doc | select(heading) | where(level=3) | promote()
    result.to_file("guide_updated.md")

[bold]More Information:[/bold]
    Documentation: https://github.com/tommcd/doctk
    """
    console.print(help_text)


def run_outline(console: Console, args: list[str]) -> None:
    """Run outline command."""
    if not args:
        console.print("[red]Error: No file specified[/red]")
        console.print("Usage: doctk outline <file> [options]")
        sys.exit(1)

    file_path = args[0]

    if not Path(file_path).exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        sys.exit(1)

    # Parse options
    headings_only = "--headings-only" in args
    show_content = "--content" in args
    max_depth = None

    # Check for depth option
    if "--depth" in args:
        try:
            depth_idx = args.index("--depth")
            if depth_idx + 1 < len(args):
                max_depth = int(args[depth_idx + 1])
        except (ValueError, IndexError):
            console.print("[red]Error: Invalid --depth value[/red]")
            sys.exit(1)

    # Load document
    try:
        doc = Document.from_file(file_path)
    except Exception as e:
        console.print(f"[red]Error parsing document: {e}[/red]")
        sys.exit(1)

    # Show outline
    console.print(f"\n[bold]Document:[/bold] {file_path}\n")

    if headings_only:
        outline_headings_only(doc, console)
    else:
        outline(doc, show_content=show_content, max_depth=max_depth, console=console)

    console.print()


def run_demo(console: Console) -> None:
    """Run interactive demo."""
    console.print("\n[bold cyan]doctk Interactive Demo[/bold cyan]\n")

    # Create sample document
    sample_md = """# My Document

This is a sample document to demonstrate doctk.

## Introduction

Welcome to doctk! This toolkit provides composable operations for document manipulation.

### Getting Started

First, install doctk:

```bash
pip install doctk
```

### Basic Usage

Here's how to use it:

- Load a document
- Apply transformations
- Save the result

## Features

doctk supports many operations:

1. Selecting nodes
2. Transforming structure
3. Querying content

### Advanced Operations

You can compose operations using the pipe operator.

## Conclusion

Try it out!
"""

    console.print("[bold]Sample Document:[/bold]")
    console.print("[dim]" + sample_md[:200] + "...[/dim]\n")

    # Parse document
    doc = Document.from_string(sample_md)

    # Demo 1: Outline
    console.print("[bold yellow]Demo 1: Document Outline[/bold yellow]")
    outline_headings_only(doc, console)
    console.print()

    # Demo 2: Select headings
    console.print("[bold yellow]Demo 2: Select Level 2 Headings[/bold yellow]")
    headings_doc = doc | select(lambda n: hasattr(n, "level") and n.level == 2)
    console.print(f"Found {len(headings_doc)} level-2 headings:")
    for node in headings_doc:
        if hasattr(node, "text"):
            console.print(f"  - {node.text}")
    console.print()

    # Demo 3: Promote headings
    console.print("[bold yellow]Demo 3: Promote All Level-3 Headings to Level-2[/bold yellow]")
    original_h3 = doc | select(lambda n: hasattr(n, "level") and n.level == 3)
    console.print(f"Before: {len(original_h3)} level-3 headings")

    transformed = doc | select(lambda n: hasattr(n, "level") and n.level == 3) | promote()
    console.print("After promotion:")
    for node in transformed:
        if hasattr(node, "level") and hasattr(node, "text"):
            console.print(f"  - [H{node.level}] {node.text}")
    console.print()

    # Demo 4: Composition
    console.print("[bold yellow]Demo 4: Composing Operations[/bold yellow]")
    console.print("Code: doc | select(heading) | where(level=3) | promote()")

    from doctk.operations import compose

    process = compose(promote(), where(level=3), heading)
    result = process(doc)

    console.print(f"Result: {len(result)} transformed headings")
    console.print()

    console.print("[bold green]Demo complete![/bold green]")
    console.print("Try: doctk outline <your-file.md>")
    console.print()


def run_repl() -> None:
    """Start the interactive REPL."""
    from doctk.dsl.repl import REPL

    repl = REPL()
    repl.start()


def run_execute(console: Console, args: list[str]) -> None:
    """Execute a script file on a document."""
    from doctk.dsl import ExecutionError, ScriptExecutor

    if len(args) < 2:
        console.print("[red]Error: Script and document files required[/red]")
        console.print("Usage: doctk execute <script.tk> <document.md>")
        sys.exit(1)

    script_path = Path(args[0])
    document_path = Path(args[1])

    # Execute script (file validation handled by ScriptExecutor)
    try:
        executor = ScriptExecutor()
        console.print(f"[cyan]Executing {script_path.name} on {document_path.name}...[/cyan]")

        result = executor.execute_file_and_save(script_path, document_path)

        console.print("[green]✓ Script executed successfully[/green]")
        console.print(f"  Transformed document saved to {document_path}")
        console.print(f"  Document has {len(result.nodes)} nodes")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except ExecutionError as e:
        console.print(f"[red]Execution failed: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
