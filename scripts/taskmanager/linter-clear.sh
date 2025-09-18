#!/bin/bash

# Ultra-fast linter feedback clear - pure bash
# Usage: ./linter-clear-fast.sh

set -e

echo "🧹 Clearing linter feedback..."

# Check if TODO.json exists
if [[ ! -f "TODO.json" ]]; then
    echo "❌ TODO.json not found"
    exit 1
fi

# Check if linter feedback exists and remove it
if grep -q "pending_linter_feedback" TODO.json; then
    # Remove the pending_linter_feedback field using sed
    sed -i.bak '/pending_linter_feedback/d' TODO.json
    echo "✅ Linter feedback cleared"
else
    echo "ℹ️ No pending linter feedback found"
fi