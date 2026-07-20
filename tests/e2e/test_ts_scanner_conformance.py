"""Cross-language conformance: the TS outline scanner must match Python.

The VS Code extension builds its outline tree in TypeScript
(extensions/doctk-outliner/src/outlineScanner.ts) so no Python runs in the
keystroke path. Operations send the tree's node ids back to the Python
backend, so the TS scanner's stable ids must match DocumentTreeBuilder's
byte for byte - level, text, and id, in document order.

Requires the compiled extension (npm run compile) and node; skips otherwise.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from doctk import Document
from doctk.core import Heading
from doctk.integration.operations import DocumentTreeBuilder

REPO_ROOT = Path(__file__).parents[2]
SCANNER_JS = REPO_ROOT / "extensions" / "doctk-outliner" / "out" / "outlineScanner.js"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(shutil.which("node") is None, reason="node not available"),
    pytest.mark.skipif(
        not SCANNER_JS.exists(),
        reason="extension not compiled (run: cd extensions/doctk-outliner && npm run compile)",
    ),
]

CORPUS_FILES = ["README.md", "CLAUDE.md", "AGENTS.md", "docs/development/testing.md"]

SYNTHETIC_DOCS = {
    "unicode": "# Café résumé\n\n## Ünïcode — heading\n\n## 日本語の見出し\n",
    "duplicates": "## Overview\n\nA.\n\n## Overview\n\nB.\n\n## Overview\n\nC.\n",
    "fenced_headings": "# Real\n\n```md\n# Not a heading\n## Also not\n```\n\n~~~\n# Still not\n~~~\n\n## Real again\n",
    "blockquote_headings": "# Top\n\n> # Quoted heading\n> text\n\n## After\n",
    "closing_hashes": "## Title ##\n\n### Only ###\n\n#### Trailing # kept-ish ####\n",
    "tabs_and_spaces": "#\tTabbed  heading\n\n##   Spaced   out   \n",
    "setext": "Main Title\n==========\n\nSection Two\n-----------\n\nBody text.\n",
    "empty_heading": "##\n\n## \n\ntext\n",
}


def _python_outline(text: str) -> list[dict]:
    doc = Document.from_string(text)
    builder = DocumentTreeBuilder(doc)
    outline = []
    for index, node in enumerate(doc.nodes):
        if isinstance(node, Heading):
            outline.append(
                {"level": node.level, "text": node.text, "id": builder._display_ids[index]}
            )
    return outline


def _ts_outline(text: str) -> list[dict]:
    harness = (
        "const {scanHeadings} = require(process.argv[1]);"
        "let input='';"
        "process.stdin.on('data', (chunk) => { input += chunk; });"
        "process.stdin.on('end', () => {"
        "  const result = scanHeadings(input).map(({level, text, id}) => ({level, text, id}));"
        "  process.stdout.write(JSON.stringify(result));"
        "});"
    )
    completed = subprocess.run(
        ["node", "-e", harness, str(SCANNER_JS)],
        input=text.encode("utf-8"),
        capture_output=True,
        timeout=30,
        check=True,
    )
    return json.loads(completed.stdout)


@pytest.mark.parametrize("relative_path", CORPUS_FILES)
def test_scanner_matches_python_on_corpus(relative_path: str) -> None:
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    assert _ts_outline(text) == _python_outline(text), relative_path


@pytest.mark.parametrize("name", sorted(SYNTHETIC_DOCS))
def test_scanner_matches_python_on_synthetic(name: str) -> None:
    text = SYNTHETIC_DOCS[name]
    assert _ts_outline(text) == _python_outline(text), name
