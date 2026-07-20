//! Exploratory spike: doctk's stable node ids + `promote`, in Rust.
//!
//! Purpose is to feel three things before committing to any rewrite:
//!   1. writing this domain (AST-ish scanning, content hashing) in Rust,
//!   2. the Rust <-> TypeScript boundary via wasm-bindgen (see the `wasm`
//!      module and README),
//!   3. that a Rust implementation can reproduce doctk's ids **byte for
//!      byte** — verified against the Python oracle by `check_against_doctk.py`.
//!
//! This is NOT wired into the product. It is a decision aid.
//!
//! Scope is deliberately one vertical slice:
//!   - `stable_heading_id` / `scan_headings` mirror `doctk.identity` +
//!     `outlineScanner.ts` (the conformance crux),
//!   - `promote` mirrors `StructureOperations.promote` for ATX headings.
//!
//! Two honest shortcuts a real rewrite would drop:
//!   - the scanner is a line-based approximation of markdown-it (a real
//!     rewrite would use a CommonMark crate such as `comrak`/`markdown-rs`);
//!   - `promote` does line surgery rather than going through a full writer,
//!     so it covers ATX headings, not setext.
//! The oracle check is exactly what exposes where those shortcuts diverge.

use regex::Regex;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::sync::OnceLock;
use unicode_normalization::UnicodeNormalization;

// ---------------------------------------------------------------------------
// Stable id derivation — mirrors doctk/identity.py
// ---------------------------------------------------------------------------

/// NFC, tabs -> 4 spaces, strip + collapse whitespace runs to one space.
/// Mirrors `_canonicalize_node`'s `normalize_text`.
pub fn normalize_text(text: &str) -> String {
    let nfc: String = text.nfc().collect();
    let tabbed = nfc.replace('\t', "    ");
    tabbed.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// Human-readable slug. Mirrors `_generate_hint` for headings.
pub fn generate_hint(text: &str) -> String {
    let lowered: String = text.nfc().collect::<String>().to_lowercase();

    // Keep only [a-z0-9], whitespace, and '-'
    let filtered: String = lowered
        .chars()
        .filter(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c.is_whitespace() || *c == '-')
        .collect();

    // strip, then whitespace runs -> single '-'
    let mut hyphenated = String::new();
    let mut prev_ws = false;
    for c in filtered.trim().chars() {
        if c.is_whitespace() {
            if !prev_ws {
                hyphenated.push('-');
                prev_ws = true;
            }
        } else {
            hyphenated.push(c);
            prev_ws = false;
        }
    }

    // collapse consecutive '-'
    let mut collapsed = String::new();
    let mut prev_hyphen = false;
    for c in hyphenated.chars() {
        if c == '-' {
            if !prev_hyphen {
                collapsed.push('-');
                prev_hyphen = true;
            }
        } else {
            collapsed.push(c);
            prev_hyphen = false;
        }
    }

    // truncate to 32 chars, trim trailing '-'
    let truncated: String = collapsed.chars().take(32).collect();
    let trimmed = truncated.trim_end_matches('-');
    if trimmed.is_empty() {
        "heading".to_string()
    } else {
        trimmed.to_string()
    }
}

/// `heading:{hint}:{sha256(canonical)[..16]}` — matches `str(NodeId)`.
pub fn stable_heading_id(text: &str) -> String {
    let canonical = format!("heading:{}", normalize_text(text));
    let digest = Sha256::digest(canonical.as_bytes());
    let hex: String = digest.iter().map(|b| format!("{b:02x}")).collect();
    format!("heading:{}:{}", generate_hint(text), &hex[..16])
}

// ---------------------------------------------------------------------------
// Scanner — faithful port of extensions/doctk-outliner/src/outlineScanner.ts
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct Heading {
    pub level: u8,
    pub text: String,
    pub line: usize,
    pub id: String,
}

struct Patterns {
    fence_open: Regex,
    fence_close: Regex,
    atx: Regex,
    setext: Regex,
    blockquote: Regex,
    list_item: Regex,
    thematic_break: Regex,
    indented_code: Regex,
}

fn patterns() -> &'static Patterns {
    static P: OnceLock<Patterns> = OnceLock::new();
    P.get_or_init(|| Patterns {
        fence_open: Regex::new(r"^ {0,3}(`{3,}|~{3,})(.*)$").unwrap(),
        fence_close: Regex::new(r"^ {0,3}(`{3,}|~{3,})[ \t]*$").unwrap(),
        atx: Regex::new(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$").unwrap(),
        setext: Regex::new(r"^ {0,3}(=+|-+)[ \t]*$").unwrap(),
        blockquote: Regex::new(r"^ {0,3}>").unwrap(),
        list_item: Regex::new(r"^ {0,3}(?:[-*+]|\d{1,9}[.)])[ \t]").unwrap(),
        thematic_break: Regex::new(r"^ {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
            .unwrap(),
        indented_code: Regex::new(r"^ {4}").unwrap(),
    })
}

/// Returns true if a line is an ATX heading line (used by `promote`).
pub fn is_atx_heading_line(line: &str) -> bool {
    patterns().atx.is_match(line)
}

/// Scan Markdown for top-level ATX + setext headings with stable ids.
pub fn scan_headings(text: &str) -> Vec<Heading> {
    let p = patterns();
    let lines: Vec<&str> = text.split('\n').collect();
    let mut found: Vec<(u8, String, usize)> = Vec::new();

    let mut fence_char = '\0';
    let mut fence_len = 0usize;
    let mut paragraph_start: isize = -1;

    for (i, line) in lines.iter().enumerate() {
        // Inside a fenced code block: nothing is a heading
        if fence_char != '\0' {
            if let Some(c) = p.fence_close.captures(line) {
                let marker = &c[1];
                if marker.starts_with(fence_char) && marker.len() >= fence_len {
                    fence_char = '\0';
                    fence_len = 0;
                }
            }
            continue;
        }
        if let Some(c) = p.fence_open.captures(line) {
            let marker = c[1].to_string();
            let info = &c[2];
            let first = marker.chars().next().unwrap();
            // A backtick fence whose info string contains a backtick is invalid
            if !(first == '`' && info.contains('`')) {
                fence_char = first;
                fence_len = marker.len();
                paragraph_start = -1;
                continue;
            }
        }

        if line.trim().is_empty() {
            paragraph_start = -1;
            continue;
        }

        if p.blockquote.is_match(line) {
            paragraph_start = -1;
            continue;
        }

        if let Some(c) = p.atx.captures(line) {
            let level = c[1].len() as u8;
            let mut heading_text = c.get(2).map_or("", |m| m.as_str()).trim().to_string();
            // strip optional closing sequence
            let close = Regex::new(r"[ \t]+#+$").unwrap();
            heading_text = close.replace(&heading_text, "").to_string();
            if Regex::new(r"^#+$").unwrap().is_match(&heading_text) {
                heading_text = String::new();
            }
            found.push((level, heading_text, i));
            paragraph_start = -1;
            continue;
        }

        // setext underline promotes the open paragraph to a heading
        if paragraph_start >= 0 && p.setext.is_match(line) {
            let underline = line.trim_start();
            let level = if underline.starts_with('=') { 1 } else { 2 };
            let start = paragraph_start as usize;
            let heading_text = lines[start..i]
                .iter()
                .map(|l| l.trim())
                .collect::<Vec<_>>()
                .join("\n");
            found.push((level, heading_text, start));
            paragraph_start = -1;
            continue;
        }

        if p.thematic_break.is_match(line) || p.list_item.is_match(line) {
            paragraph_start = -1;
            continue;
        }

        if p.indented_code.is_match(line) && paragraph_start < 0 {
            continue;
        }

        if paragraph_start < 0 {
            paragraph_start = i as isize;
        }
    }

    assign_ids(found)
}

/// Duplicate-occurrence suffixes, mirroring DocumentTreeBuilder._build_node_map.
fn assign_ids(found: Vec<(u8, String, usize)>) -> Vec<Heading> {
    let mut occurrences: std::collections::HashMap<String, u32> = std::collections::HashMap::new();
    found
        .into_iter()
        .map(|(level, text, line)| {
            let base = stable_heading_id(&text);
            let n = occurrences.entry(base.clone()).or_insert(0);
            *n += 1;
            let id = if *n == 1 {
                base
            } else {
                format!("{base}#{n}")
            };
            Heading {
                level,
                text,
                line,
                id,
            }
        })
        .collect()
}

// ---------------------------------------------------------------------------
// promote — mirrors StructureOperations.promote for ATX headings
// ---------------------------------------------------------------------------

/// Promote a heading (decrease its level by one; h1 is identity).
/// Returns the full document text with only that heading changed.
pub fn promote(text: &str, node_id: &str) -> Result<String, String> {
    let headings = scan_headings(text);
    let target = headings
        .iter()
        .find(|h| h.id == node_id)
        .ok_or_else(|| format!("Node not found: {node_id}"))?;

    // Matches Python's early return: promoting an h1 is a no-op that returns
    // the document unchanged (so exotic source formatting is preserved).
    if target.level <= 1 {
        return Ok(text.to_string());
    }

    let mut lines: Vec<String> = text.split('\n').map(str::to_string).collect();
    if !is_atx_heading_line(&lines[target.line]) {
        return Err(format!(
            "spike promote supports ATX headings only (line {} is setext)",
            target.line
        ));
    }
    let new_level = (target.level - 1) as usize;
    // Re-render the heading line the way doctk's writer does: "#"*level + " " + text
    lines[target.line] = format!("{} {}", "#".repeat(new_level), target.text);
    Ok(lines.join("\n"))
}

// ---------------------------------------------------------------------------
// wasm-bindgen boundary (only compiled with `--features wasm`)
// ---------------------------------------------------------------------------

#[cfg(feature = "wasm")]
mod wasm {
    use wasm_bindgen::prelude::*;

    /// Scan headings, returning a JSON array of `{level, text, line, id}`.
    /// JSON keeps the boundary trivial; a real binding might use
    /// `serde_wasm_bindgen` to hand back structured objects instead.
    #[wasm_bindgen]
    pub fn scan_headings_json(text: &str) -> String {
        serde_json::to_string(&super::scan_headings(text)).unwrap()
    }

    /// Compute the stable id for a heading's text.
    #[wasm_bindgen]
    pub fn stable_heading_id(text: &str) -> String {
        super::stable_heading_id(text)
    }

    /// Promote a heading; throws a JS Error on failure.
    #[wasm_bindgen]
    pub fn promote(text: &str, node_id: &str) -> Result<String, JsError> {
        super::promote(text, node_id).map_err(|e| JsError::new(&e))
    }
}

// ---------------------------------------------------------------------------
// Rust-side unit tests (run with `cargo test`, no wasm target needed)
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn id_is_stable_and_level_independent() {
        // Level is excluded from the canonical form, so text alone drives the id.
        assert_eq!(stable_heading_id("Setup"), stable_heading_id("Setup"));
        assert!(stable_heading_id("Setup").starts_with("heading:setup:"));
    }

    #[test]
    fn hint_slugifies() {
        assert!(stable_heading_id("API Reference Guide!").starts_with("heading:api-reference-guide:"));
        assert!(stable_heading_id("   ").starts_with("heading:heading:")); // empty -> fallback
    }

    #[test]
    fn scan_nests_and_suffixes_duplicates() {
        let doc = "# Top\n\n## A\n\n## A\n";
        let hs = scan_headings(doc);
        assert_eq!(hs.len(), 3);
        assert_eq!(hs[0].level, 1);
        assert_eq!(hs[1].id, stable_heading_id("A"));
        assert_eq!(hs[2].id, format!("{}#2", stable_heading_id("A")));
    }

    #[test]
    fn scan_ignores_fenced_headings() {
        let doc = "# Real\n\n```\n# Fake\n```\n\n## Also real\n";
        let texts: Vec<_> = scan_headings(doc).into_iter().map(|h| h.text).collect();
        assert_eq!(texts, vec!["Real", "Also real"]);
    }

    #[test]
    fn promote_changes_one_line() {
        let doc = "# Top\n\n## Setup\n\nBody.\n";
        let id = stable_heading_id("Setup");
        let out = promote(doc, &id).unwrap();
        assert_eq!(out, "# Top\n\n# Setup\n\nBody.\n");
    }

    #[test]
    fn promote_h1_is_identity() {
        let doc = "# Top ##\n\nBody.\n"; // exotic formatting preserved
        let id = stable_heading_id("Top");
        assert_eq!(promote(doc, &id).unwrap(), doc);
    }
}
