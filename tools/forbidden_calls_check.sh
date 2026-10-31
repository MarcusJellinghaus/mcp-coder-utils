#!/bin/bash
# Check src for subprocess use outside the runner/streaming wrappers and git argv
#
# Usage from Git Bash: ./tools/forbidden_calls_check.sh

python tools/check_forbidden_calls.py "$@"
