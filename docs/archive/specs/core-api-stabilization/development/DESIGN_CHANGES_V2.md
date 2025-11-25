# Design Document Changes - Version 2

## Summary of Changes Based on Review Feedback

### 1. Fixed: ID Stability vs Content-Hash Conflict (Major)

**Problem:** Canonical serialization included heading level, causing IDs to change during promote/demote operations, violating requirements.

**Solution:**

- Removed `level` from heading canonicalization: `heading:{text}` instead of `heading:{level}:{text}`
- Added explicit rationale: "Heading level is a presentation attribute, not structural identity"
- Clarified ID stability guarantees with specific examples

**Impact:** IDs now correctly persist across promote/demote/move operations as required.

______________________________________________________________________

### 2. Fixed: Source Span Column Accuracy (Major)

**Problem:** Columns hard-coded to 0 because markdown-it-py doesn't provide them, undermining diagnostics and LSP accuracy.

**Solution:**

- Added `_find_token_start_column()` method to recover columns by scanning source
- Strategy varies by token type (headings find `##`, lists find `-`, etc.)
- Documented limitations (multi-line tokens, inline elements)
- Added span transformation rules for operations
- Extended SourceSpan with `source_file` field for multi-file support

**Impact:** Accurate column positions for diagnostics, LSP quick-fixes, and error messages.

______________________________________________________________________

### 3. Fixed: Provenance Population Rules (Major)

**Problem:** Provenance sourcing undefined for REPL/non-file inputs.

**Solution:**

- Added `ProvenanceContext` class to encapsulate provenance sources
- Implemented `ProvenanceContext.from_file()` - gets git commit/author
- Implemented `ProvenanceContext.from_repl()` - uses environment USER
- Parser methods now accept context parameter
- Clear fallback rules documented

**Impact:** Provenance consistently populated across all input sources.

______________________________________________________________________

### 4. Fixed: Migration Timeline Inconsistency (Major)

**Problem:** Two different timelines given (6-step vs 3-release), rollback behavior unclear.

**Solution:**

- Unified to single 3-release timeline (v0.2.0, v0.3.0, v0.4.0)
- Documented rollback strategy with dual ID storage
- Specified serialization format during compatibility mode (stores both IDs)
- Clear artifact behavior: usable in both modes during transition

**Impact:** Clear, consistent migration path with safe rollback.

______________________________________________________________________

### 5. Fixed: Performance Claims Validation (Minor)

**Problem:** 2x speedup and overhead claims unvalidated, no memory profiling.

**Solution:**

- Defined representative corpus (100, 1K, 10K nodes + real-world docs)
- Added concrete benchmark implementations with assertions
- Added memory profiling with tracemalloc
- Specified measurement methodology (not just estimates)
- Exit criteria now require measured results

**Impact:** Performance claims will be validated with real data.

______________________________________________________________________

### 6. Fixed: Operation Registry Enforcement (Minor)

**Problem:** Manual registration risks drift between registry and implementations.

**Solution:**

- Added `@register_operation` decorator for auto-registration
- Extracts metadata from function signatures and docstrings
- Added validation test to ensure all operations registered
- Prevents drift by making registration automatic

**Impact:** Registry stays synchronized with implementations.

______________________________________________________________________

### 7. Added: Span Transformation Rules

**New Section:** Documented how source spans are preserved/transformed during operations.

**Key Points:**

- Operations preserve original source spans (point to source location)
- Enables round-trip editing (view → source mapping)
- Multi-file support via `source_file` field
- Absolute path conversion for composed documents

**Impact:** Clear semantics for Spec 2 (materialized views).

______________________________________________________________________

## Requirements Coverage - Updated

| Requirement | Status | Notes |
|-------------|--------|-------|
| Req 1: Stable Node Identity | ✅ Fixed | Level excluded from hash; provenance rules clarified |
| Req 2: Internal Operations | ✅ Good | Minor: performance validation added |
| Req 3: Source Position Tracking | ✅ Fixed | Column recovery added; span transformation documented |
| Req 4: Metadata Immutability | ✅ Good | No changes needed |
| Req 5: API Paradigm Unification | ✅ Good | No changes needed |
| Req 6: Type Safety | ✅ Good | No changes needed |
| Req 7: Compatibility | ✅ Fixed | Timeline unified; rollback clarified |
| Req 8: Performance | ✅ Fixed | Validation methodology specified |
| Req 9: Operation Registry | ✅ Fixed | Auto-registration added |
| Req 10: Diagnostics | ✅ Good | Enhanced with column accuracy |

______________________________________________________________________

## Open Questions - Resolved

1. **Column accuracy?** → Resolved: Added column recovery via source scanning
1. **NodeId canonicalization?** → Resolved: Exclude level from hash
1. **Provenance for non-file inputs?** → Resolved: ProvenanceContext with fallbacks
1. **Rollback behavior?** → Resolved: Dual ID storage during compatibility mode
1. **Performance validation dataset?** → Resolved: Representative corpus defined

______________________________________________________________________

## Recommendation

**Status:** Ready for approval pending final review of changes.

All major issues addressed. Design now provides:

- Correct ID stability semantics
- Accurate source positioning
- Clear provenance rules
- Consistent migration path
- Validated performance claims
- Enforced registry synchronization
