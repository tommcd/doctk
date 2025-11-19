"""doctk Language Server implementation.

This module implements a Language Server Protocol (LSP) server for the doctk DSL,
providing intelligent code completion, validation, and documentation features.
"""

from __future__ import annotations

import difflib
import logging
import re

from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_SIGNATURE_HELP,
    WORKSPACE_DID_CHANGE_CONFIGURATION,
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeConfigurationParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentSymbol,
    DocumentSymbolParams,
    Hover,
    HoverParams,
    MessageType,
    ParameterInformation,
    Position,
    Range,
    SignatureHelp,
    SignatureHelpParams,
    SignatureInformation,
    SymbolKind,
)
from pygls.lsp.server import LanguageServer

from doctk.dsl.lexer import Lexer, LexerError
from doctk.dsl.parser import ParseError, Parser, Pipeline
from doctk.lsp.ai_support import AIAgentSupport
from doctk.lsp.completion import CompletionProvider
from doctk.lsp.config import LSPConfiguration
from doctk.lsp.hover import HoverProvider
from doctk.lsp.registry import OperationRegistry

# Get logger for this module
# Note: Logging configuration is handled by the consuming application or main()
logger = logging.getLogger(__name__)


class DocumentState:
    """Maintains state for an open document."""

    def __init__(self, uri: str, text: str, version: int):
        """
        Initialize document state.

        Args:
            uri: Document URI
            text: Document text content
            version: Document version number
        """
        self.uri = uri
        self.text = text
        self.version = version
        self.diagnostics: list[Diagnostic] = []


class DoctkLanguageServer(LanguageServer):  # type: ignore[misc]
    """Language Server for doctk DSL."""

    def __init__(self) -> None:
        """Initialize the doctk language server."""
        super().__init__("doctk-lsp", "v0.1.0")
        self.documents: dict[str, DocumentState] = {}

        # Initialize configuration with defaults
        self.config = LSPConfiguration()

        # Initialize operation registry and providers
        self.registry = OperationRegistry()
        self.completion_provider = CompletionProvider(self.registry)
        self.hover_provider = HoverProvider(self.registry)
        self.ai_support = AIAgentSupport(self.registry)

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register LSP event handlers."""

        @self.feature(TEXT_DOCUMENT_DID_OPEN)  # type: ignore[misc]
        async def did_open(_ls: LanguageServer, params: DidOpenTextDocumentParams) -> None:
            """Handle document open event."""
            logger.info(f"Document opened: {params.text_document.uri}")

            uri = params.text_document.uri
            text = params.text_document.text
            version = params.text_document.version

            # Create document state
            doc_state = DocumentState(uri, text, version)
            self.documents[uri] = doc_state

            # Parse and validate document
            await self.parse_and_validate(uri, text)

        @self.feature(TEXT_DOCUMENT_DID_CHANGE)  # type: ignore[misc]
        async def did_change(_ls: LanguageServer, params: DidChangeTextDocumentParams) -> None:
            """Handle document change event."""
            logger.info(f"Document changed: {params.text_document.uri}")

            uri = params.text_document.uri
            version = params.text_document.version

            if uri not in self.documents:
                logger.warning(f"Document not found: {uri}")
                return

            # Update document with new content
            # For full text sync, we get the full document content
            if params.content_changes:
                text = params.content_changes[0].text
                self.documents[uri].text = text
                self.documents[uri].version = version

                # Parse and validate updated document
                await self.parse_and_validate(uri, text)

        @self.feature(TEXT_DOCUMENT_DID_CLOSE)  # type: ignore[misc]
        async def did_close(_ls: LanguageServer, params: DidCloseTextDocumentParams) -> None:
            """Handle document close event."""
            logger.info(f"Document closed: {params.text_document.uri}")

            uri = params.text_document.uri
            if uri in self.documents:
                del self.documents[uri]

        @self.feature(TEXT_DOCUMENT_COMPLETION)  # type: ignore[misc]
        async def completions(_ls: LanguageServer, params: CompletionParams) -> CompletionList:
            """Handle completion request."""
            logger.info(
                f"Completion requested at {params.position.line}:{params.position.character}"
            )

            # Check if language server is enabled
            if not self.config.enabled:
                logger.debug("Language server disabled, returning empty completion list")
                return CompletionList(is_incomplete=False, items=[])

            uri = params.text_document.uri

            # Get document text
            if uri not in self.documents:
                logger.warning(f"Document not found for completion: {uri}")
                return CompletionList(is_incomplete=False, items=[])

            text = self.documents[uri].text

            # Provide completions with max_items from configuration
            return self.completion_provider.provide_completions(
                text, params.position, max_items=self.config.max_completion_items
            )

        @self.feature(TEXT_DOCUMENT_HOVER)  # type: ignore[misc]
        async def hover(_ls: LanguageServer, params: HoverParams) -> Hover | None:
            """Handle hover request."""
            logger.info(f"Hover requested at {params.position.line}:{params.position.character}")

            # Check if language server is enabled
            if not self.config.enabled:
                logger.debug("Language server disabled, returning no hover")
                return None

            uri = params.text_document.uri

            # Get document text
            if uri not in self.documents:
                logger.warning(f"Document not found for hover: {uri}")
                return None

            text = self.documents[uri].text

            # Provide hover information
            return self.hover_provider.provide_hover(text, params.position)

        @self.feature(TEXT_DOCUMENT_SIGNATURE_HELP)  # type: ignore[misc]
        async def signature_help(
            _ls: LanguageServer, params: SignatureHelpParams
        ) -> SignatureHelp | None:
            """Handle signature help request."""
            logger.info(
                f"Signature help requested at {params.position.line}:{params.position.character}"
            )

            # Check if language server is enabled
            if not self.config.enabled:
                logger.debug("Language server disabled, returning no signature help")
                return None

            uri = params.text_document.uri

            # Get document text
            if uri not in self.documents:
                logger.warning(f"Document not found for signature help: {uri}")
                return None

            text = self.documents[uri].text

            # Provide signature help
            return self.provide_signature_help(text, params.position)

        @self.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)  # type: ignore[misc]
        async def document_symbols(
            _ls: LanguageServer, params: DocumentSymbolParams
        ) -> list[DocumentSymbol] | None:
            """Handle document symbols request."""
            logger.info(f"Document symbols requested for {params.text_document.uri}")

            # Check if language server is enabled
            if not self.config.enabled:
                logger.debug("Language server disabled, returning no document symbols")
                return None

            uri = params.text_document.uri

            # Get document text
            if uri not in self.documents:
                logger.warning(f"Document not found for document symbols: {uri}")
                return None

            text = self.documents[uri].text

            # Extract document symbols
            return self.extract_document_symbols(text)

        @self.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)  # type: ignore[misc]
        async def did_change_configuration(
            _ls: LanguageServer, params: DidChangeConfigurationParams
        ) -> None:
            """Handle configuration change event."""
            logger.info("Configuration changed")

            # Extract doctk.lsp settings from the configuration
            # The settings come nested under 'doctk.lsp' if synchronize.configurationSection is set
            settings = params.settings

            # Handle both nested and flat configuration structures
            if isinstance(settings, dict):
                # Check if settings are nested under 'doctk.lsp' or 'doctk'
                lsp_config = settings.get("doctk.lsp") or settings.get("doctk", {}).get("lsp") or settings

                # Update configuration
                warnings = self.config.update_from_dict(lsp_config)

                # Display warnings to user if any validation errors occurred
                if warnings:
                    for warning in warnings:
                        self.show_message(warning, MessageType.Warning)

                logger.info(
                    f"Configuration updated: trace={self.config.trace.value}, "
                    f"maxCompletionItems={self.config.max_completion_items}, "
                    f"enabled={self.config.enabled}"
                )
            else:
                logger.warning(f"Unexpected settings format: {type(settings)}")

    async def parse_and_validate(self, uri: str, text: str) -> None:
        """
        Parse and validate document content.

        Args:
            uri: Document URI
            text: Document text content
        """
        # Check if language server is enabled
        if not self.config.enabled:
            logger.debug("Language server disabled, skipping validation")
            # Clear diagnostics when disabled
            self.text_document_publish_diagnostics(uri, [])
            return

        diagnostics = self.validate_syntax(text)

        # Store diagnostics in document state
        if uri in self.documents:
            self.documents[uri].diagnostics = diagnostics

        # Publish diagnostics to client
        self.text_document_publish_diagnostics(uri, diagnostics)

    def validate_syntax(self, text: str) -> list[Diagnostic]:
        """
        Validate DSL syntax and return diagnostics.

        Args:
            text: Document text to validate

        Returns:
            List of diagnostic messages with actionable information
        """
        diagnostics: list[Diagnostic] = []

        try:
            # Tokenize the document
            lexer = Lexer(text)
            tokens = lexer.tokenize()

            # Parse tokens into AST
            parser = Parser(tokens)
            statements = parser.parse()  # Returns list[ASTNode], not an object

            # Validate operations
            for statement in statements:
                # Only Pipeline nodes have operations
                if isinstance(statement, Pipeline):
                    for op in statement.operations:
                        # FunctionCall has 'name' attribute, not 'operation_name'
                        if hasattr(op, "name"):
                            op_name = op.name

                            # Check if operation exists
                            if not self.registry.operation_exists(op_name):
                                # Unknown operation - provide suggestions
                                # LIMITATION: FunctionCall AST nodes don't preserve token positions.
                                # All diagnostics currently report at line 0, column 0.
                                # TODO: Enhance parser to include position info in AST nodes.
                                # See: https://github.com/tommcd/doctk/pull/24#discussion_r3481216455
                                line = 0
                                column = 0

                                # Find similar operations for suggestions
                                similar_ops = self._find_similar_operations(op_name)
                                message = f"Unknown operation '{op_name}'"

                                if similar_ops:
                                    suggestions = ", ".join(f"'{op}'" for op in similar_ops[:3])
                                    message += f". Did you mean: {suggestions}?"
                                else:
                                    message += (
                                        ". Use completion (Ctrl+Space) to see available operations."
                                    )

                                diagnostic = Diagnostic(
                                    range=Range(
                                        start=Position(line=line, character=column),
                                        end=Position(line=line, character=column + len(op_name)),
                                    ),
                                    message=message,
                                    severity=DiagnosticSeverity.Error,
                                    source="doctk-lsp",
                                )
                                diagnostics.append(diagnostic)

                            # Validate operation arguments
                            else:
                                op_metadata = self.registry.get_operation(op_name)
                                if op_metadata:
                                    # Check required parameters
                                    # Count both positional args and keyword args
                                    num_positional = len(op.args) if hasattr(op, "args") else 0
                                    provided_kwargs = (
                                        list(op.kwargs.keys())
                                        if hasattr(op, "kwargs") and isinstance(op.kwargs, dict)
                                        else []
                                    )

                                    required_params = [
                                        p.name for p in op_metadata.parameters if p.required
                                    ]

                                    # For now, assume positional args satisfy required params in order
                                    # This is a simplified check - full validation would need type checking
                                    unsatisfied_params = max(
                                        0, len(required_params) - num_positional
                                    )
                                    missing_params = [
                                        p
                                        for p in required_params[num_positional:]
                                        if p not in provided_kwargs
                                    ]

                                    if missing_params and unsatisfied_params > 0:
                                        # LIMITATION: FunctionCall AST nodes don't preserve token positions.
                                        # TODO: Enhance parser to include position info in AST nodes.
                                        line = 0
                                        column = 0

                                        message = (
                                            f"Operation '{op_name}' missing required parameters: "
                                            f"{', '.join(missing_params)}"
                                        )

                                        diagnostic = Diagnostic(
                                            range=Range(
                                                start=Position(line=line, character=column),
                                                end=Position(
                                                    line=line, character=column + len(op_name)
                                                ),
                                            ),
                                            message=message,
                                            severity=DiagnosticSeverity.Error,
                                            source="doctk-lsp",
                                        )
                                        diagnostics.append(diagnostic)

        except ParseError as e:
            # Parser error with token information
            # Log detailed error information for debugging
            logger.error(
                f"Parse error: {e}",
                exc_info=True,
                extra={
                    "error_type": "ParseError",
                    "token": str(e.token) if e.token else None,
                    "text_length": len(text),
                },
            )

            line = 0
            column = 0

            if e.token:
                # Token positions are 1-indexed, LSP uses 0-indexed
                line = max(0, e.token.line - 1)
                column = max(0, e.token.column - 1)

            # Provide actionable diagnostic with context
            message = str(e)
            # Add helpful hint for common parse errors
            if "Expected" in message and "got" in message:
                message += " (Tip: Check for missing or extra operators like '|')"

            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=line, character=column),
                    end=Position(line=line, character=column + 1),
                ),
                message=message,
                severity=DiagnosticSeverity.Error,
                source="doctk-lsp",
            )
            diagnostics.append(diagnostic)

        except LexerError as e:
            # Lexer error with line/column information
            # Log detailed error information for debugging
            logger.error(
                f"Lexer error: {e}",
                exc_info=True,
                extra={
                    "error_type": "LexerError",
                    "line": e.line,
                    "column": e.column,
                    "text_length": len(text),
                },
            )

            # LexerError has line/column as attributes (1-indexed)
            # Convert to 0-indexed positions for LSP
            line = max(0, e.line - 1)
            column = max(0, e.column - 1)

            # Provide actionable diagnostic
            message = str(e)
            if "Unknown character" in message:
                message += " (Tip: Only use valid doctk DSL syntax)"

            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=line, character=column),
                    end=Position(line=line, character=column + 1),
                ),
                message=message,
                severity=DiagnosticSeverity.Error,
                source="doctk-lsp",
            )
            diagnostics.append(diagnostic)

        except Exception as e:
            # Generic error - comprehensive logging with stack trace
            # This provides detailed diagnostic information for troubleshooting
            # Note: exc_info=True automatically captures and formats the stack trace
            logger.error(
                f"Unexpected error parsing document: {e}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "text_length": len(text),
                    "text_preview": text[:100] if len(text) > 100 else text,
                },
            )

            # Still provide a diagnostic to the user, even if parsing completely failed
            # This is graceful degradation - we show what we can
            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=1),
                ),
                message=f"Internal error: {str(e)}. Check the output panel for details.",
                severity=DiagnosticSeverity.Error,
                source="doctk-lsp",
            )
            diagnostics.append(diagnostic)

        return diagnostics

    def provide_signature_help(self, text: str, position: Position) -> SignatureHelp | None:
        """
        Provide signature help for operation at cursor position.

        Args:
            text: Document text
            position: Cursor position

        Returns:
            Signature help information or None
        """
        try:
            # Extract the word at the cursor position
            lines = text.split("\n")
            if position.line >= len(lines):
                return None

            line = lines[position.line]
            if position.character > len(line):
                return None

            # Find the operation name before the cursor
            # Walk backwards to find the opening parenthesis
            before_cursor = line[: position.character]

            # Find the last unclosed opening parenthesis
            paren_depth = 0
            open_paren_pos = -1
            for i in range(len(before_cursor) - 1, -1, -1):
                if before_cursor[i] == ")":
                    paren_depth += 1
                elif before_cursor[i] == "(":
                    if paren_depth == 0:
                        open_paren_pos = i
                        break
                    paren_depth -= 1

            if open_paren_pos == -1:
                # No opening parenthesis found, try simple word match
                words = re.findall(r"\b\w+\b", before_cursor)
                if not words:
                    return None
                operation_name = words[-1]
            else:
                # Find the operation name before the opening parenthesis
                before_paren = before_cursor[:open_paren_pos].rstrip()
                match = re.search(r"(\w+)\s*$", before_paren)
                if not match:
                    return None
                operation_name = match.group(1)

            # Get operation metadata
            operation = self.registry.get_operation(operation_name)
            if not operation:
                return None

            # Build signature information
            params_str = ", ".join(
                f"{p.name}: {p.type}" + (f" = {p.default}" if p.default is not None else "")
                for p in operation.parameters
            )

            signature_label = f"{operation_name}({params_str})"

            # Create parameter information
            parameters = [
                ParameterInformation(
                    label=p.name, documentation=f"{p.description} (type: {p.type})"
                )
                for p in operation.parameters
            ]

            signature = SignatureInformation(
                label=signature_label,
                documentation=operation.description,
                parameters=parameters if parameters else None,
            )

            return SignatureHelp(signatures=[signature], active_signature=0, active_parameter=0)

        except Exception as e:
            # Comprehensive error logging with stack trace
            # Note: exc_info=True automatically captures and formats the stack trace
            logger.error(
                f"Error providing signature help: {e}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "position": f"{position.line}:{position.character}",
                    "text_length": len(text),
                },
            )
            # Graceful degradation - return None rather than crashing
            return None

    def extract_document_symbols(self, text: str) -> list[DocumentSymbol]:
        """
        Extract document symbols (operations) from document.

        Args:
            text: Document text

        Returns:
            List of document symbols representing operations in the document
        """
        symbols: list[DocumentSymbol] = []

        try:
            # Parse the document
            lexer = Lexer(text)
            tokens = lexer.tokenize()

            parser = Parser(tokens)
            statements = parser.parse()  # Returns list[ASTNode], not an object

            # Extract operations from AST
            for statement in statements:
                # Only Pipeline nodes have source and operations
                if isinstance(statement, Pipeline) and statement.source:
                    # This is a pipeline starting with a source
                    # Create a symbol for the entire pipeline
                    # LIMITATION: Pipeline AST nodes don't preserve source token positions.
                    # All document symbols currently report at line 0.
                    # TODO: Enhance parser to include position info in AST nodes.
                    # See: https://github.com/tommcd/doctk/pull/24#discussion_r3481216455
                    source_line = 0

                    # Find end line by looking at the last operation
                    end_line = source_line
                    if statement.operations:
                        # Operations don't have token info, use source line
                        end_line = source_line

                    symbol_range = Range(
                        start=Position(line=source_line, character=0),
                        end=Position(line=end_line, character=0),
                    )

                    # Create a symbol for the pipeline
                    # statement.source is a string, not an object
                    pipeline_name = f"Pipeline: {statement.source}"
                    if statement.operations:
                        pipeline_name += f" | {len(statement.operations)} operations"

                    symbol = DocumentSymbol(
                        name=pipeline_name,
                        kind=SymbolKind.Function,
                        range=symbol_range,
                        selection_range=symbol_range,
                    )

                    # Add child symbols for each operation
                    children: list[DocumentSymbol] = []
                    for op in statement.operations:
                        # FunctionCall has 'name' attribute, not 'operation_name'
                        if hasattr(op, "name"):
                            # LIMITATION: FunctionCall doesn't have token, all ops report at line 0
                            op_line = source_line
                            op_range = Range(
                                start=Position(line=op_line, character=0),
                                end=Position(line=op_line, character=0),
                            )

                            op_symbol = DocumentSymbol(
                                name=op.name,
                                kind=SymbolKind.Method,
                                range=op_range,
                                selection_range=op_range,
                            )
                            children.append(op_symbol)

                    if children:
                        symbol.children = children

                    symbols.append(symbol)

        except Exception as e:
            # Comprehensive error logging with stack trace
            # Note: exc_info=True automatically captures and formats the stack trace
            logger.error(
                f"Error extracting document symbols: {e}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "text_length": len(text),
                },
            )
            # Graceful degradation - return empty list rather than crashing
            return []

        return symbols

    def _find_similar_operations(self, operation_name: str) -> list[str]:
        """
        Find operations with similar names using simple string distance.

        Args:
            operation_name: Name to find similar operations for

        Returns:
            List of similar operation names, sorted by similarity
        """
        all_operations = self.registry.get_operation_names()

        # Use difflib to find close matches
        # cutoff=0.6 means 60% similarity
        similar = difflib.get_close_matches(operation_name, all_operations, n=5, cutoff=0.6)

        return similar


def main() -> None:
    """Start the language server."""
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    server = DoctkLanguageServer()
    server.start_io()


if __name__ == "__main__":
    main()
