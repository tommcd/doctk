# doctk - Document Toolkit

A composable, functional toolkit for structured document manipulation.

## Philosophy

Inspired by category theory, set theory, and the Zen of Python, `doctk` provides elegant primitives for document transformation:

- **Composable**: Complex operations built from simple primitives
- **Pure**: Operations transform rather than mutate
- **Format-agnostic**: Operates on universal document AST
- **Type-safe**: Well-typed transformations
- **Pipeable**: Unix-philosophy pipelines for documents

## Quick Start

```bash
# Install
pip install -e .

# View document outline
doctk read guide.md | outline

# Promote all level-3 headings to level-2
doctk read doc.md | select heading | where level=3 | map promote | write

# Extract a section
doctk read docs.md | select path="/API Reference" | write api.md
```

## Python API

```python
from doctk import Document
from doctk.operations import select, where, promote

# Load document
doc = Document.from_file("guide.md")

# Pipe-style transformations
result = doc | select(heading) | where(level=3) | promote()

# Or fluent API
result = doc.select(heading).where(level=3).promote()

# Save
result.to_file("guide_updated.md")
```

## Core Concepts

### Documents as Functors

Documents are containers that can be mapped over:

```python
doc.map(transform_fn)  # Apply to each node
doc.filter(predicate)  # Subset selection
doc.reduce(fold_fn, init)  # Fold operation
```

### Operations as Morphisms

Operations are composable transformations:

```python
from doctk.operations import compose

process = compose(
    select(heading),
    where(level=3),
    promote()
)

result = process(doc)
```

### Set Operations

Documents support set algebra:

```python
doc1.union(doc2)      # Combine
doc1.intersect(doc2)  # Common elements
doc1.diff(doc2)       # Unique to doc1
```

## Status

**Alpha**: Core architecture and outliner functionality implemented.

## License

MIT
