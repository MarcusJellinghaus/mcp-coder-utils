# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Update settings.local.json, CLAUDE.md, and refactoring_principles

- [x] Implementation: update `settings.local.json` permissions, restructure CLAUDE.md git section, update refactoring_principles.md reference ([step_1.md](steps/step_1.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Update commit_push and plan_review skills

- [x] Implementation: swap bash git entries for MCP tools in frontmatter and body of both skill files ([step_2.md](steps/step_2.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Update implementation_review, rebase skill, rebase design doc, and implementation_review_supervisor

- [x] Implementation: swap bash git entries for MCP tools in frontmatter and body of all four files ([step_3.md](steps/step_3.md))
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [x] PR review: verify all steps complete and no bash git references remain for status/diff/log
- [ ] PR summary prepared
