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

### Step 1: Amend the toolkit contract and document it

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code): `tests/test_toolkit.py`, `src/mcp_coder_utils/toolkit.py`, `vulture_whitelist.py`, `README.md`
- [x] Quality checks: pylint, pytest, mypy, vulture — fix all issues
- [x] Commit message prepared in `pr_info/.commit_message.txt`

## Pull Request

- [ ] PR review: review all changes on the branch against `pr_info/steps/summary.md`
- [ ] PR summary: prepare the title and description, including the merge order with mcp-tools-py#272
