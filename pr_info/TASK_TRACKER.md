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

### Step 1: Add notify-downstream workflow

See [step_1.md](./steps/step_1.md) for details.

- [ ] Implementation: create `.github/workflows/notify-downstream.yml` with the exact YAML content from step_1.md
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `Add notify-downstream workflow for cross-repo CI (#28)`

## Pull Request

- [ ] PR review
- [ ] PR summary

