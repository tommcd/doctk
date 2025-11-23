# doctk Core Improvements and Graph-Based Document Composition Plan

## Confirmation and Context
- This plan builds on prior analysis of doctk's core API/DSL, gaps (serialization-heavy operations, unstable IDs), and opportunities (richer operations layer, stable identity, DSL surface, LSP/VS Code alignment).
- It also captures the envisioned split/combine + transclusion feature: representing documents as fragment graphs, resolving transclusions into unified views, and enabling sharding/merging flows.

## Goals and Scope
1. **Stabilize the core operations layer** so in-process callers avoid JSON-RPC serialization and retain stable node identities.
2. **Introduce durable document identities** (UUID/content-hash) and provenance metadata to support transclusion and resilient merges.
3. **Add a fragment-graph model** for split/combine, transclusion, and link traversal with cycle safety and incremental caching.
4. **Expose coherent DSL/API surface** that mirrors the graph model and keeps LSP/VS Code tooling in sync.
5. **Deliver production-grade UX + diagnostics** (cycles, missing targets, conflicts) with clear recovery paths.

## Guiding Principles
- Preserve doctk’s composable, pure, pipeable philosophy; operations remain morphisms over persistent data structures.
- Separate **internal APIs** (rich objects, stable IDs) from **external bridges** (JSON-RPC/string payloads).
- Prefer **lazy logical views** with optional **materialized views** that keep provenance for round-tripping edits.
- Keep semantics **deterministic and auditable**: conflicts, cycles, and overlays have explicit policies and defaults.

## Kiro Spec Alignment
- **Spec sources to read first:** `.kiro/steering/*.md` for project-wide conventions, then the relevant specs under `.kiro/specs/` (e.g., `doctk-core-integration` and `doctk-language-server`) in the order `requirements.md → design.md → tasks.md`.
- **Plan for new work:** add a dedicated spec folder (e.g., `.kiro/specs/graph-fragments/`) capturing the split/combine + transclusion feature with full `requirements.md`, `design.md`, and `tasks.md`, following the Kiro checkbox workflow.
- **Task tracking:** represent each slice below as ordered tasks with references back to requirements; update checkboxes as work completes and keep success criteria explicit in `tasks.md`.
- **Spec validation:** pair functional acceptance criteria with the validation guidance in `.kiro/steering/validate-spec-accuracy.md` so tests and docs map directly to requirements.

## Phase Plan (incremental delivery)
1. **Core Foundations (stable IDs + internal API)**
   - Add durable `NodeId` (UUIDv7 or content-hash + lexical hint) and migrate `DocumentTreeBuilder` to preserve/assign IDs.
   - Introduce in-process operations layer returning `Document` objects without JSON serialization; keep JSON-RPC wrappers thin.
   - Add provenance fields (origin file, version, author, timestamp) to nodes and fragments.
   - Provide compatibility shims so existing callers can opt into stable IDs without breakage.

2. **Fragment Graph Model**
   - Define `FragmentGraph` (nodes = document blocks/sections; edges = containment, transclusion, typed links).
   - Implement logical view traversal with cycle detection (topological + depth limits) and policy hooks (error/skip/inline-once).
   - Add materialized view builder that flattens graphs into ordered documents while retaining provenance mappings for round-tripping edits.
   - Cache resolved fragments and invalidate incrementally on edits.

3. **DSL + API Surface**
   - Add DSL operations: `split(by="heading", depth=n)`, `shard(strategy, max_nodes)`, `transclude(id=...)`, `link(from, to, role)`, `hydrate()`, `merge(strategy, on_conflict)`.
   - Provide Python API mirrors with type-safe signatures and metadata consumed by LSP/JSON-RPC catalogs.
   - Extend operation metadata schema to include graph semantics (edge types, conflict policies, view/materialization hints).

4. **Tooling Integration (LSP, VS Code, CLI)**
   - LSP: expose new operations, diagnostics for cycles/missing targets/version skew, hover with provenance, completions for IDs/roles.
   - VS Code extension: graph-aware outline with transclusion badges, provenance tooltips, and error states for broken links; commands for `hydrate`, `split`, `merge`.
   - CLI: commands/subcommands for split/shard/hydrate/merge; JSON outputs include provenance + graph stats.

5. **Conflict/Consistency & Merge Semantics**
   - Define merge strategies (prefer-source/target, annotate, fail) and CRDT-inspired causal hints for reconciliation.
   - Provide overlay semantics (layered docs with priority rules) and validation to prevent ambiguous overlays.
   - Document recovery flows: resync IDs, rebuild caches, cycle resolution guidance.

6. **Performance & Observability**
   - Benchmarks for graph traversal/materialization on large docs; target <200ms for common interactions.
   - Shared performance monitor hooks accessible from CLI/LSP/extension; structured telemetry events.
   - Snapshot-based regression tests for DSL and graph outputs.

## Architecture & Data Model Changes
- **Node Identity:** `NodeId` structure with stable component + display hint; stored on AST nodes and preserved through operations.
- **Document/Fragment Types:**
  - `Document`: current tree with stable IDs and provenance.
  - `Fragment`: a subtree with origin metadata.
  - `FragmentGraph`: adjacency lists for containment, transclusion, and typed links; supports persistence per version.
- **Views:**
  - `LogicalView`: lazy traversal resolving transclusions with cycle guard; suitable for rendering and previews.
  - `MaterializedView`: flattened document with mapping `materialized_range -> {source_id, origin_file, version}` for reverse-projection of edits.
- **Caching:** keyed by graph hash + policy; invalidated on node edits or edge changes.

## API/DSL Specification (initial)
- `split(by="heading", depth=2) -> List[Fragment]`
- `shard(strategy="balanced", max_nodes=200) -> List[Fragment]`
- `transclude(id, mode="embed|link", version=None)`
- `link(from_id, to_id, role="seealso"|"refines"|"depends")`
- `hydrate(root_ids=None, policy={"cycle": "error|skip|inline-once"}) -> MaterializedView`
- `merge(strategy="prefer-source", on_conflict="annotate|fail|prefer-target", overlay=None) -> Document`
- `validate_graph(strict=True) -> Diagnostics`
- All operations emit provenance payloads and stable IDs; JSON-RPC wrappers serialize both logical and materialized views.

## Implementation Steps (detailed)
1. **Stable ID rollout**
   - Add `NodeId` class + utilities; migrate parsers/builders to assign/preserve IDs.
   - Update core operations to retain IDs; add tests covering promotions/moves with identity stability.
   - Introduce compatibility flag for legacy positional IDs; deprecate gradually.

2. **Internal operations layer**
   - Create module (e.g., `doctk.core.ops`) returning rich objects; wrap into existing `StructureOperations` JSON-RPC facade.
   - Refactor REPL/DSL executor to use internal layer directly, avoiding parse/serialize loops.

3. **Fragment graph and traversal**
   - Implement `FragmentGraph` with typed edges and persistence per version.
   - Add cycle detection and traversal policies; provide diagnostics with actionable messages.
   - Implement logical and materialized views with provenance mapping; add unit tests for cycle cases and round-trip edits.

4. **DSL/API and metadata unification**
   - Extend operation registry schema to describe parameters, edge semantics, conflict policies, and view behaviors.
   - Expose new operations in Python API and DSL grammar; add REPL help/examples.
   - Ensure LSP uses the unified metadata for completion/hover/signature help.

5. **Tooling integration**
   - CLI: add commands for split/shard/hydrate/merge with JSON/provenance output; include `--policy` flags.
   - VS Code extension: update tree view to visualize transclusions/links, add commands + diagnostics surfacing.
   - LSP: add diagnostics for cycles/missing targets/conflicts; cache-aware performance tuning.

6. **Merge/conflict resolution**
   - Define overlay rules and conflict policies; implement resolution strategies with annotations where needed.
   - Add tests for merge outcomes and failure modes; document recovery flows.

7. **Performance + observability**
   - Add benchmarks for large graphs; establish budgets and regression gates.
   - Emit structured telemetry events from core + bridges; surface performance warnings in LSP/CLI.

## Deliverables & Tracking
- **Specs & ADRs:** this plan + follow-on ADRs for NodeId scheme, graph semantics, merge policies.
- **APIs:** internal operations module, updated JSON-RPC bridge, DSL grammar extensions, operation registry schema.
- **Implementations:** stable ID builders, fragment graph, traversal/materialization, caching, conflict handling.
- **Tooling:** CLI commands, LSP features, VS Code UI updates.
- **Tests:** unit (core ops, ID stability), integration (DSL, JSON-RPC, REPL), performance benchmarks, snapshot tests for materialized views.
- **Documentation:** user guides for transclusion/sharding/merge flows, diagnostics handbook, performance tuning notes.

## Acceptance Criteria (per phase)
- **Foundations:** Stable IDs retained across edits; in-process API avoids parse/serialize; tests passing.
- **Graph model:** Transclusion resolution with cycle policies; materialized view preserves provenance; caches invalidate correctly.
- **DSL/API:** New operations available with consistent metadata; LSP completions/hovers reflect them.
- **Tooling:** CLI and VS Code commands operational; diagnostics surfaced for cycles/missing targets/conflicts.
- **Performance:** Benchmarks meet interaction budgets; telemetry available and documented.
- **Docs:** Updated guides and ADRs published; recovery playbook for common failure modes.

## Cross-review deltas (Claude comparison)
- **Identity + addressing:** Claude also flagged positional IDs as fragile and pushed for content-based IDs. Our plan already adds durable IDs; refine by pairing content hashes with human-readable hints and keeping positional IDs only as optional UI affordances.
- **API paradigms:** Claude highlighted tension between the declarative morphism API and imperative `StructureOperations`. Add a bridge that converts node IDs to predicates (and vice versa) so DSL/Python flows and JSON-RPC callers share one semantics surface.
- **DSL implementation path:** Claude recommends compiling DSL to the core API instead of duplicating logic. Adjust tasks so the DSL/REPL uses the internal operations layer directly and the registry metadata drives all surfaces (Python, JSON-RPC, DSL, LSP).
- **Type safety + dispatch:** Incorporate type narrowing (e.g., `TypeGuard`) and optional visitor-based dispatch to reduce `isinstance` scatter and make new node types easier to add.
- **Immutability hygiene:** Claude noted mutable metadata and set-union semantics. Add explicit deep-copying of metadata in transforms and either rename `union` to `concat` or implement dedup semantics with tests.
- **Source positions:** To remove brittle line-matching heuristics, store source spans on AST nodes during parse and thread them through operations and materialization.
- **Lenses/bidirectional edits:** Claude introduced lenses for bidirectional transclusion edits. Add this as an advanced slice once stable IDs and materialized views exist, so fragment edits can flow back to sources safely.

## Plan adjustments based on comparison
- **Specs:** Expand the upcoming graph-fragments spec to include: (a) ID↔predicate bridge API, (b) DSL compilation to internal ops, (c) visitor/TypeGuard guidance, (d) source-position carrying AST, and (e) lens-based bidirectional editing as an advanced milestone.
- **Tasks:** Update the phase tasks to explicitly: (1) refactor DSL/REPL to call the internal operations layer, (2) add metadata deep-copying and adjust `union` naming/behavior, and (3) add parser changes for source spans with tests replacing heuristic matching.
- **Acceptance tests:** Add cases that prove ID stability across edits, DSL↔Python parity (same registry metadata), immutability of metadata, correct union semantics, and accurate source spans for diagnostics and round-tripping.

## Open Questions for the Team
- Preferred `NodeId` strategy: UUIDv7 vs. content-hash + lexical hint? Any compliance requirements?
- Should transclusion allow version pinning (e.g., per commit hash) and how to expose that in UX?
- How strict should cycle policies be by default (error vs. inline-once)?
- Do we need cross-repo transclusion, and if so, what auth/provenance format is acceptable?
- Which conflict policies should be surfaced in UX vs. left to advanced users/DSL only?
