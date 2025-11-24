# Requirements Document: Advanced Graph Features

## Introduction

This document specifies requirements for advanced features in the doctk fragment graph system, including bidirectional lenses for edit propagation, conflict resolution strategies, reactive graph updates, and CRDT-inspired merge semantics. These features enable sophisticated document workflows like collaborative editing, overlay composition, and transactional operations.

This work builds on both the Core API Stabilization and Fragment Graph Model specs.

## Glossary

- **Lens**: A bidirectional transformation that allows viewing and updating a fragment within a larger document
- **PutGet Law**: Lens property ensuring `get(put(doc, fragment)) == fragment`
- **GetPut Law**: Lens property ensuring `put(doc, get(doc)) == doc`
- **PutPut Law**: Lens property ensuring `put(put(doc, f1), f2) == put(doc, f2)`
- **Conflict**: A situation where multiple edits affect the same fragment or overlapping regions
- **Merge Strategy**: A policy for resolving conflicts (prefer-source, prefer-target, annotate, manual)
- **Overlay**: A layered composition where one document extends or overrides another
- **CRDT**: Conflict-free Replicated Data Type - data structures that merge automatically
- **Reactive Update**: Automatic propagation of changes through transclusion dependencies
- **Speculative Edit**: A tentative change that can be committed or rolled back
- **Causal Metadata**: Timestamps, vector clocks, or other data tracking edit causality

## Requirements

### Requirement 1: Bidirectional Lenses

**User Story:** As a developer enabling inline editing, I want to edit transcluded content in place and propagate changes back to source fragments, so that users can work with unified views without losing modularity.

#### Acceptance Criteria

1. WHEN a lens is created for a fragment, THE System SHALL provide get and put operations
1. WHEN get is called, THE System SHALL extract the fragment from the containing document
1. WHEN put is called with modified content, THE System SHALL update the source fragment and recompute its content hash
1. WHEN lens laws are tested, THE System SHALL verify PutGet, GetPut, and PutPut properties
1. WHEN multiple lenses compose, THE System SHALL maintain lens laws for the composition

### Requirement 2: Edit Propagation Workflow

**User Story:** As a user editing a materialized view, I want my changes to flow back to source fragments automatically, so that I don't have to manually update multiple files.

#### Acceptance Criteria

1. WHEN an edit is detected in a materialized view, THE System SHALL identify affected source fragments via provenance
1. WHEN a source fragment is identified, THE System SHALL apply the lens put operation to propagate the edit
1. WHEN a fragment is updated, THE System SHALL recompute its content hash and update references
1. WHEN dependent documents exist, THE System SHALL notify them of available updates
1. WHEN propagation fails, THE System SHALL report conflicts with clear resolution options

### Requirement 3: Conflict Detection

**User Story:** As a developer managing concurrent edits, I want automatic conflict detection, so that I can identify when multiple changes affect the same content.

#### Acceptance Criteria

1. WHEN two edits modify the same fragment, THE System SHALL detect the conflict
1. WHEN edits modify overlapping regions, THE System SHALL detect the overlap
1. WHEN conflicts are detected, THE System SHALL report affected fragments and edit ranges
1. WHEN conflicts are reported, THE System SHALL include timestamps and author information
1. WHEN conflicts are logged, THE System SHALL provide structured data for resolution tools

### Requirement 4: Merge Strategies

**User Story:** As a developer resolving conflicts, I want multiple merge strategies, so that I can choose appropriate resolution policies for different scenarios.

#### Acceptance Criteria

1. WHEN merge strategy is "prefer-source", THE System SHALL keep the source fragment's content
1. WHEN merge strategy is "prefer-target", THE System SHALL keep the target fragment's content
1. WHEN merge strategy is "annotate", THE System SHALL mark conflicts with both versions inline
1. WHEN merge strategy is "manual", THE System SHALL require explicit user resolution
1. WHEN merge strategy is "three-way", THE System SHALL use a common ancestor for intelligent merging

### Requirement 5: Overlay Composition

**User Story:** As a developer creating document variants, I want to layer documents with priority rules, so that I can create specialized versions without duplicating content.

#### Acceptance Criteria

1. WHEN an overlay is created, THE System SHALL specify base and overlay fragments with priority rules
1. WHEN overlays are resolved, THE System SHALL apply higher-priority fragments over lower-priority ones
1. WHEN overlays conflict, THE System SHALL apply the configured merge strategy
1. WHEN overlays are validated, THE System SHALL check for ambiguous priority situations
1. WHEN overlays are materialized, THE System SHALL track which fragments came from which layer

### Requirement 6: Reactive Graph Updates

**User Story:** As a developer building live documentation, I want changes to propagate automatically through transclusion dependencies, so that dependent documents stay synchronized.

#### Acceptance Criteria

1. WHEN a fragment is edited, THE System SHALL identify all documents that transclude it
1. WHEN dependents are identified, THE System SHALL notify them of available updates
1. WHEN notifications are received, THE System SHALL optionally auto-update or prompt the user
1. WHEN updates are applied, THE System SHALL recompute affected materialized views
1. WHEN update chains exist, THE System SHALL propagate changes transitively with cycle detection

### Requirement 7: Speculative Edits

**User Story:** As a developer implementing undo/redo, I want to make tentative changes that can be committed or rolled back, so that users can experiment safely.

#### Acceptance Criteria

1. WHEN a speculative edit is started, THE System SHALL create a transaction context
1. WHEN edits are made within the transaction, THE System SHALL track changes without persisting
1. WHEN the transaction is committed, THE System SHALL apply all changes atomically
1. WHEN the transaction is rolled back, THE System SHALL discard all changes
1. WHEN transactions nest, THE System SHALL support nested commit/rollback semantics

### Requirement 8: CRDT-Inspired Merge

**User Story:** As a developer enabling collaborative editing, I want automatic conflict-free merging for common cases, so that users can work concurrently without manual conflict resolution.

#### Acceptance Criteria

1. WHEN fragments carry causal metadata, THE System SHALL use it to order concurrent edits
1. WHEN edits are commutative, THE System SHALL merge them automatically
1. WHEN edits are non-commutative, THE System SHALL apply a deterministic resolution policy
1. WHEN vector clocks are used, THE System SHALL detect concurrent vs. sequential edits
1. WHEN CRDT semantics are tested, THE System SHALL verify convergence properties

### Requirement 9: Differential Synchronization

**User Story:** As a developer implementing live collaboration, I want efficient diff-based synchronization, so that only changes are transmitted between clients.

#### Acceptance Criteria

1. WHEN a fragment is edited, THE System SHALL compute a diff from the previous version
1. WHEN diffs are transmitted, THE System SHALL use a compact representation (JSON Patch or similar)
1. WHEN diffs are received, THE System SHALL apply them to the local fragment
1. WHEN diffs conflict, THE System SHALL use the configured merge strategy
1. WHEN synchronization completes, THE System SHALL verify content hash consistency

### Requirement 10: Version Pinning and Upgrades

**User Story:** As a developer managing document stability, I want to pin transclusions to specific versions and upgrade them explicitly, so that I control when changes are incorporated.

#### Acceptance Criteria

1. WHEN a transclusion is created, THE System SHALL optionally pin it to a specific content hash
1. WHEN a pinned fragment is updated, THE System SHALL not automatically update the transclusion
1. WHEN upgrades are checked, THE System SHALL report available updates for pinned transclusions
1. WHEN an upgrade is applied, THE System SHALL update the transclusion to the new content hash
1. WHEN version history is queried, THE System SHALL show all versions of a fragment

### Requirement 11: Conflict Annotation Format

**User Story:** As a user resolving conflicts manually, I want conflicts marked clearly in the document, so that I can see both versions and choose the correct one.

#### Acceptance Criteria

1. WHEN conflicts are annotated, THE System SHALL use a standard format (similar to Git conflict markers)
1. WHEN annotations are inserted, THE System SHALL include source information (fragment ID, version, author)
1. WHEN annotations are parsed, THE System SHALL extract both versions and metadata
1. WHEN conflicts are resolved, THE System SHALL remove annotations and update the fragment
1. WHEN annotations are displayed, THE System SHALL provide syntax highlighting for clarity

### Requirement 12: Transactional Batch Operations

**User Story:** As a developer implementing complex transformations, I want to group multiple operations into atomic transactions, so that partial failures don't leave documents in inconsistent states.

#### Acceptance Criteria

1. WHEN a transaction is started, THE System SHALL create an isolated context for operations
1. WHEN operations are executed within a transaction, THE System SHALL track all changes
1. WHEN the transaction is committed, THE System SHALL apply all changes atomically
1. WHEN any operation fails, THE System SHALL roll back the entire transaction
1. WHEN transactions are nested, THE System SHALL support savepoints for partial rollback

### Requirement 13: Provenance-Based Auditing

**User Story:** As a compliance officer, I want complete audit trails for document changes, so that I can track who changed what and when.

#### Acceptance Criteria

1. WHEN a fragment is edited, THE System SHALL record author, timestamp, and change description
1. WHEN edits are propagated, THE System SHALL maintain the audit trail through the propagation
1. WHEN audit logs are queried, THE System SHALL support filtering by author, date, or fragment
1. WHEN audit logs are exported, THE System SHALL provide structured data (JSON, CSV)
1. WHEN audit logs are displayed, THE System SHALL show a clear timeline of changes

### Requirement 14: Performance Optimization for Large Graphs

**User Story:** As a developer working with large document collections, I want efficient graph operations, so that performance remains acceptable at scale.

#### Acceptance Criteria

1. WHEN graphs contain thousands of fragments, THE System SHALL complete traversals within 2 seconds
1. WHEN reactive updates propagate, THE System SHALL use incremental computation to minimize work
1. WHEN caches are used, THE System SHALL achieve >90% hit rates for typical workflows
1. WHEN memory usage is measured, THE System SHALL stay within 500MB for graphs with 10,000 fragments
1. WHEN benchmarks are run, THE System SHALL demonstrate linear or better scaling with graph size

### Requirement 15: Recovery and Consistency Checks

**User Story:** As a developer maintaining document integrity, I want tools to detect and repair inconsistencies, so that I can recover from errors or corruption.

#### Acceptance Criteria

1. WHEN consistency checks are run, THE System SHALL verify that all content hashes match fragment content
1. WHEN broken references are detected, THE System SHALL report missing fragments with suggestions
1. WHEN orphaned fragments exist, THE System SHALL identify fragments not referenced by any document
1. WHEN repairs are applied, THE System SHALL recompute hashes and rebuild indices
1. WHEN recovery completes, THE System SHALL provide a report of actions taken and remaining issues
