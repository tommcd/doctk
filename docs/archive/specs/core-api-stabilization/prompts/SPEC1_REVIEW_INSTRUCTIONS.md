# Instructions for Reviewing Spec 1 (Core API Stabilization)

## For Human Reviewers

The design document for Spec 1 is complete and ready for review:

**Location:** `.kiro/specs/core-api-stabilization/design.md`

**What to Review:**

1. Requirements coverage (all 10 requirements, 52 acceptance criteria)
1. Technical soundness of the design
1. Implementation feasibility (9-week plan)
1. Risk mitigation strategies
1. Performance claims and budgets

## For AI Agent Reviewers (Claude, Gemini, Codex, Copilot)

**Copy the prompt from:** `.kiro/specs/core-api-stabilization/AI_REVIEW_PROMPT.txt`

Or use this prompt directly:

```
Please review the doctk Core API Stabilization design document.

Files to read:
1. .kiro/specs/core-api-stabilization/requirements.md (the requirements)
2. .kiro/specs/core-api-stabilization/design.md (the design to review)
3. .kiro/specs/core-api-stabilization/REVIEW_PROMPT.md (detailed review checklist)

Follow the review checklist in REVIEW_PROMPT.md and provide:
- Overall assessment (approve/changes needed/reject)
- Detailed findings with severity levels
- Requirements coverage matrix
- Open questions for clarification
- Final recommendation

Focus on:
- Completeness: Are all requirements addressed?
- Correctness: Are the technical solutions sound?
- Feasibility: Is the 9-week implementation plan realistic?
- Performance: Are the claimed improvements achievable?
- Risks: Are risks properly identified and mitigated?
```

**That's it!** Just paste the prompt above to any AI agent with access to this codebase.

## Expected Review Time

- **Human review**: 1-2 hours
- **AI agent review**: 5-10 minutes

## After Review

Once the design is approved:

1. Create tasks.md with detailed implementation tasks
1. Begin Phase 1 implementation (Stable Node Identity)

## Questions?

If you have questions about the design or review process, please ask!
