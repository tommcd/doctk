# Generic Spec Review Prompt

This prompt guides AI reviewers through a comprehensive review of any Kiro spec, ensuring alignment across requirements, design, and implementation tasks.

## Instructions for Reviewers

You will be provided with three specification documents for review:

1. **requirements.md** - Defines WHAT needs to be built (user stories, acceptance criteria)
1. **design.md** - Defines HOW it will be built (architecture, components, correctness properties)
1. **tasks.md** - Defines the step-by-step implementation plan (discrete, actionable tasks)

**Your task**: Review these three documents to ensure they are aligned, complete, and ready for implementation. Follow the two-phase review process outlined below.

## Overview

A Kiro spec consists of three documents that must remain synchronized. This review validates alignment across all three documents in two phases:

- **Phase 1**: Requirements ↔ Design alignment (validate technical soundness)
- **Phase 2**: Design ↔ Tasks alignment + End-to-end validation (validate implementation plan)

______________________________________________________________________

## Document Formats

### requirements.md Format

Requirements follow the **EARS (Easy Approach to Requirements Syntax)** pattern with **INCOSE quality rules**:

**Structure:**

```markdown
# Requirements Document: [Feature Name]

## Introduction
[Brief overview of the feature and its purpose]

## Glossary
- **Term 1**: Definition
- **Term 2**: Definition
[All technical terms must be defined here]

## Requirements

### Requirement 1: [Requirement Name]

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. WHEN [trigger], THE System SHALL [response]
2. WHILE [condition], THE System SHALL [response]
3. IF [condition], THEN THE System SHALL [response]
4. WHERE [option], THE System SHALL [response]
5. [Complex: WHERE] [WHILE] [WHEN/IF] THE System SHALL [response]

### Requirement 2: [Requirement Name]
...
```

**EARS Patterns (must use exactly one per criterion):**

- **Ubiquitous**: THE System SHALL [response]
- **Event-driven**: WHEN [trigger], THE System SHALL [response]
- **State-driven**: WHILE [condition], THE System SHALL [response]
- **Unwanted event**: IF [condition], THEN THE System SHALL [response]
- **Optional feature**: WHERE [option], THE System SHALL [response]
- **Complex**: [WHERE] [WHILE] [WHEN/IF] THE System SHALL [response] (in this order)

**INCOSE Quality Rules:**

- Active voice (who does what)
- No vague terms ("quickly", "adequate")
- No escape clauses ("where possible")
- No negative statements ("SHALL not...")
- One thought per requirement
- Explicit and measurable conditions
- Consistent terminology from glossary
- No pronouns ("it", "them")
- Solution-free (focus on WHAT, not HOW)

### design.md Format

Design documents specify the technical approach:

**Structure:**

````markdown
# Design Document: [Feature Name]

## Overview
[High-level summary of the design approach]

## Architecture
[System architecture, layers, component relationships]
[Diagrams using Mermaid when helpful]

## Components and Interfaces
[Detailed component specifications with code examples]

### Component 1: [Name]
[Data structures, classes, functions]
```python
# Code examples showing interfaces
````

## Data Models

[Data structures, types, relationships]

## Correctness Properties

*A property is a characteristic or behavior that should hold true across
all valid executions of a system.*

### Property 1: [Name]

*For any* [universal quantification], [property statement]
**Validates: Requirements X.Y**

### Property 2: [Name]

...

## Error Handling

[Error scenarios and handling strategies]

## Testing Strategy

[Unit tests, property-based tests, integration tests]
[Specify PBT library and configuration]

## Performance Considerations

[Performance targets, optimization strategies]

## Implementation Notes

[Additional guidance for implementers]

````

**Key Requirements:**
- Each correctness property MUST start with "For any..." or "For all..."
- Each property MUST reference specific requirement acceptance criteria
- Properties must be testable via property-based testing
- Code examples should be concrete and runnable
- Architecture diagrams help but aren't required

### tasks.md Format

Tasks break down implementation into discrete steps:

**Structure:**
```markdown
# Tasks Document: [Feature Name]

## Overview
[Summary, total tasks, duration, dependencies]

## Phase 1: [Phase Name] (X weeks)

### Task 1.1: [Task Name]

**Duration:** X days
**Priority:** Critical / High / Medium / Low

**Description:**
[Clear explanation of what needs to be implemented]

**Acceptance Criteria:**
- [ ] Specific, testable criterion 1
- [ ] Specific, testable criterion 2
- [ ]* Optional criterion (marked with asterisk)
- [ ] ...

**Files to Create/Modify:**
- `path/to/file1.py`
- `path/to/file2.py`

**Dependencies:** Task X.Y, Task Z.W

**Requirements:** Req X ACY, Req Z ACW

**Testing:**
```python
# Example test code showing what to verify
````

### Task 1.2: [Task Name]

...

## Phase 2: [Phase Name] (X weeks)

...

````

**Key Requirements:**
- Tasks use checkbox format: `- [ ]` (incomplete) or `- [x]` (complete)
- Optional tasks marked with asterisk: `- [ ]*`
- Each task references specific requirements (e.g., "Req 1 AC3, AC5")
- Tasks should be 1-3 days each (appropriate granularity)
- Dependencies must be explicit
- Acceptance criteria must be testable and specific
- Property-based test tasks must reference design properties

**Task Marking Conventions:**
- `- [ ]` = Not started
- `- [x]` = Completed
- `- [ ]*` = Optional (can be skipped)
- Tasks may have sub-tasks with decimal notation (1.1, 1.2, etc.)

---

## Phase 1: Requirements ↔ Design Alignment

**Goal**: Verify that the design document fully addresses all requirements with sound technical solutions.

### Files to Review

In this phase, focus on these two documents:

1. **requirements.md** - The requirements specification
2. **design.md** - The technical design document

### Review Checklist

#### 1.1 Requirements Coverage

For each requirement in requirements.md:

- [ ] **Design Section Exists**: Is there a corresponding design section?
- [ ] **All Acceptance Criteria Addressed**: Does the design cover every acceptance criterion?
- [ ] **Correctness Properties Defined**: Are there testable correctness properties derived from acceptance criteria?
- [ ] **Solution Completeness**: Does the design provide enough detail to implement?

#### 1.2 Technical Soundness

- [ ] **Architecture**: Is the overall architecture well-designed and appropriate?
- [ ] **Data Structures**: Are data structures properly defined (types, immutability, relationships)?
- [ ] **Algorithms**: Are algorithms clearly specified and efficient?
- [ ] **Error Handling**: Is error handling comprehensive?
- [ ] **Performance**: Are performance targets realistic and measurable?
- [ ] **Type Safety**: Are type annotations and type safety mechanisms adequate?

#### 1.3 Correctness Properties

For each correctness property in design.md:

- [ ] **Universal Quantification**: Does it start with "For any..." or "For all..."?
- [ ] **Testable**: Can it be verified through property-based testing?
- [ ] **Requirement Link**: Does it reference specific acceptance criteria (format: "**Validates: Requirements X.Y**")?
- [ ] **Clear Specification**: Is the property unambiguous?
- [ ] **Property Patterns**: Does it follow common correctness patterns?
  - Invariants (properties preserved after transformation)
  - Round-trip properties (operation + inverse returns to original)
  - Idempotence (doing twice = doing once)
  - Metamorphic properties (relationships between components)
  - Error conditions (bad inputs properly rejected)

#### 1.4 Implementation Feasibility

- [ ] **Realistic Scope**: Is the design implementable within stated timeline?
- [ ] **Dependencies Clear**: Are external dependencies identified?
- [ ] **Risk Assessment**: Are risks identified and mitigated?
- [ ] **Testing Strategy**: Is the testing approach comprehensive?

#### 1.5 Consistency and Clarity

- [ ] **Terminology**: Are terms used consistently with the glossary?
- [ ] **No Contradictions**: Do different sections align?
- [ ] **Sufficient Detail**: Is there enough detail without over-specification?
- [ ] **Examples Provided**: Are code examples clear and correct?

### Phase 1 Output Format

```markdown
# Phase 1 Review: Requirements ↔ Design Alignment

## Summary
- **Assessment**: Approve / Approve with Changes / Request Major Revisions
- **Confidence**: High / Medium / Low
- **Strengths**: [3-5 key strengths]
- **Concerns**: [3-5 key concerns if any]

## Requirements Coverage Matrix

| Requirement | Design Section | Coverage | Notes |
|-------------|----------------|----------|-------|
| Req 1: [Name] | Section X | ✅/⚠️/❌ | [Details] |
| Req 2: [Name] | Section Y | ✅/⚠️/❌ | [Details] |
| ... | ... | ... | ... |

Legend:
- ✅ Fully covered with sound technical approach
- ⚠️ Partially covered or concerns exist
- ❌ Not covered or significant issues

## Correctness Properties Validation

| Property | Requirement Link | Testable? | Issues |
|----------|------------------|-----------|--------|
| Property 1: [Name] | Req X.Y | ✅/❌ | [Notes] |
| ... | ... | ... | ... |

## Detailed Findings

For each issue:

**[Severity: Critical/Major/Minor]** | **Location**: [Section]
- **Issue**: [Clear description]
- **Impact**: [What could go wrong]
- **Recommendation**: [Specific fix]

## Open Questions

1. [Question requiring clarification]
2. ...

## Recommendation

**Decision**: [Approve / Request Changes / Reject]
**Rationale**: [2-3 sentences]
**Required Changes**: [List if any]
````

______________________________________________________________________

## Phase 2: Design ↔ Tasks Alignment + End-to-End Validation

**Goal**: Verify that tasks implement the complete design and satisfy all requirements.

### Files to Review

In this phase, review all three documents together:

1. **requirements.md** - The requirements specification
1. **design.md** - The technical design document
1. **tasks.md** - The implementation task list

### Review Checklist

#### 2.1 Design Component Coverage

For each major component in design.md:

- [ ] **Implementation Tasks Exist**: Are there specific tasks implementing this component?
- [ ] **Complete Coverage**: Do tasks cover all aspects of the component?
- [ ] **Helper Functions**: Are all helper functions/utilities included in tasks?
- [ ] **Data Structures**: Are all data structures created in tasks?
- [ ] **Integration Points**: Are integrations with existing code covered?

#### 2.2 Task Quality

For each task in tasks.md:

- [ ] **Clear Objective**: Is the goal unambiguous?
- [ ] **Actionable**: Can a developer start immediately?
- [ ] **Testable**: Are acceptance criteria specific and verifiable?
- [ ] **Appropriate Scope**: Is it sized correctly (typically 1-3 days)?
- [ ] **Dependencies Clear**: Are prerequisites explicitly stated?
- [ ] **Files Specified**: Are files to create/modify listed?
- [ ] **Requirements Linked**: Does it reference specific requirements?
- [ ] **Testing Included**: Are test strategies or examples provided?

#### 2.3 Requirements → Tasks Direct Mapping

For each requirement:

- [ ] **Task Coverage**: Are there tasks directly implementing this requirement?
- [ ] **Acceptance Criteria Mapping**: Can you trace each AC to specific task ACs?
- [ ] **No Gaps**: Are all requirement ACs covered by at least one task?
- [ ] **Requirement References**: Do tasks explicitly cite requirements?

#### 2.4 Phase Organization

- [ ] **Logical Grouping**: Are related tasks grouped sensibly?
- [ ] **Dependencies Respected**: Do tasks build incrementally?
- [ ] **No Circular Dependencies**: Is the dependency graph acyclic?
- [ ] **Parallelization Identified**: Are independent tasks marked?
- [ ] **Duration Realistic**: Are time estimates reasonable?
- [ ] **Critical Path Clear**: Is the longest dependency chain identified?
- [ ] **Checkpoints Included**: Are there validation points between phases?

#### 2.5 Completeness Checks

- [ ] **All Design Components**: Every component has corresponding tasks
- [ ] **All Correctness Properties**: Each property has a testing task
- [ ] **All Integration Points**: Parser, DSL, LSP, CLI, etc. are covered
- [ ] **All Test Types**: Unit, integration, property-based, performance tests
- [ ] **Documentation Tasks**: API docs, guides, migration docs included
- [ ] **No Orphaned Tasks**: Every task maps to requirements or design

#### 2.6 Testing Strategy Validation

- [ ] **Unit Tests**: Core functionality tested in isolation
- [ ] **Property-Based Tests**: Universal properties verified across inputs
  - Each correctness property has a corresponding PBT task
  - PBT library specified (e.g., Hypothesis for Python, fast-check for TypeScript)
  - Minimum 100 iterations configured for each property test
  - Each PBT explicitly tagged with property reference (format: "**Feature: {name}, Property {N}: {text}**")
- [ ] **Integration Tests**: Multi-component interactions tested
- [ ] **Edge Cases**: Boundary conditions and error paths covered
- [ ] **Performance Tests**: Benchmarks for performance targets
- [ ] **Regression Tests**: Existing functionality protected

#### 2.7 Cross-Cutting Validation

- [ ] **Terminology Consistent**: Same terms used across all three documents
- [ ] **Numbering Correct**: Requirement/task numbers are accurate
- [ ] **Timeline Aligned**: Task timeline matches design estimates
- [ ] **Scope Bounded**: Nothing in tasks beyond requirements/design
- [ ] **No Missing Pieces**: Nothing in requirements/design missing from tasks

### Phase 2 Output Format

```markdown
# Phase 2 Review: Design ↔ Tasks Alignment + End-to-End Validation

## Summary
- **Assessment**: Approve / Approve with Changes / Request Major Revisions
- **Confidence**: High / Medium / Low
- **Strengths**: [3-5 key strengths]
- **Concerns**: [3-5 key concerns if any]

## Requirements → Tasks Coverage Matrix

| Requirement | Design Section | Tasks | Coverage | Notes |
|-------------|----------------|-------|----------|-------|
| Req 1: [Name] | Section X | Tasks 1.1-1.5 | ✅/⚠️/❌ | [Details] |
| Req 2: [Name] | Section Y | Tasks 2.1-2.3 | ✅/⚠️/❌ | [Details] |
| ... | ... | ... | ... | ... |

## Design Component → Tasks Coverage

| Design Component | Tasks | Status | Notes |
|------------------|-------|--------|-------|
| Component A | Task 1.1, 1.2 | ✅/⚠️/❌ | [Details] |
| Helper Function X | ? | ❌ | Missing |
| ... | ... | ... | ... |

## Task Quality Assessment

| Task | Clear? | Actionable? | Testable? | Scoped? | Issues |
|------|--------|-------------|-----------|---------|--------|
| 1.1 | ✅ | ✅ | ✅ | ✅ | None |
| 1.2 | ⚠️ | ✅ | ❌ | ✅ | Missing test criteria |
| ... | ... | ... | ... | ... | ... |

## Phase Analysis

### Phase 1: [Name]
- **Duration**: [X weeks] - Realistic / Too Short / Too Long
- **Dependencies**: Clear / Unclear / Circular
- **Completeness**: Complete / Missing Tasks
- **Notes**: [Concerns or suggestions]

### Phase 2: [Name]
...

## Detailed Findings

For each issue:

**[Severity: Critical/Major/Minor]** | **Location**: [Phase/Task]
- **Issue**: [Clear description]
- **Impact**: [What happens if not addressed]
- **Recommendation**: [Specific fix]

## Testing Coverage Analysis

- **Unit Tests**: [Assessment]
- **Property-Based Tests**: [Assessment]
- **Integration Tests**: [Assessment]
- **Performance Tests**: [Assessment]
- **Edge Cases**: [Assessment]
- **Gaps**: [List any missing test coverage]

## Timeline Validation

- **Total Duration**: [X weeks]
- **Critical Path**: [List key dependencies]
- **Parallelization**: [Opportunities identified?]
- **Realistic?**: Yes / No - [Rationale]

## Open Questions

1. [Question requiring clarification]
2. ...

## Final Recommendation

**Decision**: [Approve / Request Changes / Reject]
**Rationale**: [2-3 sentences explaining decision]
**Required Changes**: [Priority-ordered list if changes needed]
**Optional Improvements**: [Nice-to-have improvements]
```

______________________________________________________________________

## Common Issues to Flag

### Requirements Issues

- Vague acceptance criteria ("efficiently", "quickly")
- Non-testable requirements
- Missing EARS format (WHEN/WHILE/IF/WHERE/THE system SHALL)
- Undefined terms not in glossary

### Design Issues

- Requirements not addressed
- Missing correctness properties
- Correctness properties not universally quantified ("For any...")
- Properties don't reference specific requirements
- Vague architecture or data structures
- No error handling strategy
- Unrealistic performance targets
- Missing integration points
- No property-based testing strategy specified

### Task Issues

- Design components without tasks
- Tasks without requirement references
- Vague or non-actionable descriptions
- Missing test acceptance criteria
- Circular dependencies
- Unrealistic time estimates
- Missing helper functions or utilities
- No integration tasks

### Cross-Document Issues

- Inconsistent terminology
- Contradictions between documents
- Timeline mismatches
- Scope creep (tasks beyond design)
- Gaps (design without tasks)

______________________________________________________________________

## Review Best Practices

### For Reviewers

1. **Read Completely First**: Read all three documents before starting the review
1. **Be Thorough**: Check every requirement, component, and task
1. **Be Constructive**: Suggest specific improvements, not just problems
1. **Be Pragmatic**: Minor issues shouldn't block approval
1. **Ask Questions**: Flag ambiguities for clarification
1. **Verify Traceability**: Ensure clear links from requirements → design → tasks

### Severity Guidelines

- **Critical**: Blocks implementation, missing core functionality, major technical flaw
- **Major**: Significant gap or issue, but workarounds possible
- **Minor**: Small improvement, clarification, or nice-to-have

### When to Approve

Approve when:

- All requirements have design coverage
- All design components have implementation tasks
- Tasks are actionable and testable
- Timeline is realistic
- Only minor issues remain

### When to Request Changes

Request changes when:

- Major requirements gaps exist
- Design has significant technical flaws
- Tasks are missing or poorly defined
- Timeline is unrealistic
- Multiple major issues need addressing

### When to Reject

Reject when:

- Fundamental misunderstanding of requirements
- Design is technically unsound
- Tasks don't align with design
- Scope is wildly unrealistic

______________________________________________________________________

## How to Use This Prompt

**For AI Reviewers:**

1. You will receive this prompt along with three attached files:

   - `requirements.md`
   - `design.md`
   - `tasks.md`

1. Read all three documents completely before starting your review

1. Complete Phase 1 review:

   - Focus on requirements.md and design.md
   - Validate technical soundness and requirements coverage
   - Provide Phase 1 output using the specified format

1. Complete Phase 2 review:

   - Review all three documents together
   - Validate implementation plan and end-to-end alignment
   - Provide Phase 2 output using the specified format

1. Provide clear, actionable feedback with specific recommendations

______________________________________________________________________

## Customization Notes

This is a generic template. For specific specs, you may want to:

- Add domain-specific validation (e.g., LSP specs should check protocol compliance)
- Include project-specific quality standards
- Reference relevant design documents or ADRs
- Add performance benchmarking requirements
- Include security or compliance checks

______________________________________________________________________

## Version History

- v1.0 (2024-11-25): Initial generic spec review prompt
