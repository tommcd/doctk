# Steering Documents

This directory contains guidance documents that are automatically included in AI agent context when working on the doctk project.

## Core Documents

### For AI Agents

- **ai-agent-quick-reference.md** - Quick reference guide for AI agents

  - Golden rules (one task at a time, 80% coverage, etc.)
  - Task implementation checklist
  - Essential commands
  - Communication templates

- **workflow.md** - Complete development workflow

  - Branch strategy and PR process
  - Quality standards and coverage requirements
  - AI-assisted development protocols
  - Pre-push checklist and quality gates

- **spec-maintenance.md** - Spec quality and synchronization

  - Spec lifecycle and quality standards
  - Keeping specs synchronized with code
  - Validation and maintenance procedures

### Project Context

- **product.md** - Product overview and philosophy
- **tech.md** - Tech stack, tools, and common commands
- **structure.md** - Project organization and conventions
- **python-wsl-uv.md** - Python environment and WSL-specific rules
- **validate-spec-accuracy.md** - Spec validation testing guidelines

## How Steering Works

Steering documents are automatically included in AI agent context based on their frontmatter:

```yaml
---
title: Document Title
inclusion: always
---
```

- `inclusion: always` - Always included (default)
- `inclusion: manual` - Only when explicitly referenced with `#`
- `inclusion: fileMatch` - Included when specific files are in context

## Quick Start for AI Agents

1. **Read** `ai-agent-quick-reference.md` first
1. **Reference** `workflow.md` for complete workflow details
1. **Follow** the golden rules:
   - ONE TASK AT A TIME
   - NEVER PUSH TO MASTER
   - TEST BEFORE MARKING COMPLETE
   - 80% COVERAGE MINIMUM
   - STOP AFTER 2 FAILED ATTEMPTS

## Quick Start for Humans

1. Review `workflow.md` to understand the development process
1. Check `spec-maintenance.md` for spec quality standards
1. Use `tech.md` for common commands and tools
1. Reference `structure.md` for project organization

## Updating Steering Documents

When updating steering documents:

1. Make changes to the relevant `.md` file
1. Test that guidance is clear and actionable
1. Commit with message: `docs(steering): update <topic>`
1. Changes take effect immediately for new AI sessions

## Document Purposes

| Document | Purpose | Primary Audience |
|----------|---------|------------------|
| ai-agent-quick-reference.md | Quick reference for task execution | AI Agents |
| workflow.md | Complete development workflow | AI Agents & Humans |
| spec-maintenance.md | Spec quality and synchronization | AI Agents & Humans |
| product.md | Product overview and philosophy | Everyone |
| tech.md | Tech stack and commands | Everyone |
| structure.md | Project organization | Everyone |
| python-wsl-uv.md | Environment-specific rules | AI Agents |
| validate-spec-accuracy.md | Spec validation testing | AI Agents & Humans |

## Key Principles

1. **Quality over speed** - 80% coverage, all tests pass, no lint errors
1. **Incremental delivery** - Small, testable pieces of work
1. **Human oversight** - AI implements, humans review and approve
1. **Spec-driven** - Requirements → Design → Tasks → Implementation
1. **Automated validation** - Pre-commit hooks, CI/CD, spec validation

## Support

If steering documents are unclear or incomplete:

1. Create an issue describing the gap
1. Propose improvements
1. Update documents after approval
