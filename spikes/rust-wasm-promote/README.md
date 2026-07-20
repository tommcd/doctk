# Spike: doctk stable-id + `promote` in Rust → WASM

**Exploratory. Not wired into the product.** This is a decision aid for the
"should we rewrite the core in TypeScript, Rust, or Go?" question raised
alongside [`docs/design/07-revival-plan.md`](../../docs/design/07-revival-plan.md).
Delete it freely.

## What it answers

The biggest ongoing cost of the current Python+TS design is that **two**
implementations derive the stable node ids (the in-process TS outline scanner
and the Python backend), kept in sync by a conformance test. A rewrite is only
worth it if a single core can reproduce doctk's ids **byte for byte**. This
spike shows a Rust implementation doing exactly that, verified against doctk as
the oracle.

Verified in-session (`check_against_doctk.py`), **29/29 byte-identical**:

- `scan` over the repo corpus (README, CLAUDE, AGENTS, testing.md) plus
  adversarial docs: duplicates (`#2` suffixes), fenced/blockquoted headings,
  closing-hash sequences, setext, and unicode (`Café résumé`, `日本語` — NFC
  normalization and the ASCII-only hint fallback both match Python);
- `promote` output over the same ATX docs, including the closing-hash
  re-render and the h1 identity case.

## Layout

| File | What it is |
|------|-----------|
| `src/lib.rs` | The core: `stable_heading_id`, `scan_headings`, `promote`, and the `#[wasm_bindgen]` boundary. Rust unit tests at the bottom. |
| `src/main.rs` | Native CLI (`scan` / `promote`) used by the oracle check. |
| `check_against_doctk.py` | Compares the Rust binary to doctk byte for byte. |
| `demo.mjs` | Node demo of the core through the WASM boundary. |

## Reproduce the oracle check (no wasm target needed)

```bash
cd spikes/rust-wasm-promote
cargo test                       # Rust-side unit tests
cargo build --release            # builds the native CLI
cd ../.. && uv run python spikes/rust-wasm-promote/check_against_doctk.py
```

Expect `29/29 checks passed`. (This is the part that was run and verified in
the session — it needs only `cargo` + `doctk`, no wasm toolchain.)

## Build the WASM and run the TS-side demo (your laptop)

The `wasm32-unknown-unknown` target needs `rustup`, so this part runs where you
have a full Rust install:

```bash
rustup target add wasm32-unknown-unknown
cargo install wasm-pack
cd spikes/rust-wasm-promote
wasm-pack build --target nodejs --features wasm
node demo.mjs
```

You should see the outline, then the second `Setup` (id ending `#2`) promoted
with a single line changed. That `scan_headings_json(...)` / `promote(...)` call
site **is** the ergonomics to evaluate: this is what the extension would call
instead of shelling out to Python.

## What to notice (the point of the exercise)

**Where Rust fit this domain well**
- Content hashing / normalization is a couple of real crates (`sha2`,
  `unicode-normalization`) — no ceremony, and NFC matched Python's `unicodedata`
  exactly.
- The value types (`Heading`, the id derivation) are small and total; `serde`
  derives the JSON boundary for free.
- `cargo test` gives you the Rust-side safety net; the Python oracle gives you
  the cross-language one. Porting against an oracle that is already pinned by
  tests is the low-risk way to migrate — you never rewrite blind.

**Honest shortcuts this spike takes** (a real rewrite would drop them, and each
is a useful thing to feel now)
- The scanner is a **line-based regex approximation** of markdown-it. It matches
  doctk on everything tested here, but a real rewrite should parse with a
  CommonMark crate (`comrak` / `markdown-rs`) so the outline can never drift
  from the writer. The conformance check is precisely what would catch drift.
- `promote` does **line surgery**, so it covers ATX headings, not setext. Going
  through a real writer (as the Python side does) removes that limit.
- The WASM boundary passes **JSON strings** for simplicity. `serde-wasm-bindgen`
  would hand back structured objects instead.

**The boundary cost.** Every call serializes across JS↔WASM. For per-action
work (promote/nest) that is nothing. If the outline scan also moved into WASM
(to collapse the two-implementation problem), it would run on every debounced
change — still fine at this size, but that is the one number worth measuring on
a large document before committing.

## Takeaway for the decision

A single Rust core **can** be the one source of truth for both the in-process
outline and the operations, reproducing today's ids exactly — which neither a
Go backend (can't be in-process) nor "stay as-is" achieves. The curve is real
(the scanner and the writer both want proper CommonMark handling), but the
foundation — ids, hashing, the WASM boundary — came together cleanly and
verifiably in an afternoon.
