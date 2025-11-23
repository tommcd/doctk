---
title: Python env – WSL + uv
inclusion: always
---

# Python environment and commands

## Environment

- All Python-related commands MUST run in **WSL**, not in Windows PowerShell.
- Assume the working directory is the project root unless stated otherwise.
- Commands should use relative paths or the `path` parameter when needed.

## Tooling rules

- Use `uv` for all Python tooling:
  - Never call `pip` or `python -m pip` directly.
  - Never call `pytest` or `python -m pytest` directly from Windows.
- For dependencies:
  - Use `uv sync` to install/sync dependencies.
- For tests:
  - Run the full suite as:

    ```bash
    uv run pytest
    ```

  - Run a specific test file as:

    ```bash
    uv run pytest tests/unit/test_nested_lists.py -v
    ```

## Command generation guidelines

When generating shell commands for this workspace:

- **CRITICAL**: If you are ALREADY running inside WSL. NEVER EVER use `wsl.exe` or `wsl` prefix.
- The shell is bash in WSL, not Windows PowerShell or cmd.
- Run commands directly without any wrapper: `uv run pytest`, NOT `wsl.exe uv run pytest`
- Prefer `uv run …` for any Python or pytest invocation.
- If you would normally suggest `python -m pytest …`, instead suggest the equivalent `uv run pytest …`.
- If in doubt about the environment, explicitly state:
  "This project uses WSL with `uv`; commands should follow the rules in `python-wsl-uv.md`."
