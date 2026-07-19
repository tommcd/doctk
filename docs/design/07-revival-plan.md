# 07 - Revival Plan: A Personal Structural Editor on an Algebraic Core

**Status**: Active
**Date**: 2026-07-19
**Supersedes**: `core-api-stabilization` phases 2-8, `fragment-graph-model`, `advanced-graph-features` (all deferred indefinitely)

## Why this plan exists

Development stopped in November 2025 at phase 1 of an 8-phase, 321-checkbox
stabilization spec that was itself a precondition for a 24-30 week graph
re-architecture. A July 2026 review found the working code is good (887 passing
tests, real pygls LSP, real VS Code bridge) but incoherent as a product:

- The writer silently drops content the parser doesn't model (HTML blocks,
  thematic breaks), so any edit through the extension can corrupt a real file.
- The stable-identity system (`identity.py`, the last thing built) is imported
  by nothing in `integration/`, `lsp/`, or `dsl/`; every editing path uses
  positional IDs (`h2-0`) that its own docstrings call unstable.
- Four operation vocabularies disagree (functional ops, `StructureOperations`,
  REPL grammar, DSL executor), and the README's flagship pipeline
  `doc | select(heading) | promote()` crashes with a type error.
- The extension broke on VS Code restart (bare `python3` + inherited `PATH`)
  and felt slow (full-document JSON round trips on every keystroke).

## Goal

A personal tool: structural Markdown outlining and editing in VS Code, driven
by a small algebra of document operations that is actually lawful -
operations are total, composable, identity-stable, and never lose content.
No market goals. No PyPI/marketplace release until the tool survives a month
of daily personal use.

## The four steps

### 1. Round-trip foundation (first, everything rests on it)

Parse -> write must be faithful before any operation can be trusted.

- Every block the parser does not model becomes a `RawBlock` preserved
  verbatim - nothing is ever silently dropped.
- Nodes carry their exact source text; the writer emits it unchanged for
  untouched nodes and renders only nodes an operation actually changed.
- **Acceptance**: `write(parse(x)) == x` byte-identical for a corpus of real
  files; editing one heading changes only that heading's line; output is
  idempotent under re-parse.

### 2. One algebra

- Wire `identity.py` NodeIds into `StructureOperations` and the bridge,
  replacing positional `h2-0` IDs.
- Collapse the four operation vocabularies into one; every documented example
  must execute (fix `select`/`heading` composition, implement `nest(under=)`).
- Delete consumer-less scaffolding (`integration/memory.py`, `performance.py`,
  `compat.py`, `errors.py`, unwired `lsp/ai_support.py`, legacy parser paths).
- **Acceptance**: README examples run as doctests; one vocabulary shared by
  Python API, DSL, and bridge; operations are total (no `NotImplementedError`).

### 3. Reliable bridge

- Resolve the interpreter via the ms-python extension API, with an explicit
  `doctk.pythonPath` override; health-check on spawn.
- On failure, show an actionable message ("doctk not importable from
  /usr/bin/python3 - set doctk.pythonPath"), never a silent dead extension.
- **Acceptance**: extension works after a cold VS Code restart from the GUI,
  in a workspace that is not the doctk repo.

### 4. Performance shape

- Build the outline tree in TypeScript on document change (no Python in the
  keystroke path); call Python once per user action (promote/nest/move).
- One Python process, not two.
- **Acceptance**: outline updates feel instant on a 500-heading document;
  each edit action completes in under ~100 ms end to end.

## Explicitly descoped

Fragment graphs, transclusion, CRDT merge, bidirectional lenses, additional
formats, PyPI/marketplace release, and all of `core-api-stabilization`
phases 2-8. These stay archived unless the tool earns daily use first.

## Process rules for this revival

- Specs for this work are one page or less; this document is the spec.
- The round-trip property test is the permanent quality gate: no change that
  breaks byte-fidelity on the corpus may merge.
- Ship each step as one small PR; use the tool between steps.

## Kill criteria

If, after steps 1-3, the extension is not something reached for weekly, stop:
archive the repo with a short honest note in the README. The experiment will
still have been worth it for what it taught about spec-driven AI development.
