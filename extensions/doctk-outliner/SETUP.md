# Running the doctk Outliner extension locally

This guide gets the VS Code extension running from source on a fresh machine.
For the design context behind the current state of the extension, see
[`docs/design/07-revival-plan.md`](../../docs/design/07-revival-plan.md).

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** (for `npm`)
- **VS Code** 1.80.0 or newer

## 1. Get the code

```bash
git clone https://github.com/tommcd/doctk.git
cd doctk
git checkout claude/project-review-viability-noeos0
```

Already have the repo? `git fetch origin && git checkout claude/project-review-viability-noeos0`

## 2. Install the Python backend

The extension health-checks that `doctk` is importable **before** it starts, so
install it first. With [uv](https://docs.astral.sh/uv/) (what the project uses):

```bash
uv sync          # creates .venv at the repo root and installs doctk into it
```

No uv? Plain venv + pip works:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

Either way you now have a `.venv` at the repo root with doctk installed — which
is one of the interpreters the extension resolves automatically (see
[Interpreter resolution](#interpreter-resolution) below).

Optional sanity check that the backend is healthy:

```bash
uv run pytest -q                   # expect ~788 passed
```

## 3. Build the extension

```bash
cd extensions/doctk-outliner
npm install
npm run compile                    # produces out/ via tsc
```

Optional: `npm run lint` (expect 0 errors) and `npm run watch` (rebuild on save).

## 4. Run it (F5)

The repo ignores `.vscode/` by convention, so create a launch config once in
your local clone at `extensions/doctk-outliner/.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run doctk Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": ["--extensionDevelopmentPath=${workspaceFolder}"],
      "outFiles": ["${workspaceFolder}/out/**/*.js"]
    }
  ]
}
```

Then:

1. Open the **`extensions/doctk-outliner`** folder in VS Code.
2. Make sure the build is current — run `npm run compile` (or keep
   `npm run watch` running in a terminal for auto-rebuild on save).
3. Press **F5**. A second VS Code window launches, the **Extension Development
   Host**, with the extension loaded.
4. In that new window, open a folder that contains Markdown — the simplest
   self-contained choice is the **doctk repo root itself** (File → Open Folder →
   the `doctk` directory). It has the `.venv` you just created plus plenty of
   `.md` files.
5. Open `README.md`. The **Document Outline** view appears in the Explorer
   sidebar with the heading tree. Right-click a section for promote / demote /
   move / nest.

## Alternative: install as a real extension (.vsix)

For the most faithful "does it survive a restart" test, package and install it
like any published extension instead of using the dev host:

```bash
cd extensions/doctk-outliner
npm run compile
npx @vscode/vsce package                        # produces doctk-outliner-0.1.0.vsix
code --install-extension doctk-outliner-0.1.0.vsix
```

Then open any Markdown file in your normal VS Code.

## What to test

- **It works at all** — the outline renders, and promote/demote edits the file
  without mangling tables, HTML blocks, or front matter (source-faithful
  writer).
- **Survives a restart** — fully quit and reopen VS Code from the GUI (not from
  a terminal with the venv activated). The outline should still work. This is
  the exact "worked once, broke after restart" scenario the interpreter
  resolution + health check were built to fix.
- **Feels instant on large documents** — open a document with a few hundred
  headings. The outline updates without lag because it is built in TypeScript;
  Python is only called when you perform an action (promote/demote/move/nest).

## Interpreter resolution

The extension chooses a Python interpreter in this order:

1. The `doctk.pythonPath` setting (explicit override)
2. The legacy `doctk.lsp.pythonCommand` setting (deprecated)
3. The [ms-python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)'s
   active interpreter for the workspace
4. A `.venv` in the workspace root
5. `python3` / `python` on `PATH` (last resort)

The chosen interpreter is verified with `import doctk` before any backend
process starts. If it fails, you get an actionable error with **Open Settings**
and **Reload Window** buttons — not a silently dead tree view.

### Troubleshooting

If the outline does not appear and you see a backend error, the resolved
interpreter probably does not have doctk installed. Set `doctk.pythonPath` to
the absolute path of the venv Python from step 2:

- macOS / Linux: `/path/to/doctk/.venv/bin/python`
- Windows: `C:\path\to\doctk\.venv\Scripts\python.exe`

Set it in the Extension Development Host window (or, for a `.vsix` install, in
your normal settings) via Settings → search `doctk.pythonPath`, or in
`settings.json`:

```json
{
  "doctk.pythonPath": "/path/to/doctk/.venv/bin/python"
}
```

Extension logs are in the **Output** panel → **doctk** channel; set
`doctk.logging.level` to `debug` for detail.
