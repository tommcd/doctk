# Requirements Document: Fragment Graph Model

## Introduction

This document specifies requirements for implementing a graph-based document composition model in doctk. This feature enables splitting large documents into smaller fragments, linking fragments through transclusion, and recombining them into unified views. The model is inspired by category theory (presheaves, functors) and provides content-addressed storage for stable references.

This work builds on the Core API Stabilization spec and enables advanced features like bidirectional editing and conflict resolution.

## Glossary

- **Fragment**: A self-contained document subtree with stable identity and provenance metadata
- **Fragment Graph**: A directed graph where nodes are fragments and edges represent containment, transclusion, or typed links
- **Content Address**: A SHA-256 hash of canonical fragment content used for stable references
- **Transclusion**: Embedding one fragment's content into another document (like `{{#include path.md}}`)
- **Logical View**: A lazy traversal of a fragment graph that resolves transclusions on-demand
- **Materialized View**: An eagerly computed flattened document with provenance mappings
- **Provenance**: Metadata tracking a fragment's origin (file, version, author, timestamp)
- **Cycle Detection**: Identifying circular transclusion references to prevent infinite loops
- **Sharding**: Splitting a large document into balanced fragments based on size or structure
- **Hydration**: Resolving all transclusions in a fragment graph to produce a unified document

## Requirements

### Requirement 1: Fragment Identity and Storage

**User Story:** As a developer working with document fragments, I want each fragment to have a stable content-addressed identity, so that references remain valid even when documents are reorganized.

#### Acceptance Criteria

1. WHEN a fragment is created, THE System SHALL compute a SHA-256 content hash as its address
1. WHEN fragment content is canonicalized, THE System SHALL use UTF-8 encoding with LF line endings and sorted metadata keys
1. WHEN a fragment is stored, THE System SHALL save it with both its content hash and an optional human-readable alias
1. WHEN a fragment is retrieved by hash, THE System SHALL return the exact content or None if not found
1. WHEN a fragment is retrieved by alias, THE System SHALL resolve the alias to a content hash and return the fragment

### Requirement 2: Fragment Graph Structure

**User Story:** As a developer modeling document relationships, I want to represent documents as graphs with typed edges, so that I can express containment, transclusion, and semantic links.

#### Acceptance Criteria

1. WHEN a fragment graph is created, THE System SHALL support nodes (fragments) and typed edges (containment, transclusion, link)
1. WHEN an edge is added, THE System SHALL validate that source and target fragments exist
1. WHEN a transclusion edge is created, THE System SHALL store the target content address and optional version
1. WHEN a link edge is created, THE System SHALL support semantic roles (seealso, refines, depends)
1. WHEN the graph is persisted, THE System SHALL serialize the adjacency structure with edge metadata

### Requirement 3: Document Splitting

**User Story:** As a technical writer managing large documents, I want to split documents by heading level or size, so that I can work with manageable fragments.

#### Acceptance Criteria

1. WHEN a document is split by heading level, THE System SHALL create one fragment per top-level section
1. WHEN a document is split by size, THE System SHALL create balanced fragments respecting structural boundaries
1. WHEN fragments are created, THE System SHALL assign stable content addresses to each fragment
1. WHEN splitting completes, THE System SHALL return a fragment graph with containment edges
1. WHEN fragments are saved, THE System SHALL write each fragment to a separate file with its content hash

### Requirement 4: Transclusion Syntax and Resolution

**User Story:** As a documentation engineer, I want to embed fragments using familiar syntax, so that I can compose documents from reusable pieces.

#### Acceptance Criteria

1. WHEN a document contains `{{#include path.md}}`, THE System SHALL recognize it as a file-based transclusion
1. WHEN a document contains `{{#include sha256:abc123...}}`, THE System SHALL recognize it as a hash-based transclusion
1. WHEN a document contains `{{#include api@v1.2.0}}`, THE System SHALL recognize it as a versioned transclusion
1. WHEN transclusions are resolved, THE System SHALL replace the syntax with the target fragment's content
1. WHEN a transclusion target is missing, THE System SHALL report a diagnostic with the missing reference

### Requirement 5: Logical View Traversal

**User Story:** As a developer rendering documents, I want to traverse fragment graphs lazily, so that I can preview composed documents without materializing all content.

#### Acceptance Criteria

1. WHEN a logical view is created, THE System SHALL traverse the fragment graph starting from specified roots
1. WHEN a transclusion edge is encountered, THE System SHALL resolve the target fragment on-demand
1. WHEN cycles are detected, THE System SHALL apply the configured policy (error, skip, inline-once)
1. WHEN traversal completes, THE System SHALL return a document structure with transclusions resolved
1. WHEN traversal is interrupted, THE System SHALL provide partial results with diagnostic information
1. WHEN a graph has no transclusions, THE System SHALL return the original fragments unchanged (presheaf identity law)
1. WHEN nested transclusions are resolved, THE System SHALL produce the same result as resolving a flattened graph (presheaf composition law)

### Requirement 6: Materialized View Generation

**User Story:** As a developer enabling bidirectional editing, I want to flatten fragment graphs into documents with provenance mappings, so that edits can be propagated back to sources.

#### Acceptance Criteria

1. WHEN a materialized view is created, THE System SHALL flatten the fragment graph into a single document
1. WHEN content is included from fragments, THE System SHALL record provenance (source ID, origin file, version)
1. WHEN the view is queried, THE System SHALL map any position to its source fragment and location
1. WHEN the view is serialized, THE System SHALL include provenance metadata for debugging
1. WHEN edits are applied to the view, THE System SHALL identify affected source fragments via provenance

### Requirement 7: Cycle Detection and Policies

**User Story:** As a developer preventing infinite loops, I want automatic cycle detection with configurable policies, so that circular transclusions are handled safely.

#### Acceptance Criteria

1. WHEN a fragment graph is traversed, THE System SHALL detect cycles using depth-first search
1. WHEN a cycle is detected with policy "error", THE System SHALL raise an exception with the cycle path
1. WHEN a cycle is detected with policy "skip", THE System SHALL omit the cyclic transclusion and continue
1. WHEN a cycle is detected with policy "inline-once", THE System SHALL include the fragment once and skip subsequent references
1. WHEN diagnostics are generated, THE System SHALL report all detected cycles with clear paths

### Requirement 8: Fragment Sharding Strategies

**User Story:** As a developer optimizing large documents, I want multiple sharding strategies, so that I can balance fragments by size, structure, or semantic boundaries.

#### Acceptance Criteria

1. WHEN sharding with strategy "balanced", THE System SHALL create fragments of approximately equal node count
1. WHEN sharding with strategy "size", THE System SHALL create fragments targeting a maximum byte size
1. WHEN sharding with strategy "semantic", THE System SHALL respect heading hierarchy and section boundaries
1. WHEN sharding completes, THE System SHALL return a fragment graph with appropriate edges
1. WHEN sharding is configured, THE System SHALL accept parameters like max_nodes or max_bytes

### Requirement 9: Hydration and Recomposition

**User Story:** As a documentation engineer, I want to combine fragments into a unified document, so that I can publish complete documentation from modular sources.

#### Acceptance Criteria

1. WHEN hydration is invoked, THE System SHALL resolve all transclusions in the fragment graph
1. WHEN root fragments are specified, THE System SHALL start traversal from those roots
1. WHEN no roots are specified, THE System SHALL identify entry points automatically
1. WHEN hydration completes, THE System SHALL return a single unified document
1. WHEN hydration fails, THE System SHALL report missing fragments or unresolvable cycles

### Requirement 10: Provenance Tracking

**User Story:** As a developer maintaining document history, I want fragments to carry provenance metadata, so that I can track origins, versions, and authorship.

#### Acceptance Criteria

1. WHEN a fragment is created, THE System SHALL record origin file, creation timestamp, and author
1. WHEN a fragment is versioned, THE System SHALL store version identifiers (commit hash, tag, or semantic version)
1. WHEN fragments are transcluded, THE System SHALL preserve provenance through the composition
1. WHEN provenance is queried, THE System SHALL return complete metadata for any fragment
1. WHEN provenance is displayed, THE System SHALL format it in human-readable form

### Requirement 11: Fragment Caching

**User Story:** As a developer optimizing performance, I want resolved fragments to be cached, so that repeated traversals are fast.

#### Acceptance Criteria

1. WHEN a fragment is resolved, THE System SHALL cache the result keyed by content hash and policy
1. WHEN a fragment is edited, THE System SHALL invalidate cached entries for that fragment
1. WHEN dependent fragments exist, THE System SHALL invalidate caches transitively
1. WHEN cache size exceeds limits, THE System SHALL evict least-recently-used entries
1. WHEN cache statistics are requested, THE System SHALL report hit rate and memory usage

### Requirement 12: Typed Link Semantics

**User Story:** As a developer modeling document relationships, I want typed links between fragments, so that I can express semantic relationships beyond transclusion.

#### Acceptance Criteria

1. WHEN a link is created, THE System SHALL support roles: seealso, refines, depends, extends
1. WHEN links are queried, THE System SHALL return all links of a specified role
1. WHEN links are traversed, THE System SHALL provide navigation in both directions
1. WHEN links are validated, THE System SHALL check that target fragments exist
1. WHEN links are displayed, THE System SHALL show role and target information

### Requirement 13: DSL Operations for Graphs

**User Story:** As a developer using the doctk DSL, I want operations for splitting, transcluding, hydrating, merging, and validating graphs, so that I can work with fragment graphs interactively.

#### Acceptance Criteria

1. WHEN `split(by="heading", depth=2)` is executed, THE System SHALL split the document and return a fragment graph
1. WHEN `transclude(id="abc123")` is executed, THE System SHALL add a transclusion edge to the graph
1. WHEN `link(from="id1", to="id2", role="seealso")` is executed, THE System SHALL add a typed link edge
1. WHEN `hydrate()` is executed, THE System SHALL resolve transclusions and return a unified document
1. WHEN `shard(strategy="balanced", max_nodes=200)` is executed, THE System SHALL create balanced fragments
1. WHEN `merge(strategy="prefer-source", on_conflict="annotate")` is executed, THE System SHALL merge fragments using the specified strategy
1. WHEN `validate_graph(strict=True)` is executed, THE System SHALL check for cycles, missing targets, and return diagnostics

### Requirement 14: LSP Integration for Graphs

**User Story:** As a developer using VS Code, I want LSP support for fragment references, so that I get completions, hover info, and diagnostics for transclusions.

#### Acceptance Criteria

1. WHEN typing a transclusion reference, THE Language Server SHALL provide completions for available fragments
1. WHEN hovering over a transclusion, THE Language Server SHALL show fragment provenance and preview
1. WHEN a transclusion target is missing, THE Language Server SHALL report a diagnostic
1. WHEN a cycle exists, THE Language Server SHALL report a diagnostic with the cycle path
1. WHEN fragments are renamed, THE Language Server SHALL update transclusion references
1. WHEN a transclusion references a different version than available, THE Language Server SHALL report a version skew diagnostic

### Requirement 15: CLI Commands for Graphs

**User Story:** As a developer automating document workflows, I want CLI commands for splitting, hydrating, merging, and validating fragment graphs, so that I can integrate with build systems.

#### Acceptance Criteria

1. WHEN `doctk split <file> --by heading --depth 2` is executed, THE CLI SHALL split the document and save fragments
1. WHEN `doctk hydrate <graph>` is executed, THE CLI SHALL resolve transclusions and output a unified document
1. WHEN `doctk validate-graph <graph>` is executed, THE CLI SHALL check for cycles and missing references
1. WHEN `doctk shard <file> --strategy balanced --max-nodes 200` is executed, THE CLI SHALL create balanced fragments
1. WHEN `doctk merge <graph> --strategy prefer-source --on-conflict annotate` is executed, THE CLI SHALL merge fragments and output the result
1. WHEN CLI commands complete, THE System SHALL output JSON with provenance and statistics

### Requirement 16: VS Code Extension for Graphs

**User Story:** As a developer using VS Code, I want a graph-aware document outline with visual indicators for transclusions and links, so that I can navigate and understand document composition.

#### Acceptance Criteria

1. WHEN a document contains transclusions, THE Extension SHALL display transclusion badges in the outline view
1. WHEN hovering over a transclusion badge, THE Extension SHALL show provenance tooltips with source fragment information
1. WHEN a transclusion target is missing, THE Extension SHALL display an error state in the outline
1. WHEN a fragment has typed links, THE Extension SHALL show link indicators with role information
1. WHEN the outline is rendered, THE Extension SHALL use the LSP to retrieve graph structure and metadata

### Requirement 17: Performance and Observability

**User Story:** As a developer working with fragment graphs, I want fast operations with telemetry, so that I can monitor performance and identify bottlenecks.

#### Acceptance Criteria

1. WHEN graph operations are performed, THE System SHALL complete common interactions within 200 milliseconds
1. WHEN traversal or materialization occurs, THE System SHALL emit structured telemetry events
1. WHEN performance thresholds are exceeded, THE System SHALL log warnings with operation details
1. WHEN telemetry is enabled, THE CLI SHALL output performance statistics with results
1. WHEN the LSP processes graphs, THE Language Server SHALL expose performance metrics for monitoring

### Requirement 18: Transclusion Syntax Adapters

**User Story:** As a developer working with existing documentation, I want support for multiple transclusion syntaxes, so that I can integrate with other documentation systems.

#### Acceptance Criteria

1. WHEN a document contains mdBook-style `{{#include}}` syntax, THE System SHALL recognize and process it
1. WHEN a document contains Org-mode-style `#+INCLUDE:` syntax, THE System SHALL recognize and process it
1. WHEN a document contains DITA-style `<conref>` syntax, THE System SHALL recognize and process it
1. WHEN syntax adapters are configured, THE System SHALL allow enabling/disabling specific syntaxes
1. WHEN multiple syntaxes are present, THE System SHALL process them according to configured precedence
