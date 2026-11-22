# Step 3 — Docs: "no git knowledge" rule and README `fs` row

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step
(`pr_info/steps/step_3.md`) exactly. Docs only, no code or tests. Use the MCP
tools listed in `.claude/CLAUDE.md`. One commit for the whole step.

## Precondition

`src/mcp_coder_utils/fs/__init__.py` exports `count_line_endings`,
`dominant_newline`, `write_text` and `check_path_within` (steps 1 and 2
done). If not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `docs/architecture/architecture.md` — rule 1
- `.claude/CLAUDE.md` — "Architectural rules", first bullet
- `README.md` — Modules table, `fs` row

## WHAT / HOW

- `architecture.md` rule 1: append the sentence
  "No git knowledge (git belongs in mcp-workspace)." after the
  ecosystem sentence.
- `.claude/CLAUDE.md` first bullet becomes:
  `- Pure Python, language-agnostic. No ecosystem knowledge (no \`pyproject.toml\` parsing, no venv, no \`.csproj\`, no SQL). No git knowledge (git belongs in mcp-workspace).`
- README `fs` row:
  `| \`fs\` | Read a file as UTF-8 with a latin-1 fallback; count line endings, pick the dominant one and write UTF-8 text with a chosen ending; check that a path stays within a root (\`read_file\`, \`normalize_line_endings\`, \`count_line_endings\`, \`dominant_newline\`, \`write_text\`, \`check_path_within\`, \`normalize_path\`). |`

## ALGORITHM / DATA

None (docs only).

## Checks

`run_pytest_check` (`extra_args: ["-n", "auto"]`) to confirm nothing broke,
then `run_format_code`.
Commit message: `docs: add no-git-knowledge rule, update fs README row (#69)`.
