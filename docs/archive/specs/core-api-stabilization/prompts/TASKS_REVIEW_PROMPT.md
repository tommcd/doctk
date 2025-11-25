# Tasks Review Prompt for AI Agents

## Task

Review the tasks document (`.kiro/specs/core-api-stabilization/tasks.md`) against the requirements (`.kiro/specs/core-api-stabilization/requirements.md`) and design (`.kiro/specs/core-api-stabilization/design.md`) to ensure completeness, correctness, and implementability.

## Review Checklist

### 1. Requirements Coverage

For each of the 10 requirements, verify:

- [ ] **Requirement 1 (Stable Node Identity)**: Are all 7 acceptance criteria covered by tasks?

  - NodeId with content-hash + hint
  - ID preservation across edits
  - Re-parsing consistency
  - ID retention during promote/demote/move
  - New ID when canonical content changes
  - Provenance metadata attachment
  - Provenance updates during transforms

- [ ] **Requirement 2 (Internal Operations)**: Are all 5 acceptance criteria covered?

  - InternalOperations returns Document objects
  - No serialization in internal layer
  - ID preservation through operations
  - DSL/REPL use internal operations
  - JSON-RPC wraps internal operations

- [ ] **Requirement 3 (Source Position Tracking)**: Are all 6 acceptance criteria covered?

  - Parser attaches spans with block-level precision
  - Operations preserve/update spans
  - Errors report locations with block-level precision
  - LSP uses spans for positioning
  - Materialized views maintain mappings
  - Inline elements inherit block spans

- [ ] **Requirement 4 (Metadata Immutability)**: Are all 5 acceptance criteria covered?

  - Deep-copy on transform
  - Mutations don't affect originals
  - No shared references
  - Tests verify immutability
  - Acceptable performance (\<15% overhead)

- [ ] **Requirement 5 (API Paradigm Unification)**: Are all 4 acceptance criteria covered?

  - by_id() bridge function
  - Imperative delegates to declarative
  - Unified operation metadata
  - Documentation explains both paradigms

- [ ] **Requirement 6 (Type Safety)**: Are all 5 acceptance criteria covered?

  - TypeGuards for node types
  - Generic Document[TNode]
  - Type-safe select operations
  - mypy/pyright validation
  - Tests verify type narrowing

- [ ] **Requirement 7 (Compatibility)**: Are all 5 acceptance criteria covered?

  - Feature flags (use_stable_ids, id_compatibility_mode)
  - Dual-mode support
  - Deprecation warnings
  - Tests in both modes
  - Migration guide

- [ ] **Requirement 8 (Performance)**: Are all 5 acceptance criteria covered?

  - NodeId generation \<1ms per node
  - Deep-copy overhead \<15%
  - Internal ops 2x faster than JSON-RPC
  - Large document handling (10K nodes) \<100ms
  - Memory usage within bounds

- [ ] **Requirement 9 (Operation Registry)**: Are all 5 acceptance criteria covered?

  - Registry with metadata
  - Decorator-based registration
  - Discovery API
  - Consumers (Python, DSL, LSP, docs)
  - Completeness tests

- [ ] **Requirement 10 (Diagnostics)**: Are all 5 acceptance criteria covered?

  - Parsing errors with location
  - Operation errors with ID + location
  - Type mismatch explanations
  - LSP quick-fixes
  - Structured metadata

### 2. Design Alignment

Check that tasks implement all design components:

- [ ] **NodeId Implementation**:

  - 16-character canonical string format
  - Round-trip guarantee (from_string/\_\_str\_\_)
  - to_short_string() for display
  - \_\_eq\_\_ and \_\_hash\_\_ use first 16 chars
  - Full 64-char hash stored internally
  - Caching with \_get_node_cache_key()
  - clear_node_id_cache() for testing

- [ ] **Hint Generation**:

  - \_generate_hint() function specified
  - Deterministic slugification
  - 32-character truncation
  - Fallback for non-text nodes
  - Examples and tests

- [ ] **Canonicalization**:

  - Complete specification for all node types
  - Unicode NFC normalization
  - Whitespace/tab handling
  - Deterministic output
  - Tests for normalization variants

- [ ] **Text Edit Semantics**:

  - Methods modifying canonical fields generate new IDs
  - with_text() generates new ID
  - promote() preserves ID
  - Tests verify behavior

- [ ] **Compatibility Mode**:

  - find_node() with try/except for positional IDs
  - Safe fallback to positional lookup
  - Tests for both ID schemes

- [ ] **Source Spans**:

  - Block-level column recovery
  - \_find_token_start_column()
  - \_find_token_end_column()
  - ViewSourceMapping for materialized views
  - Tests for block-level accuracy

- [ ] **Diagnostics**:

  - Diagnostic with context_lines field
  - QuickFix and TextEdit classes
  - DiagnosticCollector
  - LSP integration examples
  - Concrete error scenarios

- [ ] **Type Safety**:

  - Generic Document[TNode]
  - TypeGuard functions (is_heading, is_paragraph)
  - Typed select() operation
  - mypy configuration

- [ ] **Operation Registry**:

  - \_\_all\_\_ list in operations.py
  - Decorator-based registration
  - Completeness test using \_\_all\_\_

### 3. Task Quality

For each task, verify:

- [ ] **Clear Objective**: Does the task description clearly state what needs to be implemented?
- [ ] **Actionable**: Can a developer start work immediately with the information provided?
- [ ] **Testable**: Are acceptance criteria specific and verifiable?
- [ ] **Scoped**: Is the task appropriately sized (not too large or too small)?
- [ ] **Dependencies**: Are dependencies on other tasks clearly stated?
- [ ] **Files Specified**: Are files to create/modify explicitly listed?
- [ ] **Testing Included**: Are test examples or strategies provided?
- [ ] **Requirements Linked**: Does the task reference specific requirements?

### 4. Phase Organization

Check phase structure:

- [ ] **Logical Grouping**: Are related tasks grouped together?
- [ ] **Dependencies Respected**: Do tasks build on previous tasks?
- [ ] **Parallelization Opportunities**: Are independent tasks identified?
- [ ] **Duration Estimates**: Are time estimates realistic?
- [ ] **Critical Path**: Is the critical path through phases clear?
- [ ] **Checkpoints**: Are there validation checkpoints between phases?

### 5. Completeness Checks

Verify nothing is missing:

- [ ] **All Design Components**: Every component in design.md has corresponding tasks
- [ ] **All Helper Functions**: \_generate_hint, \_canonicalize_node, \_get_node_cache_key, etc.
- [ ] **All Data Structures**: NodeId, Provenance, SourceSpan, ViewSourceMapping, Diagnostic, etc.
- [ ] **All Integration Points**: Parser, DSL, REPL, LSP, JSON-RPC bridge
- [ ] **All Test Types**: Unit tests, integration tests, performance tests, compatibility tests
- [ ] **All Documentation**: API docs, migration guide, performance validation

### 6. Implementation Feasibility

Assess practicality:

- [ ] **Timeline Realistic**: Is 12 weeks achievable for the scope?
- [ ] **Task Sizing**: Are tasks 1-3 days each (not too large)?
- [ ] **Skill Requirements**: Are required skills reasonable for the team?
- [ ] **Tool Availability**: Are all required tools/libraries available?
- [ ] **Risk Mitigation**: Are high-risk tasks identified and mitigated?
- [ ] **Testing Strategy**: Is test coverage adequate without being excessive?

### 7. Potential Issues to Flag

Look for:

- [ ] **Missing Tasks**: Design components without corresponding tasks
- [ ] **Orphaned Tasks**: Tasks that don't map to requirements or design
- [ ] **Circular Dependencies**: Tasks that depend on each other
- [ ] **Unrealistic Estimates**: Tasks that seem too short or too long
- [ ] **Missing Tests**: Tasks without test acceptance criteria
- [ ] **Vague Descriptions**: Tasks that aren't actionable
- [ ] **Scope Creep**: Tasks that go beyond the design
- [ ] **Missing Integration**: Tasks that don't connect to existing code

## Review Output Format

Provide your review in this format:

### Summary

- **Overall Assessment**: Approve / Changes Needed / Reject
- **Confidence Level**: High / Medium / Low
- **Key Strengths**: (3-5 bullet points)
- **Key Concerns**: (3-5 bullet points)

### Detailed Findings

For each issue found:

**Severity**: Critical / Major / Minor
**Location**: (Phase and task number)
**Issue**: (Clear description of the problem)
**Impact**: (What happens if not addressed)
**Recommendation**: (Specific fix or improvement)

### Requirements Coverage Matrix

| Requirement | Covered? | Missing Tasks | Notes |
|-------------|----------|---------------|-------|
| Req 1: Stable Node Identity | ✅/⚠️/❌ | | |
| Req 2: Internal Operations | ✅/⚠️/❌ | | |
| ... | | | |

### Design Component Coverage

| Design Component | Tasks | Status | Notes |
|------------------|-------|--------|-------|
| NodeId (16-char format) | 1.1, 1.2 | ✅/⚠️/❌ | |
| \_generate_hint() | ? | ❌ | Missing |
| ... | | | |

### Phase Analysis

For each phase:

- **Duration**: Realistic / Too Short / Too Long
- **Dependencies**: Clear / Unclear / Circular
- **Completeness**: Complete / Missing Tasks
- **Notes**: (Any concerns or suggestions)

### Open Questions

List any questions that need clarification:

1. Should Task X include Y, or is that covered elsewhere?
1. Is the timeline for Phase Z realistic given dependencies?
1. ...

### Final Recommendation

**Recommendation**: Approve / Request Changes / Reject

**Rationale**: (2-3 sentences explaining your recommendation)

**Priority Fixes**: (If changes needed, list top 3-5 fixes in priority order)

**Optional Improvements**: (Nice-to-have improvements that aren't blockers)

______________________________________________________________________

## Focus Areas

Pay special attention to:

1. **New Design Components**: Ensure tasks cover all components added in design reviews:

   - \_generate_hint() specification
   - NodeId cache documentation
   - [PLANNED] `Diagnostic.context_lines` field
   - ViewSourceMapping for materialized views
   - Text edit ID semantics

1. **Testing Coverage**: Verify tests for:

   - NodeId round-tripping
   - Canonicalization normalization (Unicode, whitespace)
   - Compatibility mode positional ID fallback
   - Block-level source span accuracy
   - Diagnostic context generation

1. **Integration Points**: Check tasks for:

   - Parser → NodeId generation
   - DSL → Internal operations
   - REPL → Internal operations
   - LSP → Diagnostics with spans
   - JSON-RPC → Internal operations wrapper

1. **Performance Validation**: Ensure tasks include:

   - Benchmarks for all performance targets
   - Memory profiling
   - Comparison with baseline (JSON-RPC)
   - Representative corpus testing (100/1K/10K nodes)

1. **Migration Path**: Verify tasks for:

   - Feature flags implementation
   - Dual-mode DocumentTreeBuilder
   - Deprecation warnings
   - Migration guide creation
   - Rollback mechanism

______________________________________________________________________

## Example Good Task

````markdown
### Task 1.2: Implement Canonical Serialization and Hint Generation

**Duration:** 2 days
**Priority:** Critical

**Description:**
Implement canonical serialization for all node types and the hint generation function for human-readable NodeIds.

**Acceptance Criteria:**
- [ ] `_canonicalize_node()` function for all node types (Heading, Paragraph, CodeBlock, ListItem, List, BlockQuote)
- [ ] Unicode NFC normalization applied
- [ ] Whitespace normalized (strip, collapse, tabs→spaces)
- [ ] Heading canonicalization excludes level
- [ ] `_generate_hint()` function with deterministic slugification
- [ ] Hint truncated to 32 characters
- [ ] Fallback to node type for non-text nodes
- [ ] Tests for normalization variants (Unicode, whitespace, tabs)
- [ ] Tests for hint generation with examples

**Files to Modify:**
- `src/doctk/core/identity.py`

**Dependencies:** Task 1.1

**Requirements:** Req 1 AC1, AC3, AC5

**Testing:**
```python
def test_canonicalization_unicode():
    h1 = Heading(level=2, text="café")  # Single char
    h2 = Heading(level=2, text="café")  # Combining char
    assert _canonicalize_node(h1) == _canonicalize_node(h2)

def test_hint_generation():
    h = Heading(level=2, text="API Reference Guide")
    hint = _generate_hint(h)
    assert hint == "api-reference-guide"
    assert len(hint) <= 32
````

```

## Example Issue to Flag

**Severity**: Major
**Location**: Phase 1, Task 1.2
**Issue**: Task implements `_canonicalize_node()` but doesn't include `_generate_hint()` which is referenced in the design and required for NodeId generation.
**Impact**: NodeId.from_node() will fail because _generate_hint() is undefined.
**Recommendation**: Add _generate_hint() implementation to Task 1.2 with acceptance criteria for deterministic slugification, 32-char truncation, and fallback rules.
```
