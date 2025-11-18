# Quick Start

This guide will walk you through the basics of using doctk to manipulate documents.

## Your First Document

Let's start by creating a simple Markdown document and loading it with doctk.

Create a file called `example.md`:

```markdown
# My Document

## Introduction

This is a sample document.

## Chapter 1

### Section 1.1

Content for section 1.1.

### Section 1.2

Content for section 1.2.

## Chapter 2

More content here.
```

## Using the CLI

### View Document Outline

The simplest way to explore a document is with the `outline` command:

```bash
doctk outline example.md
```

This displays the document structure as a tree:

```
My Document
├── Introduction
├── Chapter 1
│   ├── Section 1.1
│   └── Section 1.2
└── Chapter 2
```

To see only headings:

```bash
doctk outline example.md --headings-only
```

### Interactive Demo

Try the interactive demo to see doctk in action:

```bash
doctk demo
```

This runs through several examples showing different operations.

## Using the Python API

### Loading Documents

```python
from doctk import Document

# Load from file
doc = Document.from_file("example.md")

# Load from string
markdown_text = "# Hello\n\nWorld"
doc = Document.from_markdown(markdown_text)
```

### Selecting Nodes

Use the `select` operation to filter nodes:

```python
from doctk.operations import select, heading

# Select all heading nodes
headings = doc | select(heading)

# Print heading text
for node in headings.nodes:
    print(node.content)
```

### Filtering with Predicates

Use `where` to filter based on conditions:

```python
from doctk.operations import select, where, heading

# Select level 2 headings
h2_headings = doc | select(heading) | where(level=2)

# Select level 3 headings
h3_headings = doc | select(heading) | where(level=3)
```

### Transforming Documents

Use operations like `promote` and `demote` to change heading levels:

```python
from doctk.operations import select, where, promote, heading

# Promote all level 3 headings to level 2
result = doc | select(heading) | where(level=3) | promote()

# Save the result
result.to_file("example_modified.md")
```

### Chaining Operations

Operations can be chained together:

```python
from doctk.operations import select, where, promote, heading

# Select level 3 headings and promote them
result = (
    doc
    | select(heading)
    | where(level=3)
    | promote()
)
```

## Common Patterns

### Extract All Headings

```python
from doctk.operations import select, heading

headings = doc | select(heading)
for node in headings.nodes:
    print(f"Level {node.level}: {node.content}")
```

### Restructure Document

```python
from doctk.operations import select, where, promote, demote, heading

# Promote all subsections to main sections
result = (
    doc
    | select(heading)
    | where(level=3)
    | promote()
)
```

### Filter by Content

```python
from doctk.operations import select, heading

# Select headings containing specific text
def contains_chapter(node):
    return "Chapter" in node.content

headings = doc | select(heading)
chapters = [n for n in headings.nodes if contains_chapter(n)]
```

## Next Steps

Now that you understand the basics, explore:

- **[Development Setup](../development/setup.md)**: Set up your development environment
- **[Testing Guide](../development/testing.md)**: Learn about the test structure
