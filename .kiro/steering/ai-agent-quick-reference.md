---
title: AI Agent Quick Reference
inclusion: always
---

# AI Agent Quick Reference

Quick reference for AI agents working on doctk. Read `workflow.md` for complete details.

## Golden Rules

1. **ONE TASK AT A TIME** - Complete one task, stop, wait for human review
1. **NEVER PUSH TO MASTER** - Always work on feature branches
1. **TEST BEFORE MARKING COMPLETE** - All tests must pass
1. **80% COVERAGE MINIMUM** - No exceptions
1. **STOP AFTER 2 FAILED ATTEMPTS** - Request human help

## Before Starting Any Task

```bash
# 1. Read the spec documents
cat .kiro/specs/<spec-name>/requirements.md
cat .kiro/specs/<spec-name>/design.md
cat .kiro/specs/<spec-name>/tasks.md

# 2. Verify environment
uv run pytest  # Should pass before you start

# 3. Check current branch
git branch     # Should be on feature branch, not master
```

## Task Implementation Checklist

For EVERY task:

- [ ] Read task description and requirements reference
- [ ] Read relevant section in design.md
- [ ] Implement the code
- [ ] Write tests (unit + edge cases)
- [ ] Run tests: `uv run pytest`
- [ ] Check coverage: `uv run pytest --cov=doctk.<module> --cov-report=term-missing`
- [ ] Fix lint: `tox -e ruff-fix`
- [ ] Verify quality: `tox -e ruff`
- [ ] Update tasks.md: mark task complete `[x]`
- [ ] Commit: `git commit -m "feat(scope): description"`
- [ ] STOP - Request human review

## Essential Commands

```bash
# Run tests
uv run pytest                                    # All tests
uv run pytest tests/unit/test_foo.py -v        # Specific test
uv run pytest --lf                              # Last failed

# Check coverage
uv run pytest --cov=doctk --cov-report=term-missing

# Quality checks
tox -e ruff                                     # Check lint
tox -e ruff-fix                                 # Fix lint
tox -e docs                                     # Check markdown
tox -e docs-fix                                 # Fix markdown

# Spec validation
uv run pytest tests/docs/test_spec_quality.py -v

# All checks at once
tox
```

## When to Stop and Ask for Help

STOP and request human assistance when:

1. ❌ Tests fail after 2 fix attempts
1. ❌ Can't reach 80% coverage
1. ❌ Spec is ambiguous or contradictory
1. ❌ Multiple valid design approaches exist
1. ❌ Breaking changes to public API needed
1. ❌ Security or performance concerns
1. ❌ Unexpected behavior that's not in spec

## Communication Templates

### Starting a task

```
Starting task X.Y: <task name>

Plan:
- <what you'll implement>
- <what tests you'll write>
- <what files you'll modify>

Reading: design.md section on <topic>
```

### Completing a task

```
Completed task X.Y: <task name>

✓ Implemented: <what was built>
✓ Tests: <number> tests, all passing
✓ Coverage: <percentage>% for <module>
✓ Quality: No ruff/mypy errors
✓ Updated: tasks.md marked complete

Ready for review.
Next task: X.Z <next task name>
```

### Requesting help

```
Blocked on task X.Y: <task name>

Issue: <specific problem>

Tried:
1. <first attempt> - <result>
2. <second attempt> - <result>

Error: <exact error message>
File: <file>:<line>

Question: <specific question for human>
```

## Common Mistakes to Avoid

❌ **Don't**: Auto-continue to next task without approval
✅ **Do**: Stop after each task for human review

❌ **Don't**: Push code with failing tests
✅ **Do**: Ensure all tests pass before pushing

❌ **Don't**: Guess at ambiguous requirements
✅ **Do**: Ask for clarification

❌ **Don't**: Skip writing tests
✅ **Do**: Write tests for every feature and edge case

❌ **Don't**: Commit directly to master
✅ **Do**: Always work on feature branches

❌ **Don't**: Make up design decisions
✅ **Do**: Follow design.md or ask for guidance

❌ **Don't**: Keep trying after 2 failures
✅ **Do**: Document attempts and request help

## File Locations

```
.kiro/
├── steering/              # Always-available guidance
│   ├── workflow.md       # Complete workflow (read this!)
│   ├── tech.md           # Tech stack and commands
│   ├── structure.md      # Project organization
│   └── product.md        # Product overview
└── specs/                # Feature specifications
    └── <spec-name>/
        ├── requirements.md   # WHAT to build
        ├── design.md         # HOW to build it
        └── tasks.md          # Step-by-step plan
```

## Pre-Push Checklist

Before pushing ANY code:

```bash
# 1. All tests pass
uv run pytest
# ✓ Should see: "passed"

# 2. Coverage ≥80%
uv run pytest --cov=doctk --cov-report=term-missing
# ✓ Should see: "TOTAL ... 80%"

# 3. No lint errors
tox -e ruff
# ✓ Should see: "All checks passed!"

# 4. Specs valid (if modified)
uv run pytest tests/docs/test_spec_quality.py -v
# ✓ Should see: "passed"

# 5. Commit and push
git add .
git commit -m "feat(scope): description"
git push origin feature/<branch-name>
```

## Task Marking Format

```markdown
- [ ] Not started
- [x] Completed
- [ ]* Optional (can skip)
- [ ] In progress (add comment with status)
```

Example with progress notes:

```markdown
- [ ] 3. Implement graph model
  - [x] Create Node class
  - [x] Create Edge class
  - [ ] Implement traversal (IN PROGRESS: DFS done, BFS next)
  - [ ] Add cycle detection
```

## Coverage Tips

If coverage is below 80%:

```bash
# See what's missing
uv run pytest --cov=doctk.<module> --cov-report=term-missing

# Look for:
# - Untested functions
# - Untested edge cases
# - Untested error paths
# - Untested branches (if/else)

# Add tests for missing lines
# Re-run until ≥80%
```

## Remember

- Quality over speed
- One task at a time
- Test everything
- Stop and ask when unsure
- Keep specs synchronized
- Communicate clearly

**When in doubt, STOP and ASK.**
