I need you to implement the next deliverable unit of work from the Kiro specs located in `.kiro/specs/`.

## Target Spec

**Work on spec**: `{{SPEC_NAME}}`

Replace `{{SPEC_NAME}}` with one of:

- `doctk-core-integration`
- `vscode-outliner-extension`
- `doctk-language-server`

## Your Mission

Implement the **minimum set of tasks** that delivers a **testable, working unit** of functionality for the specified spec. Work incrementally, delivering small working pieces rather than attempting everything at once.

## Implementation Process

Work through the following phases systematically:

### Phase 1: Planning & Assessment

1. **Read the implementation order**: Start by reading `.kiro/specs/IMPLEMENTATION_ORDER.md` to understand:

   - Dependencies between specs
   - What must be done sequentially
   - What blockers exist for your target spec
   - Whether your spec's dependencies are satisfied

1. **Read the spec guide**: Read `claude-code-kiro-spec-prompt.md` to understand how to work with Kiro specifications

1. **Analyze your target spec**: For `.kiro/specs/{{SPEC_NAME}}/`, read in this order:

   - `requirements.md` - understand what needs to be built
   - `design.md` - understand how it should be built
   - `tasks.md` - see the implementation plan and current status

1. **Identify the next deliverable unit**: Based on `tasks.md`, determine:

   - What is the next uncompleted task (first `[ ]` in the list)?
   - What is the minimum set of tasks that delivers something testable?
   - Are there any blockers from other specs that must be resolved first?
   - Check IMPLEMENTATION_ORDER.md to verify dependencies are satisfied

1. **Verify completed tasks**: For all tasks marked complete `[x]` in your spec:

   - Check that the code actually exists
   - Verify it matches the requirements
   - Ensure it follows the design document
   - If anything is incomplete or incorrect, fix it before proceeding

1. **Announce your plan**: Before starting implementation, clearly state:

   - Which spec you're working on ({{SPEC_NAME}})
   - Which tasks you're implementing (minimum set for a deliverable unit)
   - Why this is the next logical step
   - What will be testable after completion
   - Confirmation that all dependencies from other specs are satisfied

### Phase 2: Implementation

For the selected deliverable unit (minimum set of tasks):

1. **Implement the tasks** following the design document exactly

1. **Write tests** for the new functionality:

   - Unit tests for individual components
   - Integration tests for component interactions
   - E2E tests if appropriate for this deliverable

1. **Run comprehensive quality checks** before marking complete:

   ```bash
   # Run all tests
   uv run pytest -m "slow or not slow"

   # Run all tox quality checks
   tox -e ruff           # Python linting
   tox -e shellcheck     # Shell script linting
   tox -e docs           # Documentation checks

   # Run mypy for type checking
   uv run mypy src/doctk
   ```

1. **Fix ALL issues found**:

   - All tests must pass (zero failures)
   - All linting must pass (zero warnings/errors)
   - All type checking must pass (zero mypy errors)
   - All documentation checks must pass
   - Zero errors, zero warnings, zero issues

1. **Update documentation**:

   - Mark completed tasks in `.kiro/specs/{{SPEC_NAME}}/tasks.md` with `[x]`
   - Update the spec's `design.md` if implementation revealed necessary changes
   - Do NOT update IMPLEMENTATION_ORDER.md (it tracks dependencies, not completion status)

1. **Verify the deliverable**: Confirm that:

   - The implemented unit is testable and working
   - All quality checks pass
   - Documentation is updated
   - The next person knows what to do next (from tasks.md)

### Phase 3: Delivery & Handoff

After completing the deliverable unit:

1. **Final verification**:

   - Run complete test suite: `uv run pytest -m "slow or not slow"`
   - Run all tox environments: `tox`
   - Run mypy type checking: `uv run mypy src/doctk`
   - Verify environment: `./scripts/check-environment.sh`

1. **Commit your work**:

   - Create a clear commit message describing what was delivered
   - Reference the spec and task numbers
   - Mention what is now testable/working

1. **Update tracking documents**:

   - Ensure `.kiro/specs/{{SPEC_NAME}}/tasks.md` reflects completed work
   - Update any relevant README files
   - Do NOT update IMPLEMENTATION_ORDER.md (it's a static dependency guide)

1. **Prepare for next iteration**:

   - Clearly state what was accomplished
   - Identify what should be done next (from tasks.md)
   - Note any blockers or dependencies for the next unit
   - Suggest the next minimum deliverable unit

## Quality Standards (CRITICAL)

Before marking ANY task as complete, ensure:

- ✅ All tests pass (unit, e2e, quality, docs) - zero failures
- ✅ All linting passes (ruff, shellcheck, shfmt, markdownlint) - zero warnings/errors
- ✅ All type checking passes (mypy) - zero errors
- ✅ All documentation builds successfully
- ✅ Code follows project conventions (see CLAUDE.md)
- ✅ Absolutely zero warnings, errors, or issues

## Mypy Configuration

If mypy is not configured in tox.ini, add this section:

```ini
[testenv:mypy]
description = Run mypy type checking
deps = mypy
commands = mypy src/doctk --strict
```

Then ensure it passes before marking tasks complete.

## Implementation Guidelines

- **Work on your assigned spec**: Focus on `.kiro/specs/{{SPEC_NAME}}/`
- **Work incrementally**: Deliver small, testable units rather than attempting everything at once
- **Follow dependencies**: Check IMPLEMENTATION_ORDER.md to ensure your spec's dependencies are satisfied
- **Minimum viable deliverable**: Pick the smallest set of tasks that delivers something testable and working
- **Verify constantly**: Run quality checks after every significant change, not just at the end
- **Fix everything**: Address all warnings and errors immediately - don't accumulate technical debt
- **Follow design**: Implement exactly what's specified in design documents
- **Meet requirements**: Satisfy all acceptance criteria from requirements.md
- **Update task tracking**: Keep `.kiro/specs/{{SPEC_NAME}}/tasks.md` current with `[x]` for completed tasks
- **Be thorough**: Verify that tasks marked as complete are actually complete before proceeding
- **Enable the next person**: Leave clear documentation about what's done and what's next in tasks.md

## Project Context

The doctk project is a Python document manipulation toolkit with these characteristics:

- Uses `uv` for Python package management
- Uses `tox` for test orchestration and quality checks
- Follows strict quality standards (documented in CLAUDE.md)
- Values immutability, type safety, and composability
- Requires comprehensive testing and documentation for all code

## Getting Started

1. **Replace `{{SPEC_NAME}}`** in this prompt with your target spec name
1. Read `.kiro/specs/IMPLEMENTATION_ORDER.md` to verify your spec's dependencies are satisfied
1. Read the spec guide (`claude-code-kiro-spec-prompt.md`) to understand how to work with specs
1. Read `.kiro/specs/{{SPEC_NAME}}/tasks.md` to see what's done and what's next
1. Identify the next minimum deliverable unit from tasks.md
1. Announce your plan before starting implementation
1. Implement, test, verify, document, and deliver

As you work, feel free to show your progress, ask questions if requirements are unclear, and share any issues you encounter. The goal is to deliver working, tested functionality incrementally while maintaining the project's high quality standards.

## Key Principle: Incremental Delivery

**Don't try to implement everything at once.** Instead:

- Pick the next logical unit from `.kiro/specs/{{SPEC_NAME}}/tasks.md`
- Implement the minimum set of tasks that delivers something testable
- Verify it works completely
- Update task documentation (mark `[x]` in tasks.md, update design.md if needed)
- Commit and hand off
- Let the next iteration pick up the next unit

This approach ensures:

- Continuous progress with working, tested code
- Clear handoff points between work sessions
- Reduced risk of large, untested changes
- Better tracking of what's done and what's next
- Multiple specs can be worked on in parallel by different instances
