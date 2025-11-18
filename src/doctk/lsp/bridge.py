"""Extension bridge for TypeScript-Python communication via JSON-RPC."""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any

from doctk.core import Document
from doctk.lsp.operations import StructureOperations
from doctk.lsp.protocols import OperationResult


class ExtensionBridge:
    """
    Bridge between VS Code extension and doctk core.

    Provides a JSON-RPC interface over stdin/stdout for executing
    document operations from the TypeScript extension.
    """

    def __init__(self):
        """Initialize the extension bridge."""
        self.operations = StructureOperations()

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Handle a JSON-RPC request.

        Args:
            request: JSON-RPC request dictionary with:
                - jsonrpc: "2.0"
                - id: Request ID
                - method: Method name
                - params: Method parameters

        Returns:
            JSON-RPC response dictionary
        """
        jsonrpc_version = request.get("jsonrpc")
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        # Validate JSON-RPC version
        if jsonrpc_version != "2.0":
            return self._error_response(
                request_id, -32600, "Invalid Request: JSON-RPC version must be 2.0"
            )

        # Validate method
        if not method:
            return self._error_response(request_id, -32600, "Invalid Request: Missing method")

        # Route to appropriate handler
        try:
            result = self._execute_method(method, params)
            return self._success_response(request_id, result)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            return self._error_response(request_id, -32603, f"Internal error: {str(e)}")

    def _execute_method(self, method: str, params: dict[str, Any]) -> Any:
        """
        Execute a method with the given parameters.

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Method result

        Raises:
            ValueError: If method is unknown
        """
        # Map of method names to handlers
        method_map = {
            "promote": self._handle_promote,
            "demote": self._handle_demote,
            "move_up": self._handle_move_up,
            "move_down": self._handle_move_down,
            "nest": self._handle_nest,
            "unnest": self._handle_unnest,
            "validate_promote": self._handle_validate_promote,
            "validate_demote": self._handle_validate_demote,
            "validate_move_up": self._handle_validate_move_up,
            "validate_move_down": self._handle_validate_move_down,
            "validate_nest": self._handle_validate_nest,
            "validate_unnest": self._handle_validate_unnest,
        }

        handler = method_map.get(method)
        if not handler:
            raise ValueError(f"Unknown method: {method}")

        return handler(params)

    def _handle_promote(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle promote operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.promote(doc, node_id)

        return self._operation_result_to_dict(result)

    def _handle_demote(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle demote operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.demote(doc, node_id)

        return self._operation_result_to_dict(result)

    def _handle_move_up(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle move_up operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.move_up(doc, node_id)

        return self._operation_result_to_dict(result)

    def _handle_move_down(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle move_down operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.move_down(doc, node_id)

        return self._operation_result_to_dict(result)

    def _handle_nest(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle nest operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")
        parent_id = params.get("parent_id")

        if not document_text or not node_id or not parent_id:
            raise ValueError("Missing required parameters: document, node_id, parent_id")

        doc = Document.from_string(document_text)
        result = self.operations.nest(doc, node_id, parent_id)

        return self._operation_result_to_dict(result)

    def _handle_unnest(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle unnest operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.unnest(doc, node_id)

        return self._operation_result_to_dict(result)

    def _handle_validate_promote(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle validate_promote operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.validate_promote(doc, node_id)

        return {"valid": result.valid, "error": result.error}

    def _handle_validate_demote(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle validate_demote operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.validate_demote(doc, node_id)

        return {"valid": result.valid, "error": result.error}

    def _handle_validate_move_up(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle validate_move_up operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.validate_move_up(doc, node_id)

        return {"valid": result.valid, "error": result.error}

    def _handle_validate_move_down(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle validate_move_down operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.validate_move_down(doc, node_id)

        return {"valid": result.valid, "error": result.error}

    def _handle_validate_nest(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle validate_nest operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")
        parent_id = params.get("parent_id")

        if not document_text or not node_id or not parent_id:
            raise ValueError("Missing required parameters: document, node_id, parent_id")

        doc = Document.from_string(document_text)
        result = self.operations.validate_nest(doc, node_id, parent_id)

        return {"valid": result.valid, "error": result.error}

    def _handle_validate_unnest(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle validate_unnest operation."""
        document_text = params.get("document")
        node_id = params.get("node_id")

        if not document_text or not node_id:
            raise ValueError("Missing required parameters: document, node_id")

        doc = Document.from_string(document_text)
        result = self.operations.validate_unnest(doc, node_id)

        return {"valid": result.valid, "error": result.error}

    def _operation_result_to_dict(self, result: OperationResult) -> dict[str, Any]:
        """
        Convert OperationResult to dictionary for JSON serialization.

        Args:
            result: OperationResult to convert

        Returns:
            Dictionary representation
        """
        return {
            "success": result.success,
            "document": result.document,
            "modified_ranges": result.modified_ranges,
            "error": result.error,
        }

    def _success_response(self, request_id: Any, result: Any) -> dict[str, Any]:
        """
        Create a JSON-RPC success response.

        Args:
            request_id: Request ID
            result: Result data

        Returns:
            JSON-RPC success response
        """
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error_response(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        """
        Create a JSON-RPC error response.

        Args:
            request_id: Request ID
            code: Error code
            message: Error message

        Returns:
            JSON-RPC error response
        """
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }

    def run(self):
        """
        Run the bridge, reading requests from stdin and writing responses to stdout.

        This is the main loop for the JSON-RPC bridge.
        """
        # Signal that the bridge is ready
        print("BRIDGE_READY", flush=True)

        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                # Send parse error response
                error_response = self._error_response(
                    None, -32700, f"Parse error: {str(e)}"
                )
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                # Send internal error response
                error_response = self._error_response(
                    None, -32603, f"Internal error: {str(e)}"
                )
                print(json.dumps(error_response), flush=True)


def main():
    """Main entry point for the extension bridge."""
    bridge = ExtensionBridge()
    bridge.run()


if __name__ == "__main__":
    main()
