# Installation

This guide will help you install doctk and set up your development environment.

## Requirements

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installing with uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that provides better dependency resolution and faster installation.

### Install uv

```bash
# On Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install doctk

```bash
# Clone the repository
git clone https://github.com/tommcd/doctk.git
cd doctk

# Install dependencies and doctk in editable mode
uv sync
uv pip install -e .
```

## Installing with pip

If you prefer to use pip:

```bash
# Clone the repository
git clone https://github.com/tommcd/doctk.git
cd doctk

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install doctk in editable mode
pip install -e .
```

## Verify Installation

After installation, verify that doctk is working:

```bash
# Check version
doctk --version

# Run the demo
doctk demo

# View help
doctk help
```

You should see the doctk CLI interface with available commands.

## Development Installation

If you want to contribute to doctk or run tests, install the development dependencies:

```bash
# With uv
uv sync --all-groups

# With pip
pip install -e ".[dev,docs]"
```

This installs additional tools for:

- Testing (pytest, coverage)
- Code quality (ruff, pre-commit)
- Documentation (mkdocs, mkdocs-material)

See the [Development Setup](../development/setup.md) guide for more details.

## Installing the VS Code Extension

After installing doctk, you can optionally install the VS Code extension for visual document manipulation.

### Prerequisites

- doctk installed (see above)
- VS Code 1.80.0 or higher
- Python 3.12+ accessible from your PATH

### Installation Steps

**Option 1: Build from Source** (recommended)

```bash
cd extensions/doctk-outliner
npm install
npm run compile
npx @vscode/vsce package
code --install-extension doctk-outliner-0.1.0.vsix
```

**Note:** The `.vsix` file is not included in the repository (it's gitignored). You must either build it yourself (Option 1) or download a pre-built version from [GitHub Releases](https://github.com/tommcd/doctk/releases) when available.

**Option 2: Install from Command Line** (after building or downloading)

```bash
code --install-extension path/to/doctk-outliner-0.1.0.vsix
```

**Option 3: Install via VS Code UI** (after building or downloading)

1. Open VS Code
1. Open the Extensions view (`Ctrl+Shift+X` or `Cmd+Shift+X`)
1. Click the "..." menu button at the top
1. Select "Install from VSIX..."
1. Navigate to and select the `.vsix` file
1. Reload VS Code when prompted

### Verify Extension Installation

1. Open a Markdown file (`.md`) in VS Code
1. The "Document Outline" view should appear in the Explorer sidebar
1. If not visible: **View → Open View → Document Outline**
1. Try right-clicking on a heading to see available operations

### Troubleshooting

**"Python bridge failed to start"**

- Verify Python is in your PATH: `python3 --version`
- Verify doctk is installed: `python3 -c "import doctk; print(doctk.__version__)"`
- Check VS Code Output panel (**View → Output**, select "doctk")
- Try setting `doctk.lsp.pythonCommand` in VS Code settings to your Python path

**Extension not activating**

- Ensure you're viewing a `.md` file
- Check the file language mode is "Markdown"
- Try running the command: **doctk: Refresh Outline** from the Command Palette

For more details, see the [extension README](https://github.com/tommcd/doctk/blob/master/extensions/doctk-outliner/README.md).

## Next Steps

Now that you have doctk installed, check out the [Quick Start](quick-start.md) guide to learn the basics.
