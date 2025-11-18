"""Configuration consistency tests.

These tests verify that configuration is consistent across different files:
- Tool versions match between pyproject.toml and .pre-commit-config.yaml
- All tox environments have descriptions
- Dependency groups are complete
- External tools have plugin files
"""

import re
import sys
from pathlib import Path

import pytest
import yaml

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
def pyproject_data(project_root):
    """Load pyproject.toml data."""
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


@pytest.fixture
def precommit_data(project_root):
    """Load .pre-commit-config.yaml data."""
    precommit_path = project_root / ".pre-commit-config.yaml"
    with open(precommit_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def tox_ini_content(project_root):
    """Load tox.ini content as text."""
    tox_path = project_root / "tox.ini"
    with open(tox_path) as f:
        return f.read()


def test_tool_versions_match_precommit(pyproject_data, precommit_data):
    """Verify tool versions in pyproject.toml match .pre-commit-config.yaml.

    This ensures that pre-commit hooks use the same versions as defined
    in the central configuration.
    """
    external_tools = pyproject_data.get("tool", {}).get("external-tools", {})

    # Map of tool names to their pre-commit repo patterns
    tool_to_repo = {
        "shellcheck": "shellcheck-py/shellcheck-py",
        "shfmt": "scop/pre-commit-shfmt",
        "ruff": "astral-sh/ruff-pre-commit",
        "mdformat": "executablebooks/mdformat",
        "taplo": "ComPWA/taplo-pre-commit",
    }

    mismatches = []

    for tool_name, repo_pattern in tool_to_repo.items():
        if tool_name not in external_tools:
            continue

        expected_version = external_tools[tool_name]

        # Find the repo in pre-commit config
        repo_found = False
        for repo in precommit_data.get("repos", []):
            repo_url = repo.get("repo", "")
            if repo_pattern in repo_url:
                repo_found = True
                actual_rev = repo.get("rev", "")

                # Extract version from rev (handle v prefix and suffixes)
                # Examples: v0.11.0.1 -> 0.11.0, v3.10.0-1 -> 3.10.0
                version_match = re.search(r"v?(\d+\.\d+\.\d+)", actual_rev)
                if version_match:
                    actual_version = version_match.group(1)

                    if actual_version != expected_version:
                        mismatches.append(
                            f"{tool_name}: pyproject.toml={expected_version}, "
                            f"pre-commit={actual_version} (rev={actual_rev})"
                        )
                break

        if not repo_found:
            mismatches.append(f"{tool_name}: not found in .pre-commit-config.yaml")

    assert not mismatches, "Tool version mismatches found:\n" + "\n".join(
        f"  - {m}" for m in mismatches
    )


def test_tox_environments_documented(tox_ini_content):
    """Verify all tox environments have descriptions.

    This ensures that `tox -l` and documentation show helpful information
    about what each environment does.
    """
    # Parse tox.ini to find all [testenv:*] sections
    env_pattern = re.compile(r"^\[testenv:([^\]]+)\]", re.MULTILINE)
    environments = env_pattern.findall(tox_ini_content)

    # Check each environment has a description
    missing_descriptions = []

    for env_name in environments:
        # Look for description line after [testenv:env_name]
        section_pattern = rf"\[testenv:{re.escape(env_name)}\]\s*\ndescription\s*="
        if not re.search(section_pattern, tox_ini_content):
            missing_descriptions.append(env_name)

    assert not missing_descriptions, "Tox environments missing descriptions:\n" + "\n".join(
        f"  - {env}" for env in missing_descriptions
    )


def test_dependency_groups_complete(pyproject_data):
    """Verify dependency groups contain all required dependencies.

    This ensures that development dependencies are properly organized
    and nothing is missing.
    """
    dep_groups = pyproject_data.get("dependency-groups", {})

    # Check dev group has essential tools
    dev_deps = dep_groups.get("dev", [])
    dev_deps_str = " ".join(dev_deps)

    required_dev_tools = [
        "pytest",
        "pytest-cov",
        "ruff",
        "pre-commit",
        "tox",
        "mdformat",
    ]

    missing_dev = []
    for tool in required_dev_tools:
        if tool not in dev_deps_str:
            missing_dev.append(tool)

    assert not missing_dev, "Missing required dev dependencies:\n" + "\n".join(
        f"  - {tool}" for tool in missing_dev
    )

    # Check docs group has essential tools
    docs_deps = dep_groups.get("docs", [])
    docs_deps_str = " ".join(docs_deps)

    required_docs_tools = [
        "mkdocs",
        "mkdocs-material",
    ]

    missing_docs = []
    for tool in required_docs_tools:
        if tool not in docs_deps_str:
            missing_docs.append(tool)

    assert not missing_docs, "Missing required docs dependencies:\n" + "\n".join(
        f"  - {tool}" for tool in missing_docs
    )


def test_external_tools_have_plugins(pyproject_data, project_root):
    """Verify all external tools in pyproject.toml have plugin files.

    This ensures that every tool defined in [tool.external-tools]
    has a corresponding plugin file in scripts/tools/.
    """
    external_tools = pyproject_data.get("tool", {}).get("external-tools", {})
    tools_dir = project_root / "scripts" / "tools"

    missing_plugins = []

    for tool_name in external_tools:
        plugin_file = tools_dir / f"{tool_name}.md"
        if not plugin_file.exists():
            missing_plugins.append(tool_name)

    assert not missing_plugins, "External tools missing plugin files:\n" + "\n".join(
        f"  - {tool} (expected: scripts/tools/{tool}.md)" for tool in missing_plugins
    )


def test_plugin_files_have_tool_entries(pyproject_data, project_root):
    """Verify all plugin files have corresponding entries in pyproject.toml.

    This ensures that plugin files are not orphaned and have version
    specifications in the central configuration.
    """
    external_tools = pyproject_data.get("tool", {}).get("external-tools", {})
    tools_dir = project_root / "scripts" / "tools"

    # Get all .md files except TEMPLATE.md
    plugin_files = [f for f in tools_dir.glob("*.md") if f.name != "TEMPLATE.md"]

    orphaned_plugins = []

    for plugin_file in plugin_files:
        tool_name = plugin_file.stem  # filename without .md extension
        if tool_name not in external_tools:
            orphaned_plugins.append(tool_name)

    assert not orphaned_plugins, "Plugin files without pyproject.toml entries:\n" + "\n".join(
        f"  - {tool} (add to [tool.external-tools] in pyproject.toml)" for tool in orphaned_plugins
    )
