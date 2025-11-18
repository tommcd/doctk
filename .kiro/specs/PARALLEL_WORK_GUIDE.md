# Guide: Working on Multiple Specs in Parallel

This guide explains how to work on multiple specs simultaneously using separate Claude Code instances.

## Overview

The doctk project has three main specs that can be worked on in parallel once their dependencies are satisfied:

1. **doctk-core-integration** - Core Python API and operations
1. **vscode-outliner-extension** - VS Code tree view and UI
1. **doctk-language-server** - LSP for DSL editing

## How to Work in Parallel

### Step 1: Check Dependencies

Before starting work on any spec, check `.kiro/specs/IMPLEMENTATION_ORDER.md` to verify that all prerequisite tasks from other specs are complete.

### Step 2: Create Spec-Specific Prompts

For each spec you want to work on, create a copy of `claude-code-implement-next-prompt.md` with the spec name filled in:

**For Core Integration:**

```bash
# Replace {{SPEC_NAME}} with doctk-core-integration
sed 's/{{SPEC_NAME}}/doctk-core-integration/g' claude-code-implement-next-prompt.md > /tmp/prompt-core.md
```

**For VS Code Extension:**

```bash
# Replace {{SPEC_NAME}} with vscode-outliner-extension
sed 's/{{SPEC_NAME}}/vscode-outliner-extension/g' claude-code-implement-next-prompt.md > /tmp/prompt-vscode.md
```

**For Language Server:**

```bash
# Replace {{SPEC_NAME}} with doctk-language-server
sed 's/{{SPEC_NAME}}/doctk-language-server/g' claude-code-implement-next-prompt.md > /tmp/prompt-lsp.md
```

### Step 3: Launch Parallel Instances

1. Open three separate Claude Code instances (or three separate chat sessions)
1. Paste the appropriate prompt into each instance
1. Each instance will work on its assigned spec independently

### Step 4: Monitor Progress

Each instance will:

- Read its spec's `tasks.md` to see what's next
- Implement the next deliverable unit
- Mark tasks complete with `[x]` in its spec's `tasks.md`
- NOT modify `IMPLEMENTATION_ORDER.md` (it's a static dependency guide)

## Task Tracking

### Where to Track Completion

- **Individual tasks**: Mark `[x]` in `.kiro/specs/{SPEC_NAME}/tasks.md`
- **Dependencies**: Check `.kiro/specs/IMPLEMENTATION_ORDER.md` (read-only)
- **Recent progress**: Visible in `tasks.md` (tasks are done top-to-bottom)

### What NOT to Update

- **IMPLEMENTATION_ORDER.md**: This is a static dependency and sequencing guide. It does NOT track completion status.
- The only source of truth for "what's done" is the `[x]` checkboxes in each spec's `tasks.md`

## Example Workflow

### Instance 1: Core Integration

```
Working on: doctk-core-integration
Current task: Task 6 (REPL implementation)
Status: Implementing DoctkREPL class
Updates: .kiro/specs/doctk-core-integration/tasks.md
```

### Instance 2: VS Code Extension

```
Working on: vscode-outliner-extension
Current task: Task 3 (Context menu operations)
Status: Implementing OperationHandler class
Updates: .kiro/specs/vscode-outliner-extension/tasks.md
```

### Instance 3: Language Server

```
Working on: doctk-language-server
Current task: Task 1 (Language server foundation)
Status: Setting up DoctkLanguageServer with pygls
Updates: .kiro/specs/doctk-language-server/tasks.md
```

## Coordination

### When Dependencies Exist

If a task in one spec depends on a task in another spec:

1. Check the other spec's `tasks.md` to see if the dependency is complete
1. If not complete, either:
   - Wait for the other instance to complete it
   - Switch to a different task in your spec that doesn't have the dependency
   - Coordinate with the other instance to prioritize the blocking task

### Avoiding Conflicts

Each spec has its own:

- Source code directories
- Test files
- Documentation files

The only shared files are:

- `IMPLEMENTATION_ORDER.md` (read-only, don't update)
- Root-level docs (coordinate if changes needed)

## Benefits of This Approach

1. **Parallel progress**: Multiple specs advance simultaneously
1. **Clear ownership**: Each instance owns one spec
1. **No merge conflicts**: Specs have separate code directories
1. **Simple tracking**: Each spec's `tasks.md` is the single source of truth
1. **Flexible coordination**: Work can proceed independently when dependencies allow

## Quick Reference

| Spec Name | Directory | Tasks File |
|-----------|-----------|------------|
| Core Integration | `src/doctk/integration/` | `.kiro/specs/doctk-core-integration/tasks.md` |
| VS Code Extension | `extensions/doctk-outliner/` | `.kiro/specs/vscode-outliner-extension/tasks.md` |
| Language Server | `src/doctk/lsp/` | `.kiro/specs/doctk-language-server/tasks.md` |

## Summary

- Use `claude-code-implement-next-prompt.md` as a template
- Replace `{{SPEC_NAME}}` with your target spec
- Each instance works on one spec
- Track completion in each spec's `tasks.md`
- Check `IMPLEMENTATION_ORDER.md` for dependencies (but don't update it)
- Coordinate when cross-spec dependencies exist
