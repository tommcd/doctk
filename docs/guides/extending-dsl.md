# Guide: Extending the doctk DSL

**Audience**: Developers adding new operations to the DSL
**Prerequisites**: Familiarity with Python, ASTs, and doctk core concepts
**Estimated Time**: 1-2 hours for a new operation

---

## Overview

This guide explains how to add new operations to the doctk Domain-Specific Language (DSL). The DSL provides a pipeline-based syntax for document manipulation that can be used in:

- REPL (interactive terminal)
- Script files (`.tk` files)
- Code blocks in Markdown documents

### What You'll Learn

- How to add a new operation to the DSL
- How to update the lexer, parser, and executor
- How to test your new operation
- Best practices for DSL extension

---

## Understanding the DSL Pipeline

### DSL Flow

```
Source Code
    ↓
Lexer (lexer.py) → Tokens
    ↓
Parser (parser.py) → AST
    ↓
Executor (executor.py) → Result
```

### Example DSL Code

```doctk
doc | promote h2-0 | demote h3-1
```

**Tokens:**
```
DOC, PIPE, IDENTIFIER(promote), IDENTIFIER(h2-0), PIPE, IDENTIFIER(demote), IDENTIFIER(h3-1)
```

**AST:**
```python
Pipeline(
    source="doc",
    operations=[
        FunctionCall(name="promote", arguments=["h2-0"]),
        FunctionCall(name="demote", arguments=["h3-1"])
    ]
)
```

**Execution:** Each operation is executed sequentially, transforming the document.

---

## Step 1: Design Your Operation

### Questions to Ask

1. **What does it do?** - Clear purpose (e.g., "Delete all empty sections")
2. **What are the inputs?** - Parameters needed (e.g., node_id, level, count)
3. **Does it already exist?** - Check `StructureOperations` in `integration/operations.py`
4. **Is it a core operation?** - Should it be added to core first?

### Operation Categories

**Structure Operations** (modify headings/sections):
- promote, demote, nest, unnest, move_up, move_down

**Content Operations** (modify content):
- delete, rename, merge, split

**Query Operations** (select/filter):
- select, where, find

**Meta Operations** (control flow):
- if, for, let

---

## Step 2: Implement in Core Integration Layer

Before adding to DSL, implement the operation in `StructureOperations`.

### Add to `integration/operations.py`

```python
class StructureOperations:
    # ... existing operations ...

    @staticmethod
    def rename(document: Document[Node], node_id: str, new_text: str) -> OperationResult:
        """
        Rename a heading (change its text).

        Args:
            document: The document to operate on
            node_id: The ID of the heading to rename
            new_text: The new text for the heading

        Returns:
            Operation result
        """
        tree_builder = DocumentTreeBuilder(document)
        node = tree_builder.find_node(node_id)

        if node is None:
            return OperationResult(success=False, error=f"Node not found: {node_id}")

        if not isinstance(node, Heading):
            return OperationResult(success=False, error=f"Node {node_id} is not a heading")

        # Get node index
        node_index = tree_builder.get_node_index(node_id)
        if node_index is None:
            return OperationResult(success=False, error=f"Could not find index for node: {node_id}")

        # Create new node with updated text
        renamed_node = Heading(
            level=node.level,
            text=new_text,
            children=node.children,
            metadata=node.metadata
        )

        # Create new document
        new_nodes = list(document.nodes)
        new_nodes[node_index] = renamed_node
        new_document = Document(new_nodes)

        # Compute modified ranges
        modified_ranges = DiffComputer.compute_ranges(
            original_doc=document,
            modified_doc=new_document,
            affected_node_ids=[node_id],
        )

        return OperationResult(
            success=True,
            document=new_document.to_string(),
            modified_ranges=modified_ranges,
        )
```

### Test the Core Operation

```python
# tests/unit/test_structure_operations.py

def test_rename_heading():
    """Test renaming a heading."""
    doc_text = "# Title\n\n## Old Name\n"
    doc = Document.from_string(doc_text)

    result = StructureOperations.rename(doc, "h2-0", "New Name")

    assert result.success
    assert "## New Name" in result.document
    assert "## Old Name" not in result.document
```

---

## Step 3: Add Token Type (if needed)

### When to Add a New Token

Only if introducing new syntax (keywords, operators, literals).

**Example:** Adding a `merge` keyword

```python
# src/doctk/dsl/lexer.py

class TokenType(Enum):
    # ... existing types ...
    MERGE = auto()  # NEW: 'merge' keyword
```

### Update Keyword Map

```python
# src/doctk/dsl/lexer.py

class Lexer:
    KEYWORDS = {
        'doc': TokenType.DOC,
        'let': TokenType.LET,
        'merge': TokenType.MERGE,  # NEW
    }
```

**Note:** Most operations don't need new tokens - they're just function names (IDENTIFIER).

---

## Step 4: Update Parser (if needed)

### When to Update Parser

Only if introducing new syntax structures (not just new operations).

**For most operations:** No parser changes needed! Operations are function calls.

### Example: If Adding Special Syntax

```python
# If you add special syntax like: doc | rename h2-0 to "New Name"
# Then you'd need parser changes:

def parse_rename_operation(self):
    """Parse: rename <node_id> to <new_text>"""
    self.expect(TokenType.IDENTIFIER)  # "rename"
    node_id = self.expect(TokenType.IDENTIFIER).value
    self.expect(TokenType.IDENTIFIER)  # "to"
    new_text = self.expect(TokenType.STRING).value
    return FunctionCall(name="rename", arguments=[node_id, new_text])
```

**Recommendation:** Stick with standard function call syntax for simplicity.

---

## Step 5: Add Executor Handler

This is the key step! Add your operation to the executor's dispatch table.

### Update `dsl/executor.py`

```python
class Executor:
    def __init__(self, document: Document[Any]):
        self.document = document
        self.variables: dict[str, Document[Any]] = {"doc": document}
        self.operations = StructureOperations()

        # Dispatch table: operation_name -> (handler_method, arg_count)
        self._operation_dispatch: dict[str, tuple[Callable[..., Document[Any]], int]] = {
            "promote": (self._exec_promote, 1),
            "demote": (self._exec_demote, 1),
            "move_up": (self._exec_move_up, 1),
            "move_down": (self._exec_move_down, 1),
            "nest": (self._exec_nest, 2),
            "unnest": (self._exec_unnest, 1),
            "rename": (self._exec_rename, 2),  # NEW: 2 arguments
        }

    # ... existing handlers ...

    def _exec_rename(self, node_id: str, new_text: str) -> Document[Any]:
        """Execute rename operation."""
        result = self.operations.rename(self.document, node_id, new_text)

        if not result.success:
            raise ExecutionError(result.error or "Rename operation failed")

        return Document.from_string(result.document)
```

### Handler Pattern

```python
def _exec_<operation_name>(self, arg1, arg2, ...) -> Document[Any]:
    """
    Execute <operation_name> operation.

    This method:
    1. Calls the corresponding StructureOperations method
    2. Checks for success
    3. Returns the resulting Document
    4. Raises ExecutionError on failure
    """
    result = self.operations.<operation_name>(self.document, arg1, arg2, ...)

    if not result.success:
        raise ExecutionError(result.error or "Operation failed")

    return Document.from_string(result.document)
```

---

## Step 6: Test Your DSL Operation

### Unit Tests

```python
# tests/unit/test_dsl_executor.py

def test_execute_rename_operation():
    """Test executing rename operation via DSL."""
    doc_text = "# Title\n\n## Old Name\n"
    doc = Document.from_string(doc_text)

    # Parse DSL
    lexer = Lexer('doc | rename h2-0 "New Name"')
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Execute
    executor = Executor(doc)
    result = executor.execute(ast)

    # Verify
    result_text = result.to_string()
    assert "## New Name" in result_text
    assert "## Old Name" not in result_text
```

### REPL Integration Test

```python
# tests/unit/test_repl.py

def test_repl_rename_command(sample_document):
    """Test rename command in REPL."""
    repl = DoctkREPL()
    repl.document = sample_document
    repl.current_doc_path = "test.md"

    # Execute command
    repl._execute_command('rename h2-0 "Updated Title"')

    # Verify
    assert repl.document is not None
    assert "Updated Title" in repl.document.to_string()
```

### E2E Script Test

```python
# tests/e2e/test_script_execution.py

def test_execute_script_with_rename(sample_document, tmp_path):
    """Test executing script with rename operation."""
    # Create script
    script_path = tmp_path / "rename.tk"
    script_path.write_text('doc | rename h2-0 "New Title"')

    # Execute
    result = ScriptExecutor.execute_file(script_path, sample_document)

    # Verify
    assert "New Title" in result.to_string()
```

---

## Step 7: Update Documentation

### Update DSL API Reference

Add your operation to `docs/api/dsl.md`:

```markdown
| Operation | Syntax | Description |
|-----------|--------|-------------|
| ... | ... | ... |
| `rename` | `rename <node_id> <new_text>` | Change heading text |
```

### Update Operation Table

```markdown
### Operations

| Operation | Syntax | Description |
|-----------|--------|-------------|
| `rename` | `rename <node_id> "text"` | Rename a heading |
```

### Add Usage Example

```markdown
### Renaming Headings

```doctk
# Rename a single heading
doc | rename h2-0 "New Title"

# Rename multiple headings
doc | rename h2-0 "First" | rename h2-1 "Second"
```
```

---

## Complete Example: Adding a `merge` Operation

Here's a complete example of adding a new operation that merges two sections.

### 1. Implement in Core

```python
# src/doctk/integration/operations.py

@staticmethod
def merge(document: Document[Node], node_id1: str, node_id2: str) -> OperationResult:
    """
    Merge two sections together.

    Args:
        document: The document to operate on
        node_id1: ID of first section
        node_id2: ID of second section (will be merged into first)

    Returns:
        Operation result
    """
    tree_builder = DocumentTreeBuilder(document)

    # Find both sections
    section1 = tree_builder.get_section_range(node_id1)
    section2 = tree_builder.get_section_range(node_id2)

    if section1 is None:
        return OperationResult(success=False, error=f"Section not found: {node_id1}")
    if section2 is None:
        return OperationResult(success=False, error=f"Section not found: {node_id2}")

    # Extract sections
    start1, end1 = section1
    start2, end2 = section2

    # Build new document
    new_nodes = []
    new_nodes.extend(document.nodes[:start1])  # Before first section
    new_nodes.extend(document.nodes[start1:end1+1])  # First section
    new_nodes.extend(document.nodes[end1+1:start2])  # Between sections (IMPORTANT!)
    new_nodes.extend(document.nodes[start2+1:end2+1])  # Second section content (skip heading)
    new_nodes.extend(document.nodes[end2+1:])  # After second section

    new_document = Document(new_nodes)

    # Compute modified ranges
    modified_ranges = DiffComputer.compute_ranges(
        original_doc=document,
        modified_doc=new_document,
        affected_node_ids=[node_id1, node_id2],
    )

    return OperationResult(
        success=True,
        document=new_document.to_string(),
        modified_ranges=modified_ranges,
    )
```

### 2. Add to Executor

```python
# src/doctk/dsl/executor.py

class Executor:
    def __init__(self, document: Document[Any]):
        # ...
        self._operation_dispatch = {
            # ... existing operations ...
            "merge": (self._exec_merge, 2),  # NEW
        }

    def _exec_merge(self, node_id1: str, node_id2: str) -> Document[Any]:
        """Execute merge operation."""
        result = self.operations.merge(self.document, node_id1, node_id2)

        if not result.success:
            raise ExecutionError(result.error or "Merge operation failed")

        return Document.from_string(result.document)
```

### 3. Test

```python
# tests/unit/test_structure_operations.py

def test_merge_sections():
    """Test merging two sections."""
    doc_text = """# Title

## Section 1

Content 1

## Section 2

Content 2
"""
    doc = Document.from_string(doc_text)

    result = StructureOperations.merge(doc, "h2-0", "h2-1")

    assert result.success
    assert "## Section 1" in result.document
    assert "## Section 2" not in result.document
    assert "Content 1" in result.document
    assert "Content 2" in result.document

# tests/unit/test_dsl_executor.py

def test_execute_merge_operation():
    """Test executing merge via DSL."""
    doc_text = """# Title

## Section 1

Content 1

## Section 2

Content 2
"""
    doc = Document.from_string(doc_text)

    lexer = Lexer("doc | merge h2-0 h2-1")
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    executor = Executor(doc)
    result = executor.execute(ast)

    result_text = result.to_string()
    assert "## Section 1" in result_text
    assert "## Section 2" not in result_text
```

### 4. Usage

```doctk
# In REPL
doctk> load document.md
doctk> merge h2-0 h2-1
doctk> save output.md

# In script file
doc | merge h2-0 h2-1 | merge h2-2 h2-3

# In Markdown code block
```doctk
doc | merge h2-introduction h2-overview
```
```

---

## Advanced: Adding Control Flow

### Example: Conditional Operations

```python
# If you want to add conditionals like:
# if level == 2 then promote h2-0

# 1. Add AST node
@dataclass
class IfStatement:
    condition: Callable[[Node], bool]
    then_operations: list[FunctionCall]

# 2. Update parser to recognize 'if' keyword
# 3. Update executor to evaluate conditions
```

**Recommendation:** Start simple. Add control flow only if truly needed.

---

## Best Practices

### 1. Keep Operations Pure

```python
# ✅ Good: Returns new document
def _exec_operation(self, node_id):
    result = self.operations.operation(self.document, node_id)
    return Document.from_string(result.document)

# ❌ Bad: Modifies in place
def _exec_operation(self, node_id):
    self.document.nodes[0].text = "Changed"  # NO!
    return self.document
```

### 2. Validate Inputs

```python
def _exec_operation(self, node_id: str) -> Document[Any]:
    # Validate node_id format
    if not node_id.startswith("h"):
        raise ExecutionError(f"Invalid node ID: {node_id}")

    result = self.operations.operation(self.document, node_id)

    if not result.success:
        # Always check success!
        raise ExecutionError(result.error or "Operation failed")

    return Document.from_string(result.document)
```

### 3. Provide Clear Error Messages

```python
if not result.success:
    # Include context in error messages
    raise ExecutionError(
        f"Failed to {operation_name} node {node_id}: {result.error}"
    )
```

### 4. Test Edge Cases

```python
def test_operation_with_invalid_node_id():
    """Test operation fails gracefully with invalid node ID."""
    with pytest.raises(ExecutionError, match="Node not found"):
        executor._exec_operation("invalid-id")

def test_operation_with_boundary_conditions():
    """Test operation at document boundaries."""
    # Test with first node, last node, single node, empty document
    pass
```

### 5. Document Your Operation

```python
def _exec_merge(self, node_id1: str, node_id2: str) -> Document[Any]:
    """
    Execute merge operation.

    Merges the second section into the first section. The second section's
    heading is removed, but its content is preserved.

    Args:
        node_id1: ID of first section (merge target)
        node_id2: ID of second section (will be merged and removed)

    Returns:
        Modified document with merged sections

    Raises:
        ExecutionError: If either section is not found or merge fails

    Example:
        >>> executor._exec_merge("h2-0", "h2-1")
        Document(merged sections)
    """
    # Implementation...
```

---

## Troubleshooting

### Issue: "Unknown operation"

**Cause:** Operation not added to executor dispatch table.

**Solution:** Add to `self._operation_dispatch` in `Executor.__init__()`.

### Issue: "Wrong number of arguments"

**Cause:** Argument count in dispatch table doesn't match handler signature.

**Solution:**
```python
# Dispatch table must match handler signature
self._operation_dispatch = {
    "rename": (self._exec_rename, 2),  # 2 args: node_id, new_text
}

def _exec_rename(self, node_id: str, new_text: str):  # 2 parameters
    pass
```

### Issue: Operation works in core but not in DSL

**Cause:** Missing executor handler.

**Solution:** Ensure handler exists and is registered in dispatch table.

---

## Testing Checklist

Before submitting your new operation:

- [ ] Core operation implemented in `StructureOperations`
- [ ] Core operation has unit tests
- [ ] Executor handler added
- [ ] Executor handler registered in dispatch table
- [ ] DSL unit tests pass
- [ ] REPL integration works
- [ ] Script file execution works
- [ ] Code block execution works
- [ ] Documentation updated
- [ ] Examples provided

---

## Additional Resources

- [DSL API Reference](../api/dsl.md)
- [Core Integration API](../api/core-integration.md)
- Executor Source: `src/doctk/dsl/executor.py`
- Operation Tests: `tests/unit/test_structure_operations.py`

---

## Getting Help

- **Issues**: https://github.com/tommcd/doctk/issues
- **Discussions**: https://github.com/tommcd/doctk/discussions

---

**Next Steps:**

1. Design your operation
2. Implement in core integration layer
3. Add executor handler
4. Test thoroughly
5. Submit a pull request!
