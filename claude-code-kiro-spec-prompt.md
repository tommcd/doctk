# Claude Code: Kiro Spec Implementation Guide

You are Claude Code, and you're being asked to implement tasks from a Kiro spec. This guide explains how to read, understand, and execute spec-based development work.

## Understanding the .kiro Directory

The `.kiro/` directory contains two important subdirectories:

### .kiro/steering/

**Purpose**: Provides always-available context and guidance for AI assistants working in this codebase.

Steering documents are automatically included in your context and contain:

- **product.md** - Product overview, philosophy, and current status
- **tech.md** - Tech stack, build system, common commands
- **structure.md** - Project organization, folder structure, conventions
- **python-wsl-uv.md** - Python environment and WSL-specific rules
- **validate-spec-accuracy.md** - Spec validation testing guidelines

These documents help you understand the project without needing to ask basic questions.

### .kiro/specs/

**Purpose**: Contains structured feature specifications for incremental development.

Each spec is a formalized design and implementation process with three documents:

1. **requirements.md** - Defines WHAT needs to be built
1. **design.md** - Defines HOW it will be built
1. **tasks.md** - Defines the step-by-step implementation plan

## What is a Kiro Spec?

A Kiro spec is a structured approach to building features. It formalizes the design and implementation process through three key documents located in `.kiro/specs/<spec-name>/`:

## How to Work with Specs

### Step 1: Read the Requirements Document

Start by reading `.kiro/specs/<spec-name>/requirements.md`:

- Look for the **Introduction** section to understand the overall goal
- Review the **Glossary** to understand domain-specific terms
- Read each **Requirement** carefully - these define acceptance criteria
- Requirements follow the format: "WHEN [condition], THE System SHALL [behavior]"
- These are your source of truth for what "done" means

### Step 2: Read the Design Document

Next, read `.kiro/specs/<spec-name>/design.md`:

- Review the **Architecture** section to understand the technical approach
- Look for code structure diagrams and file organization
- Identify key components, classes, and modules to be created
- Note any design patterns, principles, or constraints
- Understand dependencies and integration points
- This tells you HOW to implement the requirements

### Step 3: Read and Execute the Task List

Finally, read `.kiro/specs/<spec-name>/tasks.md`:

- This breaks the design into discrete, manageable implementation steps
- Tasks are listed with checkboxes: `- [ ]` (incomplete) or `- [x]` (complete)
- Tasks may have sub-tasks indented beneath them
- Each task may reference requirements (e.g., "*Requirements: 1.1, 1.2*")
- Tasks build incrementally - complete them in order unless stated otherwise

## How to Update the Task List

As you complete tasks, update `tasks.md` by changing checkboxes:

**Before:**

```markdown
- [ ] 1. Create the tool management framework
  - [ ] Create src/doctk/tools/ directory
  - [ ] Implement ToolManager class
```

**After completing sub-task:**

```markdown
- [ ] 1. Create the tool management framework
  - [x] Create src/doctk/tools/ directory
  - [ ] Implement ToolManager class
```

**After completing main task:**

```markdown
- [x] 1. Create the tool management framework
  - [x] Create src/doctk/tools/ directory
  - [x] Implement ToolManager class
```

### Task Marking Conventions

- `- [ ]` = Not started
- `- [x]` = Completed
- `- [ ]*` = Optional task (marked with asterisk)
- Tasks may have notes like "*Requirements: 1.5*" linking back to requirements

## Your Implementation Workflow

1. **Read all three documents** (requirements → design → tasks) before starting
1. **Start with the first uncompleted task** in tasks.md
1. **Implement the task** following the design document's guidance
1. **Verify against requirements** - ensure acceptance criteria are met
1. **Update tasks.md** - mark the task as complete with `[x]`
1. **Test your work** - run relevant tests or checks
1. **Move to the next task** and repeat

## Important Notes

- **Don't skip ahead**: Tasks are ordered to build incrementally
- **Check dependencies**: Some tasks depend on previous tasks being complete
- **Verify your work**: After each task, ensure it works before moving on
- **Update as you go**: Mark tasks complete immediately after finishing them
- **Read the Status Summary**: Check if there's a status section showing overall progress
- **Check Success Criteria**: The tasks.md may have success criteria at the bottom

## Example: Reading a Task

```markdown
- [ ] 2. Copy development scripts
  - Copy all scripts from python-project-template/scripts/ to doctk/scripts/
  - Update script imports to use doctk.tools instead of sstdf_python_standards.tools
  - Make all scripts executable with chmod +x
  - Test that setup-environment.sh runs without errors
  - _Requirements: 2.1, 2.2, 2.3_
```

This task tells you to:

1. Copy scripts from a template
1. Update imports in those scripts
1. Make them executable
1. Test the main setup script
1. This satisfies requirements 2.1, 2.2, and 2.3

## Finding Specs and Steering Documents

### Specs

Specs are located in `.kiro/specs/<spec-name>/`:

- Each spec has its own folder
- Look for `requirements.md`, `design.md`, and `tasks.md`
- If `tasks.md` doesn't exist yet, you may need to create it based on the design

### Steering Documents

Steering documents are located in `.kiro/steering/`:

- These are automatically included in your context
- They provide project-wide conventions, tech stack info, and structure
- Reference them when you need to understand project standards
- Common files: `product.md`, `tech.md`, `structure.md`

## When Tasks Are Complete

Check the **Status Summary** or **Success Criteria** sections in tasks.md:

- These define when the entire spec is considered complete
- May include things like "all tests pass", "documentation updated", etc.
- Don't consider the spec done until all success criteria are met

## Tips for Success

- **Be thorough**: Read all three documents completely before starting
- **Stay organized**: Work through tasks sequentially
- **Verify continuously**: Test after each task, not just at the end
- **Update diligently**: Keep tasks.md current as you work
- **Ask questions**: If requirements or design are unclear, ask for clarification
- **Reference back**: Constantly refer to requirements and design while implementing

______________________________________________________________________

Now, read the spec documents in this order:

1. `.kiro/specs/<spec-name>/requirements.md`
1. `.kiro/specs/<spec-name>/design.md`
1. `.kiro/specs/<spec-name>/tasks.md`

Then start implementing the first uncompleted task!
