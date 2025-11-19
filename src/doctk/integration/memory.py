"""Memory management for doctk LSP operations.

This module provides memory management capabilities including LRU caching
for document states, memory monitoring, and eviction strategies to ensure
the system stays within memory limits.
"""

import sys
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from doctk.core import Document, Node

T = TypeVar("T")


@dataclass
class DocumentState:
    """State information for a cached document."""

    uri: str
    document: Document[Node]
    metadata: dict[str, Any]
    access_count: int = 0


class LRUCache(Generic[T]):
    """
    Least Recently Used (LRU) cache implementation.

    Maintains a fixed-size cache that evicts the least recently used items
    when the cache reaches capacity.
    """

    def __init__(self, maxsize: int = 100):
        """
        Initialize LRU cache.

        Args:
            maxsize: Maximum number of items to cache (default: 100)
        """
        self.maxsize = maxsize
        self.cache: OrderedDict[str, T] = OrderedDict()
        self.size_evictions = 0  # Track size-based evictions

    def get(self, key: str) -> T | None:
        """
        Get an item from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        if key not in self.cache:
            return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: T) -> None:
        """
        Put an item in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing item and mark as recently used
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.maxsize:
            # Evict least recently used item due to size limit
            self.cache.popitem(last=False)
            self.size_evictions += 1

        self.cache[key] = value

    def remove(self, key: str) -> None:
        """
        Remove an item from the cache.

        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()

    def __len__(self) -> int:
        """Get the number of cached items."""
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        """Check if a key is in the cache."""
        return key in self.cache

    def popitem(self, last: bool = True) -> tuple[str, T]:
        """
        Remove and return an item from the cache.

        Args:
            last: If True, remove most recent; if False, remove least recent (default: True)

        Returns:
            Tuple of (key, value)
        """
        return self.cache.popitem(last=last)


class DocumentStateManager:
    """
    Manages document states with LRU caching and memory management.

    This class provides:
    - LRU cache for document states
    - Memory usage monitoring
    - Automatic eviction when memory limits are reached
    - Document lifecycle management
    """

    def __init__(
        self,
        max_cache_size: int = 100,
        max_memory_mb: int = 500,
        enable_memory_monitoring: bool = True,
    ):
        """
        Initialize document state manager.

        Args:
            max_cache_size: Maximum number of documents to cache (default: 100)
            max_memory_mb: Maximum memory usage in MB (default: 500)
            enable_memory_monitoring: Enable memory usage monitoring (default: True)
        """
        self.cache = LRUCache[DocumentState](maxsize=max_cache_size)
        self.max_memory_mb = max_memory_mb
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.enable_memory_monitoring = enable_memory_monitoring
        self._memory_evictions = 0  # Track memory-based evictions

    def get_document(self, uri: str) -> DocumentState | None:
        """
        Get a document from the cache.

        Args:
            uri: Document URI

        Returns:
            DocumentState if found, None otherwise
        """
        state = self.cache.get(uri)
        if state:
            state.access_count += 1
        return state

    def put_document(
        self, uri: str, document: Document[Node], metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Put a document in the cache, then enforce memory limits.

        Args:
            uri: Document URI
            document: Document to cache
            metadata: Optional metadata about the document
        """
        state = DocumentState(uri=uri, document=document, metadata=metadata or {}, access_count=0)
        self.cache.put(uri, state)

        # Enforce memory limit after insertion to ensure we don't exceed threshold
        if self.enable_memory_monitoring:
            self._enforce_memory_limit()

    def remove_document(self, uri: str) -> None:
        """
        Remove a document from the cache.

        Args:
            uri: Document URI
        """
        self.cache.remove(uri)

    def clear(self) -> None:
        """Clear all cached documents."""
        self.cache.clear()

    def get_cache_size(self) -> int:
        """Get the number of cached documents."""
        return len(self.cache)

    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in MB.

        Returns:
            Current process memory usage in megabytes
        """
        try:
            import psutil

            process = psutil.Process()
            return float(process.memory_info().rss / (1024 * 1024))
        except ImportError:
            # psutil not available, estimate based on sys.getsizeof
            return self._estimate_memory_usage()

    def _estimate_memory_usage(self) -> float:
        """
        Estimate memory usage based on cached objects using recursive size calculation.

        Returns:
            Estimated memory usage in MB
        """
        total_bytes = 0
        for key, state in self.cache.cache.items():
            total_bytes += self._get_recursive_size(key)
            total_bytes += self._get_recursive_size(state)
        return total_bytes / (1024 * 1024)

    def _get_recursive_size(self, obj: Any) -> int:
        """
        Recursively calculate the size of an object including nested containers.

        Args:
            obj: Object to measure

        Returns:
            Size in bytes
        """
        seen: set[int] = set()

        def _recurse(item: Any) -> int:
            item_id = id(item)
            if item_id in seen:
                return 0
            seen.add(item_id)

            item_size = sys.getsizeof(item)

            # Handle containers
            if isinstance(item, dict):
                item_size += sum(_recurse(k) + _recurse(v) for k, v in item.items())
            elif isinstance(item, (list, tuple, set)):
                item_size += sum(_recurse(elem) for elem in item)
            elif hasattr(item, "__dict__"):
                item_size += _recurse(item.__dict__)

            return item_size

        return _recurse(obj)

    def _enforce_memory_limit(self) -> None:
        """
        Enforce memory limit by evicting least recently used documents.

        This is called automatically after adding new documents to the cache.
        Uses batch eviction strategy to avoid O(N*M) complexity.
        """
        if not self.enable_memory_monitoring:
            return

        memory_mb = self.get_memory_usage_mb()
        if memory_mb <= self.max_memory_mb:
            return

        # Batch eviction: remove 10% of cache or until under limit
        # This reduces the number of expensive memory checks
        evictions_this_round = 0
        batch_size = max(1, len(self.cache) // 10)

        while memory_mb > self.max_memory_mb and len(self.cache) > 0:
            # Evict a batch of least recently used documents
            for _ in range(min(batch_size, len(self.cache))):
                if len(self.cache) == 0:
                    break
                self.cache.popitem(last=False)
                evictions_this_round += 1

            # Check memory only after batch eviction
            memory_mb = self.get_memory_usage_mb()

        self._memory_evictions += evictions_this_round

    def get_statistics(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics including both size-based
            and memory-based eviction counts
        """
        total_accesses = sum(state.access_count for state in self.cache.cache.values())
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.cache.maxsize,
            "memory_usage_mb": self.get_memory_usage_mb(),
            "max_memory_mb": self.max_memory_mb,
            "size_evictions": self.cache.size_evictions,
            "memory_evictions": self._memory_evictions,
            "total_evictions": self.cache.size_evictions + self._memory_evictions,
            "total_accesses": total_accesses,
        }

    def get_summary(self) -> str:
        """
        Get a human-readable summary of cache statistics.

        Returns:
            Summary string
        """
        stats = self.get_statistics()
        return (
            f"Document Cache Summary:\n"
            f"  Cache size: {stats['cache_size']}/{stats['max_cache_size']}\n"
            f"  Memory usage: {stats['memory_usage_mb']:.2f}/{stats['max_memory_mb']}MB\n"
            f"  Total evictions: {stats['total_evictions']}\n"
            f"  Total accesses: {stats['total_accesses']}"
        )
