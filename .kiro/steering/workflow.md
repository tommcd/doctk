---
title: Development Workflow
inclusion: always
---

# Development Workflow

This document defines the standard development workflow for the doctk project. All contributors and AI assistants must follow these practices.

## Branch Strategy

### Feature Branches

- **All development takes place on feature branches**
- Branch naming convention: `feature/<descriptive-name>` or `fix/<issue-description>`
- Examples: `feature/graph-model`, `fix/parser-edge-case`

### Protected Branches

- **NEVER push directly to `master`**
- All changes must go through Pull Request (PR) review
- Master branch is protected and represents production-ready code

### Branch Lifecycle

1. Create feature branch from latest `master`
1. Implement feature with incremental commits
1. Push to GitHub and create PR
1. Address code review feedback
1. Merge PR after approval
1. Pull latest `master` and delete local feature branch
1. Repeat for next feature

## Quality Standards

### Code Quality Requirements

Before pushing code, ensure ALL of the following pass:

1. **All tests pass**: `uv run pytest`
1. **No ruff errors**: `tox -e ruff`
1. **No format issues**: Code must be formatted (ruff handles this)
1. **No import sorting issues**: Automatic via ruff
1. **No type errors**: `mypy` checks (gradual adoption)
1. **No markdown lint errors**: `tox -e docs`

### Coverage Requirements

- **Minimum 80% code coverage** for all new code
- Run coverage report: `uv run pytest --cov=doctk --cov-report=html`
- View report: `reports/coverage/html/index.html`
- Coverage is measured per-module and overall

### Testing Requirements

Every feature must include:

1. **Unit tests** - Fast, isolated tests in `tests/unit/`
1. **Edge case tests** - Boundary conditions, empty inputs, error cases
1. **Integration tests** - E2E tests in `tests/e2e/` (when applicable)
1. **Documentation tests** - Spec validation if specs are modified

Test markers to use:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests (excluded by default)

## Pre-Push Checklist

Run these commands before pushing:

```bash
# 1. Run all tests
uv run pytest

# 2. Check coverage (must be ≥80%)
uv run pytest --cov=doctk --cov-report=term-missing

# 3. Run quality checks
tox -e ruff          # Linting
tox -e docs          # Markdown linting

# 4. Auto-fix any issues
tox -e ruff-fix      # Fix Python formatting
tox -e docs-fix      # Fix markdown formatting

# 5. Verify spec accuracy (if specs modified)
uv run pytest tests/docs/test_spec_quality.py -v
```

Or run everything at once:

```bash
# Run all quality checks
tox
```

### Automated Quality Gates

The following checks run automatically:

**Pre-commit hooks** (runs on `git commit`):

- Ruff formatting and linting
- Type checking (mypy)
- Trailing whitespace removal
- YAML/TOML validation

**CI/CD pipeline** (runs on push to GitHub):

- Full test suite across Python versions
- Coverage reporting
- Quality checks (ruff, mypy, shellcheck)
- Documentation build
- Spec validation

**PR checks** (must pass before merge):

- All tests pass
- Coverage ≥80%
- No lint errors
- No type errors
- Spec validation passes
- AI code reviews completed

### Quality Gate Failures

If quality gates fail:

1. **Read the error** - Don't guess, understand the issue
1. **Fix locally** - Run same check locally to reproduce
1. **Verify fix** - Ensure check passes locally
1. **Push fix** - Commit and push the fix
1. **Monitor CI** - Verify CI passes

Don't push repeatedly hoping it will pass - fix locally first.

## Pull Request Workflow

### Step 1: Creating a PR

```bash
# Push your feature branch
git push origin feature/<your-feature>

# Create PR using GitHub CLI
gh pr create --title "Feature: <description>" --body "Description of changes"
```

**IMPORTANT: Stay on your feature branch after creating the PR!**

### Step 2: Monitor PR Status

After creating the PR, **DO NOT switch branches**. Wait for:

1. CI tests to complete
1. AI code reviewers to provide feedback

Check PR status:

```bash
# View PR summary
gh pr view <PR-NUMBER>

# Check CI status
gh pr checks <PR-NUMBER>
```

### Step 3: Fetch Code Review Comments

When human confirms reviews are ready, fetch all inline review comments:

```bash
# Get all inline review comments with their IDs
gh api repos/tommcd/doctk/pulls/<PR-NUMBER>/comments --jq '.[] | {id: .id, path: .path, line: .line, body: .body}'
```

This shows:

- `id` - Comment ID (needed to reply)
- `path` - File with the comment
- `line` - Line number
- `body` - The review comment text

### Step 4: Address Review Comments

For each review comment:

1. **Make the fix** on your feature branch
1. **Commit and push** the fix
1. **Reply to the comment** to mark it resolved

```bash
# Make your fixes
git add <files>
git commit -m "fix: address review feedback - <description>"
git push origin feature/<your-feature>

# Reply to each comment (use the comment ID from step 3)
gh api -X POST repos/tommcd/doctk/pulls/<PR-NUMBER>/comments/<COMMENT-ID>/replies \
  -f body="✅ Fixed - <explanation of what you changed>"
```

**Repeat for ALL review comments** from all reviewers (Gemini, Copilot, Codex).

### Step 5: Verify Tests Pass

After addressing all feedback:

```bash
# Check that CI is now passing
gh pr checks <PR-NUMBER>

# View full PR status
gh pr view <PR-NUMBER>
```

Confirm:

- ✓ All tests passing
- ✓ All review comments addressed
- ✓ No merge conflicts

### Step 6: Notify Human

Inform the human that:

- All review comments have been addressed
- All tests are passing
- PR is ready to merge

**WAIT for human to merge the PR** - Do not merge yourself!

### Step 7: Post-Merge Cleanup (After Human Confirms Merge)

Only after human confirms the PR has been merged:

```bash
# Switch to master
git checkout master

# Pull latest changes (includes your merged PR)
git pull origin master

# Delete local feature branch
git branch -d feature/<your-feature>

# Delete remote feature branch
git push origin --delete feature/<your-feature>

# Verify cleanup
git branch -a  # Should not show your feature branch
```

### PR Requirements

- **Title**: Clear, descriptive title starting with "Feature:", "Fix:", or "Refactor:"
- **Description**: Explain what changed and why
- **Tests**: Confirm all tests pass and coverage is ≥80%
- **Checklist**: Include pre-push checklist results

### Code Review Process

This project uses **3 AI code reviewers**:

1. **Gemini** - Google's AI reviewer
1. **Copilot** - GitHub's AI reviewer
1. **Codex** - OpenAI's reviewer

**You must address ALL code review comments** from all three reviewers before merging.

## Common PR Workflow Mistakes to Avoid

❌ **Don't switch to master immediately after creating PR**

- Stay on feature branch to address review comments

❌ **Don't assume PR will auto-merge**

- Wait for human confirmation before switching branches

❌ **Don't ignore review comments**

- Address ALL comments from ALL reviewers

❌ **Don't merge yourself**

- Let human click the merge button

✅ **Do stay on feature branch until merge is confirmed**
✅ **Do use `gh api` to programmatically handle review comments**
✅ **Do verify tests pass after addressing feedback**
✅ **Do wait for human confirmation before cleanup**
git push origin --delete feature/<your-feature>

```

## Incremental Development

### Small, Testable Pieces

- Break work into small, independently testable units
- Each commit should represent a logical, working change
- Prefer multiple small PRs over one large PR
- Each PR should be reviewable in < 30 minutes

### Commit Messages

Follow conventional commit format:

```

<type>(<scope>): <subject>

<body>

<footer>
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
- `test`: Adding tests
- `docs`: Documentation changes
- `chore`: Maintenance tasks

Example:

```
feat(parser): add support for nested lists

Implements nested list parsing with proper indentation handling.
Includes edge case tests for deeply nested structures.

Closes #123
```

## Working with Specs

### Spec-Driven Development Cycle

When implementing from `.kiro/specs/`:

1. **Read requirements.md** - understand acceptance criteria
1. **Read design.md** - understand technical approach
1. **Read tasks.md** - follow implementation order
1. **Implement one task** - focus on single task
1. **Mark task complete** - update tasks.md
1. **Run spec validation**: `uv run pytest tests/docs/test_spec_quality.py -v`
1. **Stop for review** - let human verify before next task

### Spec Evolution

Specs are living documents that evolve with the code:

**When to update specs:**

- Requirements change during implementation
- Design decisions differ from original plan
- New edge cases discovered
- Better approach identified
- API changes needed

**How to update specs:**

1. Create issue documenting why change needed
1. Update spec documents (requirements/design/tasks)
1. Get human approval for spec changes
1. Continue implementation with updated spec
1. Commit spec changes with implementation

**Spec change commit format:**

```
docs(spec): update <spec-name> design for <reason>

Changed: <what changed>
Reason: <why it changed>
Impact: <what code is affected>

Related: #<issue-number>
```

### Spec Validation

Before pushing any PR that touches specs:

```bash
# Validate all spec references are correct
uv run pytest tests/docs/test_spec_quality.py -v

# Check for broken file references
# Check for invalid API references
# Check for incorrect line numbers
```

Fix any validation errors before pushing.

### Spec Completion Criteria

A spec is complete when:

1. ✅ All tasks marked complete in tasks.md
1. ✅ All requirements satisfied (check requirements.md)
1. ✅ All tests passing with ≥80% coverage
1. ✅ Spec validation passes
1. ✅ Documentation updated
1. ✅ Human review completed
1. ✅ PR merged to master

### Multiple Specs in Flight

When working on multiple specs:

- **One spec per branch** - Don't mix specs in same branch
- **One spec per PR** - Keep PRs focused
- **Finish before starting** - Complete current spec before new one
- **Document dependencies** - Note if specs depend on each other

Exception: Bug fixes can be separate from spec work.

## Environment Setup

### Initial Setup

```bash
# Full environment setup
./scripts/setup-environment.sh

# Verify everything works
./scripts/check-environment.sh
```

### Daily Development

```bash
# Sync dependencies (after pulling changes)
uv sync --all-groups

# Run tests frequently
uv run pytest

# Check quality before committing
tox -e ruff
```

## Common Workflows

### Starting a New Feature

```bash
# Ensure master is up to date
git checkout master
git pull origin master

# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit frequently
git add .
git commit -m "feat(scope): description"

# Push and create PR
git push origin feature/my-feature
gh pr create

# IMPORTANT: Stay on feature/my-feature branch!
# Wait for human to notify you about code reviews
# Address all review feedback on this branch
# Only switch to master AFTER human confirms PR is merged
```

### Fixing a Bug

```bash
# Create fix branch from master
git checkout master
git pull origin master
git checkout -b fix/bug-description

# Write failing test first
# Fix the bug
# Ensure test passes

# Commit and push
git add .
git commit -m "fix(scope): description"
git push origin fix/bug-description
gh pr create

# IMPORTANT: Stay on fix/bug-description branch!
# Wait for reviews, address feedback, then wait for merge confirmation
```

### Updating Dependencies

```bash
# Update uv.lock
uv sync --upgrade

# Test everything still works
uv run pytest
tox

# Commit lock file
git commit -m "chore: update dependencies"
```

## Troubleshooting

### Tests Failing

```bash
# Run specific test with verbose output
uv run pytest tests/unit/test_foo.py -v

# Run with print statements visible
uv run pytest tests/unit/test_foo.py -s

# Run only failed tests from last run
uv run pytest --lf
```

### Coverage Too Low

```bash
# See which lines are missing coverage
uv run pytest --cov=doctk --cov-report=term-missing

# Generate HTML report for detailed view
uv run pytest --cov=doctk --cov-report=html
# Open reports/coverage/html/index.html
```

### Ruff Errors

```bash
# See what's wrong
tox -e ruff

# Auto-fix most issues
tox -e ruff-fix

# Check again
tox -e ruff
```

### Merge Conflicts

```bash
# Update your branch with latest master
git checkout master
git pull origin master
git checkout feature/my-feature
git merge master

# Resolve conflicts in editor
# Test everything still works
uv run pytest

# Commit merge
git commit -m "chore: merge master"
```

## Best Practices

### Testing

- Write tests FIRST when fixing bugs (TDD)
- Test edge cases: empty inputs, null values, boundary conditions
- Use descriptive test names: `test_promote_heading_at_minimum_level`
- Keep tests fast - mock external dependencies
- Use fixtures for common test data

### Code Quality

- Type hints on all public functions
- Docstrings for all public APIs (Google style)
- Keep functions small and focused
- Avoid deep nesting (max 3 levels)
- Use meaningful variable names
- Follow existing code patterns

### Git Hygiene

- Commit frequently with clear messages
- Don't commit commented-out code
- Don't commit debug print statements
- Keep commits focused on one logical change
- Rebase locally to clean up history before pushing

### Documentation

- Update docs when changing public APIs
- Keep README.md current
- Update CHANGELOG.md for user-facing changes
- Add examples for new features
- Keep specs synchronized with code

## AI-Assisted Development Protocols

### Task Granularity

When working with AI agents on spec tasks:

- **One task per session**: AI should complete ONE task from tasks.md per interaction
- **Stop and verify**: After completing a task, stop and let human review before proceeding
- **No auto-continuation**: AI must NOT automatically move to next task without explicit approval
- **Checkpoint tasks**: Special tasks that require human verification before continuing

### AI Agent Handoff Protocol

When switching between AI agents or sessions:

```bash
# Before handoff, document current state
git status                    # What files changed?
git diff                      # What are the changes?
uv run pytest                 # Do tests pass?
grep -n "\- \[ \]" .kiro/specs/<spec>/tasks.md  # What's left?
```

**Handoff checklist:**

1. Current task status (complete/in-progress/blocked)
1. Test results (pass/fail with details)
1. Any blockers or questions for human
1. Next recommended task
1. Commit current work (even if incomplete)

### Context Preservation

To maintain context across AI sessions:

1. **Commit frequently** - Even incomplete work should be committed to feature branch
1. **Descriptive commit messages** - Explain what works and what doesn't
1. **Update tasks.md** - Mark partial progress with comments
1. **Document decisions** - Add comments in code explaining "why" not just "what"
1. **Leave breadcrumbs** - Use TODO comments for next session

Example task update:

```markdown
- [ ] 3. Implement graph model
  - [x] Create Node class
  - [x] Create Edge class
  - [ ] Implement graph traversal (IN PROGRESS: basic DFS works, need BFS)
  - [ ] Add cycle detection
```

### Verification Points

AI agents must verify at these points:

1. **After each task**: Run relevant tests
1. **Before marking complete**: Run full test suite
1. **Before pushing**: Run pre-push checklist
1. **After human feedback**: Re-run all checks

### AI Self-Check Protocol

Before marking a task complete, AI must verify:

```bash
# 1. Implementation matches design
# Review design.md section for this task

# 2. Requirements satisfied
# Check requirements.md acceptance criteria

# 3. Tests exist and pass
uv run pytest tests/unit/test_<feature>.py -v

# 4. Coverage adequate
uv run pytest --cov=doctk.<module> --cov-report=term-missing

# 5. No quality issues
tox -e ruff
tox -e docs

# 6. Spec references valid
uv run pytest tests/docs/test_spec_quality.py -v
```

### Human Review Triggers

AI must stop and request human review when:

1. **Ambiguity in specs**: Requirements or design unclear
1. **Design decisions needed**: Multiple valid approaches exist
1. **Test failures**: Can't resolve failing tests after 2 attempts
1. **Coverage gaps**: Can't reach 80% coverage
1. **Breaking changes**: Changes affect public APIs
1. **Security concerns**: Authentication, authorization, data handling
1. **Performance concerns**: Algorithm complexity, resource usage
1. **Spec conflicts**: Requirements contradict each other

### Error Recovery Protocol

When AI encounters errors:

**First attempt:**

1. Read error message carefully
1. Check relevant documentation
1. Try fix
1. Run tests

**Second attempt:**

1. Review design document
1. Check similar code in codebase
1. Try alternative approach
1. Run tests

**After 2 failed attempts:**

1. Document what was tried
1. Document error details
1. Commit current state
1. Request human assistance with specific question

### Spec Synchronization

AI must keep specs synchronized with code:

1. **Before implementation**: Verify spec references are current
1. **During implementation**: Update specs if design changes needed
1. **After implementation**: Validate specs match reality
1. **Run validation**: `uv run pytest tests/docs/test_spec_quality.py -v`

### Communication Protocol

AI should communicate clearly:

**Starting a task:**

```
Starting task 3.2: Implement graph traversal
- Reading design.md section on graph algorithms
- Will implement DFS and BFS
- Tests will be in tests/unit/test_graph.py
```

**Completing a task:**

```
Completed task 3.2: Implement graph traversal
✓ Implemented DFS and BFS algorithms
✓ Added 8 unit tests (all passing)
✓ Coverage: 95% for graph.py
✓ No ruff errors
✓ Updated tasks.md

Ready for review. Next task: 3.3 Add cycle detection
```

**Requesting help:**

```
Blocked on task 3.2: Implement graph traversal

Issue: BFS test failing with KeyError on line 45
Tried:
1. Added bounds checking - still fails
2. Reviewed similar code in operations.py - different pattern

Error: KeyError: 'visited' in graph.py:45
Need guidance on: Should visited set be passed or stored in Graph class?
```

## Summary

The workflow is simple:

1. **Branch** from master
1. **Develop** with tests and quality checks
1. **Push** small, testable pieces
1. **Review** and address all feedback
1. **Merge** when approved
1. **Clean up** and repeat

Quality is non-negotiable: 80% coverage, all tests pass, no lint errors, all reviews addressed.

### For AI Agents

- Complete ONE task at a time
- Stop after each task for human review
- Verify thoroughly before marking complete
- Request help after 2 failed attempts
- Keep specs synchronized with code
- Communicate clearly and specifically
