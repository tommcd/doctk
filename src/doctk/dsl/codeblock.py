"""Code block executor - Execute doctk DSL from Markdown code blocks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doctk.core import Document
from doctk.dsl.executor import ExecutionError, Executor
from doctk.dsl.lexer import Lexer, LexerError
from doctk.dsl.parser import ParseError, Parser


@dataclass
class CodeBlock:
    """Represents a doctk code block found in a Markdown file."""

    language: str
    code: str
    start_line: int
    end_line: int


class CodeBlockExecutor:
    """Executor for doctk code embedded in Markdown code blocks."""

    # Pattern to match fenced code blocks with language identifier
    # Matches: ```doctk\n<code>\n```
    CODE_BLOCK_PATTERN = re.compile(r"^```(doctk)\s*\n(.*?)\n```$", re.MULTILINE | re.DOTALL)

    def __init__(self) -> None:
        """Initialize code block executor."""
        # No instance state needed

    def find_code_blocks(self, markdown_text: str) -> list[CodeBlock]:
        """
        Find all doctk code blocks in Markdown text.

        Args:
            markdown_text: Markdown document text

        Returns:
            List of CodeBlock objects found in the document

        Example:
            ```python
            executor = CodeBlockExecutor()
            blocks = executor.find_code_blocks(markdown_text)
            for block in blocks:
                print(f"Found code block at line {block.start_line}")
            ```
        """
        code_blocks: list[CodeBlock] = []
        lines = markdown_text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for opening fence with doctk language
            if line.strip().startswith("```doctk"):
                start_line = i
                code_lines: list[str] = []
                i += 1

                # Collect code until closing fence
                while i < len(lines):
                    if lines[i].strip() == "```":
                        # Found closing fence
                        code_blocks.append(
                            CodeBlock(
                                language="doctk",
                                code="\n".join(code_lines),
                                start_line=start_line,
                                end_line=i,
                            )
                        )
                        break
                    code_lines.append(lines[i])
                    i += 1
            i += 1

        return code_blocks

    def extract_code_from_block(self, code_block: CodeBlock) -> str:
        """
        Extract executable code from a code block.

        Args:
            code_block: CodeBlock object

        Returns:
            The code content as a string
        """
        return code_block.code

    def execute_code_block(self, code_block: CodeBlock, document: Document[Any]) -> Document[Any]:
        """
        Execute a single code block on a document.

        Args:
            code_block: CodeBlock to execute
            document: Document to execute operations on

        Returns:
            Transformed document

        Raises:
            ExecutionError: If execution fails
        """
        code = self.extract_code_from_block(code_block)

        # Parse the code
        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()

            parser = Parser(tokens)
            ast = parser.parse()
        except LexerError as e:
            # Add code block location context
            actual_line = code_block.start_line + (e.line if e.line else 0) + 1
            raise ExecutionError(
                f"Syntax error in code block: {e}",
                line=actual_line,
                column=e.column,
            ) from e
        except ParseError as e:
            # Add code block location context
            token_line = e.token.line if e.token else 0
            actual_line = code_block.start_line + token_line + 1
            column = e.token.column if e.token else None
            raise ExecutionError(
                f"Parse error in code block: {e}", line=actual_line, column=column
            ) from e

        # Execute the AST
        try:
            executor = Executor(document)
            result = executor.execute(ast)
            return result
        except ExecutionError:
            # Re-raise execution errors as-is
            raise
        except Exception as e:
            raise ExecutionError(f"Execution failed: {e}") from e

    def execute_file(self, markdown_path: str | Path, block_index: int = 0) -> Document[Any]:
        """
        Execute a specific code block from a Markdown file.

        Args:
            markdown_path: Path to the Markdown file
            block_index: Index of the code block to execute (0-based)

        Returns:
            Transformed document

        Raises:
            ExecutionError: If execution fails
            FileNotFoundError: If file not found
            IndexError: If block_index is out of range
        """
        markdown_path = Path(markdown_path)

        # Read Markdown file
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

        try:
            markdown_text = markdown_path.read_text(encoding="utf-8")
        except OSError as e:
            raise ExecutionError(f"Error reading Markdown file: {e}") from e

        # Find code blocks
        code_blocks = self.find_code_blocks(markdown_text)

        if not code_blocks:
            raise ExecutionError("No doctk code blocks found in Markdown file")

        if block_index < 0 or block_index >= len(code_blocks):
            raise IndexError(
                f"Block index {block_index} out of range (found {len(code_blocks)} blocks)"
            )

        # For now, we assume the document to transform is the Markdown file itself
        # In a real scenario, this would come from a parameter or be inferred from context
        # For this implementation, we'll create a simple document from the markdown
        try:
            document = Document.from_string(markdown_text)
        except Exception as e:
            raise ExecutionError(f"Error loading document from Markdown: {e}") from e

        # Execute the specified code block
        code_block = code_blocks[block_index]
        return self.execute_code_block(code_block, document)

    def execute_all_blocks(
        self, markdown_path: str | Path, *, chain_state: bool = False
    ) -> list[tuple[CodeBlock, Document[Any]]]:
        """
        Execute all doctk code blocks in a Markdown file.

        Args:
            markdown_path: Path to the Markdown file
            chain_state: If True, each block operates on the result of the previous block.
                        If False (default), each block operates on the original document
                        independently. **WARNING**: Chained execution has limitations due
                        to node ID remapping - see Notes below.

        Returns:
            List of tuples (CodeBlock, transformed Document) for each block

        Raises:
            ExecutionError: If execution fails
            FileNotFoundError: If file not found

        Notes:
            **Node ID Remapping Limitation (chain_state=True)**:

            When operations are executed, node IDs are regenerated based on the new
            document structure. This means that if Block 1 promotes h2-0 to h1, the
            node IDs in the resulting document will be different from the original.

            If Block 2's code still references h2-0, it will operate on the wrong node
            or fail because the IDs have changed.

            **Recommendations**:
            - Use chain_state=False (default) for independent, predictable execution
            - If you need chained operations, use a single code block with multiple
              operations instead of multiple blocks
            - Or use DSL variable assignments within a single block

            **Example of the issue**:
            ```markdown
            ## Original Heading     <- This is h2-0

            ```doctk
            doc | promote h2-0     <- After this, heading becomes h1-1 (not h2-0!)
            ```

            ```doctk
            doc | demote h2-0      <- This will fail or operate on wrong node!
            ```
            ```

        Example:
            ```python
            # Safe: Each block operates on original document
            executor = CodeBlockExecutor()
            results = executor.execute_all_blocks("doc.md", chain_state=False)

            # Risky: Blocks operate on chained state (ID remapping issues)
            results = executor.execute_all_blocks("doc.md", chain_state=True)
            ```
        """
        markdown_path = Path(markdown_path)

        # Read Markdown file
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

        try:
            markdown_text = markdown_path.read_text(encoding="utf-8")
        except OSError as e:
            raise ExecutionError(f"Error reading Markdown file: {e}") from e

        # Find code blocks
        code_blocks = self.find_code_blocks(markdown_text)

        if not code_blocks:
            raise ExecutionError("No doctk code blocks found in Markdown file")

        # Load document
        try:
            original_document = Document.from_string(markdown_text)
        except Exception as e:
            raise ExecutionError(f"Error loading document from Markdown: {e}") from e

        # Execute each block
        results: list[tuple[CodeBlock, Document[Any]]] = []
        current_document = original_document

        for code_block in code_blocks:
            result = self.execute_code_block(code_block, current_document)
            results.append((code_block, result))

            # Update document for next block only if chaining is enabled
            if chain_state:
                current_document = result
            # Otherwise, next block operates on original document

        return results
