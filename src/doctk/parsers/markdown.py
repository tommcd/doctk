"""
Markdown parser using markdown-it-py.

Converts Markdown to doctk's internal AST representation.
"""

import re
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
from doctk.identity import (
    NodeId,
    Provenance,
    ProvenanceContext,
    SourceSpan,
    ViewSourceMapping,
)


class MarkdownParser:
    """Parse Markdown into doctk Document."""

    def __init__(self):
        self.md = MarkdownIt()

    def parse_file(self, path: str) -> Document[Node]:
        """Parse Markdown file with provenance."""
        content = Path(path).read_text(encoding="utf-8")
        context = ProvenanceContext.from_file(path)
        return self._parse_with_context(content, context)

    def parse_string(
        self, content: str, context: ProvenanceContext | None = None
    ) -> Document[Node]:
        """Parse Markdown string with optional provenance context."""
        if context is None:
            context = ProvenanceContext.from_repl()
        return self._parse_with_context(content, context)

    def _parse_with_context(self, content: str, context: ProvenanceContext) -> Document[Node]:
        """Parse and attach provenance, source spans, and NodeIds to all nodes."""
        tokens = self.md.parse(content)
        lines = content.split("\n")
        nodes = self._convert_tokens_with_spans(tokens, lines, context)

        # Create document with identity mappings (view = source initially)
        doc = Document(nodes)
        for node in nodes:
            if node.id and node.source_span:
                # Identity mapping: view position = source position
                mapping = ViewSourceMapping(
                    view_span=node.source_span,
                    source_span=node.source_span,
                    node_id=node.id,
                    transform="identity",
                )
                doc.add_view_mapping(mapping)

        return doc

    def _convert_tokens_with_spans(
        self, tokens: list[Token], lines: list[str], context: ProvenanceContext
    ) -> list[Node]:
        """Convert markdown-it tokens to doctk nodes with source spans and IDs."""
        nodes = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                # Heading: heading_open, inline, heading_close
                level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
                text_token = tokens[i + 1] if i + 1 < len(tokens) else None
                text = text_token.content if text_token else ""

                heading = Heading(level=level, text=text)

                # Attach source span
                if token.map:
                    heading.source_span = self._create_source_span(token, lines, context.file_path)

                # Generate and attach NodeId
                heading.id = NodeId.from_node(heading)

                # Attach provenance
                heading.provenance = Provenance.from_context(context)

                nodes.append(heading)
                i += 3  # Skip heading_open, inline, heading_close

            elif token.type == "paragraph_open":
                # Paragraph: paragraph_open, inline, paragraph_close
                text_token = tokens[i + 1] if i + 1 < len(tokens) else None
                text = text_token.content if text_token else ""

                paragraph = Paragraph(content=text)

                # Attach source span
                if token.map:
                    paragraph.source_span = self._create_source_span(
                        token, lines, context.file_path
                    )

                # Generate and attach NodeId
                paragraph.id = NodeId.from_node(paragraph)

                # Attach provenance
                paragraph.provenance = Provenance.from_context(context)

                nodes.append(paragraph)
                i += 3  # Skip paragraph_open, inline, paragraph_close

            elif token.type == "bullet_list_open" or token.type == "ordered_list_open":
                # List: list_open, (list_item_open, ..., list_item_close)*, list_close
                ordered = token.type == "ordered_list_open"
                items, consumed = self._parse_list_items_with_spans(tokens, i + 1, lines, context)

                list_node = List(ordered=ordered, items=items)

                # Attach source span
                if token.map:
                    list_node.source_span = self._create_source_span(
                        token, lines, context.file_path
                    )

                # Generate and attach NodeId
                list_node.id = NodeId.from_node(list_node)

                # Attach provenance
                list_node.provenance = Provenance.from_context(context)

                nodes.append(list_node)
                i += consumed + 2  # Skip list_open and list_close

            elif token.type == "fence" or token.type == "code_block":
                # Code block (fence has language info, code_block doesn't)
                code = token.content
                language = token.info if hasattr(token, "info") and token.info else None

                code_block = CodeBlock(code=code, language=language)

                # Attach source span
                if token.map:
                    code_block.source_span = self._create_source_span(
                        token, lines, context.file_path
                    )

                # Generate and attach NodeId
                code_block.id = NodeId.from_node(code_block)

                # Attach provenance
                code_block.provenance = Provenance.from_context(context)

                nodes.append(code_block)
                i += 1

            elif token.type == "blockquote_open":
                # Block quote: blockquote_open, ..., blockquote_close
                content_tokens, consumed = self._extract_until_close(
                    tokens, i + 1, "blockquote_close"
                )
                content_nodes = self._convert_tokens_with_spans(content_tokens, lines, context)

                block_quote = BlockQuote(content=content_nodes)

                # Attach source span
                if token.map:
                    block_quote.source_span = self._create_source_span(
                        token, lines, context.file_path
                    )

                # Generate and attach NodeId
                block_quote.id = NodeId.from_node(block_quote)

                # Attach provenance
                block_quote.provenance = Provenance.from_context(context)

                nodes.append(block_quote)
                i += consumed + 2  # Skip blockquote_open and blockquote_close

            else:
                # Skip other tokens for now
                i += 1

        return nodes

    def _convert_tokens(self, tokens: list[Token]) -> list[Node]:
        """Convert markdown-it tokens to doctk nodes (legacy method for compatibility)."""
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
                content_tokens, consumed = self._extract_until_close(
                    tokens, i + 1, "blockquote_close"
                )
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

    def _parse_list_items_with_spans(
        self, tokens: list[Token], start: int, lines: list[str], context: ProvenanceContext
    ) -> tuple[list[Node], int]:
        """Parse list items with source spans, return (items, tokens_consumed)."""
        items = []
        i = start

        while i < len(tokens):
            token = tokens[i]

            if token.type == "list_item_open":
                # List item: list_item_open, ..., list_item_close
                content_tokens, consumed = self._extract_until_close(
                    tokens, i + 1, "list_item_close"
                )
                content_nodes = self._convert_tokens_with_spans(content_tokens, lines, context)

                list_item = ListItem(content=content_nodes)

                # Attach source span
                if token.map:
                    list_item.source_span = self._create_source_span(
                        token, lines, context.file_path
                    )

                # Generate and attach NodeId
                list_item.id = NodeId.from_node(list_item)

                # Attach provenance
                list_item.provenance = Provenance.from_context(context)

                items.append(list_item)
                i += consumed + 2  # Skip list_item_open and list_item_close

            elif token.type in ("bullet_list_close", "ordered_list_close"):
                # End of list
                break
            else:
                i += 1

        return items, i - start

    def _create_source_span(
        self, token: Token, lines: list[str], source_file: str | None
    ) -> SourceSpan:
        """
        Create a SourceSpan from a markdown-it token with block-level precision.

        Block-level precision means:
        - Start line/column point to the beginning of the block
        - End line/column point to the end of the block
        - Column positions are recovered from source text (not inline-precise)

        Args:
            token: markdown-it token with map attribute
            lines: Source text split into lines
            source_file: Optional source file path

        Returns:
            SourceSpan with block-level position information
        """
        if not token.map:
            # Fallback for tokens without position info
            return SourceSpan(
                start_line=0,
                start_column=0,
                end_line=0,
                end_column=0,
                source_file=source_file,
            )

        start_line, end_line = token.map
        # markdown-it uses 0-indexed lines, which matches our convention

        # Find start column (first non-whitespace character on start line)
        start_column = self._find_token_start_column(lines, start_line)

        # Find end column (last character on end line)
        end_column = self._find_token_end_column(lines, end_line - 1)

        return SourceSpan(
            start_line=start_line,
            start_column=start_column,
            end_line=end_line - 1,  # Adjust to inclusive end
            end_column=end_column,
            source_file=source_file,
        )

    def _find_token_start_column(self, lines: list[str], line_num: int) -> int:
        """
        Find the starting column for a token (first non-whitespace character).

        Args:
            lines: Source text split into lines
            line_num: 0-indexed line number

        Returns:
            0-indexed column number of first non-whitespace character
        """
        if line_num >= len(lines):
            return 0

        line = lines[line_num]
        # Find first non-whitespace character
        match = re.search(r"\S", line)
        return match.start() if match else 0

    def _find_token_end_column(self, lines: list[str], line_num: int) -> int:
        """
        Find the ending column for a token (last character on line).

        Args:
            lines: Source text split into lines
            line_num: 0-indexed line number

        Returns:
            0-indexed column number of last character (exclusive)
        """
        if line_num >= len(lines):
            return 0

        line = lines[line_num]
        # Return length of line (exclusive end position)
        return len(line)

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
