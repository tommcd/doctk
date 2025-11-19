"""Tests for Kiro spec quality and accuracy.

These tests verify that specifications are accurate and up-to-date:
- File references point to existing files
- Code references match actual implementation
- No outdated API references
"""

import re
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def spec_files(project_root):
    """Get all spec markdown files (excluding old/ subdirectory)."""
    specs_dir = project_root / ".kiro" / "specs"
    if not specs_dir.exists():
        return []

    # Find all .md files, excluding old/ subdirectory
    all_md_files = list(specs_dir.rglob("*.md"))
    return [f for f in all_md_files if "old" not in f.parts]


@pytest.mark.docs
def test_spec_file_references_exist(project_root, spec_files):
    """Verify that file paths referenced in specs actually exist.

    Specs often reference:
    - Source files (src/doctk/...)
    - Test files (tests/...)
    - Config files (pyproject.toml, etc.)

    This test ensures those references are accurate.
    """
    if not spec_files:
        pytest.skip("No spec files found")

    violations = []

    # Pattern to match file paths in specs
    # Matches: src/doctk/module.py, tests/unit/test_foo.py, etc.
    # But NOT when preceded by another path component (to avoid matching
    # extensions/doctk-outliner/src/file.ts as src/file.ts)
    file_path_pattern = re.compile(
        r'(?:^|[^\w`])(?<![-a-zA-Z0-9_/])('
        r'(?:src|tests|docs|scripts|examples|extensions)/'
        r'[a-zA-Z0-9_/.-]+\.(?:py|md|yaml|yml|toml|txt|sh|ts|tsx|json)'
        r')',
        re.MULTILINE
    )

    for spec_file in spec_files:
        content = spec_file.read_text()

        # Remove code blocks to avoid checking example code
        content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

        # Process line by line to check for TODO/PLANNED markers
        lines = content_no_code.split('\n')
        for line in lines:
            # Skip lines marked with [TODO] or [PLANNED]
            if '[TODO]' in line or '[PLANNED]' in line:
                continue

            # Find all file path references in this line
            matches = file_path_pattern.findall(line)

            for file_path in matches:
                # Skip common false positives
                if any(skip in file_path for skip in ['example.py', 'foo.py', 'test.py']):
                    continue

                # Check if file exists
                full_path = project_root / file_path
                if not full_path.exists():
                    violations.append(
                        f"{spec_file.relative_to(project_root)}: "
                        f"References non-existent file '{file_path}'"
                    )

    if violations:
        msg = (
            "Specs reference files that don't exist:\n"
            + "\n".join(f"  - {v}" for v in violations[:20])
            + "\n\nEither:\n"
            "1. Create the missing file\n"
            "2. Update spec to reference correct file\n"
            "3. If this is planned work, mark with [TODO] or [PLANNED]"
        )
        pytest.fail(msg)


@pytest.mark.docs
def test_spec_code_references_exist(project_root, spec_files):
    """Verify that code references in specs match actual implementation.

    Similar to test_api_references_exist_in_code() but for specs.
    Validates references like:
    - DoctkLanguageServer.validate_syntax()
    - OperationRegistry.search_operations()
    - etc.
    """
    import importlib
    import inspect

    if not spec_files:
        pytest.skip("No spec files found")

    violations = []

    # Pattern to match Python-style API references
    api_ref_pattern = re.compile(
        r"(?:^|[^\w`])([A-Z][a-zA-Z0-9_]*\.(?:[a-z_][a-z0-9_]*|[A-Z][a-zA-Z0-9_]*)(?:\(\))?)",
        re.MULTILINE
    )

    for spec_file in spec_files:
        content = spec_file.read_text()

        # Remove code blocks to avoid checking example code
        content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

        # Find all API references
        matches = api_ref_pattern.findall(content_no_code)

        for ref in matches:
            # Skip common false positives
            if any(skip in ref for skip in [
                'Example.',
                'Note.',
                'TODO.',
                'FIXME.',
                'Class.',
                'Method.',
                'Type.',
            ]):
                continue

            # Remove () if present
            ref_clean = ref.rstrip("()")
            parts = ref_clean.split(".")

            if len(parts) < 2:
                continue

            # Try to validate the reference
            class_name = parts[0]
            method_or_attr = parts[1] if len(parts) > 1 else None

            # Try common module locations
            for module_path in [
                f"doctk.lsp.{class_name.lower()}",
                f"doctk.{class_name.lower()}",
                "doctk.lsp.server",
                "doctk.lsp.registry",
                "doctk.lsp.completion",
                "doctk.lsp.hover",
                "doctk.integration.bridge",
                "doctk.integration.operations",
            ]:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, class_name):
                        cls = getattr(module, class_name)
                        if method_or_attr and inspect.isclass(cls):
                            if not hasattr(cls, method_or_attr):
                                violations.append(
                                    f"{spec_file.name}: '{ref}' - "
                                    f"class '{class_name}' has no method/attribute '{method_or_attr}'"
                                )
                        break  # Found the class, stop searching
                except (ImportError, AttributeError):
                    continue

    if violations:
        msg = (
            "Specs reference code that doesn't exist:\n"
            + "\n".join(f"  - {v}" for v in violations[:20])
            + "\n\nEither:\n"
            "1. Implement the missing code\n"
            "2. Update spec to reference correct API\n"
            "3. If this is planned work, mark with [TODO] or [PLANNED]"
        )
        pytest.fail(msg)


@pytest.mark.docs
def test_spec_line_number_references_reasonable(project_root, spec_files):
    """Verify that line number references in specs are reasonable.

    Specs often reference specific lines like "src/foo.py (line 42)".
    While we can't guarantee the exact line is correct (code changes),
    we can verify the referenced file has at least that many lines.
    """
    if not spec_files:
        pytest.skip("No spec files found")

    violations = []

    # Pattern to match file references with line numbers
    # Examples: "src/foo.py (line 42)", "src/foo.py:42", "src/foo.py (lines 10-20)"
    line_ref_pattern = re.compile(
        r'([a-zA-Z0-9_/.-]+\.py)'
        r'(?:'
        r'\s*\(lines?\s*(\d+)(?:-(\d+))?\)'  # (line 42) or (lines 10-20)
        r'|'
        r':(\d+)'  # :42
        r')',
        re.MULTILINE
    )

    for spec_file in spec_files:
        content = spec_file.read_text()

        # Find all line number references
        matches = line_ref_pattern.findall(content)

        for match in matches:
            file_path = match[0]
            # Extract line numbers from different match groups
            line_start = match[1] or match[3]  # From (line X) or :X
            line_end = match[2]  # From (lines X-Y)

            if not line_start:
                continue

            line_start = int(line_start)
            line_end = int(line_end) if line_end else line_start

            # Check if file exists
            full_path = project_root / file_path
            if not full_path.exists():
                continue  # Already caught by test_spec_file_references_exist

            # Count lines in file
            try:
                with open(full_path, 'r') as f:
                    actual_lines = sum(1 for _ in f)

                # Check if referenced lines exist
                if line_end > actual_lines:
                    violations.append(
                        f"{spec_file.name}: References {file_path}:{line_start}"
                        f"{f'-{line_end}' if line_end != line_start else ''} "
                        f"but file only has {actual_lines} lines"
                    )
            except Exception:
                # Skip if we can't read the file
                pass

    if violations:
        msg = (
            "Specs reference line numbers that don't exist:\n"
            + "\n".join(f"  - {v}" for v in violations[:20])
            + "\n\nUpdate line number references or mark as [APPROXIMATE]"
        )
        pytest.fail(msg)
