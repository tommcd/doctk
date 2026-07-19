"""
Markdown writer.

Converts doctk's internal AST back to Markdown.
"""

from pathlib import Path

from doctk.core import (
    BlockQuote,
    CodeBlock,
    Document,
    Heading,
    List,
    ListItem,
    Node,
    NodeVisitor,
    Paragraph,
    RawBlock,
)


class MarkdownWriter(NodeVisitor):
    """
    Write doctk Document to Markdown.

    Source-faithful by default: nodes that still carry their exact source text
    (attached at parse time, invalidated when an operation changes content)
    are emitted verbatim. Only nodes that were created or modified in memory
    are rendered from the AST. Parsing a document and writing it back without
    modification therefore reproduces the source byte-for-byte.
    """

    def __init__(self):
        self.output = []
        self.list_depth = 0

    def write_file(self, doc: Document[Node], path: str) -> None:
        """Write document to file."""
        content = self.write_string(doc)
        Path(path).write_text(content, encoding="utf-8")

    def write_string(self, doc: Document[Node]) -> str:
        """Convert document to Markdown string."""
        all_lines: list[str] = []
        for node in doc.nodes:
            source_text = getattr(node, "source_text", None)
            if source_text is not None:
                all_lines.extend(source_text.split("\n"))
            else:
                self.output = []
                self.list_depth = 0
                node.accept(self)
                if not self.output or self.output[-1] != "":
                    self.output.append("")  # Blank line between rendered blocks
                all_lines.extend(self.output)
        return "\n".join(all_lines)

    def visit_heading(self, node: Heading) -> None:
        """Write heading."""
        prefix = "#" * node.level
        self.output.append(f"{prefix} {node.text}")
        self.output.append("")  # Blank line after heading

    def visit_paragraph(self, node: Paragraph) -> None:
        """Write paragraph."""
        self.output.append(node.content)
        self.output.append("")  # Blank line after paragraph

    def visit_list(self, node: List) -> None:
        """Write list."""
        self.list_depth += 1
        for i, item in enumerate(node.items):
            if node.ordered:
                prefix = f"{i + 1}."
            else:
                prefix = "-"

            indent = "  " * (self.list_depth - 1)
            self.output.append(f"{indent}{prefix} ")

            # Visit list item content
            item.accept(self)

        self.list_depth -= 1
        if self.list_depth == 0:
            self.output.append("")  # Blank line after list

    def visit_list_item(self, node: ListItem) -> None:
        """Write list item content (inline with bullet)."""
        # For simple items, write inline
        if len(node.content) == 1 and isinstance(node.content[0], Paragraph):
            # Remove the last blank line added, write inline
            if self.output and self.output[-1].endswith(" "):
                para = node.content[0]
                self.output[-1] += para.content
        else:
            # Complex content - write on new lines
            for child in node.content:
                child.accept(self)

    def visit_code_block(self, node: CodeBlock) -> None:
        """Write code block."""
        lang = node.language or ""
        self.output.append(f"```{lang}")
        self.output.append(node.code.rstrip())
        self.output.append("```")
        self.output.append("")  # Blank line after code block

    def visit_raw_block(self, node: RawBlock) -> None:
        """Write raw block verbatim."""
        self.output.extend(node.content.split("\n"))
        self.output.append("")  # Blank line after raw block

    def visit_block_quote(self, node: BlockQuote) -> None:
        """Write block quote."""
        # Simple implementation - just prefix with >
        for child in node.content:
            before_len = len(self.output)
            child.accept(self)
            # Prefix added lines with >
            for i in range(before_len, len(self.output)):
                if self.output[i]:  # Don't prefix blank lines
                    self.output[i] = f"> {self.output[i]}"
                else:
                    self.output[i] = ">"
        self.output.append("")  # Blank line after block quote
