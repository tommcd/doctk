# Implement Next Task Across All Specs

I need you to analyze all Kiro specs in `.kiro/specs/`, assess the current state, and suggest the next best task(s) to work on.

## Your Mission

1. **Assess the current state** across all specs except those in the 'old' directory
1. **Identify critical issues** (failing tests, missing tests, blockers)
1. **Suggest the next few steps** with rationale
1. **Offer options** for what to work on next
1. **Implement** the chosen task(s) once I approve

## Assessment Process

### Phase 1: Understand the Landscape

1. **Read the implementation guide**: Start with `claude-code-kiro-spec-prompt.md` to understand how specs work

1. **Read the dependency structure**: Check `.kiro/specs/IMPLEMENTATION_ORDER.md` to understand:

   - Dependencies between specs
   - What must be done sequentially
   - What can be done in parallel

1. **Survey all specs**: For each spec in `.kiro/specs/`, read:

   - `requirements.md` - what needs to be built
   - `design.md` - how it should be built
   - `tasks.md` - implementation plan and current status (look for `[x]` completed vs `[ ]` incomplete)

1. **Check quality status**: Run quality checks to identify issues:

   ```bash
   # Run all tests to find failures
   uv run pytest -x --tb=short

   # Check for linting issues
   tox -e ruff

   # Check for type errors
   uv run mypy src/doctk
   ```

### Phase 2: Analyze and Prioritize

Based on your assessment, identify:

1. **Critical blockers**:

   - Failing tests that need fixing
   - Missing tests for completed features
   - Dependency violations (tasks marked complete but dependencies incomplete)
   - Quality issues (linting errors, type errors)

1. **Next logical tasks**:

   - First incomplete task in each spec's `tasks.md`
   - Tasks whose dependencies are satisfied
   - Tasks that unblock other work

1. **Parallel opportunities**:

   - Tasks in different specs that can be done simultaneously
   - Independent tasks within the same spec

### Phase 3: Present Options

**Before implementing anything**, present your findings:

1. **Current State Summary**:

   - Which specs are complete, in-progress, or not started
   - Any failing tests or quality issues
   - Any blockers or dependency issues

1. **Recommended Next Steps** (2-4 options):

   - For each option, explain:
     - Which spec(s) and task(s)
     - Why this is a good next step
     - What it will accomplish
     - Estimated complexity (small/medium/large)
     - Any dependencies or prerequisites

1. **Ask for direction**:

   - "Which option would you like me to proceed with?"
   - "Or would you prefer a different approach?"

## Implementation Process

Once I approve an option, proceed with implementation:

1. **Announce your plan**: Clearly state which spec(s) and task(s) you're implementing

1. **Implement incrementally**:

   - Follow the design document exactly
   - Write tests for new functionality
   - Run quality checks frequently
   - Fix issues immediately

1. **Verify quality** before marking complete:

   ```bash
   # All tests must pass
   uv run pytest -m "slow or not slow"

   # All linting must pass
   tox -e ruff
   tox -e shellcheck

   # All type checking must pass
   uv run mypy src/doctk

   # Documentation must build
   tox -e docs
   ```

1. **Update documentation**:

   - Mark completed tasks with `[x]` in the spec's `tasks.md`
   - Update `design.md` if implementation revealed necessary changes
   - Add comments explaining complex logic

1. **Prepare for next iteration**:

   - Run final quality checks
   - Commit your work with clear messages
   - Present the updated state and suggest next steps

## Quality Standards

Before marking ANY task as complete:

- ✅ All tests pass - zero failures
- ✅ All linting passes - zero warnings/errors
- ✅ All type checking passes - zero errors
- ✅ Documentation builds successfully
- ✅ Code follows project conventions

## Key Principles

- **Be dynamic**: Don't assume anything about current state - always check
- **Be thorough**: Verify that tasks marked complete are actually complete
- **Be strategic**: Suggest tasks that maximize progress and unblock other work
- **Be flexible**: Offer multiple options so I can guide priorities
- **Be incremental**: Deliver small, testable units rather than large changes
- **Be quality-focused**: Fix issues immediately, don't accumulate technical debt

## Project Context

The doctk project is a Python document manipulation toolkit:

- Uses `uv` for Python package management
- Uses `tox` for test orchestration and quality checks
- Follows strict quality standards (documented in CLAUDE.md)
- Values immutability, type safety, and composability
- Requires comprehensive testing and documentation

## Getting Started

1. Read the spec guide (`claude-code-kiro-spec-prompt.md`)
1. Read the dependency structure (`.kiro/specs/IMPLEMENTATION_ORDER.md`)
1. Survey all specs and their current state
1. Run quality checks to identify issues
1. Present your assessment and recommendations
1. Wait for my approval before implementing

Remember: Your job is to be my intelligent assistant who understands the full picture and helps me make informed decisions about what to work on next. Don't just blindly implement - think strategically and present options.
