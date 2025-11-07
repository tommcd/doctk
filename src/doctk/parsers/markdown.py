"""
Markdown parser using markdown-it-py.

Converts Markdown to doctk's internal AST representation.
"""

from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from doctk.core import (
    BlockQuote,
    CodeBlock,
    Document,
    Heading,
    List,
    ListItem,
    Node,
    Paragraph,
)


class MarkdownParser:
    """Parse Markdown into doctk Document."""

    def __init__(self):
        self.md = MarkdownIt()

    def parse_file(self, path: str) -> Document[Node]:
        """Parse Markdown file."""
        content = Path(path).read_text(encoding="utf-8")
        return self.parse_string(content)

    def parse_string(self, content: str) -> Document[Node]:
        """Parse Markdown string."""
        tokens = self.md.parse(content)
        nodes = self._convert_tokens(tokens)
        return Document(nodes)

    def _convert_tokens(self, tokens: list[Token]) -> list[Node]:
        """Convert markdown-it tokens to doctk nodes."""
        nodes = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                # Heading: heading_open, inline, heading_close
                level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
                text_token = tokens[i + 1] if i + 1 < len(tokens) else None
                text = text_token.content if text_token else ""

                nodes.append(Heading(level=level, text=text))
                i += 3  # Skip heading_open, inline, heading_close

            elif token.type == "paragraph_open":
                # Paragraph: paragraph_open, inline, paragraph_close
                text_token = tokens[i + 1] if i + 1 < len(tokens) else None
                text = text_token.content if text_token else ""

                nodes.append(Paragraph(content=text))
                i += 3  # Skip paragraph_open, inline, paragraph_close

            elif token.type == "bullet_list_open" or token.type == "ordered_list_open":
                # List: list_open, (list_item_open, ..., list_item_close)*, list_close
                ordered = token.type == "ordered_list_open"
                items, consumed = self._parse_list_items(tokens, i + 1)

                nodes.append(List(ordered=ordered, items=items))
                i += consumed + 2  # Skip list_open and list_close

            elif token.type == "fence" or token.type == "code_block":
                # Code block (fence has language info, code_block doesn't)
                code = token.content
                language = token.info if hasattr(token, "info") and token.info else None

                nodes.append(CodeBlock(code=code, language=language))
                i += 1

            elif token.type == "blockquote_open":
                # Block quote: blockquote_open, ..., blockquote_close
                content_tokens, consumed = self._extract_until_close(tokens, i + 1, "blockquote_close")
                content_nodes = self._convert_tokens(content_tokens)

                nodes.append(BlockQuote(content=content_nodes))
                i += consumed + 2  # Skip blockquote_open and blockquote_close

            else:
                # Skip other tokens for now
                i += 1

        return nodes

    def _parse_list_items(self, tokens: list[Token], start: int) -> tuple[list[Node], int]:
        """Parse list items, return (items, tokens_consumed)."""
        items = []
        i = start

        while i < len(tokens):
            token = tokens[i]

            if token.type == "list_item_open":
                # List item: list_item_open, ..., list_item_close
                content_tokens, consumed = self._extract_until_close(
                    tokens, i + 1, "list_item_close"
                )
                content_nodes = self._convert_tokens(content_tokens)

                items.append(ListItem(content=content_nodes))
                i += consumed + 2  # Skip list_item_open and list_item_close

            elif token.type in ("bullet_list_close", "ordered_list_close"):
                # End of list
                break
            else:
                i += 1

        return items, i - start

    def _extract_until_close(
        self, tokens: list[Token], start: int, close_type: str
    ) -> tuple[list[Token], int]:
        """Extract tokens until matching close token."""
        extracted = []
        i = start
        depth = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == close_type and depth == 0:
                break
            elif token.type == close_type:
                depth -= 1

            # Track nesting for same-type opens
            open_type = close_type.replace("_close", "_open")
            if token.type == open_type:
                depth += 1

            extracted.append(token)
            i += 1

        return extracted, i - start
