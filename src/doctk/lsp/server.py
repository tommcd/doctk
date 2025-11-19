"""doctk Language Server implementation.

This module implements a Language Server Protocol (LSP) server for the doctk DSL,
providing intelligent code completion, validation, and documentation features.
"""

from __future__ import annotations

import logging

from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_HOVER,
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    Position,
    Range,
)
from pygls.lsp.server import LanguageServer

from doctk.dsl.lexer import Lexer, LexerError
from doctk.dsl.parser import ParseError, Parser
from doctk.lsp.completion import CompletionProvider
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

        # Initialize operation registry and providers
        self.registry = OperationRegistry()
        self.completion_provider = CompletionProvider(self.registry)
        self.hover_provider = HoverProvider(self.registry)

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

            uri = params.text_document.uri

            # Get document text
            if uri not in self.documents:
                logger.warning(f"Document not found for completion: {uri}")
                return CompletionList(is_incomplete=False, items=[])

            text = self.documents[uri].text

            # Provide completions
            return self.completion_provider.provide_completions(text, params.position)

        @self.feature(TEXT_DOCUMENT_HOVER)  # type: ignore[misc]
        async def hover(_ls: LanguageServer, params: HoverParams) -> Hover | None:
            """Handle hover request."""
            logger.info(f"Hover requested at {params.position.line}:{params.position.character}")

            uri = params.text_document.uri

            # Get document text
            if uri not in self.documents:
                logger.warning(f"Document not found for hover: {uri}")
                return None

            text = self.documents[uri].text

            # Provide hover information
            return self.hover_provider.provide_hover(text, params.position)

    async def parse_and_validate(self, uri: str, text: str) -> None:
        """
        Parse and validate document content.

        Args:
            uri: Document URI
            text: Document text content
        """
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
            List of diagnostic messages
        """
        diagnostics: list[Diagnostic] = []

        try:
            # Tokenize the document
            lexer = Lexer(text)
            tokens = lexer.tokenize()

            # Parse tokens into AST
            parser = Parser(tokens)
            _ = parser.parse()  # AST will be used for operation validation in future tasks

            # Validate operations (stub for now)
            # TODO: Implement operation validation
            # This would check:
            # - Unknown operations
            # - Invalid operation arguments
            # - Type mismatches

        except ParseError as e:
            # Parser error with token information
            line = 0
            column = 0

            if e.token:
                # Token positions are 1-indexed, LSP uses 0-indexed
                line = max(0, e.token.line - 1)
                column = max(0, e.token.column - 1)

            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=line, character=column),
                    end=Position(line=line, character=column + 1),
                ),
                message=str(e),
                severity=DiagnosticSeverity.Error,
                source="doctk-lsp",
            )
            diagnostics.append(diagnostic)

        except LexerError as e:
            # Lexer error with line/column information
            # LexerError has line/column as attributes (1-indexed)
            # Convert to 0-indexed positions for LSP
            line = max(0, e.line - 1)
            column = max(0, e.column - 1)

            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=line, character=column),
                    end=Position(line=line, character=column + 1),
                ),
                message=str(e),
                severity=DiagnosticSeverity.Error,
                source="doctk-lsp",
            )
            diagnostics.append(diagnostic)

        except Exception as e:
            # Generic error
            logger.error(f"Error parsing document: {e}")
            diagnostic = Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=1),
                ),
                message=f"Parse error: {str(e)}",
                severity=DiagnosticSeverity.Error,
                source="doctk-lsp",
            )
            diagnostics.append(diagnostic)

        return diagnostics


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
