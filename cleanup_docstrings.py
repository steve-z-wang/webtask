#!/usr/bin/env python3
"""Script to clean up verbose docstrings by removing Args/Returns sections."""

import re
from pathlib import Path


def clean_docstring(content: str) -> str:
    """Remove Args/Returns sections from docstrings while keeping the main description."""

    # Pattern to match docstrings with Args/Returns sections
    # Matches: """Description...\n\n        Args:\n            ...\n\n        Returns:\n            ...\n        """
    pattern = r'("""[^"]*?)\n\s+Args:.*?(?=\n\s+"""|\n\s+Returns:.*?""")'

    # First pass: Remove Args section and everything until Returns or end
    content = re.sub(
        r'("""[^"]*?)\n\s+Args:.*?(?=\n\s+Returns:)',
        r'\1',
        content,
        flags=re.DOTALL
    )

    # Second pass: Remove Returns section
    content = re.sub(
        r'("""[^"]*?)\n\s+Returns:.*?(?=""")',
        r'\1\n        ',
        content,
        flags=re.DOTALL
    )

    # Third pass: Clean up any remaining standalone Args/Returns
    content = re.sub(
        r'\n\s+(?:Args|Returns):.*?(?=\n\s{0,8}[a-z_]|\n\s{0,8}""")',
        '',
        content,
        flags=re.DOTALL
    )

    return content


def process_file(file_path: Path) -> bool:
    """Process a single Python file to clean up docstrings.

    Returns True if file was modified.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # Clean the docstrings
        cleaned = clean_docstring(content)

        # Only write if content changed
        if cleaned != original:
            file_path.write_text(cleaned, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files under _internal."""

    # Get the _internal directory
    base_dir = Path(__file__).parent / "src" / "webtask" / "_internal"

    if not base_dir.exists():
        print(f"Directory not found: {base_dir}")
        return

    # Find all Python files
    py_files = list(base_dir.rglob("*.py"))

    print(f"Found {len(py_files)} Python files under {base_dir}")
    print("Processing...")

    modified_count = 0
    for py_file in py_files:
        if process_file(py_file):
            modified_count += 1
            print(f"  ✓ Cleaned: {py_file.relative_to(base_dir)}")

    print(f"\nDone! Modified {modified_count} files.")


if __name__ == "__main__":
    main()
