# Codex Review - Fixes Applied

## Summary

All 3 real issues identified in Codex's review have been addressed. The other 4 issues were either false positives (tasks were already correct) or already fixed in previous reviews.

______________________________________________________________________

## ✅ Fix 1: Performance Targets Updated (Task 9.3)

**Issue:** Tasks said "10K nodes \<100ms" but design specifies "1s render, 200ms interaction"

**Fix Applied:** Task 9.3 now includes:

```markdown
- [ ] Existing performance budgets met (1s render, 200ms interaction)
- [ ] Large document handling (10K nodes) within performance budget
```

**Location:** `tasks.md` lines 1419-1421

**Status:** ✅ COMPLETE

______________________________________________________________________

## ✅ Fix 2: Dual-ID Serialization Added (Task 7.2)

**Issue:** Missing task for serializing both stable and positional IDs during compatibility mode

**Fix Applied:** Added Task 7.2 with:

- JSON serialization with both `id` (stable) and `legacy_id` (positional) fields
- Deserialization handling both formats
- Rollback testing from stable to positional IDs
- Forward migration testing
- Round-trip verification

**Location:** `tasks.md` lines 1137-1227

**Status:** ✅ COMPLETE

______________________________________________________________________

## ✅ Fix 3: Text Edit Semantics Completed (Task 1.7)

**Issue:** Task 1.7 missing `CodeBlock.with_code()` and other node types

**Fix Applied:** Task 1.7 now includes:

```markdown
- [ ] `CodeBlock.with_code()` method generates new NodeId
- [ ] `CodeBlock.with_language()` method generates new NodeId
- [ ] `ListItem.with_content()` method generates new NodeId
- [ ] All node types with canonical fields have `with_*` methods
```

Plus comprehensive test for CodeBlock:

```python
def test_code_block_edit_changes_id():
    """Verify code edits generate new IDs."""
    code_block = CodeBlock(language="python", code="print('hello')")
    original_id = code_block.id

    edited = code_block.with_code("print('world')")

    assert edited.id != original_id
```

**Location:** `tasks.md` lines 327-329, 365-377

**Status:** ✅ COMPLETE

______________________________________________________________________

## False Positives (No Action Needed)

### ❌ Issue 1: NodeId Format

**Codex Claim:** Tasks diverge from design (64-char vs 16-char)
**Reality:** Design DOES specify 64-char storage with 16-char canonical format
**Status:** Tasks were already correct

### ❌ Issue 2: Caching Approach

**Codex Claim:** Tasks use hash() but design uses LRU on canonical strings
**Reality:** Design DOES specify hash() keys for cache
**Status:** Tasks were already correct

______________________________________________________________________

## Already Fixed (Previous Reviews)

### ✅ Issue 7: Diagnostics Scope

**Codex Claim:** Colorized output not in design
**Reality:** Already marked as "(Optional)" in Task 8.1 after GPT-5.1 review
**Status:** Already fixed

______________________________________________________________________

## By Design (Acknowledged)

### ⚠️ Issue 4: Inline Column Precision

**Codex Claim:** Block-level only, no inline refinement
**Reality:** This is intentional scope limitation documented in requirements
**Status:** No change needed - by design

______________________________________________________________________

## Verification

All fixes have been applied and verified:

1. ✅ Task 9.3 performance targets align with design (1s render, 200ms interaction)
1. ✅ Task 7.2 implements dual-ID serialization for rollback support
1. ✅ Task 1.7 includes all node types with canonical fields (including CodeBlock)

**Tasks document is now fully aligned with design and requirements.**

______________________________________________________________________

## Next Steps

Ready for final tasks document approval.
