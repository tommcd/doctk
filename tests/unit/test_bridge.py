"""Tests for the ExtensionBridge JSON-RPC interface."""



from doctk.lsp.bridge import ExtensionBridge


class TestExtensionBridge:
    """Tests for ExtensionBridge class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bridge = ExtensionBridge()

    def test_handle_promote_request(self):
        """Test handling a promote operation request."""
        doc_text = "# Title\n\n## Section\n"
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": doc_text, "node_id": "h2-0"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["success"] is True
        assert "# Title" in response["result"]["document"]
        assert "# Section" in response["result"]["document"]  # h2 -> h1

    def test_handle_demote_request(self):
        """Test handling a demote operation request."""
        doc_text = "# Title\n"
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "demote",
            "params": {"document": doc_text, "node_id": "h1-0"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert response["result"]["success"] is True
        assert "## Title" in response["result"]["document"]  # h1 -> h2

    def test_handle_move_up_request(self):
        """Test handling a move_up operation request."""
        doc_text = "# First\n\n# Second\n"
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "move_up",
            "params": {"document": doc_text, "node_id": "h1-1"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert response["result"]["success"] is True
        # Second should now be first
        lines = response["result"]["document"].strip().split("\n")
        assert "Second" in lines[0]
        assert "First" in lines[2]  # Skip blank line

    def test_handle_move_down_request(self):
        """Test handling a move_down operation request."""
        doc_text = "# First\n\n# Second\n"
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "move_down",
            "params": {"document": doc_text, "node_id": "h1-0"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response
        assert response["result"]["success"] is True

    def test_handle_nest_request(self):
        """Test handling a nest operation request."""
        doc_text = "# Parent\n\n# Child\n"
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "nest",
            "params": {"document": doc_text, "node_id": "h1-1", "parent_id": "h1-0"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        assert response["result"]["success"] is True
        # Child should now be h2 (nested under parent)
        assert "## Child" in response["result"]["document"]

    def test_handle_unnest_request(self):
        """Test handling an unnest operation request."""
        doc_text = "## Nested\n"
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "unnest",
            "params": {"document": doc_text, "node_id": "h2-0"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 6
        assert "result" in response
        assert response["result"]["success"] is True
        assert "# Nested" in response["result"]["document"]  # h2 -> h1

    def test_handle_validate_promote_request(self):
        """Test handling a validate_promote request."""
        doc_text = "## Section\n"
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "validate_promote",
            "params": {"document": doc_text, "node_id": "h2-0"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 7
        assert "result" in response
        assert response["result"]["valid"] is True
        assert response["result"]["error"] is None

    def test_handle_validate_nest_request(self):
        """Test handling a validate_nest request."""
        doc_text = "# Parent\n\n# Child\n"
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "validate_nest",
            "params": {"document": doc_text, "node_id": "h1-1", "parent_id": "h1-0"},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 8
        assert "result" in response
        assert response["result"]["valid"] is True

    def test_invalid_jsonrpc_version(self):
        """Test error response for invalid JSON-RPC version."""
        request = {"jsonrpc": "1.0", "id": 1, "method": "promote", "params": {}}

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32600
        assert "version" in response["error"]["message"].lower()

    def test_missing_method(self):
        """Test error response for missing method."""
        request = {"jsonrpc": "2.0", "id": 1, "params": {}}

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32600

    def test_unknown_method(self):
        """Test error response for unknown method."""
        request = {"jsonrpc": "2.0", "id": 1, "method": "invalid_method", "params": {}}

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32603
        assert "unknown method" in response["error"]["message"].lower()

    def test_missing_required_parameters(self):
        """Test error response for missing required parameters."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {},  # Missing document and node_id
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32603

    def test_operation_error_handling(self):
        """Test error handling when operation fails."""
        doc_text = "# Title\n"
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": doc_text, "node_id": "h99-0"},  # Invalid node ID
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["success"] is False
        assert "not found" in response["result"]["error"].lower()


class TestExtensionBridgeIntegration:
    """Integration tests for ExtensionBridge with complex scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bridge = ExtensionBridge()

    def test_complex_document_promote_chain(self):
        """Test multiple promote operations on a complex document."""
        doc_text = """# Title

## Section 1

### Subsection 1.1

## Section 2

### Subsection 2.1
"""
        # Promote first subsection
        request1 = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": doc_text, "node_id": "h3-0"},
        }
        response1 = self.bridge.handle_request(request1)
        assert response1["result"]["success"] is True

        # Now promote the promoted section again
        new_doc = response1["result"]["document"]
        request2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "promote",
            "params": {"document": new_doc, "node_id": "h2-1"},
        }
        response2 = self.bridge.handle_request(request2)
        assert response2["result"]["success"] is True
        assert "# Subsection 1.1" in response2["result"]["document"]

    def test_nest_and_unnest_roundtrip(self):
        """Test that nest and unnest are inverses."""
        doc_text = "# Parent\n\n# Child\n"

        # Nest child under parent
        nest_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "nest",
            "params": {"document": doc_text, "node_id": "h1-1", "parent_id": "h1-0"},
        }
        nest_response = self.bridge.handle_request(nest_request)
        assert nest_response["result"]["success"] is True
        nested_doc = nest_response["result"]["document"]

        # Unnest the child
        unnest_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "unnest",
            "params": {"document": nested_doc, "node_id": "h2-0"},
        }
        unnest_response = self.bridge.handle_request(unnest_request)
        assert unnest_response["result"]["success"] is True

        # Should be back to approximately original structure
        # (Child is now h1 again)
        assert "# Child" in unnest_response["result"]["document"]

    def test_move_operations_reordering(self):
        """Test move operations for reordering sections."""
        doc_text = "# First\n\n# Second\n\n# Third\n"

        # Move third section up
        request1 = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "move_up",
            "params": {"document": doc_text, "node_id": "h1-2"},
        }
        response1 = self.bridge.handle_request(request1)
        assert response1["result"]["success"] is True

        # Move it up again
        doc2 = response1["result"]["document"]
        request2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "move_up",
            "params": {"document": doc2, "node_id": "h1-1"},
        }
        response2 = self.bridge.handle_request(request2)
        assert response2["result"]["success"] is True

        # Third should now be first
        lines = [
            line for line in response2["result"]["document"].split("\n") if line.strip()
        ]
        assert "Third" in lines[0]

    def test_validation_before_operation(self):
        """Test validation workflow before executing operation."""
        doc_text = "###### Deepest\n"  # h6

        # Validate demote (should be valid but identity)
        validate_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "validate_demote",
            "params": {"document": doc_text, "node_id": "h6-0"},
        }
        validate_response = self.bridge.handle_request(validate_request)
        assert validate_response["result"]["valid"] is True

        # Execute demote
        demote_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "demote",
            "params": {"document": doc_text, "node_id": "h6-0"},
        }
        demote_response = self.bridge.handle_request(demote_request)
        assert demote_response["result"]["success"] is True
        # Should stay at h6
        assert "###### Deepest" in demote_response["result"]["document"]

    def test_error_recovery(self):
        """Test that bridge continues working after errors."""
        doc_text = "# Title\n"

        # Send invalid request
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "promote",
            "params": {"document": doc_text, "node_id": "h99-0"},
        }
        invalid_response = self.bridge.handle_request(invalid_request)
        assert invalid_response["result"]["success"] is False

        # Send valid request - should still work
        valid_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "demote",
            "params": {"document": doc_text, "node_id": "h1-0"},
        }
        valid_response = self.bridge.handle_request(valid_request)
        assert valid_response["result"]["success"] is True
