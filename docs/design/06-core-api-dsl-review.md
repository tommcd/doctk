# Core API and DSL Review

## Overview
The doctk core exposes a functional document model (`Document`, `Node`) with composable structure operations, a DSL with REPL/script execution, and an integration layer that powers the VS Code extension and language server. Operations emphasize purity, pipeability, and granular edit metadata to keep front-end clients in sync.

## Strengths
- **Composable functional core**: Operations are pure, chainable, and reuse a common AST, making pipelines predictable and testable.
- **Integration-first architecture**: A shared JSON-RPC bridge, operation registry, and granular edit ranges let multiple clients (VS Code, LSP, REPL) share consistent behavior.
- **Performance guardrails**: Incremental parsing, caching, and benchmarking for large documents keep interaction budgets realistic.
- **Developer ergonomics**: Rich REPL/script tooling, comprehensive tests, and clear separation between platform-agnostic logic and client adapters.

## Gaps & Risks
- **Over-serialization in-process**: Internal callers still consume JSON/RPC-shaped responses, forcing reparsing and ID remapping that can break multi-step pipelines and code-block chaining.
- **Unstable identifiers**: Node IDs remain position-derived; complex edits risk drift for transclusion/link targets or long-running DSL sessions.
- **View/model divergence**: No formal notion of logical vs. materialized views, making future split/combine or overlay semantics harder to reason about.
- **Error/resilience gaps for graph features**: Cycle detection, missing-target diagnostics, and provenance tracking are not yet first-class, limiting confidence for cross-document references.

## Suggestions for a Richer Core API/DSL
- **Dual APIs (in-process + RPC wrapper)**: Expose an internal operations layer that returns `Document` objects with stable IDs, with a thin JSON-RPC facade for external clients to remove reparsing overhead.
- **Durable identity scheme**: Introduce stable node IDs (UUID or content-hash) preserved across edits; add provenance metadata to support cross-document references and merges.
- **Graph-aware views**: Define logical and materialized views for transclusion/links, with explicit cycle policies and conflict strategies; expose `hydrate`/`materialize` operations in the DSL.
- **Stateful DSL execution**: Allow REPL/scripts to hold onto parsed documents and operation results, enabling transactional batches, speculative edits, and faster multi-step pipelines.
- **Unified operation metadata**: Centralize operation schemas consumed by the registry, LSP, and DSL docs to keep signatures/descriptions synchronized across channels.

## Opportunities to Strengthen the Design
- **Graph model for split/combine**: Represent documents as fragment graphs with containment, link, and transclusion edges; lift existing tree operations to graph morphisms to support sharding and recomposition.
- **Conflict-aware merging**: Borrow CRDT/overlay filesystem ideas to resolve shard merges with policies (`prefer-source`, `annotate`, `manual`) and provenance annotations.
- **Navigation & diagnostics**: Add graph-aware outline diagnostics (cycles, missing targets, version skew) and hover/tooling that surface source provenance and link semantics.
- **Performance & observability**: Cache resolved fragments, incrementally invalidate on edit, and extend performance monitoring to graph traversals with thresholds for resolution and materialization.
- **Ecosystem alignment**: Provide adapters for common transclusion syntaxes (Markdown include, Org noweb, DITA conref) to avoid reinventing formats and ease adoption.

