# Graph Features Implementation Roadmap

## Overview

This document describes the implementation roadmap for doctk's graph-based document composition features, based on the comprehensive design analysis in `docs/design/05-split-transclusion-plan.md` and `docs/design/06-core-api-dsl-review.md`.

The work is divided into three sequential specs that build on each other:

## Spec 1: Core API Stabilization (Foundation)

**Location:** `.kiro/specs/core-api-stabilization/`

**Status:** Requirements complete, ready for design phase

**Purpose:** Establish the foundational improvements needed before graph features can be implemented.

### Key Features

- **Stable Node IDs**: Content-hash + human-readable hints that persist across edits
- **Internal Operations Layer**: Rich Python API without JSON serialization overhead
- **Source Position Tracking**: AST nodes carry original source locations
- **Metadata Immutability**: Deep-copying to ensure functional purity
- **API Paradigm Unification**: Bridge between declarative and imperative APIs
- **Type Safety**: TypeGuards and visitor patterns for better type checking
- **Compatibility**: Migration path from positional to stable IDs

### Dependencies

- None (foundational work)

### Estimated Scope

- 6-8 weeks for full implementation
- Critical path for all subsequent work

## Spec 2: Fragment Graph Model (Core Graph Features)

**Location:** `.kiro/specs/fragment-graph-model/`

**Status:** Requirements complete, ready for design phase

**Purpose:** Implement the core graph-based document composition model.

### Key Features

- **Fragment Identity**: Content-addressed storage with SHA-256 hashing
- **Graph Structure**: Typed edges (containment, transclusion, links)
- **Document Splitting**: Split by heading level, size, or semantic boundaries
- **Transclusion**: Syntax and resolution (`{{#include ...}}`)
- **Logical Views**: Lazy traversal with cycle detection
- **Materialized Views**: Flattened documents with provenance mappings
- **Sharding**: Balanced, size-based, or semantic partitioning
- **Hydration**: Resolve transclusions to create unified documents
- **DSL Operations**: `split()`, `transclude()`, `link()`, `hydrate()`, `shard()`
- **LSP Integration**: Completions, hover, diagnostics for fragments
- **CLI Commands**: `doctk split`, `doctk hydrate`, `doctk validate-graph`

### Dependencies

- **Requires:** Core API Stabilization (stable IDs, internal operations layer)
- **Blocks:** Advanced Graph Features

### Estimated Scope

- 10-12 weeks for full implementation
- Delivers core value for document composition

## Spec 3: Advanced Graph Features (Optional/Future)

**Location:** `.kiro/specs/advanced-graph-features/`

**Status:** Requirements complete, ready for design phase

**Purpose:** Add sophisticated features for collaborative editing and conflict resolution.

### Key Features

- **Bidirectional Lenses**: Edit propagation from views back to sources
- **Conflict Detection**: Identify overlapping edits
- **Merge Strategies**: prefer-source, prefer-target, annotate, manual, three-way
- **Overlay Composition**: Layered documents with priority rules
- **Reactive Updates**: Automatic propagation through dependencies
- **Speculative Edits**: Transactional operations with commit/rollback
- **CRDT-Inspired Merge**: Automatic conflict-free merging
- **Differential Sync**: Efficient diff-based synchronization
- **Version Pinning**: Pin transclusions to specific versions
- **Audit Trails**: Complete provenance tracking
- **Performance Optimization**: Scaling to large graphs
- **Recovery Tools**: Consistency checks and repair

### Dependencies

- **Requires:** Fragment Graph Model (graphs, transclusion, views)
- **Blocks:** None (terminal features)

### Estimated Scope

- 8-10 weeks for full implementation
- Can be delivered incrementally based on priority

## Implementation Strategy

### Phase 1: Foundation (Spec 1)

1. Implement stable node IDs with content hashing
1. Create internal operations layer
1. Add source position tracking to parser
1. Ensure metadata immutability
1. Build API bridge (ID ↔ predicate)
1. Add TypeGuards and visitor support
1. Implement compatibility mode

**Exit Criteria:**

- All tests pass in both compatibility and stable-ID modes
- Performance benchmarks meet targets
- JSON-RPC bridge uses internal operations layer
- DSL/REPL use internal operations directly

### Phase 2: Core Graphs (Spec 2)

1. Implement fragment storage with content addressing
1. Build fragment graph data structures
1. Add document splitting operations
1. Implement transclusion syntax and resolution
1. Create logical view traversal with cycle detection
1. Build materialized view generation with provenance
1. Add DSL operations for graphs
1. Integrate with LSP and CLI

**Exit Criteria:**

- Can split documents into fragments
- Can transclude fragments with cycle detection
- Can hydrate graphs into unified documents
- LSP provides completions and diagnostics
- CLI commands work end-to-end

### Phase 3: Advanced Features (Spec 3)

1. Implement bidirectional lenses
1. Add conflict detection and merge strategies
1. Build overlay composition
1. Implement reactive update propagation
1. Add speculative edit support
1. Implement CRDT-inspired merging
1. Add differential synchronization
1. Build audit and recovery tools

**Exit Criteria:**

- Can edit materialized views and propagate changes
- Conflicts are detected and resolved
- Reactive updates work correctly
- Performance scales to large graphs
- Audit trails are complete

## Design Document Status

The following design documents provide detailed technical guidance:

- **docs/design/05-split-transclusion-plan.md**: Comprehensive plan for graph features
- **docs/design/06-core-api-dsl-review.md**: Analysis of core API improvements

These documents incorporate feedback from:

- Claude's detailed technical analysis
- Codex's synthesis and recommendations
- Cross-review comparisons and refinements

## Next Steps

1. **Review Requirements**: Have stakeholders review the three requirements documents
1. **Create Design Documents**: For each spec, create `design.md` following the Kiro workflow
1. **Create Task Lists**: For each spec, create `tasks.md` with implementation steps
1. **Begin Implementation**: Start with Spec 1 (Core API Stabilization)

## Success Criteria

### Spec 1 Success

- Stable IDs work reliably across edits
- Internal API is faster than JSON-RPC round-trips
- Migration path is smooth with no breaking changes
- Type safety improvements reduce bugs

### Spec 2 Success

- Can split large documents into manageable fragments
- Transclusion works with cycle detection
- Can compose documents from fragments
- LSP and CLI provide good UX

### Spec 3 Success

- Bidirectional editing works reliably
- Conflicts are resolved intelligently
- Performance scales to large document collections
- Audit trails provide compliance support

## Risk Mitigation

### Technical Risks

1. **Performance degradation from stable IDs**

   - Mitigation: Benchmark early, optimize hash computation, cache aggressively

1. **Complexity of lens laws**

   - Mitigation: Start with simple cases, add property-based tests, document edge cases

1. **Cycle detection edge cases**

   - Mitigation: Comprehensive test suite, clear policies, good diagnostics

1. **Migration breaking existing code**

   - Mitigation: Compatibility mode, extensive testing, gradual rollout

### Scope Risks

1. **Feature creep in Spec 3**

   - Mitigation: Defer advanced features, focus on core value first

1. **Underestimating complexity**

   - Mitigation: Incremental delivery, regular checkpoints, adjust scope as needed

## Open Questions

These questions should be resolved during the design phase:

1. **NodeId Strategy**: UUIDv7 vs content-hash + hint? Performance implications?
1. **Transclusion Versioning**: How to handle version pinning in UX?
1. **Cycle Policies**: Default to "error" or "inline-once"?
1. **Cross-Repo Transclusion**: Needed? Auth/provenance format?
1. **Conflict Resolution UX**: Which strategies to expose in UI vs DSL only?
1. **CRDT Choice**: Which CRDT semantics best fit document editing?
1. **Storage Backend**: Filesystem only or also Git/S3?

## References

- **Category Theory**: Presheaves, functors, lens laws
- **Prior Art**: mdBook, Org-mode, Pandoc, Git submodules
- **Design Docs**: `docs/design/05-split-transclusion-plan.md`, `docs/design/06-core-api-dsl-review.md`
- **Steering Docs**: `.kiro/steering/product.md`, `.kiro/steering/tech.md`, `.kiro/steering/structure.md`
