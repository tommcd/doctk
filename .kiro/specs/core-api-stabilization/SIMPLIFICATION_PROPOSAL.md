# Simplification Proposal: Remove Backward Compatibility

## Problem

The spec includes extensive backward compatibility work (Requirement 7, entire Phase 7) to migrate from "positional IDs" (like "h2-0") to stable content-based IDs.

**But there are no users yet!** This is v0.1 (alpha/POC). We can simply delete the old system and implement only the new one.

______________________________________________________________________

## Current Situation

- **Requirement 7:** "Compatibility and Migration" - 5 acceptance criteria about dual-ID support, rollback, deprecation warnings
- **Phase 7:** "Compatibility Layer" - 6 tasks (7.1-7.6) about compatibility mode, dual-ID serialization, migration guides, deprecation warnings
- **Total overhead:** ~1 week of work + ongoing maintenance burden

______________________________________________________________________

## Proposed Changes

### 1. Remove Requirement 7 Entirely

Delete the entire "Compatibility and Migration" requirement. We don't need:

- Compatibility flags
- Dual ID schemes
- Deprecation warnings
- Migration guides
- Rollback mechanisms

### 2. Remove Phase 7 Entirely

Delete all 6 tasks:

- ~~Task 7.1: Implement Compatibility Mode~~
- ~~Task 7.2: Define Document Serialization Interface~~ (keep this, but move it)
- ~~Task 7.3: Implement Dual-ID Serialization~~
- ~~Task 7.4: Implement Deprecation Warnings~~
- ~~Task 7.5: Create Migration Guide~~
- ~~Task 7.6: Add Compatibility Tests~~

**Exception:** Task 7.2 (Define Document Serialization Interface) is still needed, but should be moved to Phase 1 or 2 where serialization is first used.

### 3. Renumber Everything

**Requirements:**

- Req 1-6: Unchanged
- ~~Req 7: Compatibility~~ → DELETED
- Req 8 → Req 7: Performance Preservation
- Req 9 → Req 8: Operation Registry Unification
- Req 10 → Req 9: Diagnostic Improvements

**Phases:**

- Phase 1-6: Unchanged
- ~~Phase 7: Compatibility Layer~~ → DELETED
- Phase 8 → Phase 7: Diagnostic Improvements
- Phase 9 → Phase 8: Performance Validation

### 4. Move Serialization Task

Move Task 7.2 (Define Document Serialization Interface) to Phase 2 as Task 2.7, since that's when we first need serialization for the JSON-RPC bridge.

______________________________________________________________________

## Benefits

1. **Saves 1 week** of implementation time
1. **Removes complexity** - no dual-ID system, no compatibility flags
1. **Cleaner codebase** - only one ID system to maintain
1. **Simpler testing** - no compatibility mode tests
1. **No technical debt** - no deprecated APIs to remove later
1. **Faster to v0.2** - ship sooner with less code

______________________________________________________________________

## Risks

**None.** There are no users yet. The current v0.1 is alpha/POC. We're free to make breaking changes.

______________________________________________________________________

## Updated Counts

**Before:**

- 10 requirements
- 9 phases
- 45 tasks
- 12 weeks

**After:**

- 9 requirements (removed Req 7)
- 8 phases (removed Phase 7)
- 39 tasks (removed 6 tasks from Phase 7)
- 11 weeks (saved 1 week)

______________________________________________________________________

## Recommendation

**APPROVE THIS SIMPLIFICATION**

Remove all backward compatibility work. Implement only the new stable ID system. Ship faster with less complexity.

______________________________________________________________________

## Implementation

If approved, I will:

1. Delete Requirement 7 from requirements.md
1. Renumber Requirements 8-10 to 7-9
1. Delete Phase 7 from tasks.md
1. Move Task 7.2 to Phase 2 as Task 2.7
1. Renumber Phases 8-9 to 7-8
1. Update all cross-references
1. Update design.md to remove compatibility mode sections
1. Update task counts in SPEC_COMPLETE.md

**Estimated time:** 30 minutes
