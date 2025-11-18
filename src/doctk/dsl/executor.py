"""DSL Executor - Execute AST against documents."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from doctk.core import Document
from doctk.dsl.lexer import Lexer, LexerError
from doctk.dsl.parser import Assignment, ASTNode, FunctionCall, ParseError, Parser, Pipeline
from doctk.lsp.operations import StructureOperations


class ExecutionError(Exception):
    """Exception raised during script execution."""

    def __init__(self, message: str, line: int | None = None, column: int | None = None):
        """
        Initialize execution error.

        Args:
            message: Error message
            line: Line number where error occurred
            column: Column number where error occurred
        """
        location = ""
        if line is not None:
            location = f" at line {line}"
            if column is not None:
                location += f", column {column}"
        super().__init__(f"{message}{location}")
        self.line = line
        self.column = column


class Executor:
    """Executor for the doctk DSL."""

    def __init__(self, document: Document[Any]):
        """
        Initialize executor with document.

        Args:
            document: Document to execute operations on
        """
        self.document = document
        self.variables: dict[str, Document[Any]] = {"doc": document}
        self.operations = StructureOperations()

        # Dispatch table for operations with their required argument counts
        self._operation_dispatch: dict[str, tuple[Callable[..., Document[Any]], int]] = {
            "promote": (self._exec_promote, 1),
            "demote": (self._exec_demote, 1),
            "move_up": (self._exec_move_up, 1),
            "move_down": (self._exec_move_down, 1),
            "nest": (self._exec_nest, 2),
            "unnest": (self._exec_unnest, 1),
        }

    def execute(self, ast: list[ASTNode]) -> Document[Any]:
        """
        Execute AST statements.

        Args:
            ast: List of AST nodes to execute

        Returns:
            Resulting document after executing all statements

        Raises:
            ExecutionError: If execution fails
        """
        result = self.document

        for node in ast:
            if isinstance(node, Assignment):
                # Execute assignment: let var = pipeline
                doc_result = self._execute_pipeline(node.pipeline)
                self.variables[node.variable] = doc_result
                result = doc_result
            elif isinstance(node, Pipeline):
                # Execute pipeline expression
                result = self._execute_pipeline(node)
            else:
                raise ExecutionError(f"Unknown AST node type: {type(node).__name__}")

        return result

    def _execute_pipeline(self, pipeline: Pipeline) -> Document[Any]:
        """
        Execute a pipeline expression.

        Args:
            pipeline: Pipeline AST node

        Returns:
            Resulting document

        Raises:
            ExecutionError: If pipeline execution fails
        """
        # Get source document
        if pipeline.source not in self.variables:
            raise ExecutionError(f"Undefined variable: {pipeline.source}")

        doc = self.variables[pipeline.source]

        # Apply each operation in the pipeline
        for operation in pipeline.operations:
            doc = self._execute_operation(doc, operation)

        return doc

    def _execute_operation(
        self, doc: Document[Any], operation: FunctionCall
    ) -> Document[Any]:
        """
        Execute a single operation on a document.

        Args:
            doc: Document to operate on
            operation: Operation to execute

        Returns:
            Resulting document

        Note:
            Currently re-parses document after each operation due to StructureOperations
            returning serialized strings (required for JSON-RPC bridge compatibility).

        Raises:
            ExecutionError: If operation execution fails
        """
        op_name = operation.name

        # Look up operation in dispatch table
        if op_name not in self._operation_dispatch:
            raise ExecutionError(f"Unknown operation: {op_name}")

        handler, required_args = self._operation_dispatch[op_name]

        # Validate argument count
        if len(operation.args) < required_args:
            arg_word = "argument" if required_args == 1 else "arguments"
            raise ExecutionError(f"{op_name} requires {required_args} {arg_word}")

        # Execute operation directly on Document object
        return handler(doc, *operation.args)

    def _exec_promote(self, doc: Document[Any], node_id: Any) -> Document[Any]:
        """Execute promote operation directly on Document object."""
        node_id_str = str(node_id)
        result = self.operations.promote(doc, node_id_str)
        if not result.success:
            raise ExecutionError(f"promote failed: {result.error}")
        if result.document is None:
            raise ExecutionError("promote returned no document")
        # Parse once and return - this is the only place we parse
        return Document.from_string(result.document)

    def _exec_demote(self, doc: Document[Any], node_id: Any) -> Document[Any]:
        """Execute demote operation directly on Document object."""
        node_id_str = str(node_id)
        result = self.operations.demote(doc, node_id_str)
        if not result.success:
            raise ExecutionError(f"demote failed: {result.error}")
        if result.document is None:
            raise ExecutionError("demote returned no document")
        return Document.from_string(result.document)

    def _exec_move_up(self, doc: Document[Any], node_id: Any) -> Document[Any]:
        """Execute move_up operation directly on Document object."""
        node_id_str = str(node_id)
        result = self.operations.move_up(doc, node_id_str)
        if not result.success:
            raise ExecutionError(f"move_up failed: {result.error}")
        if result.document is None:
            raise ExecutionError("move_up returned no document")
        return Document.from_string(result.document)

    def _exec_move_down(self, doc: Document[Any], node_id: Any) -> Document[Any]:
        """Execute move_down operation directly on Document object."""
        node_id_str = str(node_id)
        result = self.operations.move_down(doc, node_id_str)
        if not result.success:
            raise ExecutionError(f"move_down failed: {result.error}")
        if result.document is None:
            raise ExecutionError("move_down returned no document")
        return Document.from_string(result.document)

    def _exec_nest(self, doc: Document[Any], node_id: Any, parent_id: Any) -> Document[Any]:
        """Execute nest operation directly on Document object."""
        node_id_str = str(node_id)
        parent_id_str = str(parent_id)
        result = self.operations.nest(doc, node_id_str, parent_id_str)
        if not result.success:
            raise ExecutionError(f"nest failed: {result.error}")
        if result.document is None:
            raise ExecutionError("nest returned no document")
        return Document.from_string(result.document)

    def _exec_unnest(self, doc: Document[Any], node_id: Any) -> Document[Any]:
        """Execute unnest operation directly on Document object."""
        node_id_str = str(node_id)
        result = self.operations.unnest(doc, node_id_str)
        if not result.success:
            raise ExecutionError(f"unnest failed: {result.error}")
        if result.document is None:
            raise ExecutionError("unnest returned no document")
        return Document.from_string(result.document)


class ScriptExecutor:
    """Executor for .tk script files."""

    def __init__(self):
        """Initialize script executor."""
        # No instance variables needed - Executor creates its own StructureOperations

    def execute_file(self, script_path: str | Path, document_path: str | Path) -> Document[Any]:
        """
        Execute a script file on a document.

        Args:
            script_path: Path to the .tk script file
            document_path: Path to the document to transform

        Returns:
            Transformed document

        Raises:
            ExecutionError: If execution, parsing, or I/O fails
            FileNotFoundError: If script or document file not found
        """
        script_path = Path(script_path)
        document_path = Path(document_path)

        # Read script file with explicit encoding
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")

        try:
            script_content = script_path.read_text(encoding="utf-8")
        except OSError as e:
            raise ExecutionError(f"Error reading script file: {e}") from e

        # Read document file with explicit encoding
        if not document_path.exists():
            raise FileNotFoundError(f"Document file not found: {document_path}")

        try:
            document = Document.from_file(str(document_path))
        except Exception as e:
            raise ExecutionError(f"Error loading document: {e}") from e

        # Parse script
        try:
            lexer = Lexer(script_content)
            tokens = lexer.tokenize()

            parser = Parser(tokens)
            ast = parser.parse()
        except LexerError as e:
            # Re-raise with file context
            raise ExecutionError(
                f"Syntax error in {script_path.name}: {e}", line=e.line, column=e.column
            ) from e
        except ParseError as e:
            # Re-raise with file context
            line = e.token.line if e.token else None
            column = e.token.column if e.token else None
            raise ExecutionError(
                f"Parse error in {script_path.name}: {e}", line=line, column=column
            ) from e

        # Execute script
        try:
            executor = Executor(document)
            result = executor.execute(ast)
            return result
        except ExecutionError:
            # Re-raise execution errors as-is
            raise
        except Exception as e:
            raise ExecutionError(f"Execution failed: {e}") from e

    def execute_file_and_save(
        self, script_path: str | Path, document_path: str | Path
    ) -> Document[Any]:
        """
        Execute a script file on a document and save the result.

        Args:
            script_path: Path to the .tk script file
            document_path: Path to the document to transform

        Returns:
            Transformed document

        Raises:
            ExecutionError: If execution, parsing, I/O, or saving fails
            FileNotFoundError: If script or document file not found
        """
        result = self.execute_file(script_path, document_path)

        # Save result back to document file with explicit encoding
        try:
            result.to_file(str(document_path))
        except Exception as e:
            raise ExecutionError(f"Error saving document: {e}") from e

        return result
