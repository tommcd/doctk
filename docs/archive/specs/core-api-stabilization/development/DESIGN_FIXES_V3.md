# Design Fixes V3 - Addressing Final Review

## Summary of Changes Needed

This document addresses the "Request Changes" review feedback with concrete fixes to the design and requirements documents.

______________________________________________________________________

## Issue 1: NodeId Semantics vs Requirement 1.5 (MAJOR)

**Problem:** Requirement 1.5 says "WHEN a node is deleted and recreated, THE System SHALL assign a new ID," but content-hash scheme will re-use the same NodeId for identical content.

**Resolution:** Clarify that "deleted and recreated" means the logical identity is the same. Update requirement wording.

### Requirements.md Change:

**OLD:**

```
5. WHEN a node is deleted and recreated, THE System SHALL assign a new ID to reflect the new identity
```

**NEW:**

```
5. WHEN a node's canonical content changes, THE System SHALL assign a new ID to reflect the changed identity
```

**Rationale:** Content-hash IDs treat nodes with identical canonical content as the same logical entity. This is the correct semantic for:

- Undo/redo operations (recreating identical content should restore the same ID)
- Document merging (identical headings from different sources get same ID)
- Transclusion (same content transcluded multiple times shares ID)

If we need to distinguish "deleted then recreated" from "never deleted", that's a provenance concern, not an identity concern.

______________________________________________________________________

## Issue 2: NodeId String Format and Round-Tripping (MAJOR)

**Problem:**

- `_compute_hash` truncates to 16 chars
- `__str__` truncates to 8 chars
- `from_string` accepts any length
- Round-trip fails: `NodeId.from_string(str(node_id)) != node_id`

**Resolution:** Define canonical format and make `__str__` / `from_string` exact inverses.

### Design.md Changes:

```python
@dataclass(frozen=True)
class NodeId:
    """Stable node identifier."""
    content_hash: str  # Full SHA-256 hex (64 chars) - stored internally
    hint: str
    node_type: str

    def __str__(self) -> str:
        """Canonical string representation: type:hint:hash16

        Uses 16-character hash prefix for balance between uniqueness
        and readability. Collision probability: ~1 in 2^64 for typical
        document sizes (<10K nodes).
        """
        return f"{self.node_type}:{self.hint}:{self.content_hash[:16]}"

    def to_short_string(self) -> str:
        """Short display format: type:hint:hash8

        For UI display only. NOT suitable for persistence or lookup.
        """
        return f"{self.node_type}:{self.hint}:{self.content_hash[:8]}"

    @staticmethod
    def from_string(s: str) -> "NodeId":
        """Parse from canonical string representation.

        Accepts format: "type:hint:hash16" (16-character hash prefix)

        Args:
            s: String in format "node_type:hint:hash16"

        Returns:
            NodeId instance with full hash reconstructed

        Raises:
            ValueError: If format is invalid or hash length wrong
        """
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid NodeId format: {s}. "
                f"Expected 'type:hint:hash16'"
            )

        node_type, hint, hash_prefix = parts

        # Validate hash length (must be 16 chars for canonical format)
        if len(hash_prefix) != 16:
            raise ValueError(
                f"Invalid hash length: {len(hash_prefix)}. "
                f"Expected 16 characters. Use NodeId.from_string() "
                f"only with canonical format from __str__()"
            )

        # Store hash prefix (we don't have full hash from string)
        # This is acceptable because:
        # 1. 16 chars = 64 bits = sufficient uniqueness
        # 2. Full hash only needed for generation, not lookup
        return NodeId(
            node_type=node_type,
            hint=hint,
            content_hash=hash_prefix  # Store prefix as-is
        )

    @staticmethod
    def from_node(node: Node) -> "NodeId":
        """Generate stable ID from node content with caching."""
        cache_key = _get_node_cache_key(node)
        if cache_key in _node_id_cache:
            return _node_id_cache[cache_key]

        canonical = _canonicalize_node(node)
        # Generate FULL hash (64 chars)
        full_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        hint = _generate_hint(node)

        node_id = NodeId(
            content_hash=full_hash,  # Store full hash
            hint=hint,
            node_type=type(node).__name__.lower()
        )

        _node_id_cache[cache_key] = node_id
        return node_id

    def __eq__(self, other: object) -> bool:
        """Equality based on first 16 characters of hash.

        This allows NodeIds created from strings (with 16-char hashes)
        to equal NodeIds created from nodes (with 64-char hashes).
        """
        if not isinstance(other, NodeId):
            return False
        return (
            self.node_type == other.node_type and
            self.hint == other.hint and
            self.content_hash[:16] == other.content_hash[:16]
        )

    def __hash__(self) -> int:
        """Hash based on first 16 characters for consistency with __eq__."""
        return hash((self.node_type, self.hint, self.content_hash[:16]))
```

**Key Changes:**

1. `__str__()` always returns 16-character hash (canonical format)
1. `from_string()` requires exactly 16 characters
1. `to_short_string()` for 8-character display format (UI only)
1. `__eq__()` and `__hash__()` use first 16 characters for consistency
1. Round-trip guaranteed: `NodeId.from_string(str(node_id)) == node_id`

______________________________________________________________________

## Issue 3: Compatibility Mode Positional ID Handling (MAJOR)

**Problem:** `find_node` tries to parse all strings as stable IDs, will crash on "h2-0".

**Resolution:** Add try/except and explicit fallback logic.

### Design.md Changes:

```python
class DocumentTreeBuilder:
    """Enhanced with stable ID support and compatibility mode."""

    def find_node(self, node_id: str | NodeId) -> Node | None:
        """
        Find node by stable ID or positional ID (compatibility mode).

        Args:
            node_id: Stable NodeId, stable ID string, or positional ID string

        Returns:
            Node if found, None otherwise
        """
        # If already a NodeId object, use it directly
        if isinstance(node_id, NodeId):
            return self._id_index.get(node_id)

        # Try parsing as stable ID first
        try:
            stable_id = NodeId.from_string(node_id)
            node = self._id_index.get(stable_id)
            if node is not None:
                return node
        except ValueError:
            # Not a valid stable ID format, continue to positional lookup
            pass

        # Fall back to positional ID (compatibility mode)
        if self.compatibility_mode:
            return self.node_map.get(node_id)  # Legacy positional map

        # In strict mode, only stable IDs are accepted
        return None
```

**Testing:**

```python
def test_compatibility_mode_positional_ids():
    """Verify positional IDs work in compatibility mode."""
    builder = DocumentTreeBuilder(compatibility_mode=True)
    doc = builder.build(tokens)

    # Positional ID should work
    node = doc.find_node("h2-0")
    assert node is not None
    assert isinstance(node, Heading)

    # Stable ID should also work
    stable_id = str(node.id)
    node2 = doc.find_node(stable_id)
    assert node2 == node

def test_strict_mode_rejects_positional_ids():
    """Verify positional IDs rejected in strict mode."""
    builder = DocumentTreeBuilder(compatibility_mode=False)
    doc = builder.build(tokens)

    # Positional ID should NOT work
    node = doc.find_node("h2-0")
    assert node is None

    # Stable ID should work
    stable_id = str(doc.nodes[0].id)
    node = doc.find_node(stable_id)
    assert node is not None
```

______________________________________________________________________

## Issue 4: SourceSpan Granularity vs "Exact Location" (MAJOR)

**Problem:** Requirements say "exact source location" but design only provides block-level accuracy.

**Resolution:** Update requirements to clarify "block-level precision" and add note about inline elements.

### Requirements.md Changes:

**Requirement 3, AC1 - OLD:**

```
1. WHEN a document is parsed, THE System SHALL attach exact source location (line, column) to each node
```

**Requirement 3, AC1 - NEW:**

```
1. WHEN a document is parsed, THE System SHALL attach source location (line, column) to each block-level node with block-level precision
```

**Add new AC6:**

```
6. WHEN inline elements are parsed, THE System SHALL inherit source location from their containing block
```

**Add note after AC list:**

```
**Note:** "Block-level precision" means accurate line and column positions for structural elements (headings, paragraphs, lists, code blocks). Inline elements (bold, links, inline code) inherit their parent block's position. This is sufficient for LSP diagnostics, go-to-definition, and most editing operations. Inline-level precision can be added in a future enhancement if needed.
```

______________________________________________________________________

## Issue 5: Text Edit ID Stability Semantics (MAJOR)

**Problem:** Unclear whether text edits preserve or change IDs.

**Resolution:** Add explicit rule and update design.

### Design.md Addition (in "ID Stability Guarantees" section):

````markdown
### Text Edit Semantics

**Rule:** Any operation that modifies fields included in `_canonicalize_node()` MUST generate a new NodeId.

**Fields in Canonical Form:**
- Heading: `text` (level excluded)
- Paragraph: `content`
- CodeBlock: `language`, `code`
- ListItem: `content`

**Examples:**

```python
# Text edit → New ID
heading = Heading(level=2, text="Introduction")
original_id = heading.id

edited = heading.with_text("Overview")  # Text changed
assert edited.id != original_id  # NEW ID

# Structural change → Same ID
promoted = heading.promote()  # Level changed, text same
assert promoted.id == original_id  # SAME ID

# Metadata change → Same ID
tagged = heading.with_metadata({"tags": ["important"]})
assert tagged.id == original_id  # SAME ID (metadata not in canonical form)
````

**Implementation:**

All node transformation methods that modify canonical fields must call `NodeId.from_node()`:

```python
class Heading:
    def with_text(self, new_text: str) -> "Heading":
        """Create new heading with different text."""
        return Heading(
            level=self.level,
            text=new_text,
            children=self.children,
            metadata=copy.deepcopy(self.metadata),
            id=NodeId.from_node(Heading(level=self.level, text=new_text)),  # NEW ID
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span
        )

    def promote(self) -> "Heading":
        """Promote heading (decrease level)."""
        return Heading(
            level=max(1, self.level - 1),
            text=self.text,
            children=self.children,
            metadata=copy.deepcopy(self.metadata),
            id=self.id,  # PRESERVE ID (level not in canonical form)
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span
        )
```

**Testing:**

```python
def test_text_edit_changes_id():
    """Verify text edits generate new IDs."""
    heading = Heading(level=2, text="Original")
    original_id = heading.id

    edited = heading.with_text("Modified")

    assert edited.id != original_id
    assert edited.text == "Modified"
    assert edited.level == heading.level

def test_structural_change_preserves_id():
    """Verify structural changes preserve IDs."""
    heading = Heading(level=2, text="Test")
    original_id = heading.id

    promoted = heading.promote()

    assert promoted.id == original_id
    assert promoted.level == 1
    assert promoted.text == heading.text
```

```

---

## Issue 6: Implementation Plan Duration (MAJOR)

**Problem:** Phases sum to 15 weeks but document claims 9 weeks.

**Resolution:** Correct to 12 weeks (already done in tasks.md) and explain parallelization.

### Design.md Changes:

**OLD:**
```

**Total Duration:** 9 weeks

```

**NEW:**
```

**Total Duration:** 12 weeks (wall-clock time with single team)

**Parallelization Opportunities:**

- Phase 3 (Metadata) can start once Phase 2 core operations are stable (week 5)
- Phase 5 (Type Safety) can overlap with Phase 4 completion (week 8)
- Phase 6 (Registry) and Phase 7 (Compatibility) can partially overlap (weeks 9-11)
- Documentation tasks can run parallel to implementation throughout

**With 2-3 developers:** Could compress to ~9-10 weeks wall-clock time by parallelizing phases 3-7.

**Conservative Estimate:** 12 weeks assumes single developer or small team with sequential execution and buffer time for integration complexity.

````

---

## Issue 7: Canonicalization Specification (MAJOR/MINOR)

**Problem:** Canonicalization rules only partially specified.

**Resolution:** Add complete specification table.

### Design.md Addition:

```markdown
### Canonical Form Specification

**Normalization Rules:**
- Unicode: NFC normalization (composed form)
- Whitespace: Strip leading/trailing, collapse internal to single space
- Line endings: Convert to LF (`\n`)
- Tabs: Convert to 4 spaces
- Case: Preserve (case-sensitive)

**Node Type Canonical Forms:**

| Node Type | Canonical Form | Fields Included | Fields Excluded |
|-----------|----------------|-----------------|-----------------|
| Heading | `heading:{text}` | text (normalized) | level, children, metadata |
| Paragraph | `paragraph:{content}` | content (normalized) | metadata |
| CodeBlock | `codeblock:{lang}:{code}` | language, code (preserves whitespace) | metadata |
| ListItem | `listitem:{content}` | content (normalized) | list_type, metadata |
| List | `list:{type}:{items}` | list_type, canonical forms of items | metadata |
| BlockQuote | `blockquote:{content}` | content (normalized) | metadata |

**Implementation:**

```python
def _canonicalize_node(node: Node) -> str:
    """Generate canonical string representation for hashing."""

    def normalize_text(text: str) -> str:
        """Apply normalization rules."""
        import unicodedata
        # NFC normalization
        text = unicodedata.normalize('NFC', text)
        # Strip and collapse whitespace
        text = ' '.join(text.split())
        # Convert tabs to spaces
        text = text.replace('\t', '    ')
        return text

    if isinstance(node, Heading):
        return f"heading:{normalize_text(node.text)}"

    elif isinstance(node, Paragraph):
        return f"paragraph:{normalize_text(node.content)}"

    elif isinstance(node, CodeBlock):
        # Preserve whitespace in code
        return f"codeblock:{node.language}:{node.code}"

    elif isinstance(node, ListItem):
        return f"listitem:{normalize_text(node.content)}"

    elif isinstance(node, List):
        items_canonical = '|'.join(_canonicalize_node(item) for item in node.items)
        return f"list:{node.list_type}:{items_canonical}"

    elif isinstance(node, BlockQuote):
        return f"blockquote:{normalize_text(node.content)}"

    else:
        # Fallback for unknown types
        return f"{type(node).__name__.lower()}:{str(node)}"
````

**Testing:**

```python
def test_canonicalization_unicode_normalization():
    """Verify Unicode normalization in canonical form."""
    # é can be represented as single char (U+00E9) or e + combining acute (U+0065 U+0301)
    h1 = Heading(level=2, text="café")  # Single char
    h2 = Heading(level=2, text="café")  # Combining char

    assert _canonicalize_node(h1) == _canonicalize_node(h2)

def test_canonicalization_whitespace():
    """Verify whitespace normalization."""
    h1 = Heading(level=2, text="  Multiple   spaces  ")
    h2 = Heading(level=2, text="Multiple spaces")

    assert _canonicalize_node(h1) == _canonicalize_node(h2)

def test_canonicalization_tabs():
    """Verify tab conversion."""
    h1 = Heading(level=2, text="Text\twith\ttabs")
    h2 = Heading(level=2, text="Text    with    tabs")

    assert _canonicalize_node(h1) == _canonicalize_node(h2)
```

````

---

## Issue 8: Diagnostic System Mapping (MAJOR)

**Problem:** Diagnostic primitives defined but not concretely mapped to Requirement 10 ACs.

**Resolution:** Add concrete examples for each AC.

### Design.md Addition (in Diagnostic Improvements section):

```markdown
### Requirement 10 Acceptance Criteria - Concrete Mappings

**AC1: Parsing errors with location**

```python
# Example: Invalid heading level
try:
    doc = MarkdownParser().parse_string("####### Too many hashes")
except ParsingError as e:
    diagnostic = Diagnostic(
        severity="error",
        message="Invalid heading level: 7 (maximum is 6)",
        source_span=SourceSpan(start_line=0, start_column=0, end_line=0, end_column=7),
        node_id=None,
        code="E001",
        context_lines=[
            "####### Too many hashes",
            "^^^^^^^"
        ]
    )
````

**AC2: Operation errors with ID + location**

```python
# Example: Promote at minimum level
try:
    result = InternalOperations.promote(doc, node_id)
except OperationError as e:
    diagnostic = Diagnostic(
        severity="error",
        message="Cannot promote heading: already at minimum level (1)",
        source_span=node.source_span,
        node_id=node.id,
        code="E042",
        quick_fixes=[
            QuickFix(
                title="Convert to paragraph",
                edits=[TextEdit(span=node.source_span, new_text=node.text)]
            )
        ]
    )
```

**AC3: Type mismatch explanations**

```python
# Example: Wrong node type for operation
try:
    result = InternalOperations.promote(doc, paragraph_id)  # Paragraph, not heading
except TypeError as e:
    diagnostic = Diagnostic(
        severity="error",
        message="Cannot promote node: expected Heading, got Paragraph",
        source_span=node.source_span,
        node_id=node.id,
        code="E103",
        context_lines=[
            "This is a paragraph.",
            "^^^^^^^^^^^^^^^^^^^^^"
        ]
    )
```

**AC4: LSP integration**

```python
class DoctkLanguageServer:
    def handle_operation_error(self, error: OperationError) -> list[lsp.Diagnostic]:
        """Convert operation errors to LSP diagnostics."""
        diagnostics = []

        for diag in error.diagnostics:
            # Map source span to LSP range
            if diag.source_span:
                lsp_range = lsp.Range(
                    start=lsp.Position(
                        line=diag.source_span.start_line,
                        character=diag.source_span.start_column
                    ),
                    end=lsp.Position(
                        line=diag.source_span.end_line,
                        character=diag.source_span.end_column
                    )
                )
            else:
                lsp_range = lsp.Range(start=lsp.Position(0, 0), end=lsp.Position(0, 0))

            # Convert quick fixes to code actions
            code_actions = []
            for fix in diag.quick_fixes:
                action = lsp.CodeAction(
                    title=fix.title,
                    kind=lsp.CodeActionKind.QuickFix,
                    edit=lsp.WorkspaceEdit(
                        changes={
                            doc_uri: [
                                lsp.TextEdit(
                                    range=self._span_to_range(edit.span),
                                    newText=edit.new_text
                                )
                                for edit in fix.edits
                            ]
                        }
                    )
                )
                code_actions.append(action)

            diagnostics.append(lsp.Diagnostic(
                range=lsp_range,
                message=diag.message,
                severity=self._severity_to_lsp(diag.severity),
                code=diag.code,
                source="doctk",
                data={"quick_fixes": code_actions}
            ))

        return diagnostics
```

**Representative Quick-Fix Scenarios:**

1. **Out-of-range heading level:**

   - Error: "Heading level 7 exceeds maximum (6)"
   - Quick fix: "Change to level 6"
   - Edit: Replace `#######` with `######`

1. **Missing transclusion target:**

   - Error: "Transclusion target not found: 'missing.md#section'"
   - Quick fix: "Create target file"
   - Edit: Create `missing.md` with `## section` heading

1. **Invalid list nesting:**

   - Error: "List item indentation inconsistent"
   - Quick fix: "Fix indentation"
   - Edit: Adjust leading spaces to match parent level

1. **Duplicate heading IDs:**

   - Warning: "Duplicate heading text may cause ID collision"
   - Quick fix: "Make heading unique"
   - Edit: Append " (2)" to heading text

````

---

## Issue 9: Operation Registry Completeness Test (MINOR)

**Problem:** Test walks all callables in `doctk.operations`, may be brittle.

**Resolution:** Use explicit `__all__` list.

### Design.md Changes:

```python
# In doctk/operations.py

__all__ = [
    # Selection operations
    "select",
    "where",
    "by_id",

    # Transformation operations
    "promote",
    "demote",
    "nest",
    "unnest",

    # Utility operations
    "map_nodes",
    "filter_nodes",
    "fold",
]

# In tests

def test_registry_completeness():
    """Verify all public operations are registered."""
    import doctk.operations

    # Get all operations from __all__
    public_operations = doctk.operations.__all__

    # Get registered operations
    registered = set(OperationRegistry.list_operations())

    # Verify all public operations are registered
    for op_name in public_operations:
        assert op_name in registered, f"Operation {op_name} not registered"
````

______________________________________________________________________

## Issue 10: Generic Type Support (MINOR)

**Problem:** Generic support sketched but not concrete.

**Resolution:** Add concrete example.

### Design.md Addition:

```python
from typing import TypeVar, Generic, TypeGuard

TNode = TypeVar('TNode', bound=Node)

class Document(Generic[TNode]):
    """Generic document parameterized by node type."""
    nodes: list[TNode]
    _id_index: dict[NodeId, TNode]

    def find_node(self, node_id: NodeId) -> TNode | None:
        """Find node by ID with type preservation."""
        return self._id_index.get(node_id)

# TypeGuard for type narrowing
def is_heading(node: Node) -> TypeGuard[Heading]:
    """Type guard for heading nodes."""
    return isinstance(node, Heading)

# Typed select operation
def select(
    predicate: Callable[[Node], TypeGuard[TNode]]
) -> Callable[[Document[Node]], Document[TNode]]:
    """
    Select nodes matching predicate with type narrowing.

    Example:
        doc: Document[Node] = ...
        headings: Document[Heading] = doc | select(is_heading)
    """
    def _select(doc: Document[Node]) -> Document[TNode]:
        filtered = [n for n in doc.nodes if predicate(n)]
        return Document[TNode](filtered)
    return _select

# Usage example
doc: Document[Node] = MarkdownParser().parse_file("doc.md")

# Type-safe selection
headings: Document[Heading] = doc | select(is_heading)

# IDE knows headings.nodes is list[Heading]
for heading in headings.nodes:
    print(heading.level)  # Type-safe access to Heading.level
```

______________________________________________________________________

## Summary of All Changes

### Requirements.md

1. Update Req 1.5: "deleted and recreated" → "canonical content changes"
1. Update Req 3 AC1: Add "block-level precision"
1. Add Req 3 AC6: Inline elements inherit block position
1. Add note explaining block-level vs inline precision

### Design.md

1. Fix NodeId string format (16-char canonical, round-trip guaranteed)
1. Add text edit ID stability rules and examples
1. Fix compatibility mode with try/except for positional IDs
1. Add complete canonicalization specification table
1. Correct timeline to 12 weeks with parallelization notes
1. Add concrete diagnostic examples for all Req 10 ACs
1. Use `__all__` for registry completeness test
1. Add concrete generic type example

### Testing

1. Add tests for NodeId round-tripping
1. Add tests for text edit ID changes
1. Add tests for positional ID compatibility
1. Add tests for canonicalization normalization
1. Add tests for diagnostic generation

______________________________________________________________________

## Open Questions - Answered

1. **Identity semantics:** Content-hash treats identical content as same logical node. Provenance tracks creation/modification history.

1. **Stable ID format:** 16-character hash prefix is canonical. 8-character is display-only via `to_short_string()`.

1. **Positional ID compatibility:** Try stable ID first, catch ValueError, fall back to positional map.

1. **SourceSpan granularity:** Block-level precision is sufficient and explicitly documented in requirements.

1. **Phase scheduling:** 12 weeks sequential; can compress to 9-10 with 2-3 developers and parallelization.

1. **Generic typing:** `Document[TNode]` with TypeGuard-powered operations for IDE support.

1. **Diagnostics granularity:** Concrete examples added for parsing errors, operation errors, type mismatches, and LSP integration.
