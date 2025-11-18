"""DSL REPL - Interactive Read-Eval-Print Loop."""

from rich.console import Console

from doctk.core import Document

console = Console()


class REPL:
    """REPL for the doctk DSL."""

    def __init__(self):
        """Initialize REPL."""
        self.document: Document | None = None
        self.history: list[str] = []

    def start(self):
        """Start REPL loop."""
        console.print("[bold]doctk REPL[/bold]")
        console.print("Type 'help' for commands, 'exit' to quit\n")

        while True:
            try:
                # Read input
                line = input("doctk> ")
                if not line.strip():
                    continue

                # Handle special commands
                if line == "exit":
                    break
                elif line == "help":
                    self.show_help()
                    continue

                console.print("[yellow]REPL not fully implemented yet[/yellow]")

            except KeyboardInterrupt:
                console.print("\nUse 'exit' to quit")
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_help(self):
        """Show help message."""
        console.print("""
[bold]Commands:[/bold]
  help            - Show this help
  exit            - Exit REPL

[bold]Note:[/bold] Full DSL support coming soon!
        """)
