#!/usr/bin/env bash
# Run tach module dependency check
# Configuration is in tach.toml
#
# Usage from Git Bash: ./tools/tach_check.sh

set -e

if ! command -v tach &> /dev/null; then
    echo "ERROR: tach not found. Install with: uv pip install tach"
    exit 1
fi

echo "Running tach module dependency check..."
tach check "$@"
