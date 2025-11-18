"""Shell script quality tests.

These tests verify that shell scripts follow best practices:
- Pass shellcheck static analysis
- Are formatted with shfmt
- Have proper shebangs
- Are executable
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Use tomllib for Python 3.11+, tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent.parent


@pytest.fixture
def shell_scripts(project_root):
    """Find all shell scripts in the project (excluding .venv and external dirs)."""
    scripts = []
    exclude_dirs = {".venv", ".tox", ".git", "site", "node_modules", "python-project-template"}

    for sh_file in project_root.rglob("*.sh"):
        # Skip files in excluded directories
        if any(excluded in sh_file.parts for excluded in exclude_dirs):
            continue
        scripts.append(sh_file)

    return scripts


@pytest.fixture
def pyproject_data(project_root):
    """Load pyproject.toml data."""
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


def test_shell_scripts_found(shell_scripts):
    """Verify that shell scripts are found in the project."""
    assert len(shell_scripts) > 0, "No shell scripts found in project"


def test_shell_scripts_pass_shellcheck(shell_scripts, pyproject_data):
    """Verify all shell scripts pass shellcheck static analysis.

    shellcheck catches common shell scripting errors and enforces
    best practices according to the Google Shell Style Guide.
    """
    # Check if shellcheck is available
    try:
        result = subprocess.run(
            ["shellcheck", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("shellcheck not installed")
    except FileNotFoundError:
        pytest.skip("shellcheck not installed")

    failures = []

    for script in shell_scripts:
        result = subprocess.run(
            ["shellcheck", str(script)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            failures.append(
                f"\n{script.relative_to(script.parent.parent.parent.parent)}:\n{result.stdout}"
            )

    assert not failures, "Shell scripts failed shellcheck:\n" + "\n".join(failures)


def test_shell_scripts_formatted(shell_scripts, pyproject_data):
    """Verify all shell scripts are formatted with shfmt.

    shfmt enforces consistent formatting for shell scripts.
    """
    # Check if shfmt is available
    try:
        result = subprocess.run(
            ["shfmt", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("shfmt not installed")
    except FileNotFoundError:
        pytest.skip("shfmt not installed")

    failures = []

    for script in shell_scripts:
        # shfmt -d returns non-zero if file would be reformatted
        result = subprocess.run(
            ["shfmt", "-d", "-i", "2", "-ci", str(script)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            failures.append(
                f"\n{script.relative_to(script.parent.parent.parent.parent)}: "
                f"needs formatting\n{result.stdout}"
            )

    assert not failures, (
        "Shell scripts need formatting (run: shfmt -w -i 2 -ci <file>):\n" + "\n".join(failures)
    )


def test_shell_scripts_have_shebangs(shell_scripts):
    """Verify all shell scripts have proper shebangs.

    Shell scripts should start with #!/bin/bash or #!/usr/bin/env bash
    to ensure they are executed with the correct interpreter.
    """
    failures = []

    for script in shell_scripts:
        with open(script, encoding="utf-8") as f:
            first_line = f.readline().strip()

        if not first_line.startswith("#!"):
            failures.append(
                f"{script.relative_to(script.parent.parent.parent.parent)}: missing shebang"
            )
        elif "bash" not in first_line:
            failures.append(
                f"{script.relative_to(script.parent.parent.parent.parent)}: "
                f"shebang should contain 'bash' (found: {first_line})"
            )

    assert not failures, "Shell scripts with shebang issues:\n" + "\n".join(
        f"  - {f}" for f in failures
    )


def test_shell_scripts_executable(shell_scripts):
    """Verify all shell scripts are executable.

    Shell scripts should have the executable bit set so they can be
    run directly without needing to invoke bash explicitly.
    """
    failures = []

    for script in shell_scripts:
        if not os.access(script, os.X_OK):
            failures.append(f"{script.relative_to(script.parent.parent.parent.parent)}")

    assert not failures, "Shell scripts not executable (run: chmod +x <file>):\n" + "\n".join(
        f"  - {f}" for f in failures
    )
