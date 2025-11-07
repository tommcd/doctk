# doctk Specification v0.2

**Status**: Draft
**Last Updated**: 2025-11-07
**POC Version**: 0.1.0
**Target Version**: 1.0.0

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Abstractions](#core-abstractions)
4. [Operation Catalog](#operation-catalog)
5. [Selection System](#selection-system)
6. [Format Support](#format-support)
7. [CLI Design](#cli-design)
8. [Python API](#python-api)
9. [Type System](#type-system)
10. [Error Handling](#error-handling)
11. [Performance](#performance)
12. [Extension Points](#extension-points)
13. [Implementation Phases](#implementation-phases)

---

## Overview

### Vision

doctk is a **composable, format-agnostic toolkit** for structured document manipulation that brings functional programming elegance and mathematical rigor to document processing.

### Design Pillars

1. **Composability** - Complex operations from simple primitives
2. **Purity** - Immutable transformations, referential transparency
3. **Type Safety** - Well-typed operations with LSP support
4. **Format Agnostic** - Universal AST with format adapters
5. **Developer Experience** - Intuitive syntax, great tooling

### Target Users

- **Developers**: Automate documentation tasks, build doc tools
- **Technical Writers**: Refactor large doc sets, maintain consistency
- **Content Engineers**: Transform between formats, apply templates
- **Educators**: Create interactive document tutorials

---

## Architecture

### Layered Design

```
┌─────────────────────────────────────────────────────┐
│  Interface Layer                                    │
│  - CLI (doctk command)                             │
│  - Python API                                       │
│  - LSP Server                                       │
│  - VSCode Extension                                 │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  Operation Layer                                    │
│  - Selection (select, where, find)                  │
│  - Transform (map, promote, demote)                 │
│  - Structure (nest, unnest, lift, lower)            │
│  - Content (extract, replace, wrap)                 │
│  - Composition (compose, pipe, chain)               │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  Core Layer (UDAST)                                 │
│  - Document (Functor/Monad)                         │
│  - Node Hierarchy                                   │
│  - Tree Operations                                  │
│  - Visitor Pattern                                  │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  Format Adapter Layer                               │
│  - Markdown (Reader/Writer)                         │
│  - reStructuredText (Reader/Writer)                 │
│  - HTML (Reader/Writer)                             │
│  - Confluence (Reader/Writer)                       │
│  - Custom Format API                                │
└─────────────────────────────────────────────────────┘
```

### Module Organization

```
doctk/
├── core/
│   ├── __init__.py
│   ├── document.py         # Document class
│   ├── nodes.py            # Node hierarchy
│   ├── visitors.py         # Visitor patterns
│   └── types.py            # Type definitions
├── operations/
│   ├── __init__.py
│   ├── selection.py        # Select, where, find
│   ├── transform.py        # Map, filter, reduce
│   ├── structure.py        # Promote, demote, nest, etc.
│   ├── content.py          # Extract, replace, wrap
│   ├── composition.py      # Compose, pipe utilities
│   └── predicates.py       # Common predicates
├── formats/
│   ├── __init__.py
│   ├── base.py             # Reader/Writer interfaces
│   ├── markdown/
│   │   ├── reader.py
│   │   └── writer.py
│   ├── rst/
│   │   ├── reader.py
│   │   └── writer.py
│   ├── html/
│   │   ├── reader.py
│   │   └── writer.py
│   └── confluence/
│       ├── reader.py
│       └── writer.py
├── selection/
│   ├── __init__.py
│   ├── path.py             # Path-based selection
│   ├── css.py              # CSS-like selectors
│   ├── xpath.py            # XPath-like queries
│   └── pattern.py          # Pattern matching
├── tools/
│   ├── __init__.py
│   ├── outliner.py         # Structure visualization
│   ├── differ.py           # Document comparison
│   ├── validator.py        # Structure validation
│   ├── stats.py            # Document statistics
│   └── templates.py        # Template system
├── cli/
│   ├── __init__.py
│   ├── main.py             # CLI entry point
│   ├── commands/
│   │   ├── outline.py
│   │   ├── transform.py
│   │   ├── query.py
│   │   └── validate.py
│   └── tui.py              # Interactive mode
└── lsp/
    ├── __init__.py
    ├── server.py           # LSP server
    └── features.py         # Completions, hover, etc.
```

---

## Core Abstractions

### Document (UDAST)

```python
class Document(Generic[T]):
    """
    Universal Document AST.

    A Document is:
    - Functor: Can map transformations
    - Monad: Can chain operations
    - Traversable: Can fold/reduce
    - Filterable: Supports predicates
    """

    nodes: list[T]
    metadata: dict[str, Any]
    format_hints: dict[str, Any]  # Format-specific metadata

    # Functor
    def map(self, f: Callable[[T], U]) -> Document[U]
    def map_tree(self, f: Callable[[T], U]) -> Document[U]  # Recursive

    # Monad
    def flatmap(self, f: Callable[[T], Document[U]]) -> Document[U]
    def bind(self, f: Callable[[T], Document[U]]) -> Document[U]  # Alias

    # Traversable
    def reduce(self, f: Callable[[U, T], U], initial: U) -> U
    def fold(self, f: Callable[[U, T], U], initial: U) -> U  # Alias
    def traverse(self, visitor: Visitor) -> Any

    # Filterable
    def filter(self, predicate: Callable[[T], bool]) -> Document[T]
    def partition(self, predicate: Callable[[T], bool]) -> tuple[Document[T], Document[T]]

    # Pipe operator
    def __or__(self, op: Callable[[Document[T]], Document[U]]) -> Document[U]

    # Set operations
    def union(self, other: Document[T]) -> Document[T]
    def intersect(self, other: Document[T], key=None) -> Document[T]
    def diff(self, other: Document[T], key=None) -> Document[T]
    def symmetric_diff(self, other: Document[T]) -> Document[T]

    # Tree operations
    def flatten(self) -> Document[T]
    def depth_first(self) -> Iterator[T]
    def breadth_first(self) -> Iterator[T]
    def find_path(self, predicate: Callable[[T], bool]) -> list[T] | None

    # IO
    @staticmethod
    def from_file(path: str, format: str | None = None) -> Document[Node]
    @staticmethod
    def from_string(content: str, format: str) -> Document[Node]

    def to_file(self, path: str, format: str | None = None) -> None
    def to_string(self, format: str) -> str
```

### Node Hierarchy

```python
class Node(ABC):
    """Base node with location tracking."""

    id: str | None  # Optional unique identifier
    location: Location  # Source location (file, line, col)
    metadata: dict[str, Any]
    parent: Node | None  # Parent reference

    @abstractmethod
    def accept(self, visitor: Visitor) -> Any: ...
    @abstractmethod
    def children(self) -> list[Node]: ...
    @abstractmethod
    def clone(self) -> Node: ...

# Content Nodes
class Heading(Node):
    level: int  # 1-6
    text: str
    id: str | None  # HTML id attribute
    classes: list[str]
    children: list[Node]  # Content under heading

class Paragraph(Node):
    content: list[Inline]  # Mixed inline content

class Text(Node):
    content: str

# Container Nodes
class Section(Node):
    """Explicit section grouping."""
    heading: Heading | None
    content: list[Node]

class List(Node):
    ordered: bool
    start: int | None
    items: list[ListItem]
    tight: bool  # Spacing hint

class ListItem(Node):
    content: list[Node]
    checked: bool | None  # For task lists

class Table(Node):
    header: list[TableRow] | None
    body: list[TableRow]
    alignment: list[Alignment]

class TableRow(Node):
    cells: list[TableCell]

class TableCell(Node):
    content: list[Node]
    colspan: int
    rowspan: int

# Block Nodes
class CodeBlock(Node):
    code: str
    language: str | None
    meta: str | None  # Additional info

class BlockQuote(Node):
    content: list[Node]

class HorizontalRule(Node):
    pass

# Inline Nodes
class Inline(Node):
    """Base for inline content."""
    pass

class Link(Inline):
    url: str
    title: str | None
    content: list[Inline]

class Image(Inline):
    url: str
    alt: str
    title: str | None

class Code(Inline):
    code: str

class Emphasis(Inline):
    content: list[Inline]
    strong: bool  # True = strong, False = emphasis

class LineBreak(Inline):
    hard: bool  # Hard break vs soft
```

### Location Tracking

```python
@dataclass
class Location:
    """Source location for error reporting and navigation."""

    file: str | None
    line: int
    column: int
    offset: int  # Character offset from start

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

@dataclass
class Range:
    """Range spanning multiple locations."""

    start: Location
    end: Location
```

---

## Operation Catalog

### Selection Operations

#### Basic Selection

```python
# Type-based selection
select(predicate: Callable[[Node], bool]) -> Operation
select_type(node_type: type[T]) -> Operation[T]

# Convenient shortcuts
heading: Operation      # Select all headings
paragraph: Operation    # Select all paragraphs
list_node: Operation    # Select all lists
code_block: Operation   # Select all code blocks
link: Operation         # Select all links
image: Operation        # Select all images

# Predicate builders
where(**conditions) -> Operation
where_level(level: int) -> Operation
where_lang(language: str) -> Operation
where_url(pattern: str) -> Operation
```

#### Advanced Selection

```python
# Path-based (hierarchical)
select_path(path: str) -> Operation
# Examples:
#   "/Introduction"
#   "/Chapter 1/Section 2"
#   "//subsection[@id='advanced']"

# CSS-like selectors
select_css(selector: str) -> Operation
# Examples:
#   "heading[level=2]"
#   "list > item"
#   ".warning"
#   "#introduction"

# XPath-like queries
select_xpath(xpath: str) -> Operation
# Examples:
#   "//heading[@level=2]"
#   "//list[ordered=true]/item[1]"
#   "//section[contains(@id, 'api')]"

# Pattern matching
match(pattern: Pattern) -> Operation
# Examples:
#   match(heading(level=2, text__contains="API"))
#   match(list(ordered=True, items__count__gt=5))
```

#### Relational Selection

```python
# Navigate tree
parent() -> Operation          # Get parent node
children() -> Operation        # Get children
siblings() -> Operation        # Get siblings
ancestors() -> Operation       # All ancestors
descendants() -> Operation     # All descendants

# Relative positioning
next_sibling() -> Operation
prev_sibling() -> Operation
first_child() -> Operation
last_child() -> Operation

# Contextual
following() -> Operation       # All following nodes
preceding() -> Operation       # All preceding nodes
```

### Transform Operations

#### Structure Transforms

```python
# Heading level manipulation
promote() -> Operation         # Decrease level (h3 -> h2)
demote() -> Operation          # Increase level (h2 -> h3)
set_level(level: int) -> Operation

# List operations
to_ordered() -> Operation
to_unordered() -> Operation
toggle_ordered() -> Operation

# Nesting (hierarchy changes)
nest() -> Operation            # Make next sibling a child
unnest() -> Operation          # Move children up to siblings
indent() -> Operation          # Alias for nest
dedent() -> Operation          # Alias for unnest

# Ordering (sibling movement)
lift() -> Operation            # Move up in sibling order
lower() -> Operation           # Move down in sibling order
move_to(index: int) -> Operation
move_before(target) -> Operation
move_after(target) -> Operation
```

#### Type Transforms

```python
# Convert between types
to_heading(level: int) -> Operation
to_paragraph() -> Operation
to_blockquote() -> Operation
to_code_block(language: str | None) -> Operation
to_list(ordered: bool) -> Operation

# Wrap/unwrap
wrap(node_type: type[Node], **attrs) -> Operation
unwrap() -> Operation

# Split/merge
split_at(predicate) -> Operation
merge_adjacent() -> Operation
```

#### Content Transforms

```python
# Text manipulation
replace_text(pattern: str, replacement: str) -> Operation
replace_text_regex(pattern: re.Pattern, replacement: str) -> Operation
transform_text(f: Callable[[str], str]) -> Operation

# Examples:
#   transform_text(str.upper)
#   transform_text(lambda s: s.title())
#   replace_text("TODO", "DONE")

# Attribute manipulation
set_attr(name: str, value: Any) -> Operation
remove_attr(name: str) -> Operation
update_attrs(**attrs) -> Operation

# Examples:
#   set_attr("id", "introduction")
#   set_attr("class", ["warning", "important"])
```

### Content Operations

```python
# Extraction
extract() -> Operation         # Remove and return
delete() -> Operation          # Remove without returning
duplicate() -> Operation       # Clone nodes

# Insertion
prepend(nodes: list[Node]) -> Operation
append(nodes: list[Node]) -> Operation
insert_before(nodes: list[Node]) -> Operation
insert_after(nodes: list[Node]) -> Operation

# Replacement
replace_with(nodes: list[Node]) -> Operation
replace_content(nodes: list[Node]) -> Operation
```

### Query Operations

```python
# Counting
count() -> int
count_words() -> int
count_chars() -> int

# Searching
find(predicate) -> Node | None
find_all(predicate) -> list[Node]
contains(predicate) -> bool

# Statistics
stats() -> DocumentStats
word_frequency() -> dict[str, int]
reading_time(wpm: int = 200) -> timedelta
```

### Validation Operations

```python
# Structure validation
validate() -> ValidationResult
validate_heading_hierarchy() -> ValidationResult
validate_links() -> ValidationResult
validate_no_empty_sections() -> ValidationResult

# Custom validators
validate_with(validator: Validator) -> ValidationResult
```

### Composition

```python
# Function composition
compose(*operations) -> Operation
pipe(*operations) -> Operation  # Left-to-right

# Conditional
when(predicate, then_op, else_op=identity) -> Operation
unless(predicate, op) -> Operation

# Iteration
for_each(operation) -> Operation
map_nodes(f) -> Operation

# Try/catch
try_op(operation, on_error) -> Operation
```

---

## Selection System

### Path Syntax

```
Path ::= AbsolutePath | RelativePath

AbsolutePath ::= "/" Segment ("/" Segment)*
RelativePath ::= Segment ("/" Segment)*

Segment ::= Name | Name "[" Predicate "]"

Name ::= NodeType | "*" | "**"

NodeType ::= "heading" | "paragraph" | "list" | "section" | ...

Predicate ::= AttributeTest | FunctionCall | Number

AttributeTest ::= "@" Attribute Op Value
Attribute ::= "level" | "id" | "class" | "ordered" | ...
Op ::= "=" | "!=" | ">" | "<" | "contains" | "starts-with"

FunctionCall ::= Function "(" Args ")"
Function ::= "first" | "last" | "position" | "text"

Examples:
  /heading[@level=2]
  /section/heading[first()]
  //list[@ordered=true]
  /heading[@id='intro']/following-sibling::paragraph[1]
  /**[@class contains 'warning']
```

### CSS-Style Selectors

```
Selector ::= SimpleSelector (Combinator SimpleSelector)*

SimpleSelector ::= TypeSelector? IdSelector? ClassSelector* AttributeSelector* PseudoClass*

TypeSelector ::= NodeType | "*"
IdSelector ::= "#" Identifier
ClassSelector ::= "." Identifier
AttributeSelector ::= "[" Attribute (Op Value)? "]"
PseudoClass ::= ":" ("first-child" | "last-child" | "nth-child" | "empty" | ...)

Combinator ::= " " | ">" | "+" | "~"

Examples:
  heading[level=2]
  heading.important
  #introduction
  list > item:first-child
  section heading + paragraph
  .warning:not(:empty)
```

### Pattern DSL

```python
from doctk.patterns import heading, list, paragraph, section, any_node

# Pattern builders
heading(level=2, text__contains="API")
list(ordered=True, items__count__gt=3)
section(heading__level=1, children__count__lt=5)

# Combinators
any_of(heading(level=1), heading(level=2))
all_of(paragraph, has_class("warning"))
sequence(heading, paragraph, list)

# Quantifiers
one_or_more(paragraph)
zero_or_more(list)
optional(code_block)

# Example usage
doc | select(match(
    section(
        heading(level=2),
        children=one_or_more(paragraph)
    )
))
```

---

## Format Support

### Format Adapter Interface

```python
class FormatReader(ABC):
    """Read format → UDAST."""

    @abstractmethod
    def read_file(self, path: str) -> Document[Node]: ...

    @abstractmethod
    def read_string(self, content: str) -> Document[Node]: ...

    @abstractmethod
    def supports_format(self, format_hint: str) -> bool: ...

class FormatWriter(ABC):
    """Write UDAST → format."""

    @abstractmethod
    def write_file(self, doc: Document[Node], path: str) -> None: ...

    @abstractmethod
    def write_string(self, doc: Document[Node]) -> str: ...

    @abstractmethod
    def supports_format(self, format_hint: str) -> bool: ...

# Registry
class FormatRegistry:
    def register_reader(self, formats: list[str], reader: FormatReader): ...
    def register_writer(self, formats: list[str], writer: FormatWriter): ...
    def get_reader(self, format: str) -> FormatReader: ...
    def get_writer(self, format: str) -> FormatWriter: ...
```

### Markdown Support

**Extensions**:
- GFM (tables, task lists, strikethrough)
- Front matter (YAML, TOML)
- Math (LaTeX)
- Admonitions
- Definition lists
- Footnotes

**Preserves**:
- Exact whitespace in code blocks
- Link reference style
- Heading setext vs ATX style (configurable)

### reStructuredText Support

**Elements**:
- Directives (.. code-block::, .. note::, etc.)
- Roles (:ref:, :doc:, :math:, etc.)
- Explicit markup
- Tables (simple, grid, csv-table)

**Sphinx Integration**:
- Cross-references
- Autodoc directives
- Domain objects

### HTML Support

**Semantic HTML5**:
- `<article>`, `<section>`, `<header>`, `<footer>`
- `<nav>`, `<aside>`, `<figure>`
- Preserve classes and IDs

**Clean Output**:
- Minimal markup
- No inline styles (use classes)
- Accessible (ARIA attributes)

### Confluence Support

**Wiki Markup**:
- Macros ({info}, {code}, {toc})
- Tables
- Links (page links, external links)
- Attachments

**Storage Format (XHTML)**:
- Read/write Confluence storage format
- Preserve Confluence-specific metadata

---

## CLI Design

### Command Structure

```bash
doctk <command> [options] [arguments]
```

### Commands

#### outline - View document structure

```bash
doctk outline <file> [options]

Options:
  --headings-only        Show only headings (hierarchical)
  --depth N              Limit depth to N levels
  --content              Show content preview
  --format FORMAT        Force format (markdown, rst, html, confluence)
  --output FILE          Save outline to file
  --json                 Output as JSON
  --line-numbers         Show line numbers
```

#### transform - Apply transformations

```bash
doctk transform <file> <operations> [options]

Examples:
  # Promote all h3 to h2
  doctk transform doc.md "select heading | where level=3 | promote" -o out.md

  # Convert lists to ordered
  doctk transform doc.md "select list | to_ordered" -o out.md

  # Pipeline from stdin
  cat doc.md | doctk transform - "select heading | promote" > out.md

Options:
  -o, --output FILE      Output file (default: stdout)
  -i, --in-place         Modify file in place
  -f, --format FORMAT    Input format
  --to FORMAT            Output format (for conversion)
  --dry-run              Show what would be changed
  --diff                 Show diff
```

#### query - Query documents

```bash
doctk query <file> <selector> [options]

Examples:
  # Find all level-2 headings
  doctk query doc.md "heading[level=2]"

  # Find TODOs
  doctk query doc.md "//text[contains='TODO']"

  # Count code blocks by language
  doctk query doc.md "code_block" --group-by language --count

Options:
  --format FORMAT        Force format
  --output-format FMT    Output format (text, json, csv)
  --count                Count matches
  --group-by ATTR        Group results by attribute
  --extract ATTR         Extract specific attribute
```

#### validate - Validate document structure

```bash
doctk validate <file> [options]

Examples:
  # Check heading hierarchy
  doctk validate doc.md --check heading-hierarchy

  # Check all links are valid
  doctk validate doc.md --check links

  # Custom rules
  doctk validate doc.md --rules rules.yml

Options:
  --check CHECK          Specific check (heading-hierarchy, links, empty-sections)
  --rules FILE           Custom validation rules
  --strict               Fail on warnings
  --format FORMAT        Output format (text, json)
```

#### diff - Compare documents

```bash
doctk diff <file1> <file2> [options]

Options:
  --structural           Compare structure only
  --ignore-whitespace    Ignore whitespace changes
  --format FORMAT        Output format (text, json, unified, side-by-side)
```

#### split - Split document

```bash
doctk split <file> [options]

Examples:
  # Split by top-level headings
  doctk split book.md --by "heading[level=1]" --output chapters/

  # Split and name by heading text
  doctk split doc.md --by heading[level=1] --name-from heading.text

Options:
  --by SELECTOR          Split by selector
  --output DIR           Output directory
  --name-from ATTR       Name files from attribute
  --template TEMPLATE    Filename template
```

#### merge - Merge documents

```bash
doctk merge <file1> <file2> ... [options]

Options:
  -o, --output FILE      Output file
  --separator NODE       Insert separator between docs
  --toc                  Generate table of contents
```

#### stats - Document statistics

```bash
doctk stats <file> [options]

Options:
  --format FORMAT        Output format (text, json, csv)
  --verbose              Detailed statistics
```

#### tui - Interactive mode

```bash
doctk tui <file>

# Interactive terminal UI for:
# - Navigation
# - Selection
# - Transformation
# - Preview
```

### Pipeline Support

```bash
# Unix-style pipelines
doctk transform doc.md "select heading" | doctk query - "heading[level=2]"

# Process multiple files
find . -name "*.md" | xargs -I {} doctk transform {} "promote" -i

# With other tools
doctk outline doc.md --json | jq '.headings[] | select(.level == 2)'
```

---

## Python API

### Basic Usage

```python
from doctk import Document
from doctk.operations import select, where, promote, compose

# Load document
doc = Document.from_file("guide.md")

# Pipe-style transformations
result = doc | select(heading) | where(level=3) | promote()

# Save
result.to_file("guide_updated.md")
```

### Advanced Usage

```python
from doctk import Document, heading, list_node, section
from doctk.operations import (
    select, where, promote, nest,
    transform_text, replace_with, compose
)
from doctk.selection import select_path, select_css
from doctk.tools import outline, validate, stats

# Complex selection
api_sections = doc | select_path("//section[@id='api']")

# CSS-style selection
warnings = doc | select_css(".warning")

# Composition
process = compose(
    select(heading),
    where(level=3),
    promote(),
    transform_text(str.upper)
)
result = process(doc)

# Validation
validation = validate(doc, rules=["heading-hierarchy", "no-empty-sections"])
if not validation.is_valid:
    for error in validation.errors:
        print(f"{error.location}: {error.message}")

# Statistics
doc_stats = stats(doc)
print(f"Words: {doc_stats.word_count}")
print(f"Reading time: {doc_stats.reading_time}")
print(f"Headings: {doc_stats.heading_count}")
```

### Context Manager Support

```python
# Auto-save on exit
with Document.from_file("doc.md") as doc:
    doc | select(heading) | where(level=3) | promote()
    # Automatically saved to doc.md

# Explicit output
with Document.from_file("doc.md", output="output.md") as doc:
    doc | select(heading) | promote()
```

### Fluent API

```python
# Alternative to pipe operator
doc.select(heading)\
   .where(level=3)\
   .promote()\
   .save("output.md")
```

### Builder Pattern

```python
from doctk import DocumentBuilder

# Programmatically build documents
doc = DocumentBuilder()\
    .heading(1, "My Document")\
    .paragraph("Introduction text")\
    .heading(2, "Getting Started")\
    .list(ordered=True)\
        .item("Step 1")\
        .item("Step 2")\
        .item("Step 3")\
    .code_block("python", "print('hello')")\
    .build()
```

---

## Type System

### Type Annotations

```python
from typing import TypeVar, Generic, Protocol

T = TypeVar('T', bound=Node)
U = TypeVar('U', bound=Node)

# Operation type
Operation = Callable[[Document[T]], Document[U]]

# Predicate type
Predicate = Callable[[T], bool]

# Transformer type
Transformer = Callable[[T], U]

# Example typed operations
def select(predicate: Predicate[T]) -> Operation[T, T]: ...
def map_nodes(transformer: Transformer[T, U]) -> Operation[T, U]: ...
def filter_nodes(predicate: Predicate[T]) -> Operation[T, T]: ...
```

### Type Guards

```python
def is_heading(node: Node) -> TypeGuard[Heading]: ...
def is_paragraph(node: Node) -> TypeGuard[Paragraph]: ...
def is_list(node: Node) -> TypeGuard[List]: ...

# Usage with type narrowing
for node in doc:
    if is_heading(node):
        # node is Heading here
        print(f"Level {node.level}: {node.text}")
```

### Protocol Types

```python
class Wrappable(Protocol):
    """Nodes that can be wrapped."""
    def wrap(self, wrapper: Node) -> Node: ...

class Nestable(Protocol):
    """Nodes that support nesting."""
    def nest(self, child: Node) -> None: ...
    def unnest(self) -> list[Node]: ...
```

---

## Error Handling

### Error Types

```python
class DoctkError(Exception):
    """Base exception."""
    pass

class ParseError(DoctkError):
    """Failed to parse document."""
    location: Location
    message: str

class ValidationError(DoctkError):
    """Document structure invalid."""
    violations: list[Violation]

class SelectionError(DoctkError):
    """Invalid selector."""
    selector: str
    message: str

class TransformError(DoctkError):
    """Transformation failed."""
    operation: str
    node: Node
    message: str

class FormatError(DoctkError):
    """Unsupported format."""
    format: str
```

### Error Handling Strategy

```python
# Result type for operations that may fail
@dataclass
class Result(Generic[T]):
    value: T | None
    error: DoctkError | None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    def unwrap(self) -> T:
        if self.error:
            raise self.error
        return self.value

# Usage
result = try_transform(doc, operation)
if result.is_ok:
    print(f"Success: {result.value}")
else:
    print(f"Error: {result.error}")
```

### Validation Results

```python
@dataclass
class Violation:
    """Single validation violation."""
    severity: Severity  # ERROR, WARNING, INFO
    location: Location
    rule: str
    message: str

@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    violations: list[Violation]

    def errors(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == Severity.ERROR]

    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == Severity.WARNING]
```

---

## Performance

### Optimization Strategies

1. **Lazy Evaluation**
   - Defer operations until result needed
   - Stream processing for large documents

2. **Structural Sharing**
   - Reuse unchanged subtrees
   - Copy-on-write for modifications

3. **Parallel Processing**
   - Process independent files concurrently
   - Parallel tree traversal

4. **Caching**
   - Cache parsed documents
   - Memoize expensive operations

### Benchmarks (Target)

```
Operation              | Small (10KB) | Medium (100KB) | Large (1MB)
-----------------------|--------------|----------------|------------
Parse Markdown         | < 10ms       | < 50ms         | < 200ms
Simple transform       | < 5ms        | < 20ms         | < 100ms
Complex selection      | < 15ms       | < 50ms         | < 200ms
Write Markdown         | < 10ms       | < 40ms         | < 150ms
Full round-trip        | < 25ms       | < 100ms        | < 500ms
```

### Memory Usage

- Small documents (< 100KB): < 10MB
- Medium documents (100KB - 1MB): < 50MB
- Large documents (> 1MB): Linear growth, streaming support

---

## Extension Points

### Custom Operations

```python
from doctk.operations import register_operation

@register_operation("my_transform")
def my_custom_transform(config: dict) -> Operation:
    def transform(doc: Document) -> Document:
        # Custom logic
        return doc
    return transform

# Usage
doc | my_transform(config={"param": "value"})
```

### Custom Validators

```python
from doctk.tools.validator import Validator

class MyValidator(Validator):
    def validate(self, doc: Document) -> ValidationResult:
        violations = []
        # Validation logic
        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations
        )
```

### Custom Formats

```python
from doctk.formats import FormatReader, FormatWriter, register_format

class MyFormatReader(FormatReader):
    def read_string(self, content: str) -> Document[Node]:
        # Parse custom format
        pass

class MyFormatWriter(FormatWriter):
    def write_string(self, doc: Document[Node]) -> str:
        # Write custom format
        pass

# Register
register_format("myformat", MyFormatReader(), MyFormatWriter())
```

### Plugins

```python
# Plugin interface
class Plugin(Protocol):
    def activate(self, registry: Registry) -> None: ...
    def deactivate(self) -> None: ...

# Load plugins
from doctk.plugins import load_plugin

load_plugin("doctk_mermaid")  # Adds mermaid diagram support
load_plugin("doctk_latex")    # Adds LaTeX support
```

---

## Implementation Phases

### Phase 1: Core Enhancement (v0.2) - NEXT
**Goal**: Robust core with complete operation set

- [ ] Enhanced node hierarchy (Section, Table, Inline nodes)
- [ ] Location tracking for all nodes
- [ ] Complete structure operations (lift, lower, nest, unnest)
- [ ] Tree traversal utilities (depth_first, breadth_first)
- [ ] Error handling infrastructure
- [ ] Comprehensive test suite (>80% coverage)

**Deliverables**:
- All node types implemented
- All basic operations working
- Location tracking for error reporting
- Test coverage report

### Phase 2: Selection System (v0.3)
**Goal**: Powerful, expressive selection capabilities

- [ ] Path-based selection with full syntax
- [ ] CSS-style selectors
- [ ] XPath-like queries
- [ ] Pattern matching DSL
- [ ] Relational selection (parent, children, siblings)
- [ ] Performance optimization (indexing)

**Deliverables**:
- Selection system documentation
- Example gallery
- Performance benchmarks

### Phase 3: Format Support (v0.4)
**Goal**: Multi-format support with high fidelity

- [ ] Enhanced Markdown support (GFM, extensions)
- [ ] reStructuredText reader/writer
- [ ] HTML reader/writer
- [ ] Format conversion pipeline
- [ ] Format detection heuristics
- [ ] Round-trip tests for all formats

**Deliverables**:
- 4 formats fully supported
- Format conversion guide
- Compatibility matrix

### Phase 4: Advanced Tools (v0.5)
**Goal**: Rich ecosystem of document tools

- [ ] Document differ
- [ ] Structure validator with rules engine
- [ ] Statistics and analytics
- [ ] Template system
- [ ] Document splitter/merger
- [ ] Link checker

**Deliverables**:
- Tool documentation
- Example rules/templates
- CLI guides

### Phase 5: CLI & TUI (v0.6)
**Goal**: Excellent command-line experience

- [ ] Complete CLI command suite
- [ ] Pipeline support
- [ ] Interactive TUI (textual/rich)
- [ ] Shell completion
- [ ] Man pages
- [ ] Usage examples

**Deliverables**:
- CLI reference manual
- TUI user guide
- Screencast tutorials

### Phase 6: LSP & Editor Integration (v0.7)
**Goal**: First-class IDE support

- [ ] Language Server Protocol implementation
- [ ] VSCode extension
- [ ] Syntax highlighting
- [ ] Completions (context-aware)
- [ ] Hover documentation
- [ ] Go-to-definition
- [ ] Refactoring actions

**Deliverables**:
- LSP server
- VSCode extension published
- LSP developer guide

### Phase 7: Performance & Scale (v0.8)
**Goal**: Handle large documents efficiently

- [ ] Lazy evaluation implementation
- [ ] Streaming API
- [ ] Parallel processing
- [ ] Caching layer
- [ ] Benchmarking suite
- [ ] Performance guide

**Deliverables**:
- Performance benchmarks
- Optimization guide
- Large doc examples

### Phase 8: Confluence Support (v0.9)
**Goal**: Enterprise wiki integration

- [ ] Confluence reader (storage format)
- [ ] Confluence writer
- [ ] Macro support
- [ ] REST API client
- [ ] Bulk operations
- [ ] Migration tools

**Deliverables**:
- Confluence guide
- Migration scripts
- Enterprise examples

### Phase 9: Extensibility & Plugins (v0.10)
**Goal**: Rich plugin ecosystem

- [ ] Plugin system architecture
- [ ] Plugin API
- [ ] Plugin manager
- [ ] Example plugins
- [ ] Plugin registry
- [ ] Developer documentation

**Deliverables**:
- Plugin development guide
- Example plugin repository
- Plugin registry

### Phase 10: v1.0 Release
**Goal**: Production-ready, stable API

- [ ] API freeze
- [ ] Complete documentation
- [ ] Migration guide (0.x → 1.0)
- [ ] Stability guarantees
- [ ] Long-term support plan

**Deliverables**:
- v1.0 release
- Complete documentation site
- Tutorial series
- Case studies

---

## Success Metrics

### Technical Metrics
- **Test Coverage**: > 80%
- **Performance**: Meet benchmark targets
- **API Stability**: Semantic versioning, deprecation policy
- **Documentation**: All public APIs documented

### User Metrics
- **Adoption**: Downloads, GitHub stars
- **Engagement**: Issues, PRs, discussions
- **Satisfaction**: User feedback, surveys
- **Use Cases**: Real-world applications

---

## Appendices

### A. Glossary

- **UDAST**: Universal Document AST
- **Morphism**: Structure-preserving transformation
- **Functor**: Type that can be mapped over
- **Monad**: Type that supports chaining operations
- **LSP**: Language Server Protocol
- **TUI**: Terminal User Interface

### B. References

- **Category Theory**: Bartosz Milewski's "Category Theory for Programmers"
- **Pandoc**: Universal document converter
- **unified**: JavaScript content transformation ecosystem
- **Tree-sitter**: Incremental parsing library

### C. FAQ

**Q: Why not just use Pandoc?**
A: Pandoc is excellent for conversion but lacks programmable manipulation. doctk is designed for transformation, refactoring, and analysis.

**Q: Why Python instead of Rust?**
A: Python for rapid prototyping and ecosystem. Rust port possible for performance-critical parts.

**Q: How is this different from BeautifulSoup for HTML?**
A: doctk is format-agnostic with semantic understanding of document structure, not just HTML.

**Q: Can I use this in production?**
A: v0.x is experimental. v1.0 will be production-ready with stability guarantees.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-07
**Next Review**: 2025-11-14
