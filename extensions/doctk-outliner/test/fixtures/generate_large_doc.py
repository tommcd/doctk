#!/usr/bin/env python3
"""Generate a large Markdown document for performance testing.

Creates a document with configurable number of headings to test
the VSCode outliner extension's performance with large documents.
"""

import argparse
from pathlib import Path


def generate_large_document(num_headings: int, output_file: Path) -> None:
    """
    Generate a Markdown document with the specified number of headings.

    Args:
        num_headings: Total number of headings to generate
        output_file: Path to output Markdown file
    """
    with open(output_file, "w", encoding="utf-8") as f:
        # Write document title
        f.write("# Performance Test Document\n\n")
        f.write(f"This document contains {num_headings} headings for performance testing.\n\n")

        # Generate hierarchical structure
        # Create a balanced tree: h1 -> h2 -> h3 -> h4 -> h5 -> h6
        headings_per_level = {
            1: num_headings // 100,  # ~1% h1
            2: num_headings // 20,   # ~5% h2
            3: num_headings // 10,   # ~10% h3
            4: num_headings // 5,    # ~20% h4
            5: num_headings // 3,    # ~33% h5
        }
        # Level 6 gets the remaining headings
        headings_per_level[6] = num_headings - sum(headings_per_level.values())  # Remaining ~31%

        heading_count = 0

        for level in range(1, 7):
            for i in range(headings_per_level[level]):
                heading_count += 1
                hashes = "#" * level
                f.write(f"{hashes} Heading {heading_count} (Level {level})\n\n")
                f.write(f"This is content for heading {heading_count} at level {level}.\n")
                f.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n\n")

                # Stop if we've reached the target
                if heading_count >= num_headings:
                    break

            if heading_count >= num_headings:
                break

    print(f"✓ Generated {heading_count} headings in {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024:.2f} KB")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate large Markdown documents for performance testing"
    )
    parser.add_argument(
        "--headings",
        type=int,
        default=1500,
        help="Number of headings to generate (default: 1500)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "large_document.md",
        help="Output file path (default: large_document.md)",
    )

    args = parser.parse_args()

    generate_large_document(args.headings, args.output)


if __name__ == "__main__":
    main()
