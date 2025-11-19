"""Tests for error handling and recovery."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from doctk.integration.errors import ErrorCategory, ErrorHandler, RetryConfig


class NetworkError(Exception):
    """Simulated network error."""


class ValidationError(Exception):
    """Simulated validation error."""


class TestErrorClassification:
    """Tests for error classification."""

    def test_classify_network_error_by_type(self):
        """Test that network errors are classified correctly by exception type."""
        handler = ErrorHandler()
        error = NetworkError("Connection refused")
        category = handler.classify_error(error)
        assert category == ErrorCategory.NETWORK

    def test_classify_network_error_by_message(self):
        """Test that network errors are classified correctly by message."""
        handler = ErrorHandler()
        error = RuntimeError("Network timeout occurred")
        category = handler.classify_error(error)
        assert category == ErrorCategory.NETWORK

    def test_classify_validation_error_by_type(self):
        """Test that validation errors are classified correctly by exception type."""
        handler = ErrorHandler()
        error = ValidationError("Invalid input")
        category = handler.classify_error(error)
        assert category == ErrorCategory.VALIDATION

    def test_classify_validation_error_by_message(self):
        """Test that validation errors are classified correctly by message."""
        handler = ErrorHandler()
        error = RuntimeError("Invalid value provided")
        category = handler.classify_error(error)
        assert category == ErrorCategory.VALIDATION

    def test_classify_system_error_by_type(self):
        """Test that system errors are classified correctly."""
        handler = ErrorHandler()
        error = OSError("Permission denied")
        category = handler.classify_error(error)
        assert category == ErrorCategory.SYSTEM

    def test_classify_system_error_by_message(self):
        """Test that system errors are classified correctly by message."""
        handler = ErrorHandler()
        error = RuntimeError("File not found")
        category = handler.classify_error(error)
        assert category == ErrorCategory.SYSTEM

    def test_classify_parsing_error_by_type(self):
        """Test that parsing errors are classified correctly by type."""
        handler = ErrorHandler()
        error = SyntaxError("Invalid syntax")
        category = handler.classify_error(error)
        assert category == ErrorCategory.PARSING

    def test_classify_parsing_error_by_message(self):
        """Test that parsing errors are classified correctly by message."""
        handler = ErrorHandler()
        error = RuntimeError("Parse error at line 5")
        category = handler.classify_error(error)
        assert category == ErrorCategory.PARSING

    def test_classify_unknown_error(self):
        """Test that unknown errors are classified as UNKNOWN."""
        handler = ErrorHandler()
        error = RuntimeError("Some random error")
        category = handler.classify_error(error)
        assert category == ErrorCategory.UNKNOWN


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    def test_retry_config_default_values(self):
        """Test that RetryConfig has correct default values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0

    def test_retry_config_custom_values(self):
        """Test that RetryConfig accepts custom values."""
        config = RetryConfig(
            max_attempts=5, initial_delay=0.5, max_delay=60.0, exponential_base=3.0
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 60.0
        assert config.exponential_base == 3.0

    def test_retry_config_exponential_backoff(self):
        """Test that exponential backoff calculations are correct."""
        config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=30.0)

        assert config.get_delay(0) == 1.0  # 1.0 * 2^0 = 1.0
        assert config.get_delay(1) == 2.0  # 1.0 * 2^1 = 2.0
        assert config.get_delay(2) == 4.0  # 1.0 * 2^2 = 4.0
        assert config.get_delay(3) == 8.0  # 1.0 * 2^3 = 8.0
        assert config.get_delay(4) == 16.0  # 1.0 * 2^4 = 16.0
        assert config.get_delay(5) == 30.0  # 1.0 * 2^5 = 32.0, but capped at max_delay

    def test_execute_with_retry_invalid_max_attempts(self):
        """Test that invalid max_attempts raises RuntimeError."""
        handler = ErrorHandler(RetryConfig(max_attempts=0))
        func = MagicMock(return_value=42)

        with pytest.raises(RuntimeError, match="max_attempts must be a positive number"):
            handler.execute_with_retry(func, "test_operation")

        # Function should not be called if max_attempts is invalid
        assert func.call_count == 0

    def test_execute_with_retry_succeeds_first_attempt(self):
        """Test that successful operations don't retry."""
        handler = ErrorHandler()
        func = MagicMock(return_value=42)

        result = handler.execute_with_retry(func, "test_operation")

        assert result == 42
        assert func.call_count == 1

    def test_execute_with_retry_succeeds_after_retries(self):
        """Test that operations succeed after retries."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))
        func = MagicMock(side_effect=[NetworkError("Connection failed"), NetworkError("Still failing"), 42])

        result = handler.execute_with_retry(func, "test_operation")

        assert result == 42
        assert func.call_count == 3
        assert handler.recovery_count == 1

    def test_execute_with_retry_fails_all_attempts(self):
        """Test that operations fail after exhausting retries."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))
        func = MagicMock(side_effect=NetworkError("Persistent failure"))

        with pytest.raises(NetworkError, match="Persistent failure"):
            handler.execute_with_retry(func, "test_operation")

        assert func.call_count == 3

    def test_execute_with_retry_non_retryable_error(self):
        """Test that non-retryable errors fail immediately."""
        handler = ErrorHandler()
        func = MagicMock(side_effect=ValidationError("Invalid input"))

        with pytest.raises(ValidationError, match="Invalid input"):
            handler.execute_with_retry(func, "test_operation")

        # Should only attempt once, not retry
        assert func.call_count == 1

    def test_execute_with_retry_custom_retryable_categories(self):
        """Test that custom retryable categories work."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))
        func = MagicMock(side_effect=[ValidationError("Invalid"), ValidationError("Still invalid"), 42])

        # Make validation errors retryable
        result = handler.execute_with_retry(
            func, "test_operation", retryable_categories={ErrorCategory.VALIDATION}
        )

        assert result == 42
        assert func.call_count == 3

    @patch("time.sleep")
    def test_execute_with_retry_exponential_backoff(self, mock_sleep):
        """Test that retry delays follow exponential backoff."""
        handler = ErrorHandler(RetryConfig(max_attempts=4, initial_delay=1.0))
        func = MagicMock(side_effect=[NetworkError("Fail 1"), NetworkError("Fail 2"), NetworkError("Fail 3"), 42])

        handler.execute_with_retry(func, "test_operation")

        # Verify sleep was called with increasing delays
        assert mock_sleep.call_count == 3
        calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert calls[0] == 1.0  # First retry: 1.0 * 2^0
        assert calls[1] == 2.0  # Second retry: 1.0 * 2^1
        assert calls[2] == 4.0  # Third retry: 1.0 * 2^2

    def test_is_retryable_network_errors(self):
        """Test that network errors are marked as retryable."""
        handler = ErrorHandler()
        assert handler.is_retryable(ErrorCategory.NETWORK) is True

    def test_is_retryable_system_errors(self):
        """Test that system errors are marked as retryable."""
        handler = ErrorHandler()
        assert handler.is_retryable(ErrorCategory.SYSTEM) is True

    def test_is_retryable_validation_errors(self):
        """Test that validation errors are not retryable."""
        handler = ErrorHandler()
        assert handler.is_retryable(ErrorCategory.VALIDATION) is False

    def test_is_retryable_parsing_errors(self):
        """Test that parsing errors are not retryable."""
        handler = ErrorHandler()
        assert handler.is_retryable(ErrorCategory.PARSING) is False


class TestErrorLogging:
    """Tests for comprehensive error logging."""

    def test_log_error_basic(self, caplog):
        """Test basic error logging."""
        handler = ErrorHandler()
        error = RuntimeError("Test error")

        with caplog.at_level(logging.ERROR):
            handler.log_error(error, "test_operation")

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert "test_operation" in record.message
        assert "Test error" in record.message
        assert "unknown" in record.message  # Error category

    def test_log_error_with_context(self, caplog):
        """Test error logging with additional context."""
        handler = ErrorHandler()
        error = RuntimeError("Test error")
        context = {"file": "test.md", "line": 42}

        with caplog.at_level(logging.ERROR):
            handler.log_error(error, "test_operation", context)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert "file=test.md" in record.message
        assert "line=42" in record.message

    def test_log_error_includes_stack_trace(self, caplog):
        """Test that error logging includes stack traces."""
        handler = ErrorHandler()
        error = RuntimeError("Test error")

        with caplog.at_level(logging.ERROR):
            handler.log_error(error, "test_operation")

        # Check that exc_info was logged (stack trace)
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.exc_info is not None

    def test_execute_with_retry_logs_warnings(self, caplog):
        """Test that retry attempts log warnings."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))
        func = MagicMock(side_effect=[NetworkError("Connection failed"), 42])

        with caplog.at_level(logging.WARNING):
            handler.execute_with_retry(func, "test_operation")

        # Should have one warning for the failed attempt
        warnings = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warnings) == 1
        assert "Connection failed" in warnings[0].message
        assert "network" in warnings[0].message

    def test_execute_with_retry_logs_recovery(self, caplog):
        """Test that successful recovery is logged."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))
        func = MagicMock(side_effect=[NetworkError("Connection failed"), 42])

        with caplog.at_level(logging.INFO):
            handler.execute_with_retry(func, "test_operation")

        # Should have info log about recovery
        info_logs = [r for r in caplog.records if r.levelname == "INFO"]
        recovery_logs = [r for r in info_logs if "succeeded after" in r.message]
        assert len(recovery_logs) == 1
        assert "1 retries" in recovery_logs[0].message


class TestStatistics:
    """Tests for error handling statistics."""

    def test_stats_initial_values(self):
        """Test that statistics start at zero."""
        handler = ErrorHandler()
        stats = handler.get_stats()

        assert stats["error_count"] == 0
        assert stats["recovery_count"] == 0

    def test_stats_count_errors(self):
        """Test that errors are counted."""
        handler = ErrorHandler(RetryConfig(max_attempts=1))
        func = MagicMock(side_effect=ValidationError("Invalid"))

        try:
            handler.execute_with_retry(func, "test_operation")
        except ValidationError:
            # Exception is expected; suppress to verify error statistics are tracked
            pass

        stats = handler.get_stats()
        assert stats["error_count"] == 1
        assert stats["recovery_count"] == 0

    def test_stats_count_recoveries(self):
        """Test that recoveries are counted."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))
        func = MagicMock(side_effect=[NetworkError("Connection failed"), 42])

        handler.execute_with_retry(func, "test_operation")

        stats = handler.get_stats()
        assert stats["error_count"] == 1  # One error occurred
        assert stats["recovery_count"] == 1  # And we recovered from it

    def test_stats_multiple_operations(self):
        """Test that statistics accumulate across operations."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))

        # First operation: fail then succeed
        func1 = MagicMock(side_effect=[NetworkError("Fail"), 42])
        handler.execute_with_retry(func1, "operation1")

        # Second operation: immediate success
        func2 = MagicMock(return_value=100)
        handler.execute_with_retry(func2, "operation2")

        # Third operation: fail then succeed
        func3 = MagicMock(side_effect=[NetworkError("Fail"), 99])
        handler.execute_with_retry(func3, "operation3")

        stats = handler.get_stats()
        assert stats["error_count"] == 2
        assert stats["recovery_count"] == 2

    def test_reset_stats(self):
        """Test that statistics can be reset."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, initial_delay=0.01))
        func = MagicMock(side_effect=[NetworkError("Fail"), 42])

        handler.execute_with_retry(func, "test_operation")

        # Verify stats are non-zero
        stats = handler.get_stats()
        assert stats["error_count"] > 0
        assert stats["recovery_count"] > 0

        # Reset and verify
        handler.reset_stats()
        stats = handler.get_stats()
        assert stats["error_count"] == 0
        assert stats["recovery_count"] == 0
