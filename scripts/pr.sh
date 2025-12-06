#!/bin/bash
# PR checks - Auto-fix formatting and run all checks
# Usage:
#   ./scripts/pr.sh - Auto-fix then run checks

set -e  # Exit on error

# Use local venv if available
if [ -d "venv" ]; then
    source venv/bin/activate
fi

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
echo "🔍 Running PR checks..."
echo ""
echo "🔍 Running ruff (linter)..."
ruff check src/ tests/

echo ""
echo "🎨 Running black (formatter check)..."
black --check src/ tests/

echo ""
echo "🧪 Running unit tests..."
pytest tests/unit/ -v --tb=short -m unit

echo ""
echo "🧪 Running integration tests..."
pytest tests/integration/ -v --tb=short -m integration -n auto

echo ""
echo "✅ All PR checks passed!"
