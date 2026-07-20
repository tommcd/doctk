// Node demo of the Rust core through the wasm-bindgen boundary.
//
// Build first (on a machine with the wasm target — see README):
//   rustup target add wasm32-unknown-unknown
//   cargo install wasm-pack
//   wasm-pack build --target nodejs --features wasm
// Then:
//   node demo.mjs
//
// This is the TS-side experience a real rewrite would build on: the outline
// scanner and operations become calls into one WASM module, so the extension
// and the backend stop being two implementations to keep in sync.

import pkg from './pkg/doctk_spike.js';
const { scan_headings_json, promote, stable_heading_id } = pkg;

const doc = `# Guide

## Setup

Install the things.

## Setup

A second section with the same title.

### Details

More.
`;

console.log('scan_headings ->');
const headings = JSON.parse(scan_headings_json(doc));
for (const h of headings) {
  console.log(`  h${h.level}  ${h.id}  ${JSON.stringify(h.text)}`);
}

// Promote the *second* "Setup" (note the #2 occurrence suffix) and show that
// only that heading's line changes.
const secondSetup = headings.find((h) => h.id.endsWith('#2'));
console.log(`\npromote ${secondSetup.id} ->`);
const updated = promote(doc, secondSetup.id);
for (const [i, line] of updated.split('\n').entries()) {
  const before = doc.split('\n')[i];
  const mark = line === before ? '   ' : ' * ';
  console.log(`${mark}${line}`);
}

console.log(`\nstable_heading_id("Setup") -> ${stable_heading_id('Setup')}`);
