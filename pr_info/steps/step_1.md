# Step 1: Add stdin piping support to stream_subprocess

**Ref:** [summary.md](summary.md) — single-step fix for issue #26

## Test (TDD — write first)

### WHERE
`tests/test_subprocess_streaming.py`

### WHAT
Add a new test class `TestStreamStdinInput` with one test:

```python
def test_stream_subprocess_pipes_input_data_to_stdin(self) -> None
```

### HOW
- Import `CommandOptions` from `mcp_coder_utils.subprocess_runner`
- Launch a Python script that reads stdin and echoes it to stdout
- Pass `CommandOptions(input_data="hello from stdin")` to `stream_subprocess`
- Assert the echoed text appears in streamed lines

### ALGORITHM
```
script = "import sys; data = sys.stdin.read(); print(data)"
options = CommandOptions(input_data="hello from stdin")
result = stream_subprocess([sys.executable, "-c", script], options=options)
lines = list(result)
assert "hello from stdin" in lines
assert result.result.return_code == 0
```

### DATA
- Input: `CommandOptions(input_data="hello from stdin")`
- Output: streamed lines containing `"hello from stdin"`, return code 0

---

## Implementation

### WHERE
`src/mcp_coder_utils/subprocess_streaming.py` — inside `_generate()` inner function

### WHAT
Two changes to `_generate()`:

1. Set `stdin` argument in `Popen` call
2. Write `input_data` and close stdin before the stdout read loop

### HOW
No new imports, functions, or exports needed. Changes are local to `_generate()`.

### ALGORITHM
```
# Before Popen call:
stdin_pipe = subprocess.PIPE if options.input_data else subprocess.DEVNULL

# In Popen call:
process = subprocess.Popen(..., stdin=stdin_pipe, ...)

# After Popen, before stderr drain / stdout read loop:
if options.input_data and process.stdin:
    process.stdin.write(options.input_data)
    process.stdin.close()
```

### DATA
- No new data structures or return values
- `stdin` kwarg: `subprocess.PIPE | subprocess.DEVNULL`

---

## Commit
Single commit: test + fix, all checks passing.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1:
1. Add the test class TestStreamStdinInput with one test to tests/test_subprocess_streaming.py
2. Fix _generate() in src/mcp_coder_utils/subprocess_streaming.py to pipe input_data to stdin
3. Run all code quality checks (pylint, pytest, mypy) and fix any issues
```
