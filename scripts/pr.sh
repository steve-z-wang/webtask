#!/bin/bash
# PR checks - Run all checks or auto-fix issues
# Usage:
#   ./scripts/pr.sh       - Run checks only (same as CI)
#   ./scripts/pr.sh fix   - Auto-fix then run checks

set -e  # Exit on error

# Use local venv if available
if [ -d "venv" ]; then
    source venv/bin/activate
fi

if [ "$1" = "fix" ]; then
    echo "🔧 Auto-fixing issues..."
    echo ""
    echo "🎨 Running black (auto-format)..."
    black src/ tests/

    echo ""
    echo "🔧 Running ruff (auto-fix)..."
    ruff check --fix src/ tests/

    echo ""
    echo "✅ Auto-fix complete!"
    echo ""
fi

echo "🔍 Running PR checks..."
echo ""
echo "🔍 Running ruff (linter)..."
ruff check src/ tests/

echo ""
echo "🎨 Running black (formatter check)..."
black --check src/ tests/

echo ""
echo "🧪 Running tests..."
pytest tests/ -v --tb=short

echo ""
echo "✅ All PR checks passed!"
