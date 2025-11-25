# Codex Review Response

## Review Assessment

**Overall:** "Request Changes"
**Confidence:** Medium

## Issues Analysis

### Issue 1: NodeId Format Mismatch ❌ FALSE POSITIVE

**Codex Claim:** "Tasks require 64-char hashes... design uses 16-char hashes end-to-end"

**Reality:** Design DOES specify 64-char storage with 16-char canonical format:

- design.md line 88: `content_hash: str  # Full SHA-256 hex (64 chars) stored internally`
- design.md line 94-98: `__str__()` returns 16-char prefix
- design.md line 176-180: `__eq__()` and `__hash__()` use first 16 chars

**Conclusion:** ✅ Tasks ARE aligned with design. No changes needed.

______________________________________________________________________

### Issue 2: Caching Approach Diverges ❌ FALSE POSITIVE

**Codex Claim:** "Tasks add module-level dict keyed by hash()... design uses LRU on canonical strings"

**Reality:** Design DOES specify `hash()` keys:

- design.md line 184-199: `_get_node_cache_key()` uses `hash(node.text)`, `hash(node.content)`
- design.md line 186-189: Explicit note that cache keys use Python's `hash()` which is randomized

**Conclusion:** ✅ Tasks ARE aligned with design. No changes needed.

______________________________________________________________________

### Issue 3: Performance Targets Mismatch ✅ TRUE ISSUE

**Codex Claim:** "Tasks set 10K nodes \<100ms... design sets 1s render/200ms interaction"

**Reality:**

- tasks.md Task 9.3: "Large document handling (10K nodes) \<100ms"
- design.md line 2115: "Existing performance budgets met (1s render, 200ms interaction)"

**Conclusion:** ✅ MISMATCH - Need to align targets.

**Fix Required:** Update Task 9.3 to match design's performance budgets.

______________________________________________________________________

### Issue 4: Compatibility Serialization Missing ✅ TRUE ISSUE

**Codex Claim:** "Tasks don't include storing both stable and positional IDs in serialized artifacts"

**Reality:**

- design.md line 2414-2424: Shows JSON format with both `"id"` and `"legacy_id"` fields
- tasks.md Phase 7: No task for dual-ID serialization

**Conclusion:** ✅ MISSING - Need to add task for dual-ID serialization.

**Fix Required:** Add task in Phase 7 for serialization format with both IDs.

______________________________________________________________________

### Issue 5: Text Edit Semantics Incomplete ✅ TRUE ISSUE

**Codex Claim:** "Task 1.7 doesn't mention with_code for CodeBlock"

**Reality:**

- Task 1.7 has `Heading.with_text()` and `Paragraph.with_content()`
- Missing `CodeBlock.with_code()` and other node types

**Conclusion:** ✅ INCOMPLETE - Need to add all canonical field methods.

**Fix Required:** Update Task 1.7 to include all node types.

______________________________________________________________________

### Issue 6: Inline Column Precision ⚠️ ACKNOWLEDGED

**Codex Claim:** "Block-level only; no inline refinement"

**Reality:** This is by design (block-level precision is the scope).

**Conclusion:** ⚠️ ACKNOWLEDGED - Already documented as block-level scope in requirements and design.

**No Fix Required:** This is intentional scope limitation.

______________________________________________________________________

### Issue 7: Diagnostics Scope Creep ✅ ALREADY FIXED

**Codex Claim:** "Adds colorized output... not in design"

**Reality:** Already fixed in response to GPT-5.1 review:

- Task 8.1 now marks color as "(Optional)"
- Added note: "not required for spec acceptance"

**Conclusion:** ✅ ALREADY FIXED.

______________________________________________________________________

## Summary of Real Issues

| Issue | Status | Action Required |
|-------|--------|-----------------|
| 1. NodeId format | ❌ False | None - tasks correct |
| 2. Caching approach | ❌ False | None - tasks correct |
| 3. Performance targets | ✅ True | Fix Task 9.3 |
| 4. Dual-ID serialization | ✅ True | Add task in Phase 7 |
| 5. Text edit semantics | ✅ True | Update Task 1.7 |
| 6. Inline precision | ⚠️ By design | None - intentional |
| 7. Diagnostics scope | ✅ Fixed | None - already done |

______________________________________________________________________

## Fixes Required

### Fix 1: Update Performance Targets (Task 9.3)

**Current:**

```
- [ ] Large document handling (10K nodes) <100ms
```

**Should be:**

```
- [ ] Existing performance budgets met (1s render, 200ms interaction)
- [ ] Large document handling (10K nodes) within performance budget
```

______________________________________________________________________

### Fix 2: Add Dual-ID Serialization Task (Phase 7)

**New Task 7.X:**

````markdown
### Task 7.X: Implement Dual-ID Serialization for Compatibility

**Duration:** 2 days
**Priority:** High

**Description:**
Implement serialization format that includes both stable IDs and positional IDs during compatibility mode to enable rollback.

**Acceptance Criteria:**
- [ ] JSON serialization includes both `id` (stable) and `legacy_id` (positional) fields
- [ ] Deserialization handles both ID formats
- [ ] Rollback from stable to positional IDs works correctly
- [ ] Tests verify round-trip with both ID schemes
- [ ] Migration path documented

**Files to Modify:**
- `src/doctk/core.py` (Document serialization)
- `src/doctk/parsers/markdown.py` (if applicable)

**Requirements:** Req 7 AC3, AC4, AC5

**Testing:**
```python
def test_dual_id_serialization():
    """Test serialization includes both IDs."""
    doc = Document([Heading(level=2, text="Test")])

    # In compatibility mode
    config.id_compatibility_mode = True
    json_str = doc.to_json()
    data = json.loads(json_str)

    # Should have both IDs
    assert "id" in data["nodes"][0]  # Stable ID
    assert "legacy_id" in data["nodes"][0]  # Positional ID

def test_rollback_from_stable_to_positional():
    """Test rollback works with dual IDs."""
    # Create doc with stable IDs
    config.use_stable_ids = True
    doc = Document.from_string("## Test")
    json_str = doc.to_json()

    # Rollback to positional
    config.use_stable_ids = False
    doc2 = `Document.from_json`(json_str)  # [PLANNED]

    # Should use legacy_id
    assert doc2.nodes[0].id == "h2-0"
````

```

---

### Fix 3: Update Text Edit Semantics (Task 1.7)

**Add to Acceptance Criteria:**
```

- [ ] `CodeBlock.with_code()` method generates new NodeId
- [ ] `CodeBlock.with_language()` method generates new NodeId
- [ ] `ListItem.with_content()` method generates new NodeId
- [ ] All node types with canonical fields have with\_\* methods

````

**Add to Testing:**
```python
def test_code_block_edit_changes_id():
    """Verify code edits generate new IDs."""
    code_block = CodeBlock(language="python", code="print('hello')")
    original_id = code_block.id

    edited = code_block.with_code("print('world')")

    assert edited.id != original_id
    assert edited.code == "print('world')"
    assert edited.language == code_block.language
````

______________________________________________________________________

## Conclusion

**Real Issues:** 3 (performance targets, dual-ID serialization, text edit completeness)
**False Positives:** 2 (NodeId format, caching - tasks ARE correct)
**Already Fixed:** 1 (diagnostics scope)
**By Design:** 1 (inline precision)

**Action:** Apply the 3 fixes above, then tasks.md will be fully aligned with design and requirements.
