---
title: Spec Maintenance and Quality
inclusion: always
---

# Spec Maintenance and Quality

Guidelines for maintaining high-quality, synchronized specs throughout the development lifecycle.

## Spec Lifecycle

```
Idea → Requirements → Design → Tasks → Implementation → Validation → Complete
                                  ↑                           ↓
                                  └───── Feedback Loop ───────┘
```

### Phase 1: Creation

**Requirements Phase:**

- Define WHAT needs to be built
- Write user stories and acceptance criteria
- Use EARS format (WHEN/WHILE/IF/WHERE/THE system SHALL)
- Get human approval before proceeding

**Design Phase:**

- Define HOW it will be built
- Specify architecture, components, data models
- Define correctness properties for testing
- Get human approval before proceeding

**Tasks Phase:**

- Break design into discrete implementation steps
- Order tasks for incremental progress
- Reference requirements in each task
- Get human approval before implementation

### Phase 2: Implementation

**During Implementation:**

- Follow tasks in order
- One task per AI session
- Stop for human review after each task
- Update tasks.md as you progress

**Spec Synchronization:**

- Keep specs aligned with actual code
- Update specs when design changes
- Document why changes were needed
- Validate specs after changes

### Phase 3: Completion

**Validation:**

- All tasks marked complete
- All tests passing (≥80% coverage)
- Spec validation passes
- Documentation updated

**Archival:**

- Mark spec as complete in tasks.md
- Add completion date
- Link to merged PRs
- Move to completed specs (optional)

## Spec Quality Standards

### Requirements Quality

**Good requirements:**

- Follow EARS patterns exactly
- Are testable and measurable
- Use defined terms from glossary
- Are unambiguous
- Focus on WHAT, not HOW

**Bad requirements:**

- Vague terms ("quickly", "efficiently")
- Escape clauses ("where possible")
- Implementation details (HOW instead of WHAT)
- Untestable statements
- Ambiguous language

### Design Quality

**Good design:**

- Addresses all requirements
- Specifies concrete architecture
- Defines clear interfaces
- Includes correctness properties
- Considers error handling
- Provides testing strategy

**Bad design:**

- Missing requirements coverage
- Vague architecture
- No error handling plan
- No testing strategy
- Unclear interfaces

### Task Quality

**Good tasks:**

- One clear objective per task
- References specific requirements
- Builds on previous tasks
- Includes verification steps
- Appropriate granularity (2-4 hours)

**Bad tasks:**

- Multiple objectives mixed together
- No requirement references
- Unclear dependencies
- Too large (>1 day) or too small (\<30 min)
- Missing verification steps

## Keeping Specs Synchronized

### When Code Diverges from Spec

This happens! It's normal. When it does:

1. **Identify the divergence**

   - What changed?
   - Why did it change?
   - Is the change better than the spec?

1. **Decide on action**

   - Update spec to match code (if code is better)
   - Update code to match spec (if spec is correct)
   - Discuss with human (if unclear)

1. **Update the spec**

   - Modify requirements/design/tasks as needed
   - Document why change was made
   - Get human approval for spec changes

1. **Validate synchronization**

   ```bash
   uv run pytest tests/docs/test_spec_quality.py -v
   ```

### Spec Change Process

```bash
# 1. Create issue documenting need for change
gh issue create --title "Spec: Update <spec> for <reason>"

# 2. Update spec documents
# Edit .kiro/specs/<spec>/requirements.md (if needed)
# Edit .kiro/specs/<spec>/design.md (if needed)
# Edit .kiro/specs/<spec>/tasks.md (if needed)

# 3. Commit spec changes
git add .kiro/specs/<spec>/
git commit -m "docs(spec): update <spec> for <reason>

Changed: <what changed>
Reason: <why it changed>
Impact: <affected code>

Closes #<issue>"

# 4. Continue implementation with updated spec
```

## Spec Validation

### Automated Validation

Run before every push that touches specs:

```bash
uv run pytest tests/docs/test_spec_quality.py -v
```

This checks:

1. **File references exist** - All mentioned files actually exist
1. **API references exist** - All mentioned classes/methods exist
1. **Line numbers valid** - Line references don't exceed file length

### Manual Validation

Periodically review:

1. **Completeness** - Do specs cover all implemented features?
1. **Accuracy** - Do specs match actual code?
1. **Clarity** - Are specs understandable?
1. **Consistency** - Do specs use consistent terminology?

### Validation Checklist

- [ ] All file paths in spec exist or marked [PLANNED]
- [ ] All API references exist or marked [TODO]
- [ ] All line numbers are accurate or marked [APPROXIMATE]
- [ ] All requirements have corresponding design sections
- [ ] All design sections have corresponding tasks
- [ ] All tasks reference requirements
- [ ] Glossary terms are used consistently
- [ ] No broken links or references

## Common Spec Issues

### Issue: Outdated File References

**Problem:** Spec references `src/old_name.py` but file was renamed to `src/new_name.py`

**Solution:**

```bash
# Find all references
grep -r "old_name.py" .kiro/specs/

# Update all references
# Or mark as [PLANNED] if file doesn't exist yet
```

### Issue: Missing API References

**Problem:** Spec references `MyClass.my_method()` but method doesn't exist

**Solution:**

1. Check if method was renamed
1. Update spec to use correct name
1. Or implement the missing method
1. Or mark as [TODO] if planned

### Issue: Spec-Code Mismatch

**Problem:** Design says to use approach A, but code uses approach B

**Solution:**

1. Determine which is better
1. If code is better: update spec, document why
1. If spec is better: update code
1. If unclear: ask human

### Issue: Incomplete Tasks

**Problem:** Task marked complete but tests don't exist

**Solution:**

1. Unmark task as complete
1. Write missing tests
1. Verify tests pass
1. Re-mark as complete

## Spec Maintenance Schedule

### After Each Task

- [ ] Update tasks.md with completion status
- [ ] Verify task matches implementation
- [ ] Update design if approach changed

### After Each PR

- [ ] Run spec validation
- [ ] Fix any validation errors
- [ ] Update completion status
- [ ] Document any spec changes in PR

### Monthly Review

- [ ] Review all active specs
- [ ] Check for outdated references
- [ ] Update completion percentages
- [ ] Archive completed specs

### Before Release

- [ ] Validate all specs
- [ ] Ensure all references current
- [ ] Update documentation links
- [ ] Mark completed specs

## Spec Templates

### Adding New Spec

```bash
# Create spec directory
mkdir -p .kiro/specs/<spec-name>

# Create documents from templates
# (Templates should exist in .kiro/templates/)
cp .kiro/templates/requirements-template.md .kiro/specs/<spec-name>/requirements.md
cp .kiro/templates/design-template.md .kiro/specs/<spec-name>/design.md
cp .kiro/templates/tasks-template.md .kiro/specs/<spec-name>/tasks.md

# Edit documents
# Get human approval for each phase
```

### Marking Spec Complete

Add to bottom of tasks.md:

```markdown
## Completion Status

- **Status**: Complete
- **Completion Date**: YYYY-MM-DD
- **Final Coverage**: XX%
- **Related PRs**: #123, #124, #125
- **Documentation**: docs/guides/<guide>.md

All requirements satisfied and validated.
```

## Best Practices

### For AI Agents

1. **Read specs completely** before starting any task
1. **Reference specs constantly** during implementation
1. **Update specs immediately** when changes needed
1. **Validate specs** before marking tasks complete
1. **Document divergences** when code differs from spec

### For Humans

1. **Review spec changes** carefully before approving
1. **Keep specs realistic** - don't over-specify
1. **Update specs proactively** - don't let them drift
1. **Use specs for onboarding** - they document decisions
1. **Archive completed specs** - keep workspace clean

### For Everyone

1. **Specs are living documents** - they evolve with code
1. **Specs are source of truth** - code should match specs
1. **Specs enable collaboration** - AI and humans work from same plan
1. **Specs reduce rework** - catch issues in design phase
1. **Specs preserve knowledge** - document why decisions were made

## Troubleshooting

### Spec validation failing

```bash
# Run validation
uv run pytest tests/docs/test_spec_quality.py -v

# Read error messages carefully
# Fix each issue:
# - Create missing files
# - Update incorrect references
# - Mark planned items with [PLANNED]
# - Mark TODOs with [TODO]

# Re-run until passing
```

### Can't find spec for feature

```bash
# List all specs
ls -la .kiro/specs/

# Search for feature name
grep -r "feature name" .kiro/specs/

# If not found, may need to create new spec
```

### Spec conflicts with code

1. Determine which is correct
1. Update the incorrect one
1. Document why in commit message
1. Get human approval if significant change

## Summary

- Specs are living documents that evolve with code
- Keep specs synchronized through validation
- Update specs when code diverges
- One spec per feature, one feature per branch
- Validate before every push that touches specs
- Quality specs enable quality code
