# Design Review Prompt for AI Agents

## Task

Review the design document (`.kiro/specs/core-api-stabilization/design.md`) against the requirements document (`.kiro/specs/core-api-stabilization/requirements.md`) to ensure completeness, correctness, and feasibility.

## Review Checklist

### 1. Requirements Coverage

For each of the 10 requirements, verify:

- [ ] **Requirement 1 (Stable Node Identity and Provenance)**: Does the NodeId design adequately address all 7 acceptance criteria? Is the content-hash + hint approach sound?
- [ ] **Requirement 2 (Internal Operations Layer)**: Does the InternalOperations design eliminate serialization overhead? Are all 5 acceptance criteria met?
- [ ] **Requirement 3 (Source Position Tracking)**: Does the SourceSpan design provide accurate positioning? Are all 5 acceptance criteria covered?
- [ ] **Requirement 4 (Metadata Immutability)**: Does deep-copying ensure true immutability? Are performance concerns addressed?
- [ ] **Requirement 5 (API Paradigm Unification)**: Does the `by_id()` bridge effectively unify the dual APIs?
- [ ] **Requirement 6 (Type Safety)**: Are TypeGuards and Visitor patterns properly designed?
- [ ] **Requirement 7 (Compatibility)**: Is the migration strategy realistic? Is the 3-release timeline appropriate?
- [ ] **Requirement 8 (Performance)**: Are the performance budgets achievable? Are optimization strategies sound?
- [ ] **Requirement 9 (Operation Registry)**: Does the registry design support all consumers (Python, DSL, LSP)?
- [ ] **Requirement 10 (Diagnostics)**: Does the diagnostic system provide actionable error messages?

### 2. Technical Soundness

Check for:

- [ ] **Architecture**: Is the layered architecture (Core → Internal Ops → JSON-RPC Bridge) well-designed?
- [ ] **Data Structures**: Are NodeId, Provenance, and SourceSpan properly immutable (frozen dataclasses)?
- [ ] **ID Stability**: Will content-hash IDs remain stable across the operations that should preserve them?
- [ ] **Performance**: Are the claimed performance improvements realistic (2x faster internal ops, \<10% ID overhead)?
- [ ] **Type Safety**: Will TypeGuards work correctly with mypy/pyright?
- [ ] **Error Handling**: Is the Diagnostic system comprehensive enough?

### 3. Implementation Feasibility

Assess:

- [ ] **Phase Plan**: Is the 12-week plan realistic (9-10 weeks with 2-3 developers and parallelization)?
- [ ] **Dependencies**: Are phase dependencies clearly identified?
- [ ] **Testing Strategy**: Is the test coverage adequate (unit, integration, performance)?
- [ ] **Migration Path**: Is the compatibility mode implementable? Can users rollback safely?
- [ ] **Risk Mitigation**: Are the identified risks properly mitigated?

### 4. Potential Issues to Flag

Look for:

- [ ] **Missing Requirements**: Are any acceptance criteria not addressed in the design?
- [ ] **Inconsistencies**: Do different sections contradict each other?
- [ ] **Ambiguities**: Are any design decisions unclear or underspecified?
- [ ] **Performance Risks**: Could any design choices cause performance problems?
- [ ] **Complexity**: Is the design overly complex for the problem being solved?
- [ ] **Backward Compatibility**: Could the changes break existing code in unexpected ways?

### 5. Specific Technical Questions

#### NodeId Design

1. **Hash Collisions**: Is 16 characters (64 bits) sufficient to avoid collisions? Should we use the full 64-character SHA-256?
1. **Hint Generation**: How is the "hint" generated? Is it deterministic? What if two headings have the same text?
1. **ID Preservation**: The design claims IDs are preserved during promote/demote. But if the content changes (e.g., level changes), shouldn't the hash change?
1. **Canonical Serialization**: Is the canonicalization function (`_canonicalize_node`) fully specified? What about edge cases (unicode, whitespace variations)?

#### Internal Operations Layer

1. **Document Mutability**: If operations return new Document objects, how are node IDs preserved? Are nodes copied or shared?
1. **Performance Claims**: The design claims 2x faster than JSON-RPC. Is this measured or estimated? What's the basis?
1. **Memory Usage**: Won't keeping rich Document objects in memory increase memory usage significantly?

#### Source Position Tracking

1. **Parser Limitations**: The design notes that markdown-it-py doesn't provide column numbers. Is this acceptable? How will this affect error messages?
1. **Position Updates**: When nodes are moved or transformed, how are source spans updated? Or are they kept pointing to original positions?
1. **Multi-file Documents**: How do source spans work when documents are composed from multiple files?

#### Metadata Immutability

1. **Performance Impact**: The design accepts 15% overhead for deep-copying. Is this measured? Could it be higher for deeply nested metadata?
1. **Persistent Structures**: If deep-copy proves too slow, is migration to pyrsistent straightforward? Would it require API changes?
1. **Nested Objects**: Does deep-copy handle all Python objects correctly (custom classes, lambdas, etc.)?

#### API Bridge

1. **ID String Format**: The `by_id()` function accepts strings. What's the string format? Is it the `__str__()` representation of NodeId?
1. **Backward Compatibility**: Can the bridge support both old positional IDs ("h2-0") and new stable IDs simultaneously?
1. **Performance**: Does the bridge add overhead to every operation?

#### Compatibility Mode

1. **Dual ID Storage**: How are both ID schemes stored? Does every node have both a stable ID and a positional ID?
1. **Migration Complexity**: Is the 3-release migration realistic? What if users don't upgrade for years?
1. **Rollback Safety**: If a user rolls back, will documents created with stable IDs still work?

#### Type Safety

1. **TypeGuard Limitations**: TypeGuards only work for static type checkers. Do they provide runtime benefits?
1. **Visitor Pattern**: The design makes Visitor optional. Won't this lead to inconsistent code styles?
1. **Generic Support**: The design mentions "Generic support" but doesn't show how. Can you provide an example?

### 6. Comparison with Design Documents

Cross-reference with the original design documents:

- [ ] **docs/design/05-split-transclusion-plan.md**: Does this design align with Phase 1 (Core Foundations)?
- [ ] **docs/design/06-core-api-dsl-review.md**: Are all identified gaps addressed?
- [ ] **Consistency**: Are the solutions consistent with the recommendations in the design docs?

### 7. Testing Adequacy

Evaluate the testing strategy:

- [ ] **Unit Tests**: Are the proposed unit tests sufficient to verify each component?
- [ ] **Integration Tests**: Do integration tests cover multi-step pipelines and compatibility mode?
- [ ] **Performance Tests**: Are performance benchmarks comprehensive enough?
- [ ] **Edge Cases**: Are edge cases (empty documents, malformed IDs, etc.) tested?
- [ ] **Regression Tests**: Will existing tests catch regressions?

### 8. Documentation Quality

Assess documentation:

- [ ] **Code Examples**: Are code examples clear and correct?
- [ ] **API Documentation**: Is the API surface well-documented?
- [ ] **Migration Guide**: Is the migration path clear for users?
- [ ] **Decision Rationale**: Are design decisions well-justified?

## Review Output Format

Please structure your review as follows:

### Summary

- **Overall Assessment**: [Approve / Approve with Minor Changes / Major Revisions Needed]
- **Confidence Level**: [High / Medium / Low]
- **Key Strengths**: [List 3-5 strengths]
- **Key Concerns**: [List 3-5 concerns]

### Detailed Findings

For each issue found, provide:

1. **Severity**: [Critical / Major / Minor / Question]
1. **Location**: [Section/Component name]
1. **Issue**: [Clear description]
1. **Impact**: [What could go wrong?]
1. **Recommendation**: [Suggested fix or clarification]

### Requirements Coverage Matrix

| Requirement | Covered? | Notes |
|-------------|----------|-------|
| Req 1: Stable Node Identity | ✅/⚠️/❌ | ... |
| Req 2: Internal Operations | ✅/⚠️/❌ | ... |
| ... | ... | ... |

### Open Questions

List any questions that need clarification from the design author.

### Recommendation

Final recommendation: [Approve / Request Changes / Reject]
