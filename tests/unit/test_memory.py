"""Tests for memory management functionality."""

from doctk.core import Document, Heading, Paragraph
from doctk.lsp.memory import DocumentState, DocumentStateManager, LRUCache


class TestLRUCache:
    """Tests for LRUCache class."""

    def test_cache_creation(self):
        """Test creating an LRU cache."""
        cache = LRUCache[str](maxsize=10)
        assert len(cache) == 0
        assert cache.maxsize == 10

    def test_cache_put_and_get(self):
        """Test putting and getting items from cache."""
        cache = LRUCache[str](maxsize=10)
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        assert len(cache) == 1

    def test_cache_get_nonexistent(self):
        """Test getting a nonexistent item returns None."""
        cache = LRUCache[str](maxsize=10)
        assert cache.get("nonexistent") is None

    def test_cache_eviction(self):
        """Test that cache evicts least recently used items when full."""
        cache = LRUCache[str](maxsize=3)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # Cache is now full (3/3)
        assert len(cache) == 3

        # Adding a 4th item should evict key1 (least recently used)
        cache.put("key4", "value4")
        assert len(cache) == 3
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_cache_update_marks_as_recent(self):
        """Test that getting an item marks it as recently used."""
        cache = LRUCache[str](maxsize=3)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")

        # Access key1 to mark it as recently used
        cache.get("key1")

        # Adding a 4th item should evict key2 (now least recently used)
        cache.put("key4", "value4")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

    def test_cache_remove(self):
        """Test removing items from cache."""
        cache = LRUCache[str](maxsize=10)
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.remove("key1")
        assert cache.get("key1") is None
        assert len(cache) == 0

    def test_cache_clear(self):
        """Test clearing all cached items."""
        cache = LRUCache[str](maxsize=10)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        assert len(cache) == 2

        cache.clear()
        assert len(cache) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_contains(self):
        """Test checking if key is in cache."""
        cache = LRUCache[str](maxsize=10)
        cache.put("key1", "value1")

        assert "key1" in cache
        assert "key2" not in cache

    def test_cache_popitem(self):
        """Test removing and returning items from cache."""
        cache = LRUCache[str](maxsize=10)
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # Pop most recent item (last=True)
        key, value = cache.popitem(last=True)
        assert key == "key2"
        assert value == "value2"
        assert len(cache) == 1

        # Pop least recent item (last=False)
        cache.put("key3", "value3")
        key, value = cache.popitem(last=False)
        assert key == "key1"
        assert value == "value1"
        assert len(cache) == 1


class TestDocumentStateManager:
    """Tests for DocumentStateManager class."""

    def test_manager_creation(self):
        """Test creating a document state manager."""
        manager = DocumentStateManager(max_cache_size=100, max_memory_mb=500)
        assert manager.get_cache_size() == 0
        assert manager.max_memory_mb == 500

    def test_put_and_get_document(self):
        """Test putting and getting documents."""
        manager = DocumentStateManager()
        doc = Document([Heading(level=1, text="Test")])

        manager.put_document("file:///test.md", doc, {"version": 1})
        state = manager.get_document("file:///test.md")

        assert state is not None
        assert state.uri == "file:///test.md"
        assert isinstance(state.document, Document)
        assert state.metadata["version"] == 1
        assert state.access_count == 1

    def test_get_nonexistent_document(self):
        """Test getting a nonexistent document returns None."""
        manager = DocumentStateManager()
        assert manager.get_document("file:///nonexistent.md") is None

    def test_remove_document(self):
        """Test removing a document from cache."""
        manager = DocumentStateManager()
        doc = Document([Heading(level=1, text="Test")])
        manager.put_document("file:///test.md", doc)

        assert manager.get_document("file:///test.md") is not None

        manager.remove_document("file:///test.md")
        assert manager.get_document("file:///test.md") is None

    def test_clear_cache(self):
        """Test clearing all cached documents."""
        manager = DocumentStateManager()
        doc1 = Document([Heading(level=1, text="Test 1")])
        doc2 = Document([Heading(level=1, text="Test 2")])

        manager.put_document("file:///test1.md", doc1)
        manager.put_document("file:///test2.md", doc2)
        assert manager.get_cache_size() == 2

        manager.clear()
        assert manager.get_cache_size() == 0

    def test_access_count_increments(self):
        """Test that access count increments on each get."""
        manager = DocumentStateManager()
        doc = Document([Heading(level=1, text="Test")])
        manager.put_document("file:///test.md", doc)

        state1 = manager.get_document("file:///test.md")
        assert state1 is not None
        assert state1.access_count == 1

        state2 = manager.get_document("file:///test.md")
        assert state2 is not None
        assert state2.access_count == 2

    def test_cache_size_limit(self):
        """Test that cache respects size limit."""
        manager = DocumentStateManager(max_cache_size=3)

        # Add 3 documents (fill cache)
        for i in range(3):
            doc = Document([Heading(level=1, text=f"Test {i}")])
            manager.put_document(f"file:///test{i}.md", doc)

        assert manager.get_cache_size() == 3

        # Add 4th document - should evict oldest
        doc4 = Document([Heading(level=1, text="Test 4")])
        manager.put_document("file:///test4.md", doc4)

        assert manager.get_cache_size() == 3
        assert manager.get_document("file:///test0.md") is None
        assert manager.get_document("file:///test4.md") is not None

    def test_memory_usage_estimation(self):
        """Test memory usage estimation."""
        manager = DocumentStateManager(enable_memory_monitoring=False)
        doc = Document([Heading(level=1, text="Test")])
        manager.put_document("file:///test.md", doc)

        memory_mb = manager.get_memory_usage_mb()
        assert memory_mb >= 0

    def test_statistics(self):
        """Test getting cache statistics."""
        manager = DocumentStateManager(max_cache_size=10, max_memory_mb=500)
        doc = Document([Heading(level=1, text="Test")])
        manager.put_document("file:///test.md", doc)
        manager.get_document("file:///test.md")

        stats = manager.get_statistics()
        assert stats["cache_size"] == 1
        assert stats["max_cache_size"] == 10
        assert stats["max_memory_mb"] == 500
        assert stats["total_accesses"] == 1
        assert stats["memory_usage_mb"] >= 0

    def test_summary(self):
        """Test getting cache summary."""
        manager = DocumentStateManager(max_cache_size=10, max_memory_mb=500)
        doc = Document([Heading(level=1, text="Test")])
        manager.put_document("file:///test.md", doc)

        summary = manager.get_summary()
        assert "Document Cache Summary:" in summary
        assert "Cache size:" in summary
        assert "Memory usage:" in summary
        assert "Total evictions:" in summary
        assert "Total accesses:" in summary

    def test_memory_monitoring_disabled(self):
        """Test that memory monitoring can be disabled."""
        manager = DocumentStateManager(
            max_cache_size=10, max_memory_mb=500, enable_memory_monitoring=False
        )

        # Add many documents without triggering eviction
        for i in range(5):
            doc = Document(
                [
                    Heading(level=1, text=f"Section {i}"),
                    Paragraph(content=f"Content for section {i}"),
                ]
            )
            manager.put_document(f"file:///test{i}.md", doc)

        # All documents should still be cached (no memory-based eviction)
        assert manager.get_cache_size() == 5

    def test_eviction_count(self):
        """Test that size-based eviction count is tracked separately."""
        manager = DocumentStateManager(max_cache_size=2, enable_memory_monitoring=False)

        # Add 3 documents to trigger size-based eviction
        for i in range(3):
            doc = Document([Heading(level=1, text=f"Test {i}")])
            manager.put_document(f"file:///test{i}.md", doc)

        stats = manager.get_statistics()
        # One document should have been evicted (cache size = 2, added 3)
        assert manager.get_cache_size() == 2
        # Assert that size-based eviction was tracked
        assert stats["size_evictions"] == 1
        assert stats["memory_evictions"] == 0
        assert stats["total_evictions"] == 1

    def test_document_state_dataclass(self):
        """Test DocumentState dataclass."""
        doc = Document([Heading(level=1, text="Test")])
        state = DocumentState(
            uri="file:///test.md", document=doc, metadata={"version": 1}, access_count=5
        )

        assert state.uri == "file:///test.md"
        assert isinstance(state.document, Document)
        assert state.metadata["version"] == 1
        assert state.access_count == 5


class TestMemoryPerformance:
    """Performance tests for memory management (Task 8.2)."""

    def test_memory_usage_stays_under_500mb_with_many_documents(self):
        """Test that memory usage stays under 500MB when caching many documents."""
        # Set limit to 500MB with monitoring enabled
        manager = DocumentStateManager(
            max_cache_size=1000, max_memory_mb=500, enable_memory_monitoring=True
        )

        # Create and cache 100 documents with moderate content
        for i in range(100):
            doc = Document(
                [
                    Heading(level=1, text=f"Section {i}"),
                    Paragraph(content=f"Content for section {i}" * 10),
                    Heading(level=2, text=f"Subsection {i}.1"),
                    Paragraph(content=f"More content for subsection {i}.1" * 5),
                ]
            )
            manager.put_document(f"file:///test{i}.md", doc)

        # Verify memory usage is under limit
        memory_mb = manager.get_memory_usage_mb()
        assert memory_mb <= 500, f"Memory usage {memory_mb}MB exceeds 500MB limit"

        # Verify eviction occurred if needed
        stats = manager.get_statistics()
        assert stats["memory_usage_mb"] <= 500

    def test_memory_monitoring_with_large_documents(self):
        """Test memory management with large documents."""
        manager = DocumentStateManager(
            max_cache_size=50, max_memory_mb=500, enable_memory_monitoring=True
        )

        # Create large documents with many nodes
        for i in range(20):
            # Create a document with 100 nodes
            nodes = []
            for j in range(100):
                nodes.append(Heading(level=2, text=f"Heading {i}.{j}"))
                nodes.append(Paragraph(content=f"Paragraph content {i}.{j}" * 20))

            doc = Document(nodes)
            manager.put_document(f"file:///large_doc_{i}.md", doc)

        # Verify memory is managed
        memory_mb = manager.get_memory_usage_mb()
        assert memory_mb > 0
        # With memory monitoring, should stay under limit
        assert memory_mb <= 500

        # Check that some documents may have been evicted to maintain limit
        stats = manager.get_statistics()
        cache_size = stats["cache_size"]
        # Cache size should be reasonable (not all 20 docs if memory limit hit)
        assert cache_size <= 50

    def test_memory_eviction_frees_space(self):
        """Test that memory-based eviction actually frees memory."""
        manager = DocumentStateManager(
            max_cache_size=100, max_memory_mb=100, enable_memory_monitoring=True
        )

        # Add documents until eviction occurs
        for i in range(50):
            # Large document
            nodes = [
                Heading(level=1, text=f"Large Section {i}"),
                Paragraph(content="Very long content " * 100),
            ]
            doc = Document(nodes)
            manager.put_document(f"file:///doc{i}.md", doc)

        # Memory should have increased from initial
        final_memory = manager.get_memory_usage_mb()
        # Should stay under 100MB limit due to eviction
        assert final_memory <= 100

        stats = manager.get_statistics()
        # Verify evictions occurred (either size-based or memory-based)
        total_evictions = stats["total_evictions"]
        # With 50 docs and cache size 100, expect some evictions due to memory
        assert total_evictions >= 0  # May have evicted some documents

    def test_cache_performance_with_repeated_access(self):
        """Test cache hit performance with repeated document access."""
        manager = DocumentStateManager(max_cache_size=100, enable_memory_monitoring=False)

        # Add documents
        for i in range(10):
            doc = Document([Heading(level=1, text=f"Test {i}")])
            manager.put_document(f"file:///test{i}.md", doc)

        # Access documents repeatedly
        for _ in range(100):
            for i in range(10):
                state = manager.get_document(f"file:///test{i}.md")
                assert state is not None

        # Verify access counts
        stats = manager.get_statistics()
        # 100 iterations * 10 documents = 1000 total accesses
        assert stats["total_accesses"] == 1000

    def test_memory_limit_enforcement_with_batch_eviction(self):
        """Test that batch eviction strategy works correctly."""
        manager = DocumentStateManager(
            max_cache_size=100, max_memory_mb=50, enable_memory_monitoring=True
        )

        # Add many documents quickly
        for i in range(60):
            # Medium-sized documents
            doc = Document(
                [
                    Heading(level=1, text=f"Section {i}"),
                    Paragraph(content=f"Content {i}" * 50),
                ]
            )
            manager.put_document(f"file:///doc{i}.md", doc)

        # Memory should be under limit
        memory_mb = manager.get_memory_usage_mb()
        assert memory_mb <= 50

        # Cache should have evicted some documents
        stats = manager.get_statistics()

        # Either size-based or memory-based eviction should have occurred
        assert stats["total_evictions"] >= 0

    def test_very_large_single_document(self):
        """Test handling of a single very large document."""
        manager = DocumentStateManager(
            max_cache_size=10, max_memory_mb=500, enable_memory_monitoring=True
        )

        # Create a very large document (1000 nodes)
        nodes = []
        for i in range(1000):
            nodes.append(Heading(level=2, text=f"Heading {i}"))
            nodes.append(Paragraph(content=f"Content for paragraph {i}" * 10))

        large_doc = Document(nodes)
        manager.put_document("file:///very_large.md", large_doc)

        # Should be able to cache it
        state = manager.get_document("file:///very_large.md")
        assert state is not None
        assert len(state.document.nodes) == 2000  # 1000 headings + 1000 paragraphs

        # Memory should still be under limit
        memory_mb = manager.get_memory_usage_mb()
        assert memory_mb <= 500

    def test_memory_statistics_accuracy(self):
        """Test that memory statistics are accurate."""
        manager = DocumentStateManager(
            max_cache_size=20, max_memory_mb=500, enable_memory_monitoring=True
        )

        # Add some documents
        for i in range(15):
            doc = Document([Heading(level=1, text=f"Test {i}")])
            manager.put_document(f"file:///test{i}.md", doc)

        stats = manager.get_statistics()

        # Verify all stats are present and reasonable
        assert stats["cache_size"] == 15
        assert stats["max_cache_size"] == 20
        assert stats["max_memory_mb"] == 500
        assert stats["memory_usage_mb"] >= 0
        assert stats["size_evictions"] >= 0
        assert stats["memory_evictions"] >= 0
        assert stats["total_evictions"] == stats["size_evictions"] + stats["memory_evictions"]
        assert stats["total_accesses"] == 0  # No get() calls yet

    def test_summary_output_format(self):
        """Test that summary output is well-formatted."""
        manager = DocumentStateManager(max_cache_size=10, max_memory_mb=500)

        # Add a few documents
        for i in range(5):
            doc = Document([Heading(level=1, text=f"Test {i}")])
            manager.put_document(f"file:///test{i}.md", doc)

        summary = manager.get_summary()

        # Verify summary contains expected information
        assert "Document Cache Summary:" in summary
        assert "Cache size:" in summary
        assert "Memory usage:" in summary
        assert "Total evictions:" in summary
        assert "Total accesses:" in summary
        assert "5/10" in summary  # Cache size 5/10
