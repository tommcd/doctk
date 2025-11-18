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

## Next Steps

Now that you have doctk installed, check out the [Quick Start](quick-start.md) guide to learn the basics.
