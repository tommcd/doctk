# Tasks.md Updated - Ready for Review

## Status: ✅ UPDATED WITH ALL DESIGN CHANGES

All design changes from 4 review cycles have been incorporated into tasks.md.

______________________________________________________________________

## Updates Applied

### Phase 1: Stable Node Identity

**Task 1.1 - Enhanced:**

- ✅ Added 16-character canonical format requirement
- ✅ Added `to_short_string()` for 8-character display format
- ✅ Added round-trip guarantee requirement
- ✅ Added `__eq__()` and `__hash__()` using first 16 chars
- ✅ Added comprehensive tests for format, round-trip, equality

**Task 1.2 - Expanded:**

- ✅ Renamed to "Canonical Serialization and Hint Generation"
- ✅ Added complete `_generate_hint()` specification
- ✅ Added Unicode NFC normalization requirement
- ✅ Added whitespace normalization (strip, collapse, tabs→spaces)
- ✅ Added hint slugification (lowercase, hyphens, special chars removed)
- ✅ Added 32-character truncation for hints
- ✅ Added fallback for non-text nodes
- ✅ Added tests for Unicode, whitespace, tabs, hint generation

**Task 1.3 - Enhanced:**

- ✅ Added explicit "IN-PROCESS, NON-PERSISTENT cache only" documentation requirement
- ✅ Added warning: "DO NOT persist or share across processes"
- ✅ Added note that cache keys use Python's `hash()` (process-specific)
- ✅ Added documentation that cache keys are NOT stable across runs

**Task 1.6 - Expanded:**

- ✅ Renamed to include "View Mapping"
- ✅ Added `ViewSourceMapping` class requirement
- ✅ Added `Document._view_mappings` list
- ✅ Added `Document.add_view_mapping()` method
- ✅ Added `Document.find_source_position()` method
- ✅ Added identity mappings during parsing
- ✅ Added block-level precision documentation requirement
- ✅ Added note that inline elements inherit parent block spans
- ✅ Duration increased from 3 to 4 days

**Task 1.7 - NEW:**

- ✅ Added new task for text edit ID semantics
- ✅ `Heading.with_text()` generates new ID
- ✅ `Paragraph.with_content()` generates new ID
- ✅ `CodeBlock.with_code()` generates new ID
- ✅ `Heading.promote()` preserves ID
- ✅ `Node.with_metadata()` preserves ID
- ✅ Tests for text edit vs structural change

**Task 1.8 - Enhanced (was 1.7):**

- ✅ Renumbered from 1.7 to 1.8
- ✅ Added tests for 16-char format
- ✅ Added tests for round-tripping
- ✅ Added tests for `to_short_string()`
- ✅ Added tests for Unicode NFC normalization
- ✅ Added tests for whitespace/tab normalization
- ✅ Added tests for hint generation
- ✅ Added tests for hint truncation
- ✅ Added tests for text edit ID changes
- ✅ Added tests for ViewSourceMapping
- ✅ Added tests for cache being in-process only
- ✅ Added new test files: test_view_mapping.py, test_text_edit_semantics.py

______________________________________________________________________

### Phase 6: Operation Registry

**Task 6.3 - Enhanced:**

- ✅ Added `__all__` list requirement in operations.py
- ✅ Listed all public operations explicitly
- ✅ Added Requirements reference (Req 9 AC1, AC2)

**Task 6.5 - Enhanced:**

- ✅ Added completeness test using `__all__` list
- ✅ Added test code example
- ✅ Added Requirements reference (Req 9 AC5)

______________________________________________________________________

### Phase 7: Compatibility Layer

**Task 7.1 - NEW:**

- ✅ Added new task for compatibility mode with safe ID handling
- ✅ Feature flags: `use_stable_ids` and `id_compatibility_mode`
- ✅ `DocumentTreeBuilder.find_node()` with try/except
- ✅ Catches ValueError for invalid stable IDs
- ✅ Falls back to positional ID lookup
- ✅ Returns None in strict mode
- ✅ Tests for both stable and positional IDs
- ✅ Tests for compatibility mode vs strict mode
- ✅ Duration: 3 days

**Tasks 7.2, 7.3, 7.4 - Renumbered:**

- ✅ Old 7.1 → New 7.2 (Deprecation Warnings)
- ✅ Old 7.2 → New 7.3 (Migration Guide)
- ✅ Old 7.3 → New 7.4 (Compatibility Tests)

______________________________________________________________________

### Phase 8: Diagnostic Improvements

**Task 8.2 - Enhanced:**

- ✅ Renamed to include "Data Structures"
- ✅ Added `Diagnostic` dataclass with all fields
- ✅ Added `context_lines` field requirement
- ✅ Added `QuickFix` dataclass
- ✅ Added `TextEdit` dataclass
- ✅ Added helper to generate context_lines from source_span
- ✅ Added test for context_lines
- ✅ Duration increased from 2 to 3 days
- ✅ Added Requirements reference (Req 10 AC1-5)

______________________________________________________________________

## Summary of Changes

### New Tasks Added:

1. **Task 1.7**: Text Edit ID Semantics (2 days)
1. **Task 7.1**: Compatibility Mode with Safe ID Handling (3 days)

### Tasks Significantly Enhanced:

1. **Task 1.1**: NodeId format details (16-char, round-trip, equality)
1. **Task 1.2**: Hint generation + complete canonicalization
1. **Task 1.3**: Cache documentation (in-process only)
1. **Task 1.6**: ViewSourceMapping + block-level precision
1. **Task 1.8**: Comprehensive identity tests
1. **Task 6.3**: __all__ list requirement
1. **Task 6.5**: Completeness test using __all__
1. **Task 8.2**: Diagnostic data structures with context_lines

### Tasks Renumbered:

- Old 1.7 → New 1.8
- Old 7.1 → New 7.2
- Old 7.2 → New 7.3
- Old 7.3 → New 7.4

### Total Task Count:

- **Before**: 41 tasks
- **After**: 43 tasks (2 new tasks added)

### Timeline Impact:

- Phase 1: +1 day (Task 1.6: 3→4 days, Task 1.7 new: 2 days, offset by better estimates)
- Phase 6: No change
- Phase 7: +3 days (Task 7.1 new)
- Phase 8: +1 day (Task 8.2: 2→3 days)
- **Total**: Still ~12 weeks (buffer absorbed new work)

______________________________________________________________________

## Coverage Verification

### All Design Components Now Have Tasks:

✅ **NodeId**:

- 16-char canonical format (Task 1.1)
- to_short_string() (Task 1.1)
- Round-trip guarantee (Task 1.1)
- __eq__ and __hash__ (Task 1.1)

✅ **\_generate_hint()**:

- Complete specification (Task 1.2)
- Slugification rules (Task 1.2)
- 32-char truncation (Task 1.2)
- Fallback logic (Task 1.2)

✅ **\_canonicalize_node()**:

- All node types (Task 1.2)
- Unicode NFC normalization (Task 1.2)
- Whitespace/tab handling (Task 1.2)

✅ **NodeId Cache**:

- In-process documentation (Task 1.3)
- Warning about persistence (Task 1.3)
- Cache key non-stability (Task 1.3)

✅ **Text Edit Semantics**:

- with_text() generates new ID (Task 1.7)
- promote() preserves ID (Task 1.7)
- Tests for both behaviors (Task 1.7)

✅ **ViewSourceMapping**:

- Data structure (Task 1.6)
- Document integration (Task 1.6)
- Projection methods (Task 1.6)

✅ **Diagnostic.context_lines**:

- Field added to dataclass (Task 8.2)
- Helper to generate from span (Task 8.2)
- Tests (Task 8.2)

✅ **Compatibility Mode**:

- find_node() with try/except (Task 7.1)
- Positional ID fallback (Task 7.1)
- Tests for both modes (Task 7.1)

✅ **Operation Registry __all__**:

- List defined (Task 6.3)
- Completeness test (Task 6.5)

______________________________________________________________________

## Requirements Coverage

All 10 requirements now have complete task coverage:

| Requirement | Tasks | Status |
|-------------|-------|--------|
| Req 1: Stable Node Identity | 1.1-1.8 | ✅ Complete |
| Req 2: Internal Operations | 2.1-2.6 | ✅ Complete |
| Req 3: Source Position Tracking | 1.6, 1.8, 8.1-8.4 | ✅ Complete |
| Req 4: Metadata Immutability | 3.1-3.4 | ✅ Complete |
| Req 5: API Paradigm Unification | 4.1-4.4 | ✅ Complete |
| Req 6: Type Safety | 5.1-5.4 | ✅ Complete |
| Req 7: Compatibility | 7.1-7.4 | ✅ Complete |
| Req 8: Performance | 9.1-9.4 | ✅ Complete |
| Req 9: Operation Registry | 6.1-6.5 | ✅ Complete |
| Req 10: Diagnostics | 8.1-8.4 | ✅ Complete |

______________________________________________________________________

## Ready for Review

**Status**: ✅ All design changes incorporated
**Low-hanging fruit**: ✅ Eliminated
**Task count**: 43 tasks across 9 phases
**Timeline**: 12 weeks (realistic with buffer)
**Coverage**: 100% of design components

**Next Step**: Run AI review using TASKS_REVIEW_PROMPT.md and AI_TASKS_REVIEW_PROMPT.txt

The tasks document is now comprehensive and ready for thorough review!
