# Validating Kiro Spec Accuracy

## Purpose

Kiro specs must stay synchronized with the codebase. This document explains how to validate that specs don't reference outdated code, missing files, or incorrect APIs.

## Validation Tests

Run the following test suite to validate all Kiro specs:

```bash
pytest tests/docs/test_spec_quality.py -v
```

This test suite performs three critical checks:

### 1. File References Exist (`test_spec_file_references_exist`)

**What it checks**: All file paths mentioned in specs actually exist in the project.

**Examples caught**:
- `src/doctk/lsp/server.py` - Valid ✓
- `src/doctk/missing.py` - Invalid ✗
- `tests/unit/test_foo.py` - Valid ✓

**How it works**:
- Scans all `.md` files in `.kiro/specs/` (excluding `old/` subdirectory)
- Uses regex to detect file path patterns (src/, tests/, docs/, scripts/, examples/, extensions/)
- Excludes code blocks and common example files (example.py, foo.py, test.py)
- Verifies each path exists relative to project root

**Fix violations by**:
1. Creating the missing file
2. Updating the spec to reference the correct file path
3. Marking planned work with `[TODO]` or `[PLANNED]`

### 2. Code References Exist (`test_spec_code_references_exist`)

**What it checks**: All API references (classes, methods) mentioned in specs actually exist in the codebase.

**Examples caught**:
- `DoctkLanguageServer.validate_syntax()` - Valid if method exists ✓
- `OperationRegistry.missing_method()` - Invalid if method doesn't exist ✗

**How it works**:
- Scans all spec markdown files
- Uses regex to detect Python-style references (Class.method(), module.Class)
- Excludes code blocks and common false positives (Example., Note., TODO., etc.)
- Attempts to import and introspect using `importlib` and `inspect`
- Checks common module locations (doctk.lsp.*, doctk.integration.*, etc.)

**Fix violations by**:
1. Implementing the missing code
2. Updating the spec to reference the correct API
3. Marking planned work with `[TODO]` or `[PLANNED]`

### 3. Line Number References Are Reasonable (`test_spec_line_number_references_reasonable`)

**What it checks**: Line number references don't exceed the actual file length.

**Examples caught**:
- `src/foo.py (line 42)` - Valid if file has ≥42 lines ✓
- `src/foo.py:100` - Invalid if file only has 50 lines ✗

**How it works**:
- Detects patterns like `file.py (line 42)`, `file.py:42`, `file.py (lines 10-20)`
- Counts actual lines in the referenced file
- Verifies line numbers are within bounds

**Fix violations by**:
1. Updating line number references to match current code
2. Marking approximate references with `[APPROXIMATE]`

## Running Tests

```bash
# Run only spec quality tests
pytest tests/docs/test_spec_quality.py -v

# Run all documentation tests (includes spec quality)
pytest tests/docs/ -v

# Run all tests marked as 'docs'
pytest -m docs -v
```

## Design Notes

### Why Generic?

The tests use **zero hardcoded paths**. They work by:
- Automatically discovering all `.md` files in `.kiro/specs/`
- Using regex patterns to detect file/API references
- Dynamically resolving paths relative to project root
- Introspecting Python modules at runtime

This means the tests will work for any new spec added to `.kiro/specs/` without modification.

### Why No Link Enforcement?

We don't control how specs are created, so we can't enforce that all references are markdown links. Instead:
- We detect file paths via regex patterns (with/without backticks, in various contexts)
- We validate the detected paths actually exist
- We provide actionable error messages when paths are wrong

### Pattern Matching Details

**File paths detected**:
- Patterns starting with: `src/`, `tests/`, `docs/`, `scripts/`, `examples/`, `extensions/`
- File extensions: `.py`, `.md`, `.yaml`, `.yml`, `.toml`, `.txt`, `.sh`, `.ts`, `.tsx`, `.json`
- Avoids false positives like matching `src/file.ts` in `extensions/foo/src/file.ts`

**API references detected**:
- Python-style patterns: `Class.method()`, `module.Class.method()`
- Excludes common false positives: Example., Note., TODO., etc.
- Excludes content in code blocks (```...```)

## When to Run

**Before committing spec changes**:
```bash
pytest tests/docs/test_spec_quality.py
```

**After refactoring code**:
```bash
# Ensure specs still reference correct paths/APIs
pytest tests/docs/test_spec_quality.py -v
```

**During CI/CD**:
These tests run automatically with the `@pytest.mark.docs` marker.

## Implementation

See: `tests/docs/test_spec_quality.py` (259 lines)
- Generic fixtures for project_root and spec_files
- Regex-based pattern matching
- Python introspection for API validation
- Clear, actionable error messages
