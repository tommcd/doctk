# Design Document: Core API Stabilization

## Overview

This document details the technical design for stabilizing the doctk core API and DSL. The work addresses critical architectural gaps: unstable node identities, over-serialization in internal operations, scattered type checking, mutable metadata, and dual API paradigms that confuse users.

The design establishes a foundation for future graph-based features (document splitting, transclusion, bidirectional editing) by providing stable node IDs, an efficient internal operations layer, source position tracking, and a unified API surface.

## Architecture

### Current State Analysis

**Existing Strengths:**

- Functional, composable core with category theory foundations
- Clean separation: parsers → core → operations → integration → bridges
- Pipe operator syntax for readable transformations
- Comprehensive test coverage (749 tests)

**Critical Gaps:**

1. **Positional IDs**: `DocumentTreeBuilder` generates IDs like `h2-0`, `h2-1` based on parse order
   - IDs break when documents are edited or re-parsed
   - No way to reference nodes persistently across operations
1. **Over-serialization**: Internal Python callers use JSON-RPC-shaped responses
   - Forces reparsing: `Document` → `str` → `Document` in multi-step pipelines
   - ID remapping required after each operation
1. **No source positions**: AST nodes lack original source locations
   - Line position calculated via fragile text matching heuristics
   - Error messages can't report accurate locations
1. **Mutable metadata**: `metadata: dict[str, Any] = field(default_factory=dict)`
   - Shared references break immutability guarantees
   - Transformations can accidentally mutate original nodes
1. **Dual API confusion**: Declarative (`doc | select | promote`) vs imperative (`StructureOperations.promote(doc, id)`)
   - Different mental models, duplicate implementations
   - No bridge between paradigms

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     External Clients                         │
│              (VS Code, LSP, CLI, REPL)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  JSON-RPC Bridge                             │
│         (Thin wrapper, serialization boundary)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Internal Operations Layer                       │
│    (Rich Document objects, stable IDs, no serialization)    │
│                                                              │
│  • by_id() predicate bridge                                 │
│  • Unified operation registry                               │
│  • TypeGuard-based dispatch                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Core Document Model                         │
│                                                              │
│  Node (with stable ID + provenance + source span)           │
│  Document (functor/monad with immutable metadata)           │
│  Operations (pure morphisms)                                │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Stable Node Identity System

**NodeId Structure:**

```python
@dataclass(frozen=True)
class NodeId:
    """
    Stable, durable node identifier.

    Combines content-based stability with human-readable hints.
    Immutable to prevent accidental modification.
    """
    content_hash: str  # Full SHA-256 hex (64 chars) stored internally
    hint: str          # Human-readable hint (e.g., "introduction", "api-reference")
    node_type: str     # "heading", "paragraph", etc.

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
            NodeId instance with hash prefix stored

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

# Module-level cache for NodeId generation
# NOTE: This is an IN-PROCESS, NON-PERSISTENT cache only.
# Cache keys use Python's hash() which is randomized per process.
# DO NOT persist or share this cache across processes.
_node_id_cache: dict[str, NodeId] = {}

def _get_node_cache_key(node: Node) -> str:
    """
    Generate cache key for node (lightweight hash).

    Uses Python's built-in hash() which is process-specific and randomized.
    This is acceptable because the cache is strictly in-memory and per-process.
    Cache keys are NOT stable across runs and must never be persisted.
    """
    if isinstance(node, Heading):
        return f"h:{node.level}:{hash(node.text)}"
    elif isinstance(node, Paragraph):
        return f"p:{hash(node.content[:100])}"
    else:
        return f"{type(node).__name__.lower()}:{hash(str(node)[:100])}"

def clear_node_id_cache() -> None:
    """Clear NodeId cache (for testing or memory management)."""
    global _node_id_cache
    _node_id_cache.clear()

def _generate_hint(node: Node) -> str:
    """
    Generate human-readable hint for NodeId.

    Rules:
    - Deterministic: Same node content → same hint
    - Lowercase: All hints are lowercase for consistency
    - Slugified: Spaces → hyphens, special chars removed
    - Truncated: Maximum 32 characters
    - Fallback: Node type for non-text nodes

    Examples:
        Heading("Introduction") → "introduction"
        Heading("API Reference Guide") → "api-reference-guide"
        Heading("Getting Started!") → "getting-started"
        Heading("Very Long Heading That Exceeds Limit") → "very-long-heading-that-exceeds"
        Paragraph("Some text") → "paragraph"
        CodeBlock(...) → "codeblock"

    Collision Handling:
        Hints are for human readability only. The content_hash ensures
        uniqueness. Two headings with identical text will have the same
        hint but different hashes (if any other content differs).
    """
    import re
    import unicodedata

    # Get text content based on node type
    if isinstance(node, Heading):
        text = node.text
    elif isinstance(node, Paragraph):
        # Use first 50 chars of paragraph for hint
        text = node.content[:50]
    elif isinstance(node, CodeBlock):
        # Use language as hint if available
        return node.language.lower() if node.language else "codeblock"
    else:
        # Fallback to node type
        return type(node).__name__.lower()

    # Normalize Unicode
    text = unicodedata.normalize('NFC', text)

    # Convert to lowercase
    text = text.lower()

    # Remove non-alphanumeric except spaces and hyphens
    text = re.sub(r'[^a-z0-9\s-]', '', text)

    # Collapse whitespace and convert to hyphens
    text = re.sub(r'\s+', '-', text.strip())

    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Truncate to 32 characters
    text = text[:32].rstrip('-')

    # Ensure non-empty
    if not text:
        return type(node).__name__.lower()

    return text
```

**Canonical Serialization:**

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
        # IMPORTANT: Exclude level so promote/demote preserve ID
        return f"heading:{normalize_text(node.text)}"

    elif isinstance(node, Paragraph):
        return f"paragraph:{normalize_text(node.content)}"

    elif isinstance(node, CodeBlock):
        # Preserve whitespace in code
        return f"codeblock:{node.language or 'none'}:{node.code}"

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
```

**ID Stability Guarantees:**

- **Preserved**: When structural identity unchanged
  - ✅ promote/demote (level changes don't affect hash)
  - ✅ move operations (position doesn't affect hash)
  - ✅ metadata changes (metadata not in hash)
- **Regenerated**: When structural identity changes
  - ❌ Text edits (heading text or paragraph content changes)
  - ❌ Node type changes (heading → paragraph)
- **Consistent**: Re-parsing same content produces same IDs

**Rationale:** Heading level is a presentation attribute, not structural identity. A heading "Introduction" remains the same conceptual node whether it's h2 or h3.

**Text Edit Semantics:**

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
```

### 2. Provenance Metadata

**Provenance Structure:**

```python
@dataclass(frozen=True)
class Provenance:
    """
    Tracks origin and history of a node.
    Immutable to ensure audit trail integrity.
    """
    origin_file: str | None          # Source file path
    version: str | None               # Git commit hash, version tag, or timestamp
    author: str | None                # Creator/last modifier
    created_at: datetime              # Creation timestamp
    modified_at: datetime | None      # Last modification timestamp
    parent_id: NodeId | None          # Parent node ID (for fragments)

    def with_modification(self, author: str | None = None) -> "Provenance":
        """Create new provenance with updated modification time."""
        return Provenance(
            origin_file=self.origin_file,
            version=self.version,
            author=author or self.author,
            created_at=self.created_at,
            modified_at=datetime.now(),
            parent_id=self.parent_id
        )

    @staticmethod
    def from_context(context: "ProvenanceContext") -> "Provenance":
        """Create provenance from execution context."""
        return Provenance(
            origin_file=context.file_path,
            version=context.version,
            author=context.author,
            created_at=datetime.now(),
            modified_at=None,
            parent_id=None
        )

@dataclass
class ProvenanceContext:
    """
    Context for provenance generation.
    Populated by parser/REPL/CLI based on source.
    """
    file_path: str | None = None      # File being parsed (None for REPL/stdin)
    version: str | None = None         # Git commit or version tag
    author: str | None = None          # From git config or environment

    @staticmethod
    def from_file(path: str) -> "ProvenanceContext":
        """Create context for file parsing."""
        return ProvenanceContext(
            file_path=path,
            version=_get_git_commit(),  # Try to get git commit
            author=_get_git_author()     # Try to get git user
        )

    @staticmethod
    def from_repl() -> "ProvenanceContext":
        """Create context for REPL input."""
        return ProvenanceContext(
            file_path=None,
            version=None,
            author=os.environ.get('USER') or os.environ.get('USERNAME')
        )
```

**Integration with Nodes:**

```python
@dataclass
class Node(ABC):
    """Base class with stable ID and provenance."""
    id: NodeId | None = None              # Stable identifier
    provenance: Provenance | None = None  # Origin tracking
    source_span: SourceSpan | None = None # Original source location

    # ... existing methods
```

**Parser Integration:**

```python
class MarkdownParser:
    def parse_file(self, path: str) -> Document[Node]:
        """Parse file with provenance."""
        context = ProvenanceContext.from_file(path)
        return self._parse_with_context(Path(path).read_text(), context)

    def parse_string(self, content: str, context: ProvenanceContext | None = None) -> Document[Node]:
        """Parse string with optional provenance context."""
        if context is None:
            context = ProvenanceContext.from_repl()
        return self._parse_with_context(content, context)

    def _parse_with_context(self, content: str, context: ProvenanceContext) -> Document[Node]:
        """Parse and attach provenance to all nodes."""
        # ... parsing logic ...
        for node in nodes:
            node.provenance = Provenance.from_context(context)
        return Document(nodes)
```

### 3. Source Position Tracking

**SourceSpan Structure:**

```python
@dataclass(frozen=True)
class SourceSpan:
    """
    Precise source location for AST nodes.
    Enables accurate error reporting and round-trip mapping.
    """
    start_line: int      # 0-indexed line number
    start_column: int    # 0-indexed column number
    end_line: int        # 0-indexed line number
    end_column: int      # 0-indexed column number

    def contains(self, line: int, column: int) -> bool:
        """Check if position is within this span."""
        if line < self.start_line or line > self.end_line:
            return False
        if line == self.start_line and column < self.start_column:
            return False
        if line == self.end_line and column > self.end_column:
            return False
        return True

    def overlaps(self, other: "SourceSpan") -> bool:
        """Check if this span overlaps with another."""
        return not (self.end_line < other.start_line or
                   other.end_line < self.start_line)
```

**Parser Integration:**

````python
class MarkdownParser:
    def parse_string(self, content: str) -> Document[Node]:
        """Parse with source position tracking."""
        md = MarkdownIt()
        tokens = md.parse(content)
        lines = content.split('\n')
        nodes = []

        for token in tokens:
            node = self._token_to_node(token)

            # Attach source span with column recovery
            if token.map:
                start_line = token.map[0]
                end_line = token.map[1] - 1

                # Recover columns by scanning source
                start_column = self._find_token_start_column(
                    lines[start_line], token
                )
                end_column = len(lines[end_line]) if end_line < len(lines) else 0

                node.source_span = SourceSpan(
                    start_line=start_line,
                    start_column=start_column,
                    end_line=end_line,
                    end_column=end_column
                )

            nodes.append(node)

        return Document(nodes)

    def _find_token_start_column(self, line: str, token: Token) -> int:
        """
        Recover column position by scanning line content.

        Strategy:
        - For headings: find '##' prefix
        - For lists: find '-' or '1.' prefix
        - For code blocks: find '```' fence
        - Default: skip leading whitespace

        Note: This provides best-effort column accuracy. Exact columns
        for inline elements (bold, links) within blocks are not available
        from markdown-it-py and would require a separate lexer pass.
        """
        if token.type == 'heading_open':
            # Find '##' prefix
            match = re.match(r'^(\s*)(#{1,6})', line)
            return len(match.group(1)) if match else 0
        elif token.type == 'list_item_open':
            # Find list marker
            match = re.match(r'^(\s*)[-*+]|\d+\.', line)
            return len(match.group(1)) if match else 0
        elif token.type == 'fence':
            # Find code fence
            match = re.match(r'^(\s*)```', line)
            return len(match.group(1)) if match else 0
        else:
            # Skip leading whitespace (best effort)
            return len(line) - len(line.lstrip())
````

**Column Accuracy Limitations:**

- **Block-level elements**: Accurate (headings, lists, code blocks)
- **Inline elements**: Share parent block's column (bold, links, code spans)
- **Multi-line tokens**: Start column only, end column is line length
- **Future improvement**: Could add lightweight lexer pass for inline precision

````

**Benefits:**

- Accurate column positions for diagnostics and LSP
- Eliminates fragile text-matching heuristics in `DocumentTreeBuilder._build_line_position_cache`
- Precise error messages: "Error at line 42, column 15"
- Enables accurate cursor positioning in LSP
- Supports round-trip editing (materialized view → source)

**Limitations:**

- Column accuracy depends on token type recognition
- Multi-line tokens use start column for entire span
- Inline elements (bold, links) within blocks share block's column

**Span Transformation During Operations:**

```python
class InternalOperations:
    @staticmethod
    def promote(document: Document[Node], node_id: NodeId) -> OperationResult:
        """Promote with span preservation."""
        node = document.find_node(node_id)

        # Create promoted node with PRESERVED source span
        promoted = Heading(
            level=max(1, node.level - 1),
            text=node.text,
            children=node.children,
            metadata=copy.deepcopy(node.metadata),
            id=node.id,
            provenance=node.provenance.with_modification() if node.provenance else None,
            source_span=node.source_span  # Preserve original span!
        )

        # Span points to original source location
        # This enables round-trip: edit in view → map back to source
        return OperationResult(success=True, document=new_doc, modified_nodes=[node_id])
````

**Multi-File Span Mapping (for Spec 2):**

```python
@dataclass(frozen=True)
class SourceSpan:
    """Extended for multi-file support."""
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    source_file: str | None = None  # For multi-file documents

    def to_absolute(self, base_path: str) -> "SourceSpan":
        """Convert relative path to absolute."""
        if self.source_file and not Path(self.source_file).is_absolute():
            abs_file = str(Path(base_path) / self.source_file)
            return SourceSpan(
                start_line=self.start_line,
                start_column=self.start_column,
                end_line=self.end_line,
                end_column=self.end_column,
                source_file=abs_file
            )
        return self
```

**Inline Span Accuracy and Acceptance Scope:**

This design provides **block-level column accuracy** for the following elements:

- Headings (`##`, `###`, etc.)
- List items (`-`, `*`, `1.`)
- Code blocks (```` ``` ````)
- Paragraphs (start of content)

**Inline elements** (bold `**text**`, links `[text](url)`, inline code `` `code` ``) inherit their parent block's column position. This is a limitation of markdown-it-py's token model, which provides line-level mapping (`token.map`) but not character-level positions within lines.

**Acceptance Criteria Interpretation:**

- **Req 3 AC1** ("exact source location"): Satisfied for block-level elements; inline elements have block-level precision
- **Req 3 AC3** ("accurate cursor positioning"): LSP can position cursor at block start; inline positioning requires user to navigate within block
- **Req 3 AC5** ("round-trip mapping"): Preserved spans enable mapping transformed nodes back to source blocks; inline edits within blocks are not precisely mapped

**Future Enhancement (Out of Scope for This Spec):**
If inline-level precision becomes critical for diagnostics or quick-fixes, a follow-up enhancement could:

1. Add a lightweight inline lexer pass after markdown-it-py parsing
1. Scan paragraph/heading content for inline markers (`**`, `[`, `` ` ``)
1. Generate sub-spans for inline elements
1. Store in `Node.inline_spans: list[InlineSpan]` field

**Testing Strategy:**

- Unit tests will validate block-level column accuracy
- Integration tests will document inline element behavior (inherits block column)
- Performance tests will ensure column recovery overhead is \<5% of parse time

**Materialized View to Source Mapping:**

When documents are transformed (promoted, nested, split across files), the materialized view's positions differ from the original source. To support LSP features (go-to-definition, diagnostics, quick-fixes), we need to map view positions back to source.

**Design Approach:**

```python
@dataclass(frozen=True)
class ViewSourceMapping:
    """
    Maps positions in a materialized view back to original source.
    Used for LSP diagnostics, quick-fixes, and go-to-definition.
    """
    view_span: SourceSpan      # Position in materialized/transformed document
    source_span: SourceSpan    # Position in original source file
    node_id: NodeId            # Stable node identifier
    transform: str             # e.g., "promoted", "nested", "split"

    def project_to_source(self, view_line: int, view_column: int) -> tuple[str, int, int]:
        """
        Project a position in the view back to source file coordinates.

        Returns: (source_file, source_line, source_column)
        """
        if not self.view_span.contains(view_line, view_column):
            raise ValueError(f"Position ({view_line}, {view_column}) not in view span")

        # Calculate offset within view span
        if view_line == self.view_span.start_line:
            offset = view_column - self.view_span.start_column
        else:
            # Multi-line: approximate offset
            offset = view_column

        # Map to source span
        source_line = self.source_span.start_line
        source_column = self.source_span.start_column + offset

        return (self.source_span.source_file or "", source_line, source_column)


class Document:
    """Extended with view mapping support."""
    nodes: list[Node]
    _id_index: dict[NodeId, Node]
    _view_mappings: list[ViewSourceMapping] = field(default_factory=list)

    def add_view_mapping(self, mapping: ViewSourceMapping) -> None:
        """Register a view-to-source mapping."""
        self._view_mappings.append(mapping)

    def find_source_position(self, view_line: int, view_column: int) -> tuple[str, int, int] | None:
        """
        Find the source position for a given view position.

        Returns: (source_file, source_line, source_column) or None if not mapped
        """
        for mapping in self._view_mappings:
            if mapping.view_span.contains(view_line, view_column):
                return mapping.project_to_source(view_line, view_column)
        return None
```

**When Mappings Are Created:**

1. **During Parsing**: Initial mappings are identity (view = source)

   ```python
   doc = MarkdownParser().parse_file("doc.md")
   # Each node's source_span is both view and source position
   ```

1. **During Transformations**: Operations create new mappings

   ```python
   result = InternalOperations.promote(doc, node_id)
   # result.document has updated view_mappings:
   # - Promoted node: view_span (new position) → source_span (original position)
   ```

1. **During Multi-File Composition** (Spec 2): Mappings track file origins

   ```python
   composed = Document.compose([doc1, doc2])
   # Mappings preserve source_file for each node
   ```

**LSP Integration:**

```python
class DoctkLanguageServer:
    def handle_diagnostic(self, error: Exception, view_position: tuple[int, int]) -> Diagnostic:
        """Convert error to LSP diagnostic with source mapping."""
        view_line, view_column = view_position

        # Map view position to source
        source_pos = self.current_document.find_source_position(view_line, view_column)

        if source_pos:
            source_file, source_line, source_column = source_pos
            return Diagnostic(
                range=Range(
                    start=Position(line=source_line, character=source_column),
                    end=Position(line=source_line, character=source_column + 10)
                ),
                message=str(error),
                source=source_file
            )
        else:
            # Fallback: use view position
            return Diagnostic(
                range=Range(
                    start=Position(line=view_line, character=view_column),
                    end=Position(line=view_line, character=view_column + 10)
                ),
                message=str(error)
            )
```

**Scope for This Spec:**

- ✅ **In Scope**: Basic view mapping infrastructure (`ViewSourceMapping`, `Document._view_mappings`)
- ✅ **In Scope**: Identity mappings during parsing (view = source)
- ✅ **In Scope**: Preserved source spans during single-document transformations
- ⚠️ **Partial Scope**: Mapping updates during operations (promote/demote preserve spans; nest/unnest may need offset adjustments)
- ❌ **Out of Scope**: Multi-file composition mappings (deferred to Spec 2: Fragment Graph Model)
- ❌ **Out of Scope**: Complex offset calculations for nested transformations (can be added incrementally)

**Testing Strategy:**

- Unit tests: `ViewSourceMapping.project_to_source()` with various span configurations
- Integration tests: Transform document, verify mappings point to original source
- LSP tests: Trigger diagnostic, verify it reports correct source file/line/column

**Performance Considerations:**

- Mapping lookup is O(n) where n = number of mappings (typically small, \<1000 for most documents)
- Future optimization: spatial index (R-tree) if mapping count becomes large
- Memory overhead: ~64 bytes per mapping (acceptable for typical documents)

### 4. Internal Operations Layer

**Core Principle:** Operations return rich `Document` objects, not serialized strings.

**Current Problem:**

```python
# Current: StructureOperations returns strings
result = StructureOperations.promote(doc, "h2-0")
# result.document is a string!
# Must reparse to continue: Document.from_string(result.document)
```

**New Design:**

```python
# Module: doctk.core.internal_ops

class InternalOperations:
    """
    Internal operations layer returning rich Document objects.
    No serialization - preserves node identity and metadata.
    """

    @staticmethod
    def promote(document: Document[Node], node_id: NodeId) -> OperationResult:
        """
        Promote heading (internal API).

        Returns:
            OperationResult with Document object (not string)
        """
        node = document.find_node(node_id)
        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error="Not a heading")

        # Create promoted node with preserved ID
        promoted = Heading(
            level=max(1, node.level - 1),
            text=node.text,
            children=node.children,
            metadata=copy.deepcopy(node.metadata),  # Immutability!
            id=node.id,  # Preserve stable ID
            provenance=node.provenance.with_modification() if node.provenance else None,
            source_span=node.source_span
        )

        # Replace in document
        new_nodes = [promoted if n.id == node_id else n for n in document.nodes]
        new_doc = Document(new_nodes)

        return OperationResult(
            success=True,
            document=new_doc,  # Rich object, not string!
            modified_nodes=[node_id]
        )
```

**JSON-RPC Bridge (Thin Wrapper):**

```python
# Module: doctk.integration.bridge

class StructureOperations:
    """
    JSON-RPC bridge - wraps internal operations.
    Serialization happens ONLY at this boundary.
    """

    @staticmethod
    def promote(document: Document[Node], node_id: str) -> OperationResult:
        """
        External API for JSON-RPC clients.

        Args:
            node_id: String representation of NodeId

        Returns:
            OperationResult with serialized document string
        """
        # Parse node_id string to NodeId
        parsed_id = NodeId.from_string(node_id)

        # Call internal operation
        result = InternalOperations.promote(document, parsed_id)

        if not result.success:
            return result

        # Serialize ONLY at boundary
        return OperationResult(
            success=True,
            document=result.document.to_string(),  # Serialize here
            modified_ranges=_compute_ranges(document, result.document, result.modified_nodes)
        )
```

### 5. API Paradigm Unification

**Problem:** Two incompatible APIs confuse users.

**Solution:** Bridge via `by_id()` predicate.

```python
# Module: doctk.operations

def by_id(node_id: NodeId | str) -> Callable[[Node], bool]:
    """
    Convert stable node ID to predicate.
    Bridges declarative and imperative paradigms.

    Args:
        node_id: Stable NodeId object or canonical string format (type:hint:hash16)

    Returns:
        Predicate function that matches nodes with the given ID

    Raises:
        ValueError: If string is not a valid stable ID format

    Note:
        This function only accepts stable IDs in canonical format.
    """
    if isinstance(node_id, str):
        node_id = NodeId.from_string(node_id)  # May raise ValueError

    def predicate(node: Node) -> bool:
        return node.id == node_id

    return predicate

# Usage: Declarative API can now target specific nodes
doc | select(by_id("heading:intro:a3f5b9c2")) | promote()

# Imperative API delegates to declarative internally
class StructureOperations:
    @staticmethod
    def promote(doc: Document[Node], node_id: str) -> OperationResult:
        # Use declarative pipeline internally!
        result_doc = doc | select(by_id(node_id)) | operations.promote()
        return OperationResult(success=True, document=result_doc)
```

**Unified Mental Model:**

- **Declarative**: Filter-then-transform (operates on sets)
- **Imperative**: Direct manipulation (operates on specific IDs)
- **Bridge**: `by_id()` converts IDs to predicates, unifying both approaches

### 6. Type Safety Improvements

**Current Problem:** Scattered `isinstance` checks, no type narrowing.

**Solution:** TypeGuards + Generic Document + optional Visitor pattern.

**Generic Document with Type Parameters:**

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

def is_paragraph(node: Node) -> TypeGuard[Paragraph]:
    """Type guard for paragraph nodes."""
    return isinstance(node, Paragraph)

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

**Usage in operations:**

```python
def promote_operation(node: Node) -> Node:
    if is_heading(node):
        # Type checker knows node is Heading here!
        return node.promote()
    raise TypeError(f"Cannot promote {type(node).__name__}")
```

**Visitor Pattern (Optional):**

```python
class PromoteVisitor(NodeVisitor):
    """Visitor for promote operation."""

    def visit_heading(self, node: Heading) -> Node:
        return node.promote()

    def visit_paragraph(self, node: Paragraph) -> Node:
        return node  # Identity for non-headings

    def visit_list(self, node: List) -> Node:
        return node

    # ... other node types

# Usage
def promote() -> Callable[[Document[Node]], Document[Node]]:
    visitor = PromoteVisitor()
    return lambda doc: doc.map(lambda n: n.accept(visitor))
```

**Benefits:**

- Type checkers (mypy, pyright) correctly narrow types
- Better IDE autocomplete with `Document[TNode]`
- Type-safe node access after filtering
- Centralized dispatch logic
- Easier to add new node types

### 7. Metadata Immutability

**Current Problem:**

```python
@dataclass
class Heading(Node):
    metadata: dict[str, Any] = field(default_factory=dict)  # Mutable!

# Bug:
h1 = Heading(level=2, text="Intro", metadata={"tags": ["important"]})
h2 = h1.promote()
h2.metadata["tags"].append("promoted")  # Mutates h1.metadata too! 🐛
```

**Solution:** Deep-copy metadata in all transformations.

```python
@dataclass
class Heading(Node):
    metadata: dict[str, Any] = field(default_factory=dict)

    def promote(self) -> "Heading":
        return Heading(
            level=max(1, self.level - 1),
            text=self.text,
            children=self.children,
            metadata=copy.deepcopy(self.metadata),  # Safe copy!
            id=self.id,
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span
        )
```

**Alternative (Advanced):** Use immutable data structures.

```python
from pyrsistent import pmap, pvector

@dataclass
class Heading(Node):
    metadata: pmap = field(default_factory=pmap)  # Immutable map

    def promote(self) -> "Heading":
        return Heading(
            level=max(1, self.level - 1),
            text=self.text,
            children=self.children,
            metadata=self.metadata,  # No copy needed - immutable!
            id=self.id,
            provenance=self.provenance,
            source_span=self.source_span
        )
```

**Testing:**

```python
def test_metadata_immutability():
    """Verify metadata mutations don't affect originals."""
    h1 = Heading(level=2, text="Test", metadata={"key": "value"})
    h2 = h1.promote()

    h2.metadata["key"] = "modified"

    assert h1.metadata["key"] == "value"  # Original unchanged
    assert h2.metadata["key"] == "modified"
```

### 8. Operation Registry Unification

**Goal:** Single source of truth for operation metadata.

```python
# Module: doctk.core.registry

@dataclass
class OperationMetadata:
    """Metadata for a single operation."""
    name: str
    description: str
    parameters: list[ParameterSpec]
    return_type: str
    examples: list[str]
    category: str  # "structure", "selection", "transformation"

@dataclass
class ParameterSpec:
    """Parameter specification."""
    name: str
    type_hint: str
    description: str
    required: bool
    default: Any | None = None

class OperationRegistry:
    """
    Central registry for all operations.
    Consumed by Python API, DSL, LSP, and documentation.
    """

    def __init__(self):
        self._operations: dict[str, OperationMetadata] = {}

    def register(self, metadata: OperationMetadata) -> None:
        """Register an operation."""
        self._operations[metadata.name] = metadata

    def get(self, name: str) -> OperationMetadata | None:
        """Get operation metadata."""
        return self._operations.get(name)

    def list_by_category(self, category: str) -> list[OperationMetadata]:
        """List operations in a category."""
        return [op for op in self._operations.values() if op.category == category]

    def to_json_schema(self) -> dict:
        """Export as JSON schema for LSP."""
        return {
            "operations": [
                {
                    "name": op.name,
                    "description": op.description,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type_hint,
                            "description": p.description,
                            "required": p.required,
                            "default": p.default
                        }
                        for p in op.parameters
                    ],
                    "returnType": op.return_type,
                    "examples": op.examples
                }
                for op in self._operations.values()
            ]
        }

# Usage: Register operations
registry = OperationRegistry()

registry.register(OperationMetadata(
    name="promote",
    description="Decrease heading level by one (h3 -> h2)",
    parameters=[],
    return_type="Document[Node]",
    examples=["doc | select(heading) | promote()"],
    category="structure"
))
```

**Integration Points:**

- **Python API**: Type hints derived from registry
- **DSL Parser**: Validates commands against registry
- **LSP**: Provides completions/hover from registry
- **Documentation**: Auto-generated from registry

**Registry Enforcement:**

```python
# Module: doctk.core.registry

def register_operation(func: Callable) -> Callable:
    """
    Decorator to auto-register operations.
    Extracts metadata from function signature and docstring.
    """
    import inspect
    from docstring_parser import parse

    sig = inspect.signature(func)
    doc = parse(func.__doc__ or "")

    # Extract metadata from function
    metadata = OperationMetadata(
        name=func.__name__,
        description=doc.short_description or "",
        parameters=[
            ParameterSpec(
                name=param.name,
                type_hint=str(param.annotation),
                description=next((p.description for p in doc.params if p.arg_name == param.name), ""),
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None
            )
            for param in sig.parameters.values()
        ],
        return_type=str(sig.return_annotation),
        examples=doc.examples or [],
        category=func.__dict__.get('_category', 'general')
    )

    # Auto-register
    global_registry.register(metadata)

    return func

# Usage
@register_operation
def promote() -> Callable[[Document[Node]], Document[Node]]:
    """
    Decrease heading level by one (h3 -> h2).

    Examples:
        doc | select(heading) | promote()
    """
    # ... implementation

# In doctk/operations.py - Define public API explicitly
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

# Validation test
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
```

## Data Models

### Core Data Structures

```python
# Module: doctk.core.identity

@dataclass(frozen=True)
class NodeId:
    """Stable node identifier."""
    content_hash: str
    hint: str
    node_type: str

    def __str__(self) -> str:
        return f"{self.node_type}:{self.hint}:{self.content_hash[:8]}"

    @staticmethod
    def from_string(s: str) -> "NodeId":
        """Parse from string representation."""
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid NodeId format: {s}")
        return NodeId(
            node_type=parts[0],
            hint=parts[1],
            content_hash=parts[2]
        )

@dataclass(frozen=True)
class Provenance:
    """Node provenance metadata."""
    origin_file: str | None
    version: str | None
    author: str | None
    created_at: datetime
    modified_at: datetime | None
    parent_id: NodeId | None

@dataclass(frozen=True)
class SourceSpan:
    """Source position information."""
    start_line: int
    start_column: int
    end_line: int
    end_column: int

# Module: doctk.core

@dataclass
class Node(ABC):
    """Base node with stable identity."""
    id: NodeId | None = None
    provenance: Provenance | None = None
    source_span: SourceSpan | None = None

    @abstractmethod
    def accept(self, visitor: "NodeVisitor") -> Any:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

@dataclass
class Heading(Node):
    """Heading node with immutable metadata."""
    level: int
    text: str
    children: list[Node] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def promote(self) -> "Heading":
        """Promote with metadata deep-copy."""
        return Heading(
            level=max(1, self.level - 1),
            text=self.text,
            children=self.children,
            metadata=copy.deepcopy(self.metadata),
            id=self.id,
            provenance=self.provenance.with_modification() if self.provenance else None,
            source_span=self.source_span
        )
```

### Operation Result Types

```python
# Module: doctk.integration.protocols

@dataclass
class OperationResult:
    """Result from an operation."""
    success: bool
    document: Document[Node] | str  # Rich object (internal) or string (external)
    modified_nodes: list[NodeId] | None = None  # For internal API
    modified_ranges: list[ModifiedRange] | None = None  # For external API
    error: str | None = None

@dataclass
class ValidationResult:
    """Result from operation validation."""
    valid: bool
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

@dataclass
class ModifiedRange:
    """Text range modified by an operation."""
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    new_text: str
```

### Document Extensions

```python
# Module: doctk.core

class Document(Generic[T]):
    """Document with node lookup by ID."""

    def __init__(self, nodes: list[T]):
        self.nodes = nodes
        self._id_index: dict[NodeId, T] = {}
        self._build_id_index()

    def _build_id_index(self) -> None:
        """Build index for O(1) node lookup by ID."""
        for node in self.nodes:
            if hasattr(node, 'id') and node.id is not None:
                self._id_index[node.id] = node

    def find_node(self, node_id: NodeId) -> T | None:
        """Find node by stable ID (O(1) lookup)."""
        return self._id_index.get(node_id)

    def find_nodes(self, predicate: Callable[[T], bool]) -> list[T]:
        """Find all nodes matching predicate."""
        return [n for n in self.nodes if predicate(n)]

    # ... existing methods (map, filter, etc.)
```

**Recursive Indexing:**
The ID index is built recursively to include all nodes in the document tree, not just top-level nodes. This ensures O(1) lookup for:

- Top-level document nodes
- Nested list items (`List.items`)
- BlockQuote nested content (`BlockQuote.content`)
- Heading children (`Heading.children`)
- Any other nested structures

**Implementation:** The `_build_id_index()` method uses a recursive helper function to traverse the entire node tree and index every node that has an ID.

## Error Handling

### Diagnostic System

```python
# Module: doctk.core.diagnostics

@dataclass
class Diagnostic:
    """Structured diagnostic message."""
    severity: Literal["error", "warning", "info"]
    message: str
    source_span: SourceSpan | None
    node_id: NodeId | None
    code: str  # e.g., "E001", "W042"
    quick_fixes: list["QuickFix"] = field(default_factory=list)
    context_lines: list[str] = field(default_factory=list)  # Source context for display

@dataclass
class QuickFix:
    """Suggested fix for a diagnostic."""
    title: str
    description: str
    edits: list["TextEdit"]

@dataclass
class TextEdit:
    """Text edit for a quick fix."""
    span: SourceSpan
    new_text: str

class DiagnosticCollector:
    """Collects diagnostics during operations."""

    def __init__(self):
        self.diagnostics: list[Diagnostic] = []

    def error(self, message: str, span: SourceSpan | None = None,
              node_id: NodeId | None = None, code: str = "E000") -> None:
        """Add error diagnostic."""
        self.diagnostics.append(Diagnostic(
            severity="error",
            message=message,
            source_span=span,
            node_id=node_id,
            code=code
        ))

    def warning(self, message: str, span: SourceSpan | None = None,
                node_id: NodeId | None = None, code: str = "W000") -> None:
        """Add warning diagnostic."""
        self.diagnostics.append(Diagnostic(
            severity="warning",
            message=message,
            source_span=span,
            node_id=node_id,
            code=code
        ))
```

### Error Messages

**Before (vague):**

```
Error: Node not found: h2-0
```

**After (precise):**

```
Error [E001]: Node not found
  --> document.md:42:5
   |
42 |   ## Introduction
   |   ^^^^^^^^^^^^^^^ heading:introduction:a3f5b9c2
   |
   = note: This node may have been deleted or its ID changed
   = help: Use `doctk validate` to check document integrity
```

## Testing Strategy

### Unit Tests

**ID Stability Tests:**

```python
def test_stable_id_preserved_across_promote():
    """Verify IDs remain stable during promote operation."""
    doc = Document.from_string("## Heading\\n\\nContent")
    node = doc.nodes[0]
    original_id = node.id

    promoted_doc = doc | select(by_id(original_id)) | promote()
    promoted_node = promoted_doc.find_node(original_id)

    assert promoted_node is not None
    assert promoted_node.id == original_id
    assert promoted_node.level == 1

def test_stable_id_consistent_across_reparse():
    """Verify re-parsing produces same IDs."""
    content = "## Introduction\\n\\nSome text"
    doc1 = Document.from_string(content)
    doc2 = Document.from_string(content)

    assert doc1.nodes[0].id == doc2.nodes[0].id
```

**Metadata Immutability Tests:**

```python
def test_metadata_deep_copy():
    """Verify metadata mutations don't affect originals."""
    h1 = Heading(level=2, text="Test", metadata={"tags": ["a", "b"]})
    h2 = h1.promote()

    h2.metadata["tags"].append("c")

    assert h1.metadata["tags"] == ["a", "b"]
    assert h2.metadata["tags"] == ["a", "b", "c"]
```

**Source Span Tests:**

```python
def test_source_span_attached():
    """Verify parser attaches source spans."""
    doc = Document.from_string("## Heading\\n\\nParagraph")

    heading = doc.nodes[0]
    assert heading.source_span is not None
    assert heading.source_span.start_line == 0
    assert heading.source_span.end_line == 0

def test_source_span_preserved():
    """Verify operations preserve source spans."""
    doc = Document.from_string("## Heading")
    original_span = doc.nodes[0].source_span

    promoted_doc = doc | select(is_heading) | promote()

    assert promoted_doc.nodes[0].source_span == original_span
```

**API Bridge Tests:**

```python
def test_by_id_predicate():
    """Verify by_id() creates correct predicate."""
    node_id = NodeId(content_hash="abc123", hint="intro", node_type="heading")
    h1 = Heading(level=2, text="Intro", id=node_id)
    h2 = Heading(level=2, text="Other", id=NodeId(content_hash="def456", hint="other", node_type="heading"))

    predicate = by_id(node_id)

    assert predicate(h1) == True
    assert predicate(h2) == False
```

### Integration Tests

**Internal Operations Layer:**

```python
def test_internal_ops_no_serialization():
    """Verify internal operations avoid serialization."""
    doc = Document.from_string("## Heading")
    node_id = doc.nodes[0].id

    # Internal API returns Document object
    result = InternalOperations.promote(doc, node_id)

    assert result.success
    assert isinstance(result.document, Document)  # Not string!
    assert result.document.nodes[0].level == 1

def test_multi_step_pipeline_preserves_ids():
    """Verify multi-step operations preserve node identity."""
    doc = Document.from_string("### Heading")
    node_id = doc.nodes[0].id

    # Multi-step: promote twice
    result1 = InternalOperations.promote(doc, node_id)
    result2 = InternalOperations.promote(result1.document, node_id)

    final_node = result2.document.find_node(node_id)
    assert final_node.level == 1
    assert final_node.id == node_id  # ID preserved!
```

### Performance Tests

```python
def test_id_generation_performance():
    """Verify ID generation within 10% of baseline."""
    content = "\\n".join([f"## Heading {i}" for i in range(1000)])

    # Baseline: parse without IDs
    config.use_stable_ids = False
    start = time.time()
    doc1 = Document.from_string(content)
    baseline_time = time.time() - start

    # With stable IDs
    config.use_stable_ids = True
    start = time.time()
    doc2 = Document.from_string(content)
    stable_id_time = time.time() - start

    overhead = (stable_id_time - baseline_time) / baseline_time
    assert overhead < 0.10  # Less than 10% overhead

def test_internal_ops_faster_than_json_rpc():
    """Verify internal ops faster than JSON-RPC round-trips."""
    doc = Document.from_string("## Heading")
    node_id = doc.nodes[0].id

    # Internal API
    start = time.time()
    for _ in range(100):
        result = InternalOperations.promote(doc, node_id)
        doc = result.document
    internal_time = time.time() - start

    # JSON-RPC (with serialization)
    doc = Document.from_string("## Heading")
    start = time.time()
    for _ in range(100):
        result = StructureOperations.promote(doc, str(node_id))
        doc = Document.from_string(result.document)
    json_rpc_time = time.time() - start

    assert internal_time < json_rpc_time
```

## Implementation Plan

**Total Duration:** 11 weeks (wall-clock time with single team)

**Note:** Backward compatibility work has been removed since there are no users yet (v0.1 is alpha/POC). We implement only the new stable ID system.

**Parallelization Opportunities:**

- Phase 3 (Metadata) can start once Phase 2 core operations are stable (week 5)
- Phase 5 (Type Safety) can overlap with Phase 4 completion (week 7)
- Phase 6 (Registry) can partially overlap with Phase 5 (weeks 8-9)
- Documentation tasks can run parallel to implementation throughout

**With 2-3 developers:** Could compress to ~9-10 weeks wall-clock time by parallelizing phases 3-6.

### Phase 1: Stable Node Identity (3 weeks)

**Tasks:**

1. Create `NodeId`, `Provenance`, `SourceSpan` data structures
1. Add fields to `Node` base class
1. Implement `NodeId.from_node()` with canonical serialization (excluding level)
1. Implement `NodeId.from_string()` for parsing
1. Add hash caching with LRU eviction
1. Update `MarkdownParser` to attach source spans with column recovery
1. Add `Document.find_node()` with ID index
1. Write unit tests for ID stability
1. Write tests for provenance population (file, REPL, CLI)

**Deliverables:**

- `doctk/core/identity.py` - NodeId, Provenance, SourceSpan, ProvenanceContext
- Updated `doctk/core.py` - Node with new fields
- Updated `doctk/parsers/markdown.py` - Source span attachment with column recovery
- Tests: `tests/unit/test_stable_ids.py`, `tests/unit/test_provenance.py`

**Exit Criteria:**

- IDs remain stable across promote/demote/move operations
- Re-parsing produces consistent IDs
- Source spans have accurate columns for block-level elements
- Provenance populated correctly for file/REPL/CLI inputs
- Hash caching reduces overhead
- All existing tests pass

### Phase 2: Internal Operations Layer (3 weeks)

**Tasks:**

1. Create `doctk/core/internal_ops.py` module
1. Implement internal versions of all operations
1. Update `StructureOperations` to wrap internal ops
1. Refactor DSL executor to use internal layer
1. Refactor REPL to use internal layer
1. Write integration tests

**Deliverables:**

- `doctk/core/internal_ops.py` - InternalOperations class
- Updated `doctk/integration/operations.py` - Thin wrappers
- Updated `doctk/dsl/executor.py` - Use internal ops
- Updated `doctk/dsl/repl.py` - Use internal ops
- Tests: `tests/integration/test_internal_ops.py`

**Exit Criteria:**

- Internal operations return Document objects
- Multi-step pipelines preserve node identity
- DSL/REPL avoid serialization round-trips
- Performance improves vs baseline
- All existing tests pass

### Phase 3: Metadata Immutability (1 week)

**Tasks:**

1. Add `copy.deepcopy()` to all node transformation methods
1. Write tests verifying immutability
1. Measure performance impact
1. Document immutability guarantees

**Deliverables:**

- Updated node classes with deep-copy
- Tests: `tests/unit/test_metadata_immutability.py`
- Performance benchmarks

**Exit Criteria:**

- Metadata mutations don't affect originals
- Performance within 15% of baseline
- All tests pass

### Phase 4: API Unification (2 weeks)

**Tasks:**

1. Implement `by_id()` predicate function
1. Update `StructureOperations` to delegate to declarative API
1. Write tests for API bridge
1. Document unified mental model

**Deliverables:**

- Updated `doctk/operations.py` - `by_id()` function
- Updated `doctk/integration/operations.py` - Delegation
- Tests: `tests/unit/test_api_bridge.py`
- Documentation: API paradigm guide

**Exit Criteria:**

- `by_id()` correctly converts IDs to predicates
- Imperative operations delegate to declarative
- Both APIs produce identical results
- Documentation explains when to use each

### Phase 5: Type Safety (1 week)

**Tasks:**

1. Create `doctk/core/type_guards.py` module
1. Implement TypeGuard functions for all node types
1. Update operations to use TypeGuards
1. Optionally implement visitor-based dispatch
1. Run mypy/pyright to verify type narrowing

**Deliverables:**

- `doctk/core/type_guards.py` - TypeGuard functions
- Updated operations using TypeGuards
- Type checking configuration
- Tests: `tests/unit/test_type_guards.py`

**Exit Criteria:**

- Type checkers correctly narrow types
- IDE autocomplete works correctly
- No new type errors introduced
- All tests pass

### Phase 6: Operation Registry (2 weeks)

**Tasks:**

1. Create `doctk/core/registry.py` module
1. Define `OperationMetadata` and `ParameterSpec`
1. Register all existing operations
1. Update LSP to consume registry
1. Update DSL parser to validate against registry

**Deliverables:**

- `doctk/core/registry.py` - OperationRegistry class
- Registered metadata for all operations
- Updated LSP integration
- Updated DSL parser
- Tests: `tests/unit/test_registry.py`

**Exit Criteria:**

- All operations registered with complete metadata
- LSP provides accurate completions/hover
- DSL validates commands against registry
- Documentation auto-generated from registry

### Phase 7: Diagnostic Improvements (2 weeks)

**Tasks:**

1. Create `doctk/core/diagnostics.py` module
1. Implement `Diagnostic`, `QuickFix`, `TextEdit` classes
1. Update error handling to use diagnostics
1. Add structured logging
1. Improve error messages with source locations

**Deliverables:**

- `doctk/core/diagnostics.py` - Diagnostic system
- Updated error handling throughout codebase
- Improved error messages
- Tests: `tests/unit/test_diagnostics.py`

**Exit Criteria:**

- All errors include source locations
- Error messages are clear and actionable
- Quick fixes provided where applicable
- Structured metadata for debugging tools

### Phase 8: Performance Validation (1 week)

**Tasks:**

1. Create representative document corpus
1. Write comprehensive performance benchmarks
1. Measure ID generation overhead
1. Measure internal ops vs JSON-RPC
1. Measure metadata deep-copy overhead
1. Profile memory usage
1. Optimize hot paths if needed

**Representative Corpus:**

- Small: 100 nodes, 10KB (typical README)
- Medium: 1,000 nodes, 100KB (typical documentation)
- Large: 10,000 nodes, 1MB (large technical manual)
- Real-world: doctk's own documentation, Python stdlib docs

**Benchmarks:**

```python
# tests/performance/test_core_api_performance.py

def test_id_generation_overhead():
    """Measure ID generation overhead on representative corpus."""
    for doc_size in [100, 1000, 10000]:
        content = generate_document(num_nodes=doc_size)

        # Baseline: parse without IDs
        config.use_stable_ids = False
        baseline_time = timeit(lambda: Document.from_string(content), number=10)

        # With stable IDs
        config.use_stable_ids = True
        stable_id_time = timeit(lambda: Document.from_string(content), number=10)

        overhead = (stable_id_time - baseline_time) / baseline_time
        assert overhead < 0.10, f"ID overhead {overhead:.1%} exceeds 10% for {doc_size} nodes"

def test_internal_ops_performance():
    """Verify internal ops 2x faster than JSON-RPC."""
    doc = Document.from_file("tests/fixtures/large_doc.md")  # 1000 nodes
    node_id = doc.nodes[500].id

    # Internal API (100 operations)
    start = time.time()
    for _ in range(100):
        result = InternalOperations.promote(doc, node_id)
        doc = result.document
    internal_time = time.time() - start

    # JSON-RPC (100 operations)
    doc = Document.from_file("tests/fixtures/large_doc.md")
    start = time.time()
    for _ in range(100):
        result = StructureOperations.promote(doc, str(node_id))
        doc = Document.from_string(result.document)
    json_rpc_time = time.time() - start

    speedup = json_rpc_time / internal_time
    assert speedup >= 2.0, f"Internal ops only {speedup:.1f}x faster (expected 2x)"

def test_memory_usage():
    """Verify memory usage within 20% of baseline."""
    import tracemalloc

    content = generate_document(num_nodes=10000)

    # Baseline memory
    tracemalloc.start()
    config.use_stable_ids = False
    doc1 = Document.from_string(content)
    baseline_memory = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    # With stable IDs
    tracemalloc.start()
    config.use_stable_ids = True
    doc2 = Document.from_string(content)
    stable_id_memory = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    increase = (stable_id_memory - baseline_memory) / baseline_memory
    assert increase < 0.20, f"Memory increase {increase:.1%} exceeds 20%"
```

**Deliverables:**

- Representative document corpus in `tests/fixtures/`
- `tests/performance/test_core_api_performance.py`
- Performance report with baseline measurements
- Memory profiling results
- Optimization patches if needed

**Exit Criteria:**

- ID generation within 10% of baseline (measured on all corpus sizes)
- Internal ops 2x faster than JSON-RPC (measured, not estimated)
- Metadata deep-copy within 15% of baseline
- Existing performance budgets met (1s render, 200ms interaction)
- Memory usage within 20% of baseline (measured with tracemalloc)

## Acceptance Criteria Mapping

### Requirement 1: Stable Node Identity and Provenance

- **AC 1**: NodeId combines content-hash + hint → `NodeId.from_node()`
- **AC 2**: IDs preserved during edits → Internal operations preserve `node.id`
- **AC 3**: Re-parsing produces same IDs → Canonical serialization deterministic
- **AC 4**: IDs retained during promote/demote/move → Tests verify
- **AC 5**: New ID when content changes → `NodeId.from_node()` recomputes
- **AC 6**: Provenance attached on creation → Parser sets `node.provenance`
- **AC 7**: Provenance preserved/updated → `provenance.with_modification()`

### Requirement 2: Internal Operations Layer

- **AC 1**: Returns Document objects → `InternalOperations` methods
- **AC 2**: Preserves identity in chains → No re-parsing
- **AC 3**: DSL uses internal layer → `dsl/executor.py` refactored
- **AC 4**: REPL uses internal layer → `dsl/repl.py` refactored
- **AC 5**: JSON-RPC wraps internal → `StructureOperations` delegates

### Requirement 3: Source Position Tracking

- **AC 1**: Parser attaches spans with block-level precision → `MarkdownParser.parse_string()`
- **AC 2**: Operations preserve spans → Transformations copy `source_span`
- **AC 3**: Errors report locations with block-level precision → Diagnostic system uses spans
- **AC 4**: LSP uses spans → Accurate positioning
- **AC 5**: Materialized views map positions → Provenance + spans + `ViewSourceMapping`
- **AC 6**: Inline elements inherit block spans → Inline nodes use parent block `SourceSpan`

### Requirement 4: Metadata Immutability

- **AC 1**: Deep-copy on transform → `copy.deepcopy(self.metadata)`
- **AC 2**: Mutations don't affect originals → Tests verify
- **AC 3**: No shared references → Each node owns metadata
- **AC 4**: Tests verify immutability → `test_metadata_immutability.py`
- **AC 5**: Acceptable performance → Benchmarks within 15%

### Requirement 5: API Paradigm Unification

- **AC 1**: `by_id()` predicate → `operations.by_id()`
- **AC 2**: Declarative supports ID targeting → `doc | select(by_id(...))`
- **AC 3**: StructureOperations delegates → Uses declarative internally
- **AC 4**: Single operation schema → `OperationRegistry`
- **AC 5**: Documentation explains both → API guide

### Requirement 6: Type Safety Improvements

- **AC 1**: TypeGuard functions → `type_guards.py`
- **AC 2**: Visitor dispatch option → `NodeVisitor` pattern
- **AC 3**: Type checkers narrow correctly → mypy/pyright pass
- **AC 4**: Clear type signatures → Generic support
- **AC 5**: Tests verify narrowing → Type tests

### Requirement 7: Compatibility and Migration

- **AC 1**: Compatibility flag → `config.use_stable_ids`
- **AC 2**: Dual-mode support → `id_compatibility_mode`
- **AC 3**: Deprecation warnings → Gradual migration
- **AC 4**: Tests in both modes → Regression suite
- **AC 5**: Rollback mechanism → CLI command

### Requirement 8: Performance Preservation

- **AC 1**: ID generation \<10% overhead → Benchmarks
- **AC 2**: Internal ops faster → Performance tests
- **AC 3**: Metadata copy \<15% overhead → Benchmarks
- **AC 4**: Meet existing budgets → 1s render, 200ms interaction
- **AC 5**: Memory \<20% increase → Memory profiling

### Requirement 9: Operation Registry Unification

- **AC 1**: Registry stores metadata → `OperationRegistry`
- **AC 2**: Python API uses registry → Type hints derived
- **AC 3**: DSL validates against registry → Parser integration
- **AC 4**: LSP uses registry → Completions/hover
- **AC 5**: Documentation from registry → Auto-generated

### Requirement 10: Diagnostic Improvements

- **AC 1**: Parsing errors with location → `Diagnostic` with `SourceSpan`
- **AC 2**: Operation errors with ID + location → Structured errors
- **AC 3**: Type mismatch explanations → Clear messages
- **AC 4**: LSP quick-fixes → `QuickFix` suggestions
- **AC 5**: Structured metadata → `Diagnostic` class

**Concrete Examples:**

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
```

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

**AC4: LSP integration with quick-fixes**

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

## Open Questions and Decisions

### Q1: NodeId Strategy - UUIDv7 vs Content-Hash?

**Options:**

1. **Content-Hash**: SHA-256 of canonical content

   - ✅ Deterministic (same content → same ID)
   - ✅ Enables deduplication
   - ❌ Changes when content changes

1. **UUIDv7**: Time-ordered UUID

   - ✅ Stable even when content changes
   - ✅ Sortable by creation time
   - ❌ Not deterministic (re-parse → different IDs)

**Decision:** Use **content-hash + hint** hybrid

- Content-hash provides determinism
- Hint provides human-readability
- Best of both worlds for our use case

### Q2: Metadata Immutability - Deep Copy vs Persistent Data Structures?

**Options:**

1. **Deep Copy**: `copy.deepcopy(metadata)`

   - ✅ Simple, no new dependencies
   - ✅ Works with existing dict/list
   - ❌ Performance overhead (~15%)

1. **Persistent Data Structures**: `pyrsistent.pmap`

   - ✅ Zero-copy (structural sharing)
   - ✅ Better performance
   - ❌ New dependency
   - ❌ Different API (learning curve)

**Decision:** Start with **deep copy**, migrate to persistent structures if performance becomes an issue

- Simpler implementation
- Acceptable performance (\<15% overhead)
- Can optimize later without API changes

### Q3: Compatibility Mode Duration?

**Options:**

1. **Short (1 release)**: Quick migration
1. **Medium (3 releases)**: Balanced
1. **Long (6+ releases)**: Maximum safety

**Decision:** **Medium (3 releases)** with clear rollback support

**Migration Timeline:**

- **v0.2.0**: Deploy with `use_stable_ids=False`, `id_compatibility_mode=True`
  - Both ID schemes work
  - Positional IDs are default
  - Stable IDs can be enabled via config
- **v0.3.0**: Switch to `use_stable_ids=True` by default
  - Stable IDs are default
  - Positional IDs still work via compatibility mode
  - Deprecation warnings for positional ID usage
- **v0.4.0**: Remove positional ID support
  - Only stable IDs supported
  - Compatibility mode removed

**Rollback Strategy:**

- Documents store both ID schemes during compatibility mode
- Rollback: `doctk config set use_stable_ids false`
- Artifacts remain usable in both modes
- No data loss during rollback

**Serialization Format (Compatibility Mode):**

```json
{
  "id": "heading:introduction:a3f5b9c2",
  "legacy_id": "h2-0",
  "type": "heading",
  "level": 2,
  "text": "Introduction"
}
```

### Q4: TypeGuard vs Visitor Pattern?

**Options:**

1. **TypeGuard only**: Simpler, type-safe
1. **Visitor only**: Traditional OOP
1. **Both**: Maximum flexibility

**Decision:** **Both, with TypeGuard as default**

- TypeGuard for simple type checks
- Visitor for complex traversals
- Let developers choose based on use case

## Risks and Mitigation

### Risk 1: Performance Degradation

**Risk:** Stable IDs and metadata deep-copying add overhead.

**Mitigation:**

- Benchmark early and often
- Set clear performance budgets (\<10% ID overhead, \<15% metadata overhead)
- Optimize hot paths (ID generation, metadata copying)
- Consider persistent data structures if needed
- Cache computed IDs where possible

**Monitoring:**

- Automated performance tests in CI
- Performance regression alerts
- Memory profiling for large documents

### Risk 2: Breaking Changes

**Risk:** Existing code depends on positional IDs.

**Mitigation:**

- Compatibility mode supports both ID schemes
- Gradual migration over 3 releases
- Comprehensive regression testing
- Clear migration guide
- Rollback mechanism

**Monitoring:**

- Run existing test suite in both modes
- Monitor user feedback during beta
- Track adoption metrics

### Risk 3: Complexity Increase

**Risk:** New abstractions (NodeId, Provenance, SourceSpan) increase cognitive load.

**Mitigation:**

- Clear documentation with examples
- Gradual introduction (stable IDs first, then provenance)
- Hide complexity behind simple APIs
- Provide migration tools

**Monitoring:**

- Developer feedback
- Documentation clarity metrics
- Support ticket volume

### Risk 4: ID Collision

**Risk:** Content-hash collisions (though extremely unlikely with SHA-256).

**Mitigation:**

- Use 16-character hash (64 bits) - collision probability negligible
- Include node type in ID to reduce collision space
- Add hint for additional uniqueness
- Log warnings if collision detected

**Monitoring:**

- Track collision events (should be zero)
- Alert if any collisions occur

## Success Metrics

### Functional Metrics

- ✅ **ID Stability**: 100% of operations preserve node IDs
- ✅ **ID Consistency**: Re-parsing produces identical IDs
- ✅ **Metadata Immutability**: Zero mutations of original nodes
- ✅ **Source Accuracy**: 100% of nodes have accurate source spans
- ✅ **API Parity**: Declarative and imperative APIs produce identical results

### Performance Metrics

- ✅ **ID Generation**: \<10% overhead vs baseline parsing
- ✅ **Internal Operations**: >2x faster than JSON-RPC round-trips
- ✅ **Metadata Copying**: \<15% overhead vs baseline operations
- ✅ **Render Time**: \<1s for documents with 1000 headings
- ✅ **Interaction Time**: \<200ms for common operations
- ✅ **Memory Usage**: \<20% increase for typical documents

### Quality Metrics

- ✅ **Test Coverage**: >90% for new code
- ✅ **Type Coverage**: 100% of public APIs type-annotated
- ✅ **Documentation**: All new APIs documented with examples
- ✅ **Regression**: Zero regressions in existing functionality
- ✅ **Migration**: \<5% of users report migration issues

### Adoption Metrics

- ✅ **Compatibility Mode**: Successfully supports both ID schemes
- ✅ **Migration Rate**: >80% of users migrate within 3 releases
- ✅ **Rollback Rate**: \<1% of users need to rollback
- ✅ **Support Tickets**: \<10 tickets related to migration

## Conclusion

This design establishes a solid foundation for doctk's future by addressing critical architectural gaps. The stable node identity system, internal operations layer, and unified API paradigm enable sophisticated features like document splitting, transclusion, and bidirectional editing while maintaining backward compatibility and performance.

The phased implementation approach (9 weeks total) allows for incremental delivery and validation at each step. The compatibility mode ensures a smooth migration path for existing users.

**Next Steps:**

1. Review and approve this design document
1. Create tasks.md with detailed implementation tasks
1. Begin Phase 1: Stable Node Identity implementation
