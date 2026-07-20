#!/usr/bin/env python3
"""Verify the Rust spike reproduces doctk's output byte for byte.

doctk (Python) is the oracle; the Rust binary is tested against it — the same
migration-harness idea pitched for a real rewrite: you port against a spec
that is already pinned by tests, so you never rewrite blind.

Run from the repo root:  uv run python spikes/rust-wasm-promote/check_against_doctk.py
(Build the binary first: cd spikes/rust-wasm-promote && cargo build --release)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from doctk import Document
from doctk.core import Heading
from doctk.integration.operations import DocumentTreeBuilder, StructureOperations

REPO_ROOT = Path(__file__).resolve().parents[2]
BINARY = Path(__file__).resolve().parent / "target" / "release" / "doctk-spike"

CORPUS_FILES = ["README.md", "CLAUDE.md", "AGENTS.md", "docs/development/testing.md"]

# ATX-only synthetic docs (promote in the spike is ATX-only); scan covers all.
SYNTHETIC_ATX = {
    "duplicates": "## Overview\n\nA.\n\n## Overview\n\nB.\n\n## Overview\n\nC.\n",
    "fenced": "# Real\n\n```md\n# Not a heading\n```\n\n## Real again\n",
    "blockquote": "# Top\n\n> # Quoted\n> text\n\n## After\n",
    "closing_hashes": "## Title ##\n\n### Only ###\n\n#### Kept ####\n",
    "nested": "# A\n\n## B\n\n### C\n\n## D\n\n# E\n",
    "unicode": "# Café résumé\n\n## 日本語\n",
}
# Scan-only extras that exercise setext (spike promote does not handle these).
SYNTHETIC_SCAN_ONLY = {
    "setext": "Main Title\n==========\n\nSection Two\n-----------\n\nBody.\n",
}


def python_scan(text: str) -> list[dict]:
    doc = Document.from_string(text)
    builder = DocumentTreeBuilder(doc)
    out = []
    for index, node in enumerate(doc.nodes):
        if isinstance(node, Heading):
            out.append({"level": node.level, "text": node.text, "id": builder._display_ids[index]})
    return out


def rust_scan(text: str) -> list[dict]:
    result = subprocess.run(
        [str(BINARY), "scan"], input=text.encode(), capture_output=True, check=True
    )
    return [
        {"level": h["level"], "text": h["text"], "id": h["id"]} for h in json.loads(result.stdout)
    ]


def rust_promote(text: str, node_id: str) -> str:
    result = subprocess.run(
        [str(BINARY), "promote", node_id], input=text.encode(), capture_output=True, check=True
    )
    return result.stdout.decode()


def python_promote(text: str, node_id: str) -> str:
    result = StructureOperations.promote(Document.from_string(text), node_id)
    assert result.success, result.error
    return result.document


def main() -> int:
    if not BINARY.exists():
        print(f"binary not built: {BINARY}\n  cd spikes/rust-wasm-promote && cargo build --release")
        return 2

    failures = 0
    checks = 0

    # --- scan conformance -------------------------------------------------
    scan_docs: list[tuple[str, str]] = [
        (p, (REPO_ROOT / p).read_text(encoding="utf-8")) for p in CORPUS_FILES
    ]
    scan_docs += [
        (f"synthetic:{k}", v) for k, v in {**SYNTHETIC_ATX, **SYNTHETIC_SCAN_ONLY}.items()
    ]

    print("scan  (Rust vs doctk):")
    for name, text in scan_docs:
        checks += 1
        py, rs = python_scan(text), rust_scan(text)
        if py == rs:
            print(f"  ok    {name}  ({len(py)} headings)")
        else:
            failures += 1
            print(f"  FAIL  {name}")
            for a, b in zip(py, rs, strict=False):
                if a != b:
                    print(f"          python: {a}")
                    print(f"          rust:   {b}")
                    break
            if len(py) != len(rs):
                print(f"          count: python={len(py)} rust={len(rs)}")

    # --- promote conformance (ATX) ---------------------------------------
    print("\npromote  (Rust vs doctk):")
    promote_docs = [(p, (REPO_ROOT / p).read_text(encoding="utf-8")) for p in CORPUS_FILES]
    promote_docs += [(f"synthetic:{k}", v) for k, v in SYNTHETIC_ATX.items()]

    for name, text in promote_docs:
        headings = python_scan(text)
        # first heading with level >= 2 (promote actually changes something),
        # plus the first heading overall (often h1 -> identity path)
        targets = []
        if headings:
            targets.append(headings[0]["id"])
        deep = next((h["id"] for h in headings if h["level"] >= 2), None)
        if deep and deep not in targets:
            targets.append(deep)

        for node_id in targets:
            checks += 1
            py, rs = python_promote(text, node_id), rust_promote(text, node_id)
            short = node_id.split(":")[1] if ":" in node_id else node_id
            if py == rs:
                print(f"  ok    {name}  [{short}]")
            else:
                failures += 1
                print(f"  FAIL  {name}  [{short}]")
                for i, (a, b) in enumerate(zip(py.split(chr(10)), rs.split(chr(10)), strict=False)):
                    if a != b:
                        print(f"          line {i} python: {a!r}")
                        print(f"          line {i} rust:   {b!r}")
                        break

    print(f"\n{checks - failures}/{checks} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
