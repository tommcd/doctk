# Requirements Document: Core API Stabilization

## Introduction

This document specifies requirements for stabilizing the doctk core API and DSL to address architectural gaps identified in the design review. The work focuses on establishing stable node identities, creating an internal operations layer that avoids over-serialization, improving type safety, ensuring immutability, and unifying the dual API paradigms (declarative morphisms vs imperative structure operations).

This is foundational work that enables future graph-based features like document splitting, transclusion, and bidirectional editing.

## Glossary

- **Node ID**: A stable, durable identifier for document nodes that persists across edits and parsing
- **Content Hash**: A SHA-256 hash of canonical node content used for content-addressable storage
- **Internal Operations Layer**: Python API that returns rich Document objects without JSON serialization
- **JSON-RPC Bridge**: External interface that wraps internal operations for TypeScript/LSP clients
- **Predicate**: A function that tests whether a node matches certain criteria
- **Source Span**: Line and column position information for AST nodes from original source
- **Metadata Immutability**: Ensuring metadata dictionaries are deep-copied during transformations
- **TypeGuard**: Python type narrowing mechanism (PEP 647) for safer type checking
- **Visitor Pattern**: Design pattern for traversing and operating on AST nodes by type

## Requirements

### Requirement 1: Stable Node Identity and Provenance

**User Story:** As a developer building document transformations, I want node IDs to remain stable across edits and re-parsing with provenance metadata, so that I can reliably reference specific nodes in multi-step operations and track their origins.

#### Acceptance Criteria

1. WHEN a document is parsed, THE System SHALL assign each node a stable ID that combines content-hash with a human-readable hint
1. WHEN a node is edited, THE System SHALL preserve the node ID if the structural identity remains unchanged
1. WHEN a document is re-parsed, THE System SHALL assign the same IDs to structurally equivalent nodes
1. WHEN nodes are promoted, demoted, or moved, THE System SHALL retain their stable IDs
1. WHEN a node's canonical content changes, THE System SHALL assign a new ID to reflect the changed identity
1. WHEN a node is created, THE System SHALL attach provenance metadata (origin file, version, author, timestamp)
1. WHEN nodes are transformed, THE System SHALL preserve or update provenance metadata appropriately

**Note:** Acceptance Criterion 5 clarifies that nodes with identical canonical content (after normalization) are treated as the same logical entity and receive the same ID. This supports undo/redo, document merging, and transclusion use cases. Provenance metadata tracks creation and modification history separately from identity.

### Requirement 2: Internal Operations Layer

**User Story:** As a developer using doctk operations in Python, I want to work with rich Document objects directly, so that I avoid the overhead and fragility of JSON serialization/deserialization in multi-step pipelines.

#### Acceptance Criteria

1. WHEN an operation is invoked through the internal API, THE System SHALL return a Document object with stable node IDs
1. WHEN multiple operations are chained, THE System SHALL preserve node identity without re-parsing
1. WHEN the DSL executor runs commands, THE DSL Executor SHALL use the internal operations layer directly
1. WHEN the REPL processes commands, THE REPL SHALL maintain document state using internal operations
1. WHEN the JSON-RPC bridge receives requests, THE Bridge SHALL wrap internal operations and serialize results only at the boundary

### Requirement 3: Source Position Tracking

**User Story:** As a developer debugging document operations, I want AST nodes to carry their original source positions, so that error messages are accurate and I can map between materialized views and source documents.

#### Acceptance Criteria

1. WHEN a document is parsed, THE Parser SHALL attach source spans (line, column ranges) to each block-level AST node with block-level precision
1. WHEN operations transform nodes, THE System SHALL preserve or update source spans appropriately
1. WHEN an error occurs during parsing or execution, THE System SHALL report the source location with block-level precision
1. WHEN the LSP provides diagnostics, THE Language Server SHALL use source spans for accurate positioning
1. WHEN materialized views are created, THE System SHALL maintain mappings from view positions to source positions
1. WHEN inline elements are parsed, THE System SHALL inherit source location from their containing block

**Note:** "Block-level precision" means accurate line and column positions for structural elements (headings, paragraphs, lists, code blocks). Inline elements (bold, links, inline code) inherit their parent block's position. This is sufficient for LSP diagnostics, go-to-definition, and most editing operations. Inline-level precision can be added in a future enhancement if needed.

### Requirement 4: Metadata Immutability

**User Story:** As a developer relying on functional purity, I want node metadata to be truly immutable, so that transformations don't accidentally mutate shared state.

#### Acceptance Criteria

1. WHEN a node is transformed, THE System SHALL deep-copy the metadata dictionary
1. WHEN a transformed node's metadata is modified, THE Original Node SHALL remain unchanged
1. WHEN operations create new nodes, THE System SHALL ensure metadata is not shared by reference
1. WHEN tests verify immutability, THE Tests SHALL confirm that metadata mutations don't affect original nodes
1. WHEN performance is measured, THE System SHALL demonstrate acceptable overhead from deep-copying

### Requirement 5: API Paradigm Unification

**User Story:** As a developer learning doctk, I want a unified mental model for operations, so that I can seamlessly use both declarative pipelines and imperative structure operations without confusion.

#### Acceptance Criteria

1. WHEN a node ID is provided, THE System SHALL offer a predicate function that selects by that ID
1. WHEN declarative operations are used, THE System SHALL support targeting specific nodes via ID predicates
1. WHEN StructureOperations are invoked, THE Implementation SHALL delegate to the declarative pipeline internally
1. WHEN operation metadata is defined, THE System SHALL use a single schema consumed by Python API, DSL, and LSP
1. WHEN documentation is written, THE Documentation SHALL clearly explain when to use each API style

### Requirement 6: Type Safety Improvements

**User Story:** As a developer adding new node types, I want type-safe dispatch mechanisms, so that I can avoid scattered isinstance checks and get better IDE support.

#### Acceptance Criteria

1. WHEN operations check node types, THE System SHALL use TypeGuard functions for type narrowing
1. WHEN new node types are added, THE System SHALL support visitor-based dispatch as an option
1. WHEN type checkers analyze code, THE Type Checker SHALL correctly narrow types after TypeGuard checks
1. WHEN operations are defined, THE System SHALL provide clear type signatures with Generic support
1. WHEN tests verify type safety, THE Tests SHALL confirm that type narrowing works correctly

### Requirement 7: Performance Preservation

**User Story:** As a user working with large documents, I want the stabilization work to maintain or improve performance, so that my workflows remain responsive.

#### Acceptance Criteria

1. WHEN stable IDs are computed, THE System SHALL complete ID generation within 10% of baseline parsing time
1. WHEN internal operations are used, THE System SHALL demonstrate faster execution than JSON-RPC round-trips
1. WHEN metadata is deep-copied, THE System SHALL maintain operation performance within 15% of baseline
1. WHEN benchmarks are run, THE System SHALL meet the existing performance budgets (1s render, 200ms interaction)
1. WHEN memory is measured, THE System SHALL not increase memory usage by more than 20% for typical documents

### Requirement 8: Operation Registry Unification

**User Story:** As a developer maintaining multiple interfaces (Python, DSL, LSP), I want a single source of truth for operation metadata, so that signatures and documentation stay synchronized.

#### Acceptance Criteria

1. WHEN an operation is registered, THE Registry SHALL store its signature, parameters, return type, and documentation
1. WHEN the Python API is used, THE API SHALL derive type hints from the registry
1. WHEN the DSL parser validates commands, THE Parser SHALL use registry metadata for validation
1. WHEN the LSP provides completions, THE Language Server SHALL use registry metadata for suggestions
1. WHEN documentation is generated, THE System SHALL extract operation docs from the registry

### Requirement 9: Diagnostic Improvements

**User Story:** As a developer debugging document operations, I want clear, actionable error messages with source locations, so that I can quickly identify and fix issues.

#### Acceptance Criteria

1. WHEN a parsing error occurs, THE System SHALL report the exact line and column with context
1. WHEN an operation fails, THE System SHALL include the node ID and source location in the error
1. WHEN type mismatches occur, THE System SHALL explain what type was expected and what was received
1. WHEN the LSP reports diagnostics, THE Language Server SHALL provide quick-fix suggestions where applicable
1. WHEN errors are logged, THE System SHALL include structured metadata for debugging tools
