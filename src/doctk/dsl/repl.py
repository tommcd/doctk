"""DSL REPL - Interactive Read-Eval-Print Loop for doctk."""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from doctk.core import Document
from doctk.lsp.operations import DocumentTreeBuilder, StructureOperations

console = Console()


class REPL:
    """Interactive REPL for doctk operations."""

    def __init__(self) -> None:
        """Initialize REPL."""
        self.document: Document[Any] | None = None
        self.document_path: Path | None = None
        self.history: list[str] = []
        self.operations = StructureOperations()
        self.tree_builder: DocumentTreeBuilder | None = None

    def start(self) -> None:
        """Start the REPL loop."""
        console.print("[bold cyan]doctk REPL v0.1.0[/bold cyan]")
        console.print("Interactive document manipulation shell")
        console.print("Type [bold]help[/bold] for commands, [bold]exit[/bold] to quit\n")

        while True:
            try:
                # Read input
                line = input("doctk> ")
                if not line.strip():
                    continue

                # Execute command
                self.execute_command(line.strip())

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]")

        console.print("\n[cyan]Goodbye![/cyan]")

    def execute_command(self, command: str) -> None:
        """
        Execute a REPL command.

        Args:
            command: The command string to execute
        """
        # Special commands
        if command == "exit":
            raise EOFError

        if command == "help":
            self.show_help()
            return

        if command.startswith("load "):
            file_path = command[5:].strip()
            self.load_document(file_path)
            return

        if command == "save":
            self.save_document()
            return

        if command == "tree":
            self.show_tree()
            return

        if command == "list":
            self.list_nodes()
            return

        # Operation commands
        if not self.document:
            console.print("[yellow]No document loaded. Use 'load <file>' first.[/yellow]")
            return

        # Parse and execute operation
        self.execute_operation(command)

    def load_document(self, file_path: str) -> None:
        """
        Load a document from file.

        Args:
            file_path: Path to the document file
        """
        try:
            path = Path(file_path)
            if not path.exists():
                console.print(f"[red]Error: File not found: {file_path}[/red]")
                return

            self.document = Document.from_file(str(path))
            self.document_path = path
            self.tree_builder = DocumentTreeBuilder(self.document)

            console.print(f"[green]✓ Loaded {path.name}[/green]")
            console.print(f"  {len(self.document.nodes)} nodes")

        except Exception as e:
            console.print(f"[red]Error loading document: {e}[/red]")

    def save_document(self) -> None:
        """Save the current document to file."""
        if not self.document or not self.document_path:
            console.print("[yellow]No document loaded[/yellow]")
            return

        try:
            self.document.to_file(str(self.document_path))
            console.print(f"[green]✓ Saved to {self.document_path.name}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving document: {e}[/red]")

    def show_tree(self) -> None:
        """Display the document structure as a tree."""
        if not self.document or not self.tree_builder:
            console.print("[yellow]No document loaded[/yellow]")
            return

        try:
            from rich.tree import Tree

            tree = self.tree_builder.build_tree_with_ids()

            # Create rich tree visualization
            rich_tree = Tree(f"[bold]{tree.label}[/bold]")
            self._add_tree_nodes(rich_tree, tree.children)

            console.print(rich_tree)

        except Exception as e:
            console.print(f"[red]Error displaying tree: {e}[/red]")

    def _add_tree_nodes(self, rich_tree: Any, nodes: list[Any]) -> None:
        """
        Recursively add nodes to rich tree.

        Args:
            rich_tree: Rich tree object
            nodes: List of TreeNode objects to add
        """
        for node in nodes:
            label = f"[cyan]{node.id}[/cyan]: {node.label} [dim](level {node.level})[/dim]"
            branch = rich_tree.add(label)
            if node.children:
                self._add_tree_nodes(branch, node.children)

    def list_nodes(self) -> None:
        """List all nodes with their IDs."""
        if not self.document or not self.tree_builder:
            console.print("[yellow]No document loaded[/yellow]")
            return

        table = Table(title="Document Nodes")
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Content", style="white")

        for node_id, node in self.tree_builder.node_map.items():
            from doctk.core import Heading

            if isinstance(node, Heading):
                content = f"{'#' * node.level} {node.text}"
                table.add_row(node_id, "Heading", content)

        console.print(table)

    def execute_operation(self, command: str) -> None:
        """
        Execute a document operation.

        Args:
            command: Operation command (e.g., "promote h2-0")
        """
        parts = command.split()
        if len(parts) < 2:
            console.print(
                "[yellow]Invalid command. Format: <operation> <node_id> [params][/yellow]"
            )
            return

        operation = parts[0]
        node_id = parts[1]

        # Get additional parameters if needed
        params = {}
        if len(parts) > 2:
            # For operations like 'nest h2-0 h1-0'
            if operation == "nest" and len(parts) == 3:
                params["parent_id"] = parts[2]

        # Execute operation
        try:
            if not self.document:
                console.print("[yellow]No document loaded[/yellow]")
                return

            result = None

            # Map operation names to methods
            if operation == "promote":
                result = self.operations.promote(self.document, node_id)
            elif operation == "demote":
                result = self.operations.demote(self.document, node_id)
            elif operation == "move_up":
                result = self.operations.move_up(self.document, node_id)
            elif operation == "move_down":
                result = self.operations.move_down(self.document, node_id)
            elif operation == "unnest":
                result = self.operations.unnest(self.document, node_id)
            elif operation == "nest":
                if "parent_id" not in params:
                    console.print("[yellow]Nest requires parent_id: nest <node_id> <parent_id>[/yellow]")
                    return
                result = self.operations.nest(self.document, node_id, params["parent_id"])
            else:
                console.print(f"[yellow]Unknown operation: {operation}[/yellow]")
                console.print("Available operations: promote, demote, move_up, move_down, nest, unnest")
                return

            # Check result
            if not result or not result.success:
                error_msg = result.error if result else "Unknown error"
                console.print(f"[red]Operation failed: {error_msg}[/red]")
                return

            # Update document
            self.document = Document.from_string(result.document)
            self.tree_builder = DocumentTreeBuilder(self.document)

            console.print(f"[green]✓ {operation} completed[/green]")

            # Show modified ranges if available
            if result.modified_ranges:
                console.print(f"  Modified {len(result.modified_ranges)} range(s)")

            # Add to history
            self.history.append(command)

        except Exception as e:
            console.print(f"[red]Error executing operation: {e}[/red]")

    def show_help(self) -> None:
        """Display help message."""
        help_text = """
[bold cyan]Commands:[/bold cyan]
  [bold]load <file>[/bold]        Load a document
  [bold]save[/bold]               Save the current document
  [bold]tree[/bold]               Show document structure as tree
  [bold]list[/bold]               List all nodes with IDs
  [bold]help[/bold]               Show this help
  [bold]exit[/bold]               Exit REPL

[bold cyan]Operations:[/bold cyan]
  [bold]promote <node_id>[/bold]      Decrease heading level (h3 -> h2)
  [bold]demote <node_id>[/bold]       Increase heading level (h2 -> h3)
  [bold]move_up <node_id>[/bold]      Move section up
  [bold]move_down <node_id>[/bold]    Move section down
  [bold]nest <node_id> <parent_id>[/bold]  Nest section under parent
  [bold]unnest <node_id>[/bold]       Move section up one level

[bold cyan]Examples:[/bold cyan]
  doctk> load example.md
  doctk> list
  doctk> promote h2-0
  doctk> tree
  doctk> save
        """
        console.print(help_text)
