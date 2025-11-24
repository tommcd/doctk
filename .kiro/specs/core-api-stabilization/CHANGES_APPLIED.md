# Changes Applied - Design V3 Fixes

## Summary

All fixes from DESIGN_FIXES_V3.md have been successfully applied to requirements.md and design.md.

**Status:** ✅ Ready for final approval

______________________________________________________________________

## Changes Applied to requirements.md

### 1. Requirement 1.5 - NodeId Semantics (MAJOR)

**Changed:**

```
OLD: 5. WHEN a node is deleted and recreated, THE System SHALL assign a new ID to reflect the new identity
NEW: 5. WHEN a node's canonical content changes, THE System SHALL assign a new ID to reflect the changed identity
```

**Added Note:**

> Acceptance Criterion 5 clarifies that nodes with identical canonical content (after normalization) are treated as the same logical entity and receive the same ID. This supports undo/redo, document merging, and transclusion use cases. Provenance metadata tracks creation and modification history separately from identity.

### 2. Requirement 3 - Source Position Tracking (MAJOR)

**Changed AC1:**

```
OLD: 1. WHEN a document is parsed, THE Parser SHALL attach source spans (line, column ranges) to each AST node
NEW: 1. WHEN a document is parsed, THE Parser SHALL attach source spans (line, column ranges) to each block-level AST node with block-level precision
```

**Changed AC3:**

```
OLD: 3. WHEN an error occurs during parsing or execution, THE System SHALL report the exact source location
NEW: 3. WHEN an error occurs during parsing or execution, THE System SHALL report the source location with block-level precision
```

**Added AC6:**

```
6. WHEN inline elements are parsed, THE System SHALL inherit source location from their containing block
```

**Added Note:**

> "Block-level precision" means accurate line and column positions for structural elements (headings, paragraphs, lists, code blocks). Inline elements (bold, links, inline code) inherit their parent block's position. This is sufficient for LSP diagnostics, go-to-definition, and most editing operations. Inline-level precision can be added in a future enhancement if needed.

______________________________________________________________________

## Changes Applied to design.md

### 1. NodeId String Format and Round-Tripping (MAJOR)

**Updated NodeId class:**

- `content_hash` now stores full 64-char SHA-256 hash
- `__str__()` returns 16-character canonical format
- Added `to_short_string()` for 8-character display format
- `from_string()` requires exactly 16 characters
- `__eq__()` and `__hash__()` use first 16 characters for consistency
- **Round-trip guaranteed:** `NodeId.from_string(str(node_id)) == node_id`

**Added caching:**

- Module-level `_node_id_cache` dictionary
- `_get_node_cache_key()` for lightweight cache keys
- `clear_node_id_cache()` for testing

### 2. Canonical Serialization Specification (MAJOR)

**Added complete specification:**

- Normalization rules (Unicode NFC, whitespace, tabs, line endings)
- Complete table of node types with canonical forms
- Full `_canonicalize_node()` implementation with `normalize_text()` helper
- Handles all node types (Heading, Paragraph, CodeBlock, ListItem, List, BlockQuote)

### 3. Text Edit ID Stability Semantics (MAJOR)

**Added "Text Edit Semantics" section:**

- Explicit rule: Operations modifying canonical fields MUST generate new NodeId
- Table of fields in canonical form per node type
- Code examples showing text edit → new ID, structural change → same ID
- Implementation examples for `with_text()` and `promote()` methods

### 4. Compatibility Mode Positional ID Handling (MAJOR)

**Updated `DocumentTreeBuilder.find_node()`:**

- Added try/except around `NodeId.from_string()`
- Catches `ValueError` for invalid stable ID formats
- Falls back to positional ID lookup in compatibility mode
- Returns None in strict mode for invalid IDs
- Comprehensive docstring explaining behavior

### 5. Implementation Plan Timeline (MAJOR)

**Added timeline clarification:**

- **Total Duration:** 12 weeks (wall-clock time with single team)
- Documented parallelization opportunities
- Explained how 2-3 developers could compress to 9-10 weeks
- Conservative estimate accounts for sequential execution and integration complexity

### 6. Diagnostic System Concrete Examples (MAJOR)

**Added "Concrete Examples" section under Requirement 10:**

- AC1: Parsing error example (invalid heading level)
- AC2: Operation error example (promote at minimum level)
- AC3: Type mismatch example (wrong node type)
- AC4: Complete LSP integration example with quick-fix conversion
- Representative quick-fix scenarios (4 examples)

### 7. Operation Registry Completeness Test (MINOR)

**Updated registry completeness approach:**

- Added `__all__` list in `doctk/operations.py`
- Updated test to iterate over `__all__` instead of `dir()`
- More robust and explicit about public API

### 8. Generic Type Support (MINOR)

**Added concrete generic types example:**

- `Document[TNode]` generic class definition
- `select()` function with TypeGuard parameter
- Complete usage example showing type-safe filtering
- IDE autocomplete benefits documented

______________________________________________________________________

## Verification Checklist

- ✅ All 10 issues from review addressed
- ✅ Requirements.md updated (2 changes)
- ✅ Design.md updated (8 changes)
- ✅ Round-trip NodeId guaranteed
- ✅ Canonicalization fully specified
- ✅ Text edit semantics clarified
- ✅ Compatibility mode error handling added
- ✅ Timeline corrected to 12 weeks
- ✅ Diagnostic examples added
- ✅ Registry test improved
- ✅ Generic types example added

______________________________________________________________________

## Reviewer Feedback

> "The only follow-through I'd watch for in implementation is keeping the config/compatibility flags consistent across modules, but conceptually, V3 fixes are sufficient to resolve the earlier review and I'd move to 'approve' once these edits are applied to requirements.md and design.md."

**Status:** All edits applied. Ready for approval.

______________________________________________________________________

## Next Steps

1. ✅ Requirements.md updated
1. ✅ Design.md updated
1. ⏭️ Await final approval
1. ⏭️ Begin implementation using tasks.md

______________________________________________________________________

## Files Modified

1. `.kiro/specs/core-api-stabilization/requirements.md`

   - Updated Req 1.5 (NodeId semantics)
   - Updated Req 3 AC1, AC3 (block-level precision)
   - Added Req 3 AC6 (inline elements)
   - Added notes explaining scope

1. `.kiro/specs/core-api-stabilization/design.md`

   - Updated NodeId class (string format, round-trip, caching)
   - Added complete canonicalization specification
   - Added text edit semantics section
   - Updated compatibility mode with error handling
   - Added timeline clarification
   - Added diagnostic concrete examples
   - Updated registry completeness test
   - Added generic types example

1. `.kiro/specs/core-api-stabilization/tasks.md`

   - Already created with 12-week timeline
   - No changes needed (already aligned with design)

______________________________________________________________________

## Implementation Notes

**Key points for implementation:**

1. **Config flags consistency:** Ensure `use_stable_ids` and `id_compatibility_mode` are consistently checked across all modules (parser, operations, LSP, DSL)

1. **NodeId format:** Always use 16-character canonical format for persistence and lookup. Use `to_short_string()` only for UI display.

1. **Text edits:** Any method modifying canonical fields must call `NodeId.from_node()` to generate new ID.

1. **Compatibility mode:** Always wrap `NodeId.from_string()` in try/except when accepting user input.

1. **Testing:** Add tests for all new behaviors (round-trip, canonicalization normalization, positional ID fallback, etc.)
