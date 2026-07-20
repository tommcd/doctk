/**
 * Pure Markdown heading scanner with backend-compatible stable ids.
 *
 * This module keeps Python out of the keystroke path: the outline tree is
 * built here, in-process, on every (debounced) document change. Python is
 * only consulted when the user performs an action (promote/nest/move).
 *
 * The ids emitted here MUST match doctk's Python implementation
 * (doctk.identity NodeId + doctk.integration DocumentTreeBuilder) byte for
 * byte, because operations send these ids back to the backend for
 * resolution. The derivation is:
 *
 *   canonical = "heading:" + normalize(text)   // level excluded, so ids
 *                                              // survive promote/demote
 *   id = "heading:" + hint(text) + ":" + sha256(canonical)[0..16]
 *   duplicates get "#2", "#3", ... suffixes in document order
 *
 * Conformance is enforced by tests/e2e/test_ts_scanner_conformance.py,
 * which runs this compiled module against doctk's Python output over a
 * corpus of real and adversarial documents.
 *
 * No vscode imports here - this module is plain Node and unit-testable.
 */

import { createHash } from 'crypto';

export interface ScannedHeading {
  /** Heading level 1-6. */
  level: number;
  /** Raw inline text (markup preserved, as markdown-it token content). */
  text: string;
  /** 0-indexed line of the heading start (paragraph start for setext). */
  line: number;
  /** Backend-resolvable stable id, with occurrence suffix for duplicates. */
  id: string;
}

/**
 * Normalize text exactly as doctk.identity._canonicalize_node does:
 * NFC, tabs to 4 spaces, strip + collapse all whitespace runs to one space.
 */
function normalizeText(text: string): string {
  let normalized = text.normalize('NFC');
  normalized = normalized.replace(/\t/g, '    ');
  // Python str.split() splits on Unicode whitespace; \s with the u flag is
  // the closest JS equivalent (divergence only on exotic control chars).
  const parts = normalized.split(/\s+/u).filter((part) => part.length > 0);
  return parts.join(' ');
}

/**
 * Generate the human-readable hint exactly as doctk.identity._generate_hint.
 */
function generateHint(text: string): string {
  let hint = text.normalize('NFC').toLowerCase();
  hint = hint.replace(/[^a-z0-9\s-]/gu, '');
  hint = hint.trim().replace(/\s+/gu, '-');
  hint = hint.replace(/-+/g, '-');
  hint = hint.slice(0, 32).replace(/-+$/, '');
  return hint || 'heading';
}

/**
 * Compute the stable id string for a heading text (no occurrence suffix).
 */
export function stableHeadingId(text: string): string {
  const canonical = `heading:${normalizeText(text)}`;
  const hash = createHash('sha256').update(canonical, 'utf8').digest('hex');
  return `heading:${generateHint(text)}:${hash.slice(0, 16)}`;
}

const FENCE_OPEN = /^ {0,3}(`{3,}|~{3,})(.*)$/;
const ATX_HEADING = /^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$/;
const SETEXT_UNDERLINE = /^ {0,3}(=+|-+)[ \t]*$/;
const BLOCKQUOTE = /^ {0,3}>/;
const LIST_ITEM = /^ {0,3}(?:[-*+]|\d{1,9}[.)])[ \t]/;
const THEMATIC_BREAK = /^ {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$/;
const INDENTED_CODE = /^ {4}/;

/**
 * Scan Markdown text for top-level headings (ATX and setext).
 *
 * Mirrors what doctk's parser surfaces in the outline: headings inside
 * fenced code blocks are ignored, and headings inside block quotes are not
 * top-level nodes so they are skipped. A heading this scanner misses simply
 * does not appear in the tree; a false positive produces an id the backend
 * cannot resolve and the operation fails with a clear error - neither case
 * can corrupt a document.
 */
export function scanHeadings(text: string): ScannedHeading[] {
  const lines = text.split('\n');
  const found: Array<{ level: number; text: string; line: number }> = [];

  let fenceChar = '';
  let fenceLength = 0;
  let paragraphStart = -1; // -1 = no open paragraph

  const closeParagraph = () => {
    paragraphStart = -1;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Fenced code blocks: nothing inside them is a heading
    if (fenceChar) {
      const close = line.match(/^ {0,3}(`{3,}|~{3,})[ \t]*$/);
      if (close && close[1][0] === fenceChar && close[1].length >= fenceLength) {
        fenceChar = '';
        fenceLength = 0;
      }
      continue;
    }
    const fenceOpen = line.match(FENCE_OPEN);
    if (fenceOpen && !(fenceOpen[1][0] === '`' && fenceOpen[2].includes('`'))) {
      fenceChar = fenceOpen[1][0];
      fenceLength = fenceOpen[1].length;
      closeParagraph();
      continue;
    }

    if (line.trim() === '') {
      closeParagraph();
      continue;
    }

    if (BLOCKQUOTE.test(line)) {
      closeParagraph();
      continue;
    }

    const atx = line.match(ATX_HEADING);
    if (atx) {
      let headingText = (atx[2] ?? '').trim();
      // Optional closing sequence: trailing #s preceded by space, or a
      // heading whose content is only #s
      headingText = headingText.replace(/[ \t]+#+$/, '');
      if (/^#+$/.test(headingText)) {
        headingText = '';
      }
      found.push({ level: atx[1].length, text: headingText, line: i });
      closeParagraph();
      continue;
    }

    // Setext underline: promotes the open paragraph to a heading
    const setext = line.match(SETEXT_UNDERLINE);
    if (setext && paragraphStart >= 0) {
      const level = setext[1][0] === '=' ? 1 : 2;
      const headingText = lines
        .slice(paragraphStart, i)
        .map((paragraphLine) => paragraphLine.trim())
        .join('\n');
      found.push({ level, text: headingText, line: paragraphStart });
      closeParagraph();
      continue;
    }

    // Thematic breaks and list items interrupt paragraphs
    if (THEMATIC_BREAK.test(line) || LIST_ITEM.test(line)) {
      closeParagraph();
      continue;
    }

    // Indented code cannot start a paragraph (but can continue one lazily;
    // treating it as a break only risks missing an exotic setext heading)
    if (INDENTED_CODE.test(line) && paragraphStart < 0) {
      continue;
    }

    // Ordinary text line: opens or continues a paragraph
    if (paragraphStart < 0) {
      paragraphStart = i;
    }
  }

  return assignStableIds(found);
}

/**
 * Assign stable ids with duplicate-occurrence suffixes, matching
 * DocumentTreeBuilder._build_node_map: the first occurrence uses the plain
 * id; later occurrences get "#2", "#3", ... in document order.
 */
function assignStableIds(
  headings: Array<{ level: number; text: string; line: number }>
): ScannedHeading[] {
  const occurrences = new Map<string, number>();
  return headings.map((heading) => {
    const base = stableHeadingId(heading.text);
    const occurrence = (occurrences.get(base) ?? 0) + 1;
    occurrences.set(base, occurrence);
    const id = occurrence === 1 ? base : `${base}#${occurrence}`;
    return { ...heading, id };
  });
}
