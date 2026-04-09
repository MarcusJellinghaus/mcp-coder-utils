The CI pipeline failed on the pylint job due to two W1404 (implicit-str-concat) warnings, which are treated as errors by the project's pylint configuration. Pylint exited with code 4, indicating warnings were found.

The first issue is in tests/test_subprocess_runner.py at line 457, inside the test_python_subprocess_timeout method. The call to write_text() uses implicit string concatenation across multiple adjacent string literals: `"import time\n" "time.sleep(10)\n" "print('Should not reach here')\n"`. While Python allows adjacent string literals to concatenate automatically, pylint flags this as error-prone, especially inside function call arguments where a missing comma could silently merge unrelated strings.

The second issue is in tests/test_subprocess_streaming.py at line 19, inside the test_stream_inactivity_timeout_kills_process method. The variable assignment uses the same pattern: `"import sys, time; " "print('start', flush=True); " "time.sleep(60)"`.

Both issues require the same fix: replace the implicit string concatenation with explicit concatenation (using the `+` operator) or combine the adjacent literals into a single string. The simplest fix is to merge each set of adjacent string literals into one continuous string, since they are intentionally concatenated to build inline Python scripts.
