# Requirements Document: Integrate Python Project Template Tooling

## Introduction

This document specifies the requirements for integrating comprehensive development tooling from the python-project-template into the doctk project. The integration includes quality tools (shellcheck, shfmt, lychee, markdownlint, taplo, hadolint), test infrastructure, documentation tooling (MkDocs), and development scripts for environment management.

The tooling will be managed through a plugin-based system where external tools are defined in Markdown files with installation/verification instructions, and versions are centrally managed in pyproject.toml. This ensures reproducible builds and consistent development environments across all contributors.

## Glossary

- **External Tools**: Non-Python development tools (shellcheck, shfmt, etc.) installed to ~/.local/bin
- **Tool Plugin**: A Markdown file defining how to install, check, and uninstall an external tool
- **sstdf-python-standards**: A package containing the tool management framework (to be inlined)
- **tox**: Test orchestration tool that runs multiple test environments
- **pre-commit**: Git hook framework for running checks before commits
- **MkDocs**: Documentation site generator using Markdown
- **uv**: Modern Python package manager and project manager
- **Plugin System**: Framework for managing external tools via Markdown definitions
- **Tool Registry**: JSON file tracking which tools are managed by the plugin system

## Requirements

### Requirement 1: Inline sstdf-python-standards Package

**User Story:** As a developer, I want the tool management framework integrated directly into doctk, so that the project is self-contained without external dependencies.

#### Acceptance Criteria

1. WHEN the sstdf-python-standards code is inlined, THE System SHALL copy all Python modules to a doctk.tools package
1. WHEN the tool management code is integrated, THE System SHALL preserve all functionality from ToolManager, ToolPlugin, and ToolRegistry classes
1. WHEN scripts reference the tool framework, THE System SHALL update imports to use doctk.tools instead of sstdf_python_standards.tools
1. WHEN the integration is complete, THE System SHALL remove the external sstdf-python-standards dependency from pyproject.toml
1. WHEN the inlined code is tested, THE System SHALL verify all tool management operations work correctly

### Requirement 2: Copy Development Scripts

**User Story:** As a developer, I want comprehensive setup and management scripts, so that I can easily configure my development environment.

#### Acceptance Criteria

1. WHEN scripts are copied, THE System SHALL create a scripts/ directory with all template scripts
1. WHEN setup-environment.sh is copied, THE System SHALL adapt it for doctk-specific paths and configuration
1. WHEN check-environment.sh is copied, THE System SHALL verify it checks all required tools and dependencies
1. WHEN tool management scripts are copied, THE System SHALL ensure they work with the inlined tool framework
1. WHEN all scripts are in place, THE System SHALL make them executable with chmod +x

### Requirement 3: Copy Tool Plugin Definitions

**User Story:** As a developer, I want tool definitions for all quality tools, so that I can install and manage them consistently.

#### Acceptance Criteria

1. WHEN tool plugins are copied, THE System SHALL create scripts/tools/ directory with all .md files
1. WHEN shellcheck plugin is copied, THE System SHALL include installation, version check, and uninstall instructions
1. WHEN shfmt plugin is copied, THE System SHALL include installation, version check, and uninstall instructions
1. WHEN lychee plugin is copied, THE System SHALL include installation, version check, and uninstall instructions
1. WHEN markdownlint-cli2 plugin is copied, THE System SHALL include installation, version check, and uninstall instructions
1. WHEN taplo plugin is copied, THE System SHALL include installation, version check, and uninstall instructions
1. WHEN hadolint plugin is copied, THE System SHALL include installation, version check, and uninstall instructions
1. WHEN TEMPLATE.md is copied, THE System SHALL provide documentation for creating new tool plugins

### Requirement 4: Restructure Test Directory

**User Story:** As a developer, I want organized test directories for different test types, so that I can run targeted test suites efficiently.

#### Acceptance Criteria

1. WHEN test structure is created, THE System SHALL create tests/unit/, tests/e2e/, tests/quality/, and tests/docs/ directories
1. WHEN existing tests are preserved, THE System SHALL keep tests/test_basic.py in its current location
1. WHEN __init__.py files are created, THE System SHALL add them to all test subdirectories
1. WHEN test markers are configured, THE System SHALL ensure pytest.ini_options in pyproject.toml defines unit, e2e, quality, docs, and slow markers
1. WHEN tests are run, THE System SHALL verify pytest discovers tests in all directories

### Requirement 5: Add Quality Meta Tests

**User Story:** As a developer, I want automated tests that verify project configuration consistency, so that configuration drift is caught early.

#### Acceptance Criteria

1. WHEN quality tests are added, THE System SHALL create tests/quality/meta/test_config_consistency.py
1. WHEN config consistency is tested, THE System SHALL verify tool versions match between pyproject.toml and .pre-commit-config.yaml
1. WHEN config consistency is tested, THE System SHALL verify all tox environments are documented
1. WHEN config consistency is tested, THE System SHALL verify dependency groups are properly defined
1. WHEN quality tests run, THE System SHALL report any configuration inconsistencies

### Requirement 6: Add Shell Quality Tests

**User Story:** As a developer, I want automated tests for shell script quality, so that bash scripts follow Google Shell Style Guide.

#### Acceptance Criteria

1. WHEN shell tests are added, THE System SHALL create tests/quality/shell/test_shell_quality.py
1. WHEN shell scripts are tested, THE System SHALL verify all .sh files pass shellcheck
1. WHEN shell scripts are tested, THE System SHALL verify all .sh files are formatted with shfmt
1. WHEN shell scripts are tested, THE System SHALL verify all .sh files have proper shebangs
1. WHEN shell tests run, THE System SHALL report any style violations

### Requirement 7: Add Documentation Quality Tests

**User Story:** As a developer, I want automated tests for documentation quality, so that docs remain accurate and well-formatted.

#### Acceptance Criteria

1. WHEN doc tests are added, THE System SHALL create tests/docs/test_documentation_quality.py
1. WHEN README is tested, THE System SHALL verify it contains required sections (Features, Installation, Usage, Development)
1. WHEN important files are referenced, THE System SHALL verify they are linked (not just mentioned as text)
1. WHEN markdown files are tested, THE System SHALL verify they pass markdownlint
1. WHEN links are tested, THE System SHALL verify all links are valid using lychee

### Requirement 8: Configure MkDocs Documentation

**User Story:** As a developer, I want a documentation site generated from Markdown, so that project documentation is accessible and well-organized.

#### Acceptance Criteria

1. WHEN MkDocs is configured, THE System SHALL create mkdocs.yml with project metadata
1. WHEN MkDocs is configured, THE System SHALL use mkdocs-material theme
1. WHEN documentation structure is defined, THE System SHALL organize docs into sections (Getting Started, User Guide, Development, API Reference)
1. WHEN MkDocs is built, THE System SHALL generate a static site in site/ directory
1. WHEN MkDocs is served locally, THE System SHALL provide live preview at http://127.0.0.1:8000

### Requirement 9: Update pyproject.toml Configuration

**User Story:** As a developer, I want comprehensive pyproject.toml configuration, so that all tools are configured in one place.

#### Acceptance Criteria

1. WHEN pyproject.toml is updated, THE System SHALL already have merged ruff, pytest, and coverage configurations (completed)
1. WHEN pyproject.toml is updated, THE System SHALL already have added [tool.external-tools] section (completed)
1. WHEN pyproject.toml is updated, THE System SHALL already have added [dependency-groups] for dev and docs (completed)
1. WHEN pyproject.toml is updated, THE System SHALL include all required development dependencies
1. WHEN pyproject.toml is validated, THE System SHALL verify it is valid TOML syntax

### Requirement 10: Configure Pre-commit Hooks

**User Story:** As a developer, I want pre-commit hooks that automatically check code quality, so that issues are caught before commits.

#### Acceptance Criteria

1. WHEN pre-commit is configured, THE System SHALL already have created .pre-commit-config.yaml (completed)
1. WHEN pre-commit hooks run, THE System SHALL check trailing whitespace, end-of-file, YAML syntax, and large files
1. WHEN pre-commit hooks run, THE System SHALL run shellcheck and shfmt on .sh files
1. WHEN pre-commit hooks run, THE System SHALL run ruff linting and formatting on Python files
1. WHEN pre-commit hooks run, THE System SHALL run mdformat on Markdown files
1. WHEN pre-commit hooks run, THE System SHALL run taplo on TOML files
1. WHEN pre-commit hooks are installed, THE System SHALL run pre-commit install successfully

### Requirement 11: Configure tox Test Environments

**User Story:** As a developer, I want tox environments for all quality checks, so that I can run comprehensive tests locally before CI.

#### Acceptance Criteria

1. WHEN tox is configured, THE System SHALL already have created tox.ini (completed)
1. WHEN tox environments are defined, THE System SHALL include check-environment, bash-syntax, shellcheck, shfmt, ruff, taplo, docs, pytest, and quality
1. WHEN tox is run, THE System SHALL execute all environments in sequence
1. WHEN specific tox environment is run, THE System SHALL execute only that environment
1. WHEN tox completes, THE System SHALL report pass/fail status for each environment

### Requirement 12: Add Lychee Link Checker Configuration

**User Story:** As a developer, I want automated link checking, so that broken links in documentation are detected.

#### Acceptance Criteria

1. WHEN lychee is configured, THE System SHALL already have created .lychee.toml (completed)
1. WHEN lychee runs, THE System SHALL check all Markdown files for broken links
1. WHEN lychee runs, THE System SHALL exclude localhost URLs and mailto links
1. WHEN lychee runs, THE System SHALL retry failed requests up to 2 times
1. WHEN lychee finds broken links, THE System SHALL report them with file locations

### Requirement 13: Add Markdownlint Configuration

**User Story:** As a developer, I want consistent Markdown formatting, so that documentation follows style guidelines.

#### Acceptance Criteria

1. WHEN markdownlint is configured, THE System SHALL already have created .markdownlint.yaml (completed)
1. WHEN markdownlint runs, THE System SHALL check heading hierarchy, list formatting, and code block style
1. WHEN markdownlint runs, THE System SHALL allow some rules to be disabled (line length, bare URLs)
1. WHEN markdownlint finds issues, THE System SHALL report them with line numbers
1. WHEN markdownlint is run with --fix, THE System SHALL auto-fix formatting issues

### Requirement 14: Update .gitignore

**User Story:** As a developer, I want comprehensive .gitignore rules, so that generated files are not committed.

#### Acceptance Criteria

1. WHEN .gitignore is updated, THE System SHALL already have added tox, coverage, and build tool entries (completed)
1. WHEN .gitignore is updated, THE System SHALL exclude site/ (MkDocs output)
1. WHEN .gitignore is updated, THE System SHALL exclude reports/ (test reports)
1. WHEN .gitignore is updated, THE System SHALL exclude .copier-answers.yml
1. WHEN git status is run, THE System SHALL not show generated files as untracked

### Requirement 15: Create Tool Registry System

**User Story:** As a developer, I want a registry tracking which tools are managed by the plugin system, so that uninstall operations only remove plugin-managed tools.

#### Acceptance Criteria

1. WHEN a tool is installed via plugin, THE System SHALL record it in ~/.local/share/doctk/tool-registry.json
1. WHEN a tool is checked, THE System SHALL verify if it is plugin-managed by checking the registry
1. WHEN a tool is uninstalled, THE System SHALL only remove it if it is in the registry
1. WHEN the registry is corrupted, THE System SHALL handle errors gracefully and allow manual cleanup
1. WHEN multiple projects use the plugin system, THE System SHALL maintain separate registries per project

### Requirement 16: Verify Environment Setup Script

**User Story:** As a new developer, I want a single command to set up my entire development environment, so that I can start contributing quickly.

#### Acceptance Criteria

1. WHEN setup-environment.sh is run, THE System SHALL install uv if not present
1. WHEN setup-environment.sh is run, THE System SHALL install Python 3.10+ if not present
1. WHEN setup-environment.sh is run, THE System SHALL install all external tools from plugins
1. WHEN setup-environment.sh is run, THE System SHALL run uv sync --all-groups to install Python dependencies
1. WHEN setup-environment.sh is run, THE System SHALL install tox globally
1. WHEN setup-environment.sh is run, THE System SHALL install pre-commit hooks
1. WHEN setup-environment.sh completes, THE System SHALL verify installation with check-environment.sh

### Requirement 17: Verify Environment Check Script

**User Story:** As a developer, I want to verify my environment is correctly configured, so that I can troubleshoot setup issues.

#### Acceptance Criteria

1. WHEN check-environment.sh is run, THE System SHALL verify Python 3.10+ is installed
1. WHEN check-environment.sh is run, THE System SHALL verify uv is installed
1. WHEN check-environment.sh is run, THE System SHALL verify all external tools are installed with correct versions
1. WHEN check-environment.sh is run, THE System SHALL verify git is installed
1. WHEN check-environment.sh is run, THE System SHALL verify pre-commit hooks are installed
1. WHEN check-environment.sh is run, THE System SHALL verify Python dependencies are installed
1. WHEN environment is ready, THE System SHALL exit with code 0
1. WHEN environment has issues, THE System SHALL exit with code 1 and display helpful error messages

### Requirement 18: Create Clean Environment Script

**User Story:** As a developer, I want to clean all generated files, so that I can reset to a fresh state when troubleshooting.

#### Acceptance Criteria

1. WHEN clean-environment.sh is run, THE System SHALL remove .venv/ directory
1. WHEN clean-environment.sh is run, THE System SHALL remove .tox/ directory
1. WHEN clean-environment.sh is run, THE System SHALL remove build artifacts (dist/, build/, \*.egg-info/)
1. WHEN clean-environment.sh is run, THE System SHALL remove cache directories (.pytest_cache/, .ruff_cache/, __pycache__/)
1. WHEN clean-environment.sh is run, THE System SHALL remove coverage reports (reports/, .coverage, htmlcov/)
1. WHEN clean-environment.sh is run, THE System SHALL remove MkDocs output (site/)
1. WHEN clean-environment.sh completes, THE System SHALL report what was cleaned

### Requirement 19: Create Utility Scripts

**User Story:** As a developer, I want utility scripts for common tasks, so that I can work more efficiently.

#### Acceptance Criteria

1. WHEN show-tox-commands.py is run, THE System SHALL display all tox environments with descriptions
1. WHEN sync-precommit-versions.py is run, THE System SHALL update .pre-commit-config.yaml with versions from pyproject.toml
1. WHEN validate-plugins.py is run, THE System SHALL check all tool plugin Markdown files for required sections
1. WHEN validate-plugins.py is run, THE System SHALL verify each plugin has install, check, and uninstall code blocks
1. WHEN utility scripts are run, THE System SHALL provide clear output and exit codes

### Requirement 20: Documentation for Tooling System

**User Story:** As a developer, I want comprehensive documentation for the tooling system, so that I understand how to use and extend it.

#### Acceptance Criteria

1. WHEN documentation is created, THE System SHALL create scripts/README.md with overview of all scripts
1. WHEN documentation is created, THE System SHALL document the tool plugin system architecture
1. WHEN documentation is created, THE System SHALL provide examples of adding new tools
1. WHEN documentation is created, THE System SHALL document the workflow for daily development
1. WHEN documentation is created, THE System SHALL document troubleshooting common issues
