# Next Actions for PR #56 - Phase 1 Completion

**Status:** BLOCKING ISSUE - Must fix before merge
**Review Date:** 2025-11-26
**Review Document:** [docs/archive/specs/core-api-stabilization/reviews/phase1-pr56-review.md](../../../docs/archive/specs/core-api-stabilization/reviews/phase1-pr56-review.md)

______________________________________________________________________

## 🔴 BLOCKING: Fix Finding #5 - Recursive ID Indexing

### Problem

`Document._build_id_index()` only indexes top-level nodes. Nested nodes (ListItem inside List, content inside BlockQuote, children in Heading) are not indexed, causing `find_node()` to return `None` for any nested node.

**Impact:** Critical - breaks O(1) lookup for nested structures, violating Task 1.5 spec.

### Required Changes

#### 1. Fix Implementation

**File:** `src/doctk/core.py`

**Current code (lines 539-544):**

```python
def _build_id_index(self) -> None:
    """Build index of nodes by their IDs for O(1) lookup."""
    self._id_index.clear()
    for node in self.nodes:
        if hasattr(node, "id") and node.id is not None:
            self._id_index[node.id] = node
```

**Replace with:**

```python
def _build_id_index(self) -> None:
    """Build index recursively for all nodes in document tree."""
    self._id_index.clear()

    def _index_recursive(node: T) -> None:
        """Recursively index node and all descendants."""
        # Index this node
        if hasattr(node, "id") and node.id is not None:
            self._id_index[node.id] = node

        # Recursively index children based on node type
        if hasattr(node, "children") and isinstance(node.children, list):
            for child in node.children:
                _index_recursive(child)

        if hasattr(node, "items") and isinstance(node.items, list):  # List
            for item in node.items:
                _index_recursive(item)

        if hasattr(node, "content") and isinstance(node.content, list):  # ListItem, BlockQuote
            for child in node.content:
                _index_recursive(child)

    # Start recursive indexing from top-level nodes
    for node in self.nodes:
        _index_recursive(node)
```

#### 2. Add Tests

**File:** `tests/unit/test_document_indexing.py`

Add these test cases:

```python
def test_find_node_in_nested_list_item():
    """Verify find_node works for nested ListItem."""
    from doctk.core import List, ListItem, Paragraph
    from doctk.identity import NodeId

    list_item = ListItem(content=[Paragraph(content="Nested")])
    list_item.id = NodeId.from_node(list_item)

    doc = Document([List(ordered=True, items=[list_item])])

    # Should find the nested list item
    found = doc.find_node(list_item.id)
    assert found is not None
    assert found == list_item


def test_find_node_in_blockquote():
    """Verify find_node works for BlockQuote nested content."""
    from doctk.core import BlockQuote, Paragraph
    from doctk.identity import NodeId

    para = Paragraph(content="Quoted")
    para.id = NodeId.from_node(para)

    doc = Document([BlockQuote(content=[para])])

    # Should find the nested paragraph
    found = doc.find_node(para.id)
    assert found is not None
    assert found == para


def test_find_node_in_heading_children():
    """Verify find_node works for Heading children."""
    from doctk.core import Heading, Paragraph
    from doctk.identity import NodeId

    child = Paragraph(content="Child paragraph")
    child.id = NodeId.from_node(child)

    heading = Heading(level=2, text="Parent", children=[child])

    doc = Document([heading])

    # Should find the nested child
    found = doc.find_node(child.id)
    assert found is not None
    assert found == child


def test_find_node_deeply_nested():
    """Verify find_node works for deeply nested structures."""
    from doctk.core import BlockQuote, List, ListItem, Paragraph
    from doctk.identity import NodeId

    # Create deeply nested structure: BlockQuote > List > ListItem > Paragraph
    para = Paragraph(content="Deep content")
    para.id = NodeId.from_node(para)

    list_item = ListItem(content=[para])
    list_node = List(ordered=True, items=[list_item])
    blockquote = BlockQuote(content=[list_node])

    doc = Document([blockquote])

    # Should find the deeply nested paragraph
    found = doc.find_node(para.id)
    assert found is not None
    assert found == para
```

#### 3. Validation

Run tests to verify fix:

```bash
uv run pytest tests/unit/test_document_indexing.py -xvs
uv run pytest  # Ensure all existing tests still pass
```

______________________________________________________________________

## 📋 Spec Updates Required

After fixing Finding #5, update spec files to reflect completion and document follow-up work:

### 1. Update tasks.md

**File:** `.kiro/specs/core-api-stabilization/tasks.md`

**Line 294 (Task 1.5 acceptance criteria):**

Current:

```markdown
- [x] Index automatically built/updated when nodes change
```

Add clarification:

```markdown
- [x] Index automatically built/updated when nodes change (recursive indexing of entire tree)
```

**Add after line 300 (new section):**

```markdown
**Implementation Note (2025-11-26):**
Initial implementation only indexed top-level nodes. Fixed to recursively index entire node tree including:
- `List.items` (ListItem children)
- `BlockQuote.content` (nested nodes)
- `Heading.children` (child nodes)
- Any nested structures

This ensures `find_node()` provides true O(1) lookup for all nodes with IDs, not just top-level nodes.
```

### 2. Update tasks.md - Phase 1 Complete Section

**After line 467 (end of Task 1.8), add:**

```markdown
---

## Phase 1 Completion Notes

**Completed:** 2025-11-26
**Status:** ✅ All 8 tasks complete with fixes applied

**Post-Completion Fixes:**
- **Finding #5 (Critical):** Added recursive indexing to `_build_id_index()` to support nested node lookup
- Review document: `docs/archive/specs/core-api-stabilization/reviews/phase1-pr56-review.md`

**Deferred to Follow-up PR (Non-blocking):**
- **Finding #2:** Freeze `ProvenanceContext` dataclass per Task 1.1 spec (~30 min)
- **Finding #3:** Add LRU cache eviction policy per Task 1.3 spec (~2-3 hours)
- **Finding #4:** Update design.md to document List canonicalization excludes ordered status (~15 min)
- **Finding #1:** Decide on hash validation strategy (strict vs flexible parsing) (~1 hour)

**Test Coverage:** 95.50% (889 passing tests, 91 new for Phase 1)
**Performance:** All targets met (ID generation <10% overhead, cache 50%+ speedup)
```

### 3. Update design.md - Document Indexing Section

**File:** `.kiro/specs/core-api-stabilization/design.md`

Find the section on Document ID indexing (search for "Document ID Indexing" or Task 1.5) and clarify:

**Add after the indexing description:**

```markdown
**Recursive Indexing:**
The ID index is built recursively to include all nodes in the document tree, not just top-level nodes. This ensures O(1) lookup for:
- Top-level document nodes
- Nested list items (`List.items`)
- BlockQuote nested content (`BlockQuote.content`)
- Heading children (`Heading.children`)
- Any other nested structures

**Implementation:** The `_build_id_index()` method uses a recursive helper function to traverse the entire node tree and index every node that has an ID.
```

______________________________________________________________________

## 🟡 Future Work (Non-Blocking)

Document these items in a follow-up PR:

### Finding #2: Freeze ProvenanceContext

- **File:** `src/doctk/identity.py` line 534
- **Change:** Add `frozen=True` to `@dataclass` decorator
- **Effort:** 30 minutes
- **Test:** Add immutability test to `tests/unit/test_provenance.py`

### Finding #3: Add Cache Eviction Policy

- **Files:** `src/doctk/identity.py` lines 195-242
- **Change:** Replace `dict` with `OrderedDict`, add LRU eviction with max size 10,000
- **Effort:** 2-3 hours
- **Test:** Add eviction tests to `tests/unit/test_stable_ids.py`
- **Spec Update:** Document cache size limit in design.md

### Finding #4: Update Spec for List Canonicalization

- **File:** `.kiro/specs/core-api-stabilization/design.md`
- **Change:** Update canonical forms table: `list:{items}` (not `list:{type}:{items}`)
- **Rationale:** List ordering (bullets vs numbers) is presentation, like heading level
- **Effort:** 15 minutes (spec update only)

### Finding #1: Hash Validation Strategy Decision

- **Options:**
  - A) Strict: Reject non-16-char hashes in `from_string()` per spec
  - B) Flexible: Update spec to document flexible parsing (8-char, 16-char, 64-char)
  - C) Hybrid: Add `strict=True` parameter
- **Recommendation:** Option B (update spec) - flexible parsing is tested and useful
- **Effort:** 1 hour (decision + implementation or spec update)

______________________________________________________________________

## Validation Checklist

After fixing Finding #5:

- [ ] Run `uv run pytest tests/unit/test_document_indexing.py -xvs` - all new tests pass
- [ ] Run `uv run pytest` - all 889+ tests pass
- [ ] Run `uv run pytest --cov=doctk` - coverage remains >95%
- [ ] Update tasks.md with implementation note
- [ ] Update design.md with recursive indexing clarification
- [ ] Add Phase 1 completion notes to tasks.md
- [ ] Commit with message: `fix(core): implement recursive node ID indexing (Finding #5)`
- [ ] Push and verify CI passes
- [ ] Ready to merge ✅

______________________________________________________________________

## For Kiro Agent

**Priority:** Fix Finding #5 FIRST (blocking)

**Command sequence:**

1. Read this file completely
1. Read the review document for full context
1. Implement the recursive indexing fix in `src/doctk/core.py`
1. Add the 4 test cases to `tests/unit/test_document_indexing.py`
1. Run validation: `uv run pytest tests/unit/test_document_indexing.py -xvs`
1. Update spec files: tasks.md and design.md as specified above
1. Commit: `fix(core): implement recursive node ID indexing (Finding #5)`

**After Finding #5 is fixed:**
The PR is ready to merge. Findings #1-4 will be addressed in a follow-up PR.
