"""Tests for LSP configuration management."""

from __future__ import annotations

import pytest

from doctk.lsp.config import LSPConfiguration, TraceLevel


class TestTraceLevel:
    """Tests for TraceLevel enum."""

    def test_trace_level_values(self) -> None:
        """Test that TraceLevel has expected values."""
        assert TraceLevel.OFF.value == "off"
        assert TraceLevel.MESSAGES.value == "messages"
        assert TraceLevel.VERBOSE.value == "verbose"

    def test_trace_level_from_string(self) -> None:
        """Test creating TraceLevel from string."""
        assert TraceLevel("off") == TraceLevel.OFF
        assert TraceLevel("messages") == TraceLevel.MESSAGES
        assert TraceLevel("verbose") == TraceLevel.VERBOSE

    def test_trace_level_invalid(self) -> None:
        """Test that invalid trace level raises ValueError."""
        with pytest.raises(ValueError):
            TraceLevel("invalid")


class TestLSPConfiguration:
    """Tests for LSPConfiguration class."""

    def test_default_configuration(self) -> None:
        """Test that default configuration has expected values."""
        config = LSPConfiguration()

        assert config.trace == TraceLevel.OFF
        assert config.max_completion_items == 50
        assert config.enabled is True
        assert config.python_command == "python3"
        assert not config.has_warnings()

    def test_from_dict_valid_config(self) -> None:
        """Test creating configuration from valid dictionary."""
        config_dict = {
            "trace": "verbose",
            "maxCompletionItems": 100,
            "enabled": True,
            "pythonCommand": "python",
        }

        config = LSPConfiguration.from_dict(config_dict)

        assert config.trace == TraceLevel.VERBOSE
        assert config.max_completion_items == 100
        assert config.enabled is True
        assert config.python_command == "python"
        assert not config.has_warnings()

    def test_from_dict_partial_config(self) -> None:
        """Test creating configuration with partial dictionary."""
        config_dict = {
            "trace": "messages",
        }

        config = LSPConfiguration.from_dict(config_dict)

        # Specified setting
        assert config.trace == TraceLevel.MESSAGES

        # Default settings
        assert config.max_completion_items == 50
        assert config.enabled is True
        assert config.python_command == "python3"
        assert not config.has_warnings()

    def test_from_dict_invalid_trace_level(self) -> None:
        """Test that invalid trace level uses default and generates warning."""
        config_dict = {
            "trace": "invalid",
        }

        config = LSPConfiguration.from_dict(config_dict)

        # Should use default value
        assert config.trace == TraceLevel.OFF

        # Should have warning
        assert config.has_warnings()
        warnings = config.get_warnings()
        assert len(warnings) == 1
        assert "invalid trace level" in warnings[0].lower()
        assert "invalid" in warnings[0]

    def test_from_dict_invalid_max_completion_items(self) -> None:
        """Test that invalid max_completion_items uses default and generates warning."""
        test_cases = [
            {"maxCompletionItems": -1},  # Negative
            {"maxCompletionItems": 0},  # Zero
            {"maxCompletionItems": "invalid"},  # Wrong type
        ]

        for config_dict in test_cases:
            config = LSPConfiguration.from_dict(config_dict)

            # Should use default value
            assert config.max_completion_items == 50

            # Should have warning
            assert config.has_warnings()
            warnings = config.get_warnings()
            assert len(warnings) == 1
            assert "maxcompletionitems" in warnings[0].lower()

    def test_from_dict_invalid_enabled(self) -> None:
        """Test that invalid enabled value uses default and generates warning."""
        config_dict = {
            "enabled": "yes",  # Wrong type
        }

        config = LSPConfiguration.from_dict(config_dict)

        # Should use default value
        assert config.enabled is True

        # Should have warning
        assert config.has_warnings()
        warnings = config.get_warnings()
        assert len(warnings) == 1
        assert "enabled" in warnings[0].lower()

    def test_from_dict_multiple_invalid_settings(self) -> None:
        """Test that multiple invalid settings generate multiple warnings."""
        config_dict = {
            "trace": "bad_trace",
            "maxCompletionItems": -5,
            "enabled": "not_a_bool",
        }

        config = LSPConfiguration.from_dict(config_dict)

        # Should use all default values
        assert config.trace == TraceLevel.OFF
        assert config.max_completion_items == 50
        assert config.enabled is True

        # Should have 3 warnings
        assert config.has_warnings()
        warnings = config.get_warnings()
        assert len(warnings) == 3

    def test_update_from_dict(self) -> None:
        """Test updating configuration from dictionary."""
        config = LSPConfiguration()

        # Initial values
        assert config.trace == TraceLevel.OFF
        assert config.max_completion_items == 50

        # Update
        warnings = config.update_from_dict(
            {
                "trace": "verbose",
                "maxCompletionItems": 200,
            }
        )

        # Should be updated
        assert config.trace == TraceLevel.VERBOSE
        assert config.max_completion_items == 200
        assert len(warnings) == 0

    def test_update_from_dict_with_warnings(self) -> None:
        """Test updating configuration with invalid values generates warnings."""
        config = LSPConfiguration()

        # Set initial values
        config.trace = TraceLevel.MESSAGES
        config.max_completion_items = 75

        # Update with invalid values
        warnings = config.update_from_dict(
            {
                "trace": "bad",
                "maxCompletionItems": -1,
            }
        )

        # Should keep current values (not defaults)
        assert config.trace == TraceLevel.MESSAGES
        assert config.max_completion_items == 75

        # Should have warnings
        assert len(warnings) == 2
        assert config.has_warnings()

    def test_update_clears_previous_warnings(self) -> None:
        """Test that update clears previous warnings."""
        config = LSPConfiguration()

        # First update with invalid value
        warnings1 = config.update_from_dict({"trace": "invalid"})
        assert len(warnings1) == 1
        assert config.has_warnings()

        # Second update with valid value
        warnings2 = config.update_from_dict({"trace": "verbose"})
        assert len(warnings2) == 0
        assert not config.has_warnings()

    def test_to_dict(self) -> None:
        """Test converting configuration to dictionary."""
        config = LSPConfiguration(
            trace=TraceLevel.VERBOSE,
            max_completion_items=100,
            enabled=False,
            python_command="python",
        )

        result = config.to_dict()

        assert result == {
            "trace": "verbose",
            "maxCompletionItems": 100,
            "enabled": False,
            "pythonCommand": "python",
        }

    def test_get_warnings_returns_copy(self) -> None:
        """Test that get_warnings returns a copy, not the internal list."""
        config = LSPConfiguration.from_dict({"trace": "invalid"})

        warnings1 = config.get_warnings()
        warnings2 = config.get_warnings()

        # Should be equal but not the same object
        assert warnings1 == warnings2
        assert warnings1 is not warnings2

    def test_python_command_not_validated(self) -> None:
        """Test that python_command is accepted without validation."""
        config = LSPConfiguration.from_dict({"pythonCommand": "/usr/bin/python3.12"})

        assert config.python_command == "/usr/bin/python3.12"
        assert not config.has_warnings()


class TestConfigurationIntegration:
    """Integration tests for configuration management."""

    def test_configuration_roundtrip(self) -> None:
        """Test that configuration can be serialized and deserialized."""
        original = LSPConfiguration(
            trace=TraceLevel.MESSAGES,
            max_completion_items=75,
            enabled=True,
            python_command="python3.11",
        )

        # Convert to dict and back
        config_dict = original.to_dict()
        restored = LSPConfiguration.from_dict(config_dict)

        assert restored.trace == original.trace
        assert restored.max_completion_items == original.max_completion_items
        assert restored.enabled == original.enabled
        assert restored.python_command == original.python_command

    def test_configuration_partial_update(self) -> None:
        """Test updating only some configuration values."""
        config = LSPConfiguration()

        # Update only trace level
        config.update_from_dict({"trace": "messages"})
        assert config.trace == TraceLevel.MESSAGES
        assert config.max_completion_items == 50  # Unchanged

        # Update only max_completion_items
        config.update_from_dict({"maxCompletionItems": 25})
        assert config.trace == TraceLevel.MESSAGES  # Unchanged
        assert config.max_completion_items == 25

    def test_configuration_validation_messages(self) -> None:
        """Test that validation messages are informative."""
        config = LSPConfiguration.from_dict(
            {
                "trace": "wrong",
                "maxCompletionItems": "not_a_number",
            }
        )

        warnings = config.get_warnings()

        # Check trace warning
        trace_warning = next(w for w in warnings if "trace" in w.lower())
        assert "wrong" in trace_warning
        assert "off" in trace_warning or "messages" in trace_warning or "verbose" in trace_warning

        # Check max_completion_items warning
        max_items_warning = next(w for w in warnings if "maxcompletionitems" in w.lower())
        assert "not_a_number" in max_items_warning
        assert "positive integer" in max_items_warning.lower()
