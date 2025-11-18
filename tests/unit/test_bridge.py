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
        lines = [line for line in response2["result"]["document"].split("\n") if line.strip()]
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


class TestGetDocumentTree:
    """Tests for get_document_tree RPC method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bridge = ExtensionBridge()

    def test_get_document_tree_single_heading(self):
        """Test getting document tree with single heading."""
        doc_text = "# Title\n"
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        response = self.bridge.handle_request(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "root" in response["result"]
        assert "version" in response["result"]

        # Check root node
        root = response["result"]["root"]
        assert root["id"] == "root"
        assert root["label"] == "Document"
        assert len(root["children"]) == 1

        # Check first child
        child = root["children"][0]
        assert child["id"] == "h1-0"
        assert child["label"] == "Title"
        assert child["level"] == 1

    def test_get_document_tree_flat_structure(self):
        """Test getting document tree with flat structure."""
        doc_text = "# First\n\n# Second\n\n# Third\n"
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        response = self.bridge.handle_request(request)

        assert "result" in response
        root = response["result"]["root"]

        # Should have 3 children
        assert len(root["children"]) == 3
        assert root["children"][0]["id"] == "h1-0"
        assert root["children"][0]["label"] == "First"
        assert root["children"][1]["id"] == "h1-1"
        assert root["children"][1]["label"] == "Second"
        assert root["children"][2]["id"] == "h1-2"
        assert root["children"][2]["label"] == "Third"

    def test_get_document_tree_nested_structure(self):
        """Test getting document tree with nested structure."""
        doc_text = """# Chapter 1

## Section 1.1

## Section 1.2

# Chapter 2
"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        response = self.bridge.handle_request(request)

        assert "result" in response
        root = response["result"]["root"]

        # Should have 2 top-level chapters
        assert len(root["children"]) == 2

        # Chapter 1 should have 2 sections
        chapter1 = root["children"][0]
        assert chapter1["id"] == "h1-0"
        assert chapter1["label"] == "Chapter 1"
        assert len(chapter1["children"]) == 2
        assert chapter1["children"][0]["id"] == "h2-0"
        assert chapter1["children"][0]["label"] == "Section 1.1"
        assert chapter1["children"][1]["id"] == "h2-1"
        assert chapter1["children"][1]["label"] == "Section 1.2"

        # Chapter 2 should have no children
        chapter2 = root["children"][1]
        assert chapter2["id"] == "h1-1"
        assert chapter2["label"] == "Chapter 2"
        assert len(chapter2["children"]) == 0

    def test_get_document_tree_deep_nesting(self):
        """Test getting document tree with deep nesting."""
        doc_text = """# Level 1

## Level 2

### Level 3

#### Level 4
"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        response = self.bridge.handle_request(request)

        assert "result" in response
        root = response["result"]["root"]

        # Navigate through the tree
        level1 = root["children"][0]
        assert level1["id"] == "h1-0"
        assert level1["label"] == "Level 1"

        level2 = level1["children"][0]
        assert level2["id"] == "h2-0"
        assert level2["label"] == "Level 2"

        level3 = level2["children"][0]
        assert level3["id"] == "h3-0"
        assert level3["label"] == "Level 3"

        level4 = level3["children"][0]
        assert level4["id"] == "h4-0"
        assert level4["label"] == "Level 4"
        assert len(level4["children"]) == 0

    def test_get_document_tree_empty_document(self):
        """Test getting document tree for empty document."""
        doc_text = ""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        response = self.bridge.handle_request(request)

        assert "result" in response
        root = response["result"]["root"]
        assert root["id"] == "root"
        assert root["label"] == "Document"
        assert len(root["children"]) == 0

    def test_get_document_tree_version_timestamp(self):
        """Test that version is a valid timestamp."""
        doc_text = "# Title\n"
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        response = self.bridge.handle_request(request)

        assert "result" in response
        version = response["result"]["version"]
        # Version should be a positive integer (timestamp in milliseconds)
        assert isinstance(version, int)
        assert version > 0

    def test_get_document_tree_missing_document_parameter(self):
        """Test error handling when document parameter is missing."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {},
        }

        response = self.bridge.handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == -32603
        assert "missing" in response["error"]["message"].lower()

    def test_get_document_tree_consistency_across_calls(self):
        """Test that tree structure is consistent across multiple calls."""
        doc_text = """# Title

## Section 1

### Subsection 1.1

## Section 2
"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        # Call twice
        response1 = self.bridge.handle_request(request)
        response2 = self.bridge.handle_request(request)

        # Trees should have the same structure (excluding version)
        root1 = response1["result"]["root"]
        root2 = response2["result"]["root"]

        # Same structure
        assert root1["id"] == root2["id"]
        assert len(root1["children"]) == len(root2["children"])

        # Same child IDs
        assert root1["children"][0]["id"] == root2["children"][0]["id"]
        assert root1["children"][0]["label"] == root2["children"][0]["label"]

    def test_get_document_tree_node_structure(self):
        """Test that each node has all required fields."""
        doc_text = "# Title\n\n## Section\n"
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "get_document_tree",
            "params": {"document": doc_text},
        }

        response = self.bridge.handle_request(request)

        def check_node_structure(node):
            """Verify node has all required fields."""
            assert "id" in node
            assert "label" in node
            assert "level" in node
            assert "line" in node
            assert "column" in node
            assert "children" in node
            assert isinstance(node["children"], list)

            # Check all children recursively
            for child in node["children"]:
                check_node_structure(child)

        root = response["result"]["root"]
        check_node_structure(root)
