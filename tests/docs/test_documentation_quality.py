"""Documentation quality tests.

These tests verify that documentation is complete, well-formatted, and accurate:
- README has required sections
- Important files are properly linked (not just mentioned as text)
- Markdown files pass linting
- Links are valid
"""

import re
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def readme_content(project_root):
    """Load README.md content."""
    readme_path = project_root / "README.md"
    with open(readme_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def important_files(project_root):
    """Load list of important files that should be linked."""
    doc_quality_files = project_root / ".doc-quality-files.txt"
    if not doc_quality_files.exists():
        return []

    with open(doc_quality_files, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


def test_readme_has_required_sections(readme_content):
    """Verify README has all required sections.

    A good README should have:
    - Features or Philosophy section (what it does)
    - Installation section (how to install)
    - Usage section (how to use)
    - Development or Contributing section (how to contribute)
    """
    # Convert to lowercase for case-insensitive matching
    content_lower = readme_content.lower()

    required_sections = {
        "Features": ["## features", "## philosophy", "## core concepts"],
        "Installation": ["## installation", "## quick start", "### installation"],
        "Usage": ["## usage", "## quick start", "### usage", "## python api"],
        "Development": [
            "## development",
            "## contributing",
            "## documentation",
            "## project status",
        ],
    }

    missing_sections = []

    for section_name, patterns in required_sections.items():
        if not any(pattern in content_lower for pattern in patterns):
            missing_sections.append(f"{section_name} (looked for: {', '.join(patterns)})")

    assert not missing_sections, (
        "README.md is missing required sections:\n"
        + "\n".join(f"  - {section}" for section in missing_sections)
        + "\n\nA good README should have Features, Installation, Usage, and Development sections."
    )


def test_important_files_are_linked(readme_content, important_files, project_root):
    """Verify important files are linked, not just mentioned as text.

    Files should be referenced as markdown links [text](file) or [file](file),
    not just mentioned as plain text like "see CONTRIBUTING.md".
    """
    if not important_files:
        pytest.skip("No .doc-quality-files.txt found or file is empty")

    # Extract all markdown links from README
    # Pattern matches [text](url) format
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
    links = link_pattern.findall(readme_content)

    # Get all linked files (normalize paths)
    linked_files = set()
    for text, url in links:
        # Skip external URLs
        if url.startswith(("http://", "https://", "#")):
            continue
        # Normalize path (remove leading ./)
        normalized = url.lstrip("./")
        linked_files.add(normalized)

    # Check each important file
    not_linked = []
    for file_path in important_files:
        # Check if file exists
        full_path = project_root / file_path
        if not full_path.exists():
            not_linked.append(f"{file_path} (file does not exist)")
            continue

        # Check if it's linked
        if file_path not in linked_files:
            # Check if it's mentioned as plain text (which is not good enough)
            if file_path in readme_content:
                not_linked.append(
                    f"{file_path} (mentioned but not linked - use [{file_path}]({file_path}))"
                )
            else:
                not_linked.append(f"{file_path} (not mentioned at all)")

    assert not not_linked, (
        "Important files are not properly linked in README.md:\n"
        + "\n".join(f"  - {item}" for item in not_linked)
        + "\n\nImportant files should be markdown links, not plain text."
    )


def test_readme_links_are_valid(readme_content, project_root):
    """Verify all local file links in README point to existing files.

    This catches broken links to documentation, contributing guides, etc.
    """
    # Extract all markdown links
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
    links = link_pattern.findall(readme_content)

    broken_links = []

    for text, url in links:
        # Skip external URLs and anchors
        if url.startswith(("http://", "https://", "#", "mailto:")):
            continue

        # Check if file exists
        file_path = project_root / url.lstrip("./")
        if not file_path.exists():
            broken_links.append(f"[{text}]({url}) -> {file_path} does not exist")

    assert not broken_links, "README.md contains broken links:\n" + "\n".join(
        f"  - {link}" for link in broken_links
    )


def test_readme_has_project_metadata(readme_content):
    """Verify README has essential project metadata.

    A good README should include:
    - Project name/title
    - Brief description
    - Badges (optional but recommended)
    """
    # Check for title (# heading at start)
    assert re.search(r"^#\s+\w+", readme_content, re.MULTILINE), (
        "README.md should start with a title (# heading)"
    )

    # Check for description (some text after title, before first ## heading)
    title_match = re.search(r"^#\s+[^\n]+\n", readme_content, re.MULTILINE)
    if title_match:
        after_title = readme_content[title_match.end() :]
        first_section = re.search(r"^##", after_title, re.MULTILINE)
        if first_section:
            intro_text = after_title[: first_section.start()].strip()
            # Should have at least one sentence of description
            assert len(intro_text) > 20, "README.md should have a description after the title"


def test_code_blocks_have_language_tags(readme_content):
    """Verify code blocks specify language for syntax highlighting.

    Code blocks should use ```language format, not just ```.
    """
    # Find all opening code block tags (``` at start of line, possibly followed by language)
    # We need to distinguish opening tags from closing tags
    # Opening tags: ```language or ``` followed by content
    # Closing tags: ``` on a line by itself (preceded by code content)

    # Split into lines and find opening code blocks
    lines = readme_content.split("\n")
    opening_blocks = []
    in_code_block = False

    for line in lines:
        if line.startswith("```"):
            if not in_code_block:
                # This is an opening tag
                lang = line[3:].strip()
                opening_blocks.append(lang)
                in_code_block = True
            else:
                # This is a closing tag
                in_code_block = False

    # Count blocks without language tags
    untagged_blocks = sum(1 for lang in opening_blocks if not lang)

    # Allow a few untagged blocks (for generic output), but most should be tagged
    total_blocks = len(opening_blocks)
    if total_blocks > 0:
        untagged_ratio = untagged_blocks / total_blocks
        assert untagged_ratio < 0.3, (
            f"Too many code blocks without language tags: {untagged_blocks}/{total_blocks}\n"
            "Use ```python, ```bash, etc. for syntax highlighting"
        )
