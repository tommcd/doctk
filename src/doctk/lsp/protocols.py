"""Protocol definitions for doctk LSP integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Protocol

if TYPE_CHECKING:
    from doctk.core import Document, Node


@dataclass
class ValidationResult:
    """Result of validating an operation."""

    valid: bool
    error: Optional[str] = None


@dataclass
class OperationResult:
    """Result of executing a document operation."""

    success: bool
    document: Optional[str] = None
    modified_ranges: Optional[list[tuple[int, int, int, int]]] = None
    error: Optional[str] = None


class DocumentOperation(Protocol):
    """Protocol for all document operations."""

    def execute(self, doc: "Document", target: "Node") -> "Document":
        """
        Execute the operation on the document.

        Args:
            doc: The document to operate on
            target: The target node for the operation

        Returns:
            The modified document
        """
        ...

    def validate(self, doc: "Document", target: "Node") -> ValidationResult:
        """
        Validate that the operation can be executed.

        Args:
            doc: The document to validate against
            target: The target node for the operation

        Returns:
            ValidationResult indicating whether the operation is valid
        """
        ...


class DocumentInterface(ABC):
    """Abstract interface for document manipulation UIs."""

    @abstractmethod
    def display_tree(self, tree: Any) -> None:
        """
        Display document structure as a tree.

        Args:
            tree: The document tree to display
        """
        pass

    @abstractmethod
    def get_user_selection(self) -> Optional[Any]:
        """
        Get currently selected node(s).

        Returns:
            The selected node or None if no selection
        """
        pass

    @abstractmethod
    def apply_operation(self, operation: Any) -> OperationResult:
        """
        Apply an operation and update the display.

        Args:
            operation: The operation to apply

        Returns:
            Result of the operation
        """
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        """
        Display error message to user.

        Args:
            message: The error message to display
        """
        pass


@dataclass
class ParameterInfo:
    """Information about an operation parameter."""

    name: str
    type: str
    required: bool
    description: str
    default: Optional[Any] = None


@dataclass
class OperationMetadata:
    """Metadata about a doctk operation."""

    name: str
    description: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_type: str = "Document"
    examples: list[str] = field(default_factory=list)
    category: str = "general"
