"""Error handling and recovery for doctk integration layer.

This module provides error classification, retry logic with exponential backoff,
and comprehensive error logging for the integration layer.
"""

import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorCategory(Enum):
    """Categories of errors for classification and handling."""

    NETWORK = "network"  # Network-related errors (connection, timeout)
    VALIDATION = "validation"  # Input validation errors
    SYSTEM = "system"  # System-level errors (file I/O, permissions)
    PARSING = "parsing"  # Document parsing errors
    OPERATION = "operation"  # Document operation errors
    UNKNOWN = "unknown"  # Unclassified errors


class RetryConfig:
    """Configuration for retry logic."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 30.0)
            exponential_base: Base for exponential backoff (default: 2.0)
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt using exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


class ErrorHandler:
    """Handles error classification, retry logic, and error logging."""

    def __init__(self, retry_config: RetryConfig | None = None):
        """Initialize error handler.

        Args:
            retry_config: Retry configuration (defaults to RetryConfig())
        """
        self.retry_config = retry_config or RetryConfig()
        self.error_count = 0
        self.recovery_count = 0

    def classify_error(self, error: Exception) -> ErrorCategory:
        """Classify an error into a category.

        Args:
            error: The exception to classify

        Returns:
            ErrorCategory enum value
        """
        error_type = type(error).__name__
        error_type_lower = error_type.lower()
        error_msg = str(error).lower()

        # Parsing errors (check first to avoid false matches with "type" in SyntaxError)
        if any(keyword in error_type_lower for keyword in ["parse", "syntax", "token", "lexer"]):
            return ErrorCategory.PARSING

        if any(keyword in error_msg for keyword in ["syntax error", "parse error", "unexpected"]):
            return ErrorCategory.PARSING

        # Validation errors (check early to avoid "io" in "validation" matching SYSTEM)
        # Consolidated type-based and message-based checks
        is_validation_error_type = (
            "validation" in error_type_lower
            or "valueerror" in error_type_lower
            or "typeerror" in error_type_lower
        )
        is_validation_error_msg = any(
            keyword in error_msg for keyword in ["invalid", "required", "missing", "expected"]
        )
        if is_validation_error_type or is_validation_error_msg:
            return ErrorCategory.VALIDATION

        # Network errors
        # Consolidated type-based and message-based checks
        is_network_error_type = any(
            keyword in error_type_lower
            for keyword in ["connection", "timeout", "network", "socket"]
        )
        is_network_error_msg = any(
            keyword in error_msg for keyword in ["connection", "timeout", "network"]
        )
        if is_network_error_type or is_network_error_msg:
            return ErrorCategory.NETWORK

        # System errors
        if any(
            keyword in error_type_lower
            for keyword in ["ioerror", "oserror", "permission", "file", "path"]
        ):
            return ErrorCategory.SYSTEM

        if any(
            keyword in error_msg
            for keyword in ["file not found", "permission denied", "access denied"]
        ):
            return ErrorCategory.SYSTEM

        # Operation errors (only check message, not type - RuntimeError is too generic)
        if any(keyword in error_msg for keyword in ["operation failed", "execution failed"]):
            return ErrorCategory.OPERATION

        return ErrorCategory.UNKNOWN

    def is_retryable(self, category: ErrorCategory) -> bool:
        """Determine if an error category is retryable.

        Args:
            category: Error category

        Returns:
            True if errors in this category should be retried
        """
        # Only network and system errors are retryable
        return category in (ErrorCategory.NETWORK, ErrorCategory.SYSTEM)

    def execute_with_retry(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
        retryable_categories: set[ErrorCategory] | None = None,
    ) -> T:
        """Execute a function with retry logic.

        Args:
            func: Function to execute
            operation_name: Name of operation for logging
            retryable_categories: Set of error categories to retry (defaults to network/system)

        Returns:
            Result of function execution

        Raises:
            Last exception if all retries fail
            RuntimeError: If max_attempts is not a positive number
        """
        if retryable_categories is None:
            retryable_categories = {ErrorCategory.NETWORK, ErrorCategory.SYSTEM}

        # Validate retry configuration
        if self.retry_config.max_attempts <= 0:
            msg = f"Operation '{operation_name}' failed: max_attempts must be a positive number"
            raise RuntimeError(msg)

        last_exception: Exception | None = None
        last_category: ErrorCategory | None = None

        for attempt in range(self.retry_config.max_attempts):
            try:
                result = func()
                if attempt > 0:
                    # Recovered after retry
                    self.recovery_count += 1
                    logger.info(
                        "Operation '%s' succeeded after %d retries",
                        operation_name,
                        attempt,
                    )
                return result

            except Exception as e:
                last_exception = e
                last_category = self.classify_error(e)
                self.error_count += 1

                # Log the error with full context
                logger.warning(
                    "Operation '%s' failed (attempt %d/%d): %s [%s]",
                    operation_name,
                    attempt + 1,
                    self.retry_config.max_attempts,
                    e,
                    last_category.value,
                    exc_info=True,
                )

                # Check if error is retryable
                if last_category not in retryable_categories:
                    logger.error(
                        "Operation '%s' failed with non-retryable error: %s [%s]",
                        operation_name,
                        e,
                        last_category.value,
                    )
                    raise

                # Check if we have more attempts
                if attempt + 1 >= self.retry_config.max_attempts:
                    logger.error(
                        "Operation '%s' failed after %d attempts: %s [%s]",
                        operation_name,
                        self.retry_config.max_attempts,
                        e,
                        last_category.value,
                    )
                    raise

                # Calculate delay and sleep
                delay = self.retry_config.get_delay(attempt)
                logger.info(
                    "Retrying operation '%s' in %.2f seconds (attempt %d/%d)",
                    operation_name,
                    delay,
                    attempt + 2,
                    self.retry_config.max_attempts,
                )
                time.sleep(delay)

        # If we've exhausted all retries, raise the last exception
        # (max_attempts > 0 is guaranteed by validation above, so last_exception is always set)
        if last_exception:
            raise last_exception

        # This should be unreachable due to validation, but keep for type safety
        msg = f"Operation '{operation_name}' failed unexpectedly"
        raise RuntimeError(msg)

    def log_error(
        self,
        error: Exception,
        operation_name: str = "operation",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log an error with comprehensive diagnostic information.

        Args:
            error: The exception to log
            operation_name: Name of operation that failed
            context: Additional context information
        """
        category = self.classify_error(error)

        log_message = f"Error in '{operation_name}': {error} [{category.value}]"

        # Add context if provided
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            log_message += f" (context: {context_str})"

        # Log with stack trace
        logger.error(log_message, exc_info=True)

    def get_stats(self) -> dict[str, int]:
        """Get error handling statistics.

        Returns:
            Dictionary with error_count and recovery_count
        """
        return {
            "error_count": self.error_count,
            "recovery_count": self.recovery_count,
        }

    def reset_stats(self) -> None:
        """Reset error handling statistics."""
        self.error_count = 0
        self.recovery_count = 0
