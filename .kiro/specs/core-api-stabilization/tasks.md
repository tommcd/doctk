# Tasks Document: Core API Stabilization

## Overview

This document breaks down the implementation of Core API Stabilization into specific, actionable tasks. The work is organized into 8 phases over 11 weeks, with each task including acceptance criteria, dependencies, and deliverables.

**Total Tasks:** 41 tasks
**Total Duration:** 11 weeks (wall-clock time)
**Dependencies:** None (foundational work)
**Blocks:** Fragment Graph Model (Spec 2), Advanced Graph Features (Spec 3)

**Note:** Backward compatibility work has been removed since there are no users yet (v0.1 is alpha/POC). We implement only the new stable ID system.

**Timeline & Parallelization:**
The 11-week timeline assumes some parallel work:

- Phase 3 (Metadata) can start once Phase 2 core operations are stable (week 5)
- Phase 5 (Type Safety) can overlap with Phase 4 completion (week 7)
- Phase 6 (Registry) can partially overlap with Phase 5 (weeks 8-9)
- Documentation tasks can run parallel to implementation throughout

Per-phase durations sum to ~13 weeks if fully sequential, but with 1-2 developers and the overlaps above, the realistic wall-clock time is 11 weeks.

______________________________________________________________________

## Phase 1: Stable Node Identity (2 weeks)

### Task 1.1: Create Core Identity Data Structures

**Duration:** 2 days
**Priority:** Critical

**Description:**
Implement the core data structures for stable node identity: NodeId, Provenance, SourceSpan, and ProvenanceContext.

**Acceptance Criteria:**

- [x] `NodeId` class with content_hash (full 64-char SHA-256), hint, node_type fields
- [x] `NodeId.__str__()` returns 16-character canonical format (type:hint:hash16)
- [x] `NodeId.to_short_string()` returns 8-character display format (for UI only)
- [x] `NodeId.from_string()` method with validation (requires exactly 16-char hash)
- [x] `NodeId.from_node()` method with caching
- [x] `NodeId.__eq__()` and `__hash__()` use first 16 characters for consistency
- [x] Round-trip guarantee: `NodeId.from_string(str(node_id)) == node_id`
- [x] `Provenance` class with origin tracking fields
- [x] `ProvenanceContext` class for context management
- [x] `SourceSpan` class with line/column positions
- [x] All classes are frozen dataclasses (immutable)
- [x] Comprehensive docstrings and type hints

**Files to Create:**

- `src/doctk/core/identity.py`

**Dependencies:** None

**Requirements:** Req 1 AC1, AC6

**Testing:**

```python
def test_node_id_canonical_format():
    """Test 16-character canonical format."""
    node_id = NodeId(
        content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
        hint="intro",
        node_type="heading"
    )
    assert str(node_id) == "heading:intro:a3f5b9c2d1e4f6a7"  # 16 chars

def test_node_id_short_format():
    """Test 8-character display format."""
    node_id = NodeId(
        content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5",
        hint="intro",
        node_type="heading"
    )
    assert node_id.to_short_string() == "heading:intro:a3f5b9c2"  # 8 chars

def test_node_id_round_trip():
    """Test round-trip from_string/str."""
    original = NodeId(
        content_hash="a3f5b9c2d1e4f6a7b8c9d0e1f2a3b4c5",
        hint="intro",
        node_type="heading"
    )
    string_repr = str(original)
    parsed = NodeId.from_string(string_repr)
    assert parsed == original  # Round-trip works

def test_node_id_from_string_validation():
    """Test validation of string format."""
    # Valid 16-char format
    NodeId.from_string("heading:intro:a3f5b9c2d1e4f6a7")

    # Invalid formats
    with pytest.raises(ValueError, match="Invalid NodeId format"):
        NodeId.from_string("invalid")

    with pytest.raises(ValueError, match="Invalid hash length"):
        NodeId.from_string("heading:intro:a3f5")  # Too short

def test_node_id_equality():
    """Test equality uses first 16 characters."""
    id1 = NodeId(content_hash="a3f5b9c2d1e4f6a7" + "0" * 48, hint="test", node_type="heading")
    id2 = NodeId(content_hash="a3f5b9c2d1e4f6a7" + "1" * 48, hint="test", node_type="heading")
    assert id1 == id2  # Same first 16 chars
```

### Task 1.2: Implement Canonical Serialization and Hint Generation

**Duration:** 2 days
**Priority:** Critical

**Description:**
Implement canonical serialization for all node types and the hint generation function for human-readable NodeIds.

**Acceptance Criteria:**

- [x] `_canonicalize_node()` function for all node types (Heading, Paragraph, CodeBlock, ListItem, List, BlockQuote)
- [x] Unicode NFC normalization applied to all text
- [x] Whitespace normalized (strip leading/trailing, collapse internal to single space)
- [x] Tabs converted to 4 spaces
- [x] Line endings converted to LF (\\n)
- [x] Heading canonicalization excludes level (preserves ID across promote/demote)
- [x] Paragraph canonicalization uses content only
- [x] CodeBlock canonicalization includes language and code (preserves whitespace in code)
- [x] `_generate_hint()` function with deterministic slugification
- [x] Hint generation: lowercase, spaces→hyphens, special chars removed
- [x] Hint truncated to 32 characters
- [x] Fallback to node type for non-text nodes
- [x] Deterministic output (same input → same output)
- [x] UTF-8 encoding specified

**Files to Modify:**

- `src/doctk/core/identity.py`

**Dependencies:** Task 1.1

**Requirements:** Req 1 AC1, AC3, AC5

**Testing:**

```python
def test_heading_canonicalization():
    """Test heading canonicalization excludes level."""
    h1 = Heading(level=2, text="Introduction")
    h2 = Heading(level=3, text="Introduction")  # Different level

    # Same canonical form (level excluded)
    assert _canonicalize_node(h1) == _canonicalize_node(h2)
    assert _canonicalize_node(h1) == "heading:introduction"

def test_canonicalization_unicode_normalization():
    """Test Unicode NFC normalization."""
    # é can be single char (U+00E9) or e + combining acute (U+0065 U+0301)
    h1 = Heading(level=2, text="café")  # Single char
    h2 = Heading(level=2, text="café")  # Combining char
    assert _canonicalize_node(h1) == _canonicalize_node(h2)

def test_canonicalization_whitespace():
    """Test whitespace normalization."""
    h1 = Heading(level=2, text="  Multiple   spaces  ")
    h2 = Heading(level=2, text="Multiple spaces")
    assert _canonicalize_node(h1) == _canonicalize_node(h2)

def test_canonicalization_tabs():
    """Test tab conversion."""
    h1 = Heading(level=2, text="Text\twith\ttabs")
    h2 = Heading(level=2, text="Text    with    tabs")
    assert _canonicalize_node(h1) == _canonicalize_node(h2)

def test_canonicalization_deterministic():
    """Test deterministic output."""
    node = Heading(level=2, text="Test")
    canonical1 = _canonicalize_node(node)
    canonical2 = _canonicalize_node(node)
    assert canonical1 == canonical2

def test_hint_generation():
    """Test hint generation with slugification."""
    h = Heading(level=2, text="API Reference Guide")
    hint = _generate_hint(h)
    assert hint == "api-reference-guide"
    assert len(hint) <= 32

def test_hint_generation_special_chars():
    """Test special character removal."""
    h = Heading(level=2, text="Getting Started!")
    hint = _generate_hint(h)
    assert hint == "getting-started"
    assert "!" not in hint

def test_hint_generation_truncation():
    """Test 32-character truncation."""
    h = Heading(level=2, text="Very Long Heading That Definitely Exceeds The Thirty Two Character Limit")
    hint = _generate_hint(h)
    assert len(hint) <= 32
    assert hint == "very-long-heading-that-definit"

def test_hint_generation_fallback():
    """Test fallback for non-text nodes."""
    p = Paragraph(content="Some text")
    hint = _generate_hint(p)
    # Should use first 50 chars of content or fallback to "paragraph"
    assert hint in ["some-text", "paragraph"] or len(hint) <= 32
```

### Task 1.3: Add NodeId Caching System

**Duration:** 1 day
**Priority:** High

**Description:**
Implement caching system for NodeId generation to optimize performance on large documents. Cache must be explicitly documented as in-process only.

**Acceptance Criteria:**

- [x] Module-level cache dictionary `_node_id_cache`
- [x] Explicit documentation: "IN-PROCESS, NON-PERSISTENT cache only"
- [x] Warning comment: "DO NOT persist or share this cache across processes"
- [x] `_get_node_cache_key()` function for lightweight cache keys
- [x] Cache keys use Python's `hash()` (process-specific, randomized)
- [x] Documentation that cache keys are NOT stable across runs
- [x] Cache integration in `NodeId.from_node()`
- [x] `clear_node_id_cache()` function for testing
- [x] Cache size management (prevent memory leaks)
- [x] Performance improvement measurable (>50% speedup on repeated parsing)

**Files to Modify:**

- `src/doctk/core/identity.py`

**Dependencies:** Task 1.2

**Requirements:** Req 7 AC1 (performance)

**Testing:**

```python
def test_node_id_caching():
    """Test cache improves performance."""
    node = Heading(level=2, text="Test")

    # First call generates and caches
    id1 = NodeId.from_node(node)

    # Second call uses cache
    id2 = NodeId.from_node(node)

    assert id1 == id2
    assert id1 is id2  # Same object (cached)
```

### Task 1.4: Update Node Base Class

**Duration:** 1 day
**Priority:** Critical

**Description:**
Add NodeId, Provenance, and SourceSpan fields to the Node base class and update all node subclasses.

**Acceptance Criteria:**

- [x] `Node` base class has `id`, `provenance`, `source_span` fields
- [x] All node subclasses (Heading, Paragraph, CodeBlock, etc.) updated
- [x] Default values are None (optional fields)
- [x] Existing constructors remain compatible
- [x] Type hints updated throughout
- [x] No breaking changes to existing API

**Files to Modify:**

- `src/doctk/core.py`

**Dependencies:** Task 1.1

### Task 1.5: Enhance Document Class with ID Indexing

**Duration:** 2 days
**Priority:** High

**Description:**
Add NodeId-based indexing to Document class for O(1) node lookup and update related methods.

**Acceptance Criteria:**

- [x] `Document._id_index` dictionary for fast lookup
- [x] `Document.find_node(node_id)` method
- [x] `Document.find_nodes(predicate)` method
- [x] Index automatically built/updated when nodes change
- [x] Existing Document API remains stable (no breaking changes)
- [x] Performance: O(1) lookup by ID, O(n) by predicate

**Files to Modify:**

- `src/doctk/core.py`

**Dependencies:** Task 1.4

### Task 1.6: Update Markdown Parser with Source Spans and View Mapping

**Duration:** 4 days
**Priority:** High

**Description:**
Enhance MarkdownParser to attach accurate source spans with block-level precision, generate stable NodeIds during parsing, and implement view-to-source mapping infrastructure.

**Acceptance Criteria:**

- [x] `MarkdownParser.parse_file()` method with provenance
- [x] `MarkdownParser.parse_string()` method with context
- [x] `_find_token_start_column()` method for block-level column recovery
- [x] `_find_token_end_column()` method for end positions
- [x] Block-level source spans attached to all structural nodes (headings, paragraphs, lists, code blocks)
- [x] Inline elements inherit parent block's source span
- [x] Documentation of block-level precision scope
- [x] NodeIds generated and attached during parsing
- [x] Provenance populated from context
- [x] Support for file-based and REPL contexts
- [x] `ViewSourceMapping` class for materialized view tracking
- [x] `Document._view_mappings` list for storing mappings
- [x] `Document.add_view_mapping()` method
- [x] `Document.find_source_position()` method for view→source projection
- [x] Identity mappings created during parsing (view = source initially)

**Files to Modify:**

- `src/doctk/parsers/markdown.py`
- `src/doctk/core/identity.py` (add ViewSourceMapping)
- `src/doctk/core.py` (add \_view_mappings to Document)

**Dependencies:** Task 1.5

**Requirements:** Req 3 AC1, AC2, AC5, AC6

### Task 1.7: Implement Text Edit ID Semantics

**Duration:** 2 days
**Priority:** Critical

**Description:**
Implement methods that handle text edits correctly - generating new IDs when canonical content changes, preserving IDs when only structural attributes change.

**Acceptance Criteria:**

- [x] `Heading.with_text()` method generates new NodeId
- [x] `Paragraph.with_content()` method generates new NodeId
- [x] `CodeBlock.with_code()` method generates new NodeId
- [x] `CodeBlock.with_language()` method generates new NodeId
- [x] `ListItem.with_content()` method generates new NodeId
- [x] All node types with canonical fields have `with_*` methods
- [x] `Heading.promote()` preserves NodeId (level not in canonical form)
- [x] `Heading.demote()` preserves NodeId
- [x] `Node.with_metadata()` preserves NodeId (metadata not in canonical form)
- [x] All transformation methods use `copy.deepcopy()` for metadata
- [x] Provenance updated appropriately (with_modification())
- [x] Source spans preserved
- [x] Documentation of text edit vs structural change semantics

**Files to Modify:**

- `src/doctk/core.py` (all node classes)

**Dependencies:** Task 1.6

**Requirements:** Req 1 AC2, AC4, AC5

**Testing:**

```python
def test_text_edit_changes_id():
    """Verify text edits generate new IDs."""
    heading = Heading(level=2, text="Original")
    original_id = heading.id

    edited = heading.with_text("Modified")

    assert edited.id != original_id
    assert edited.text == "Modified"
    assert edited.level == heading.level

def test_structural_change_preserves_id():
    """Verify structural changes preserve IDs."""
    heading = Heading(level=2, text="Test")
    original_id = heading.id

    promoted = heading.promote()

    assert promoted.id == original_id
    assert promoted.level == 1
    assert promoted.text == heading.text

def test_metadata_change_preserves_id():
    """Verify metadata changes preserve IDs."""
    heading = Heading(level=2, text="Test")
    original_id = heading.id

    tagged = heading.with_metadata({"tags": ["important"]})

    assert tagged.id == original_id
    assert tagged.metadata["tags"] == ["important"]

def test_code_block_edit_changes_id():
    """Verify code edits generate new IDs."""
    code_block = CodeBlock(language="python", code="print('hello')")
    original_id = code_block.id

    edited = code_block.with_code("print('world')")

    assert edited.id != original_id
    assert edited.code == "print('world')"
    assert edited.language == code_block.language

def test_code_block_language_edit_changes_id():
    """Verify language edits generate new IDs."""
    code_block = CodeBlock(language="python", code="print('hello')")
    original_id = code_block.id

    edited = code_block.with_language("javascript")

    assert edited.id != original_id
    assert edited.language == "javascript"
    assert edited.code == code_block.code
```

### Task 1.8: Write Unit Tests for Stable Identity

**Duration:** 2 days
**Priority:** High

**Description:**
Create comprehensive unit tests for the stable identity system.

**Acceptance Criteria:**

- [x] Test NodeId creation and string conversion (16-char format)
- [x] Test NodeId round-tripping (from_string/\_\_str\_\_)
- [x] Test to_short_string() for display
- [x] Test canonical serialization determinism
- [x] Test Unicode NFC normalization
- [x] Test whitespace and tab normalization
- [x] Test hint generation with slugification
- [x] Test hint truncation to 32 characters
- [x] Test ID stability across operations (promote/demote)
- [x] Test ID changes on text edits
- [x] Test ID consistency across re-parsing
- [x] Test provenance population and updates
- [x] Test source span block-level accuracy
- [x] Test ViewSourceMapping projection
- [x] Test caching performance (>50% speedup)
- [x] Test cache is in-process only
- [x] Test error handling and edge cases
- [x] >95% code coverage for identity module

**Files to Create:**

- `tests/unit/test_stable_ids.py`
- `tests/unit/test_provenance.py`
- `tests/unit/test_source_spans.py`
- `tests/unit/test_view_mapping.py`
- `tests/unit/test_text_edit_semantics.py`

**Dependencies:** Task 1.7

______________________________________________________________________

## Phase 2: Internal Operations Layer (3 weeks)

### Task 2.1: Create Internal Operations Module

**Duration:** 3 days
**Priority:** Critical

**Description:**
Create the new internal operations layer that works with rich Document objects instead of serialized strings.

**Acceptance Criteria:**

- [ ] `InternalOperations` class with all core operations
- [ ] Operations return `OperationResult` with Document objects
- [ ] Node IDs preserved across operations
- [ ] Metadata deep-copied to ensure immutability
- [ ] Provenance updated during transformations
- [ ] Source spans preserved where appropriate
- [ ] No JSON serialization in internal layer

**Files to Create:**

- `src/doctk/core/internal_ops.py`

**Dependencies:** Phase 1 complete

**Requirements:** Req 2 AC1, AC2, AC3

### Task 2.2: Implement All Core Operations Internally

**Duration:** 4 days
**Priority:** Critical

**Description:**
Implement internal versions of all existing operations: promote, demote, nest, unnest, etc.

**Acceptance Criteria:**

- [ ] `promote()` operation with ID preservation
- [ ] `demote()` operation with ID preservation
- [ ] `nest()` operation with relationship tracking
- [ ] `unnest()` operation with structure updates
- [ ] All operations handle metadata immutability
- [ ] All operations update provenance appropriately
- [ ] Error handling for invalid operations
- [ ] Consistent return format (OperationResult)

**Files to Modify:**

- `src/doctk/core/internal_ops.py`

**Dependencies:** Task 2.1

**Requirements:** Req 2 AC1, Req 1 AC2, AC4

### Task 2.3: Update JSON-RPC Bridge to Use Internal Operations

**Duration:** 3 days
**Priority:** High

**Description:**
Refactor StructureOperations to be a thin wrapper around internal operations, handling serialization only at the boundary.

**Acceptance Criteria:**

- [ ] `StructureOperations` methods delegate to `InternalOperations`
- [ ] String NodeId parsing handled in bridge
- [ ] Document serialization only at JSON-RPC boundary
- [ ] Range calculation for modified nodes
- [ ] Existing JSON-RPC API remains stable
- [ ] Error propagation from internal layer
- [ ] Performance improvement measurable

**Files to Modify:**

- `src/doctk/integration/operations.py`

**Dependencies:** Task 2.2

### Task 2.4: Refactor DSL Executor to Use Internal Operations

**Duration:** 3 days
**Priority:** High

**Description:**
Update DSL executor to use internal operations layer, eliminating serialization round-trips.

**Acceptance Criteria:**

- [ ] DSL executor imports `InternalOperations`
- [ ] Command execution uses internal operations
- [ ] Document state maintained as objects between commands
- [ ] No string serialization during DSL execution
- [ ] Error handling updated for internal operations
- [ ] Performance improvement in multi-command pipelines
- [ ] Existing DSL syntax remains supported

**Files to Modify:**

- `src/doctk/dsl/executor.py`

**Dependencies:** Task 2.2

### Task 2.5: Refactor REPL to Use Internal Operations

**Duration:** 2 days
**Priority:** Medium

**Description:**
Update REPL to maintain document state using internal operations, providing faster interactive experience.

**Acceptance Criteria:**

- [ ] REPL maintains Document object state
- [ ] Commands use internal operations
- [ ] No serialization between REPL commands
- [ ] Document display/preview still works
- [ ] History tracking with Document objects
- [ ] Undo/redo functionality preserved
- [ ] Interactive performance improved

**Files to Modify:**

- `src/doctk/dsl/repl.py`

**Dependencies:** Task 2.2

### Task 2.6: Write Integration Tests for Internal Operations

**Duration:** 2 days
**Priority:** High

**Description:**
Create comprehensive integration tests for the internal operations layer.

**Acceptance Criteria:**

- [ ] Test multi-step operation pipelines
- [ ] Test ID preservation across complex operations
- [ ] Test performance vs JSON-RPC baseline
- [ ] Test error propagation and handling
- [ ] Test DSL executor integration
- [ ] Test REPL integration
- [ ] Test memory usage (no leaks)
- [ ] >90% code coverage for internal operations

**Files to Create:**

- `tests/integration/test_internal_ops.py`
- `tests/integration/test_dsl_internal_ops.py`
- `tests/integration/test_repl_internal_ops.py`

**Dependencies:** Task 2.5

### Task 2.7: Define Document Serialization Interface

**Duration:** 1 day
**Priority:** High

**Description:**
Formally define the [PLANNED] `Document.to_json()` and [PLANNED] `Document.from_json()` methods with their JSON schema for use in JSON-RPC bridge and testing.

**Acceptance Criteria:**

- [ ] [PLANNED] `Document.to_json()` method signature defined
- [ ] [PLANNED] `Document.from_json()` class method signature defined
- [ ] JSON schema documented (nodes array, metadata, version)
- [ ] Node serialization format specified (type, fields, id)
- [ ] Deserialization error handling specified
- [ ] Version field for future compatibility
- [ ] Documentation with examples

**Files to Modify:**

- `src/doctk/core.py` (add method signatures and docstrings)
- `docs/api/serialization.md` (new documentation)

**Dependencies:** Task 2.3

**Requirements:** Req 2 AC3

______________________________________________________________________

## Phase 3: Metadata Immutability (1 week)

### Task 3.1: Implement Deep Copy in Node Transformations

**Duration:** 2 days
**Priority:** High

**Description:**
Add deep-copying of metadata in all node transformation methods to ensure immutability.

**Acceptance Criteria:**

- [ ] All node transformation methods use `copy.deepcopy()`
- [ ] `promote()`, `demote()`, `nest()`, etc. deep-copy metadata
- [ ] Custom objects in metadata handled correctly
- [ ] Performance impact measured and within 15% overhead
- [ ] No shared references between original and transformed nodes

**Files to Modify:**

- `src/doctk/core.py` (all node classes)

**Dependencies:** Phase 2 complete

### Task 3.2: Add Immutability Tests

**Duration:** 1 day
**Priority:** High

**Description:**
Create comprehensive tests to verify metadata immutability across all operations.

**Acceptance Criteria:**

- [ ] Test all node transformation methods
- [ ] Test nested metadata structures
- [ ] Test custom objects in metadata
- [ ] Test edge cases (None, empty dict, circular references)
- [ ] Performance benchmarks for deep-copy overhead
- [ ] Memory usage tests (no leaks)

**Files to Create:**

- `tests/unit/test_metadata_immutability.py`

**Dependencies:** Task 3.1

### Task 3.3: Document Immutability Guarantees

**Duration:** 1 day
**Priority:** Medium

**Description:**
Document the immutability guarantees and best practices for metadata handling.

**Acceptance Criteria:**

- [ ] Documentation explains immutability guarantees
- [ ] Examples of safe vs unsafe metadata usage
- [ ] Performance implications documented
- [ ] Best practices for metadata design

**Files to Create:**

- `docs/guides/metadata-immutability.md`

**Dependencies:** Task 3.2

### Task 3.4: Performance Benchmarking

**Duration:** 2 days
**Priority:** Medium

**Description:**
Measure and optimize metadata deep-copy performance to ensure it meets the 15% overhead target. This focused benchmark validates the specific deep-copy implementation; comprehensive performance validation happens in Phase 9.

**Acceptance Criteria:**

- [ ] Baseline performance measurements
- [ ] Deep-copy overhead measurements
- [ ] Optimization if overhead exceeds 15%
- [ ] Memory usage profiling
- [ ] Performance regression tests
- [ ] Documentation of performance characteristics

**Files to Create:**

- `tests/performance/test_metadata_performance.py`

**Dependencies:** Task 3.2

______________________________________________________________________

## Phase 4: API Paradigm Unification (1 week)

### Task 4.1: Implement by_id() Predicate Bridge

**Duration:** 2 days
**Priority:** High

**Description:**
Implement the `by_id()` function that converts NodeIds to predicates, bridging declarative and imperative APIs.

**Acceptance Criteria:**

- [ ] `by_id()` function accepts NodeId or string
- [ ] Returns predicate function for use with `select()`
- [ ] Handles NodeId string parsing
- [ ] Error handling for invalid NodeId strings
- [ ] Type hints for proper IDE support
- [ ] Integration with existing operations pipeline

**Files to Modify:**

- `src/doctk/operations.py`

**Dependencies:** Phase 3 complete

### Task 4.2: Update StructureOperations to Delegate

**Duration:** 2 days
**Priority:** High

**Description:**
Refactor StructureOperations to use the declarative API internally via by_id() bridge.

**Acceptance Criteria:**

- [ ] All StructureOperations methods use declarative pipeline
- [ ] `by_id()` used to convert string IDs to predicates
- [ ] No duplicate operation logic
- [ ] Same results as before (no breaking changes)
- [ ] Error handling preserved
- [ ] Performance maintained or improved

**Files to Modify:**

- `src/doctk/integration/operations.py`

**Dependencies:** Task 4.1

### Task 4.3: Add API Unification Tests

**Duration:** 1 day
**Priority:** High

**Description:**
Create tests to verify both APIs produce identical results.

**Acceptance Criteria:**

- [ ] Test declarative vs imperative equivalence
- [ ] Test by_id() with all operations
- [ ] Test error handling consistency
- [ ] Test performance parity
- [ ] >90% code coverage for by_id() bridge

**Files to Create:**

- `tests/unit/test_api_unification.py`

**Dependencies:** Task 4.2

### Task 4.4: Update Documentation for Unified API

**Duration:** 2 days
**Priority:** Medium

**Description:**
Update documentation to explain the unified API approach and when to use each style.

**Acceptance Criteria:**

- [ ] Documentation explains both API styles
- [ ] Examples showing equivalent operations
- [ ] Guidance on when to use each style
- [ ] API reference updated

**Files to Modify:**

- `docs/api/operations.md`
- `docs/guides/api-styles.md` (new)

**Dependencies:** Task 4.3

______________________________________________________________________

## Phase 5: Type Safety Improvements (1 week)

### Task 5.1: Implement TypeGuards and Generic Document

**Duration:** 3 days
**Priority:** Critical

**Description:**
Implement TypeGuard functions for type narrowing and generic Document[TNode] for type-safe operations.

**Acceptance Criteria:**

- [ ] Create `src/doctk/core/type_guards.py` module
- [ ] `is_heading(node: Node) -> TypeGuard[Heading]` function
- [ ] `is_paragraph(node: Node) -> TypeGuard[Paragraph]` function
- [ ] `is_code_block(node: Node) -> TypeGuard[CodeBlock]` function
- [ ] `is_list(node: Node) -> TypeGuard[List]` function
- [ ] `is_list_item(node: Node) -> TypeGuard[ListItem]` function
- [ ] `is_block_quote(node: Node) -> TypeGuard[BlockQuote]` function
- [ ] TypeGuards for all structural node types (can add more opportunistically later)
- [ ] Generic `Document[TNode]` class in `core.py`
- [ ] `select()` uses TypeGuard parameter for type narrowing
- [ ] `select()` returns `Document[TNode]` with narrowed type
- [ ] Type hints work correctly in IDEs (autocomplete after select)
- [ ] mypy/pyright correctly narrow types
- [ ] No runtime overhead from type annotations

**Files to Create:**

- `src/doctk/core/type_guards.py`

**Files to Modify:**

- `src/doctk/operations.py` (typed select)
- `src/doctk/core.py` (generic Document)

**Dependencies:** Phase 4 complete

**Requirements:** Req 6 AC1, AC2, AC3

**Testing:**

```python
def test_type_guard_narrows_type():
    """Test TypeGuard enables type narrowing."""
    node: Node = Heading(level=2, text="Test")

    if is_heading(node):
        # Type checker knows node is Heading here
        assert node.level == 2  # No type error
        assert node.text == "Test"

def test_generic_document_preserves_type():
    """Test generic Document preserves node types."""
    doc: Document[Node] = Document([
        Heading(level=2, text="H1"),
        Paragraph(content="P1")
    ])

    # Type-safe selection
    headings: Document[Heading] = doc | select(is_heading)

    # IDE knows headings.nodes is list[Heading]
    for h in headings.nodes:
        print(h.level)  # Type-safe access
```

### Task 5.2: Add Optional Visitor Pattern

**Duration:** 2 days
**Priority:** Medium

**Description:**
Implement optional Visitor pattern as an alternative dispatch mechanism for operations.

**Acceptance Criteria:**

- [ ] `NodeVisitor` base class with visit methods for each node type
- [ ] `visit_heading()`, `visit_paragraph()`, `visit_code_block()`, etc.
- [ ] `Node.accept(visitor)` method for double dispatch
- [ ] Example visitor: `PromoteVisitor` that promotes headings
- [ ] Documentation explaining when to use Visitor vs TypeGuards
- [ ] Tests for visitor pattern
- [ ] Optional - not required for core functionality

**Files to Create:**

- `src/doctk/core/visitor.py`

**Files to Modify:**

- `src/doctk/core.py` (add accept() method to Node)

**Dependencies:** Task 5.1

**Requirements:** Req 6 AC4 (optional pattern)

**Testing:**

```python
def test_visitor_pattern():
    """Test visitor pattern for operations."""
    class PromoteVisitor(NodeVisitor):
        def visit_heading(self, node: Heading) -> Node:
            return node.promote()

        def visit_paragraph(self, node: Paragraph) -> Node:
            return node  # Identity

    heading = Heading(level=2, text="Test")
    visitor = PromoteVisitor()
    result = heading.accept(visitor)

    assert isinstance(result, Heading)
    assert result.level == 1
```

### Task 5.3: Add Result Type for Operations

**Duration:** 1 day
**Priority:** High

**Description:**
Implement proper Result type for operation outcomes with success/error handling, integrated with diagnostic system.

**Acceptance Criteria:**

- [ ] `OperationResult` class with success/error states
- [ ] Type-safe error handling
- [ ] Chainable result operations
- [ ] Integration with existing operations
- [ ] Type errors produce `Diagnostic` instances (not just exceptions)
- [ ] Error results include source spans and node IDs
- [ ] Existing error handling patterns remain supported

**Files to Create:**

- `src/doctk/core/result.py`

**Dependencies:** Task 5.2

**Requirements:** Req 6 AC5, Req 9 AC3

### Task 5.4: Run mypy Validation

**Duration:** 1 day
**Priority:** High

**Description:**
Run mypy on entire codebase and fix type errors.

**Acceptance Criteria:**

- [ ] mypy runs without errors on core modules
- [ ] Type stubs for external dependencies
- [ ] Type ignore comments documented
- [ ] CI integration for mypy checks
- [ ] Type coverage >80%

**Files to Modify:**

- `pyproject.toml` (mypy config)
- Various source files (type fixes)

**Dependencies:** Task 5.3

**Requirements:** Req 6 AC4

### Task 5.5: Add Type Safety Tests

**Duration:** 1 day
**Priority:** Medium

**Description:**
Create tests that verify type safety and IDE support.

**Acceptance Criteria:**

- [ ] Test TypeGuard type narrowing
- [ ] Test generic Document[TNode] type preservation
- [ ] Test Result type handling
- [ ] Test Visitor pattern (if implemented)
- [ ] Verify IDE autocomplete works after select()
- [ ] Document type safety guarantees

**Files to Create:**

- `tests/unit/test_type_safety.py`
- `tests/unit/test_type_guards.py`

**Dependencies:** Task 5.4

**Requirements:** Req 6 AC5

______________________________________________________________________

## Phase 6: Operation Registry (2 weeks)

### Task 6.1: Design Operation Registry Interface

**Duration:** 2 days
**Priority:** High

**Description:**
Design the interface for the operation registry that will support dynamic operation discovery.

**Acceptance Criteria:**

- [ ] Registry interface defined
- [ ] Operation metadata structure defined
- [ ] Registration mechanism designed
- [ ] Discovery API designed
- [ ] Extension points identified
- [ ] Documentation of design decisions

**Files to Create:**

- `docs/design/operation-registry.md`

**Dependencies:** Phase 5 complete

### Task 6.2: Implement Core Registry

**Duration:** 3 days
**Priority:** Critical

**Description:**
Implement the core operation registry with registration and discovery.

**Acceptance Criteria:**

- [ ] `OperationRegistry` class
- [ ] `register_operation()` decorator
- [ ] `discover_operations()` function
- [ ] Operation metadata storage
- [ ] Thread-safe registration
- [ ] Plugin support hooks (mechanism: explicit registration via decorator, extensible for future entry points)

**Files to Create:**

- `src/doctk/core/registry.py`

**Dependencies:** Task 6.1

### Task 6.3: Register All Existing Operations

**Duration:** 2 days
**Priority:** High

**Description:**
Register all existing operations with the new registry and define public API explicitly.

**Acceptance Criteria:**

- [ ] `__all__` list defined in `src/doctk/operations.py` with all public operations
- [ ] All core operations registered (select, where, by_id, promote, demote, nest, unnest, map_nodes, filter_nodes, fold)
- [ ] Metadata populated for each operation
- [ ] Categories assigned
- [ ] Documentation strings included
- [ ] Examples provided
- [ ] Existing operation signatures remain stable

**Files to Modify:**

- `src/doctk/operations.py` (add `__all__` list)
- `src/doctk/core/internal_ops.py`

**Dependencies:** Task 6.2

**Requirements:** Req 8 AC1, AC2

### Task 6.4: Update LSP Server to Use Registry

**Duration:** 3 days
**Priority:** High

**Description:**
Update LSP server to discover operations dynamically from registry.

**Acceptance Criteria:**

- [ ] LSP completion uses registry
- [ ] LSP hover uses registry metadata
- [ ] Dynamic operation discovery
- [ ] No hardcoded operation lists
- [ ] Performance maintained
- [ ] Error handling for missing operations

**Files to Modify:**

- `src/doctk/lsp/server.py`
- `src/doctk/lsp/completion.py`
- `src/doctk/lsp/hover.py`

**Dependencies:** Task 6.3

### Task 6.5: Add Registry Tests

**Duration:** 2 days
**Priority:** High

**Description:**
Create comprehensive tests for the operation registry, including completeness test using __all__.

**Acceptance Criteria:**

- [ ] Test registration mechanism
- [ ] Test discovery API
- [ ] Test metadata retrieval
- [ ] Test thread safety
- [ ] Test plugin integration
- [ ] Completeness test using `__all__` list (verifies all public operations are registered)
- [ ] >90% code coverage

**Files to Create:**

- `tests/unit/test_operation_registry.py`

**Dependencies:** Task 6.4

**Requirements:** Req 8 AC5

**Testing:**

```python
def test_registry_completeness():
    """Verify all public operations are registered."""
    import doctk.operations

    # Get all operations from __all__
    public_operations = doctk.operations.__all__

    # Get registered operations
    registered = set(OperationRegistry.list_operations())

    # Verify all public operations are registered
    for op_name in public_operations:
        assert op_name in registered, f"Operation {op_name} not registered"
```

______________________________________________________________________

## Phase 7: Diagnostic Improvements (2 weeks)

### Task 7.1: Enhance Error Messages with Source Spans

**Duration:** 3 days
**Priority:** High

**Description:**
Update all error messages to include source span information for better debugging.

**Acceptance Criteria:**

- [ ] All operation errors include source spans
- [ ] Parser errors include line/column info
- [ ] Error messages show context (surrounding lines)
- [ ] Consistent error format across codebase
- [ ] IDE-friendly error format
- [ ] (Optional) Simple color-coded terminal output (if time permits, not required for spec acceptance)

**Files to Modify:**

- `src/doctk/core/internal_ops.py`
- `src/doctk/parsers/markdown.py`
- All operation files

**Dependencies:** Phase 6 complete

**Requirements:** Req 9 AC1, AC2, AC3

**Note:** Color-coded output is a nice-to-have enhancement. Focus on source spans, context, and consistent formatting first. Simple ANSI color support can be added if time permits, but should not block spec completion.

### Task 7.2: Add Diagnostic Context Manager and Data Structures

**Duration:** 3 days
**Priority:** Medium

**Description:**
Create diagnostic data structures and context manager for collecting and reporting diagnostics during operations.

**Acceptance Criteria:**

- [ ] `Diagnostic` dataclass with all fields (severity, message, source_span, node_id, code, quick_fixes, context_lines)
- [ ] `context_lines` field added for source context display
- [ ] `QuickFix` dataclass with title, description, edits
- [ ] `TextEdit` dataclass with span and new_text
- [ ] `DiagnosticContext` class for collecting diagnostics
- [ ] Collects warnings and errors
- [ ] Supports nested contexts
- [ ] Integration with operations
- [ ] Configurable severity levels
- [ ] Export to LSP diagnostic format
- [ ] Helper to generate context_lines from source_span and document text

**Files to Create:**

- `src/doctk/core/diagnostics.py`

**Dependencies:** Task 7.1

**Requirements:** Req 9 AC1, AC2, AC3, AC4, AC5

**Testing:**

```python
def test_diagnostic_with_context_lines():
    """Test diagnostic includes source context."""
    span = SourceSpan(start_line=5, start_column=0, end_line=5, end_column=10)
    diag = Diagnostic(
        severity="error",
        message="Test error",
        source_span=span,
        node_id=None,
        code="E001",
        context_lines=["Line 5 content", "^^^^^^^^^^"]
    )
    assert len(diag.context_lines) == 2
    assert diag.context_lines[0] == "Line 5 content"
```

### Task 7.3: Update LSP Server with Enhanced Diagnostics

**Duration:** 3 days
**Priority:** High

**Description:**
Update LSP server to provide rich diagnostics using source spans and diagnostic context.

**Acceptance Criteria:**

- [ ] LSP diagnostics include source spans
- [ ] Real-time diagnostic updates
- [ ] Severity levels (error, warning, info)
- [ ] Quick fixes suggested where possible
- [ ] Performance maintained
- [ ] Integration with VS Code problems panel

**Files to Modify:**

- `src/doctk/lsp/server.py`
- `src/doctk/lsp/diagnostics.py` (new)

**Dependencies:** Task 7.2

### Task 7.4: Add Diagnostic Tests

**Duration:** 2 days
**Priority:** High

**Description:**
Create tests for diagnostic system and error reporting.

**Acceptance Criteria:**

- [ ] Test error message formatting
- [ ] Test source span inclusion
- [ ] Test diagnostic context
- [ ] Test LSP diagnostic integration
- [ ] Test error recovery
- [ ] >85% code coverage

**Files to Create:**

- `tests/unit/test_diagnostics.py`
- `tests/integration/test_lsp_diagnostics.py`

**Dependencies:** Task 7.3

______________________________________________________________________

## Phase 8: Performance Validation (1 week)

### Task 8.1: Create Performance Benchmark Suite

**Duration:** 2 days
**Priority:** High

**Description:**
Create comprehensive performance benchmarks for all operations.

**Acceptance Criteria:**

- [ ] Benchmarks for all core operations
- [ ] Large document tests (10K+ nodes)
- [ ] Memory usage profiling
- [ ] Comparison with v0.1 baseline
- [ ] Automated benchmark running
- [ ] Performance regression detection

**Files to Create:**

- `tests/performance/test_operation_performance.py`
- `tests/performance/test_memory_usage.py`

**Dependencies:** Phase 7 complete

### Task 8.2: Optimize Critical Paths

**Duration:** 2 days
**Priority:** High

**Description:**
Profile and optimize any performance bottlenecks discovered in benchmarks.

**Acceptance Criteria:**

- [ ] Profile all operations
- [ ] Identify bottlenecks
- [ ] Optimize critical paths
- [ ] Verify improvements with benchmarks
- [ ] Document optimization decisions
- [ ] No functionality regressions

**Files to Modify:**

- Various source files based on profiling

**Dependencies:** Task 8.1

### Task 8.3: Validate Performance Targets

**Duration:** 1 day
**Priority:** Critical

**Description:**
Verify all performance targets from requirements are met.

**Acceptance Criteria:**

- [ ] NodeId generation \<1ms per node
- [ ] Deep-copy overhead \<15%
- [ ] Internal ops 2x faster than JSON-RPC
- [ ] Existing performance budgets met (1s render, 200ms interaction)
- [ ] Large document handling (10K nodes) within performance budget
- [ ] Memory usage within acceptable bounds (within 20% of baseline)
- [ ] All targets documented and verified

**Files to Create:**

- `docs/performance-validation.md`

**Dependencies:** Task 8.2

### Task 8.4: Final Integration Testing

**Duration:** 2 days
**Priority:** Critical

**Description:**
Run full integration test suite and verify all systems work together.

**Acceptance Criteria:**

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All e2e tests pass
- [ ] Performance tests pass
- [ ] No memory leaks detected
- [ ] Documentation complete
- [ ] Ready for release

**Dependencies:** Task 8.3

______________________________________________________________________

## Success Criteria

The Core API Stabilization spec is complete when:

- [ ] All 8 phases completed
- [ ] All 41 tasks marked as done
- [ ] Test coverage >90% for new code
- [ ] All performance targets met (1s render, 200ms interaction)
- [ ] Documentation complete and reviewed
- [ ] No critical bugs in issue tracker
- [ ] Code review approved by team
- [ ] Ready to merge to main branch

## Progress Tracking

**Phase 1:** ⬜⬜⬜⬜⬜⬜⬜⬜ 0/8 tasks complete
**Phase 2:** ⬜⬜⬜⬜⬜⬜⬜ 0/7 tasks complete
**Phase 3:** ⬜⬜⬜⬜ 0/4 tasks complete
**Phase 4:** ⬜⬜⬜⬜ 0/4 tasks complete
**Phase 5:** ⬜⬜⬜⬜⬜ 0/5 tasks complete
**Phase 6:** ⬜⬜⬜⬜⬜ 0/5 tasks complete
**Phase 7:** ⬜⬜⬜⬜ 0/4 tasks complete
**Phase 8:** ⬜⬜⬜⬜ 0/4 tasks complete

**Overall Progress:** 0/41 tasks complete (0%)

______________________________________________________________________

## Notes

- Tasks should be completed in order within each phase
- Some tasks can be parallelized (e.g., documentation while coding)
- Timeline: 11 weeks wall-clock time (after removing backward compatibility work)
- Regular code reviews recommended after each phase
- Performance validation should happen continuously, not just in Phase 8
- No backward compatibility work needed (v0.1 is alpha with no users)
