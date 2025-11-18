# doctk Initial Design

**Date**: 2025-11-07
**Status**: Design Phase → POC Implementation

## Vision

A composable, functional toolkit for structured document manipulation inspired by:

- **Category Theory**: Operations as morphisms, composition as fundamental
- **Set Theory**: Documents as sets with algebraic operations
- **The Zen of Python**: Beautiful, explicit, simple, readable

## Problem Statement

Existing tools (Pandoc, unified/remark) provide AST manipulation but lack:

- User-friendly DSL for structural operations (outlining, moving sections, type transforms)
- Composable primitives following functional programming principles
- Format-agnostic abstraction layer
- Interactive workflows for document refactoring

## Design Principles

### 1. Mathematical Foundations

**Category Theory Concepts**:

- **Objects**: Documents, Sections, Elements (nodes in AST)
- **Morphisms**: Transformations between documents/elements
- **Composition**: `f ∘ g` - operations compose naturally
- **Functors**: Map between categories (format conversions)
- **Identity**: Operations that preserve structure

**Set Theory Operations**:

- Union, Intersection, Difference for document manipulation
- Filter as subset selection
- Power set for exploring document structures

### 2. The Zen of Python Applied

```
Beautiful is better than ugly          → Clean, readable syntax
Explicit is better than implicit       → Clear operation names
Simple is better than complex          → Primitive operations compose
Flat is better than nested             → Pipeline over deep nesting
Sparse is better than dense            → One operation per step
Readability counts                     → Self-documenting commands
There should be one obvious way        → Canonical patterns
```

## Core Abstractions

### Document as Monad/Functor

```python
class Document(Generic[T]):
    """A document is a container - forms a Monad"""

    # Functor
    def map(self, f: Callable[[T], U]) -> Document[U]:
        """Apply transformation to each node"""

    # Monad
    def flatmap(self, f: Callable[[T], Document[U]]) -> Document[U]:
        """Map and flatten"""

    def filter(self, predicate: Callable[[T], bool]) -> Document[T]:
        """Filter by predicate - subset selection"""

    def reduce(self, f: Callable[[U, T], U], initial: U) -> U:
        """Fold operation"""

    # Pipe operator support
    def __or__(self, operation) -> Document[U]:
        """Enable pipeline syntax: doc | operation"""

    # Set operations
    def union(self, other: Document[T]) -> Document[T]
    def intersect(self, other: Document[T]) -> Document[T]
    def diff(self, other: Document[T]) -> Document[T]
```

### Operations as Pure Functions (Morphisms)

```python
# Higher-order functions returning transformations
def select(predicate) -> Callable[[Document], Document]
def where(**conditions) -> Callable[[Document], Document]
def map(transform) -> Callable[[Document], Document]
def promote() -> Callable[[Document], Document]
def demote() -> Callable[[Document], Document]

# Function composition
def compose(*operations):
    """Compose operations right-to-left (mathematical composition)"""
```

## Primitive Operations

### Core Primitives (Morphisms)

**Identity**: Returns document unchanged

```python
identity()
```

**Selectors** (Filters - like set membership):

```python
select(predicate)      # Select elements matching predicate
where(condition)       # Alias for functional style
first()                # Take first element
last()                 # Take last element
nth(n)                 # Take nth element
slice(start, end)      # Range selection
```

**Projections** (Extract properties):

```python
content()              # Extract text content
metadata()             # Extract metadata/attributes
children()             # Get children nodes
parent()               # Get parent node
siblings()             # Get siblings
path()                 # Get document path/location
```

**Transformations** (Endofunctors - Type → Type):

```python
map(f)                 # Apply function to each element
filter(p)              # Keep elements matching predicate
reduce(f, init)        # Fold operation
flatmap(f)             # Map then flatten
```

**Structural Operations** (Morphisms on structure):

```python
promote()              # Increase level (h3 → h2)
demote()               # Decrease level (h2 → h3)
lift()                 # Move up in sibling order
lower()                # Move down in sibling order
nest()                 # Make sibling a child
unnest()               # Make child a sibling
```

**Set Operations**:

```python
union(other)           # Combine documents
intersect(other)       # Common elements
diff(other)            # Difference
concat(other)          # Sequential composition
```

**Type Transforms**:

```python
to_ordered()           # Convert list to ordered
to_unordered()         # Convert list to unordered
to_heading(level)      # Convert to heading
to_blockquote()        # Convert to blockquote
```

## Syntax Design

### Python API - Pipe Operator

**Chosen for LSP support**: Linear flow enables type-aware completions

```python
# Pipe operator (Python 3.10+ with __or__ overload)
doc | select(heading) | where(level=2) | promote()

# Also supports fluent API (both work!)
doc.select(heading).where(level=2).promote()

# Pure function composition
process = compose(
    select(heading),
    where(level=2),
    promote()
)
result = process(doc)
```

### CLI - Unix Philosophy Pipes

```bash
# Each command is a pure function
doctk read file.md | select heading | where 'level == 2' | promote | write

# Elegant examples
doctk read doc.md | select heading | where 'level == 3' | map promote | write
doctk read docs.md | select 'path == "/API"' | children | write api.md
doctk read doc.md | select list | flatmap unnest | write
```

### LSP Support Benefits

1. **Type-aware completions** - After `|`, LSP suggests valid operations for current document state
1. **Parameter hints** - Shows expected arguments with types
1. **Hover documentation** - Inline help for each operation
1. **Real-time validation** - Catch type errors before execution
1. **Go-to-definition** - Jump to operation implementations

## Example Use Cases

### Outliner Operations

```python
# View document structure
doc | outline()

# Navigate and transform
doc | select(path="/Introduction") | children() | promote()
```

### Structural Transforms

```python
# Promote all h3 to h2
doc | select(heading) | where(level=3) | map(promote)

# Reorder sections
doc | select(path="/Advanced") | lift() | lift()

# Flatten nested lists
doc | select(list) | flatmap(unnest)
```

### Query Operations

```python
# Find all TODOs
doc | select(text) | where(contains("TODO"))

# Extract API section
doc | select(path="/API Reference") | extract()

# Diff documents structurally
doc1 | diff(doc2) | where(is_structural_change)
```

### Batch Operations

```python
# Convert all lists to ordered
doc | select(list) | map(to_ordered)

# Normalize heading hierarchy
doc | select(heading) | reduce(normalize_levels)

# Generate table of contents
doc | select(heading) | map(to_link) | reduce(to_list)
```

## Architecture

```
┌─────────────────────────────────────┐
│   Interfaces (CLI, API, plugins)    │
├─────────────────────────────────────┤
│   DSL Parser & Operation Pipeline   │
├─────────────────────────────────────┤
│   Universal Document AST (UDAST)    │
├─────────────────────────────────────┤
│   Format Adapters                   │
│   (Markdown, RST, Confluence, HTML) │
└─────────────────────────────────────┘
```

### Technology Stack

**Language**: Python (for POC; Rust if performance needed later)

**Core Libraries**:

- `markdown-it-py` - Markdown parser (produces tokens/AST)
- `mdit-py-plugins` - Extended Markdown features
- `rich` - Beautiful CLI output
- `click` - CLI framework (if needed)

**AST Strategy**:

- Build adapters to/from existing standards (mdast, Pandoc AST)
- Define simplified UDAST (Universal Document AST) for operations
- Format-specific readers/writers

## MVP Roadmap

### Phase 1: Core Infrastructure (Current)

- [x] Project setup with uv, ruff
- [x] Git configuration for personal projects
- [ ] Core abstractions: Document, Node, Operation
- [ ] Basic Markdown parser/adapter

### Phase 2: Outliner (First Feature)

- [ ] Document structure visualization
- [ ] Heading hierarchy display
- [ ] Section navigation
- [ ] Rich CLI output

### Phase 3: Basic Structure Operations

- [ ] promote/demote (heading levels)
- [ ] lift/lower (sibling order)
- [ ] nest/unnest (hierarchy changes)
- [ ] Basic selection (by type, by path)

### Phase 4: Query System

- [ ] `select(predicate)` implementation
- [ ] `where(**conditions)` builder
- [ ] Path-based selection
- [ ] CSS-like selectors

### Phase 5: Transform System

- [ ] `map(transform)` implementation
- [ ] Type conversions (list, heading, etc.)
- [ ] Content operations (extract, delete, duplicate)
- [ ] Composition utilities

### Future Phases

- Full format support (RST, HTML, Confluence)
- Interactive TUI mode
- VSCode extension
- Language Server Protocol implementation
- Advanced operations (split, merge, templates)

## Composition Laws

Following category theory, operations must satisfy:

**Associativity**: `(f ∘ g) ∘ h = f ∘ (g ∘ h)`

```python
doc | select(heading) | filter(level2) | promote()
```

**Identity**: `f ∘ id = id ∘ f = f`

```python
doc | identity() | select(heading)  # Same as: doc | select(heading)
```

**Functoriality**: `map(f ∘ g) = map(f) ∘ map(g)`

```python
doc | map(promote . capitalize)  # Same as: doc | map(promote) | map(capitalize)
```

## Design Decisions

### 1. Pipe Operator vs Method Chaining

**Decision**: Support both, with pipe operator as primary

**Rationale**:

- Pipe operator better for LSP (linear type inference)
- Method chaining familiar to Python developers
- CLI uses pipe (Unix philosophy)
- Both have same mental model

### 2. Python First, Rust Later

**Decision**: Build POC in Python, port to Rust if needed

**Rationale**:

- Faster prototyping to validate design
- Rich ecosystem for parsers and CLI
- Can use Rust for performance-critical parts later
- Many users comfortable with Python

### 3. Format Adapters vs Universal Parser

**Decision**: Build format-specific adapters to/from UDAST

**Rationale**:

- Leverage existing mature parsers
- Each format has quirks better handled by specialists
- UDAST can be simpler, operation-friendly
- Easier to add new formats incrementally

### 4. MVP Focus: Outliner + Structure Ops

**Decision**: Start with outliner and basic structural operations

**Rationale**:

- Immediately useful standalone feature
- Validates core abstractions
- Simpler than full query/transform system
- Can iterate based on user feedback

## Open Questions

1. **Selector Syntax**: CSS-like, XPath-like, or custom?
1. **UDAST Design**: How minimal can we make it while being universal?
1. **Lazy Evaluation**: Should operations be lazy or eager?
1. **Immutability**: Pure functional (all copies) or pragmatic (some mutation)?
1. **Error Handling**: Exceptions, Result types, or silent failures?

## References

- **Pandoc**: https://pandoc.org/filters.html
- **unified/remark/rehype**: https://unifiedjs.com/
- **mdast spec**: https://github.com/syntax-tree/mdast
- **Category Theory for Programmers**: https://bartoszmilewski.com/
- **The Zen of Python**: PEP 20

______________________________________________________________________

**Next Steps**: Implement core abstractions and Markdown adapter
