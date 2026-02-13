#!/usr/bin/env python3
"""
scaffold_new_dataset.py - Generate a blank CSV with the Standard Schema headers.

Usage:
    python src/scaffold_new_dataset.py

The script will ask you what you're tracking and create a correctly-formatted
blank CSV file so you don't have to remember or type the column headers manually.

The generated CSV follows the Data Schema Standard defined in docs/DATA_SCHEMA_STANDARD.md.
"""

import os
import sys
from datetime import datetime

import pandas as pd


# ── Standard Schema columns ──────────────────────────────────────────────────
# Required columns that every dataset must have.
REQUIRED_COLUMNS = [
    "date",                  # ISO 8601 (YYYY-MM-DD)
    "entity",                # What/who is being tracked
    "event_type",            # Classification (Policy, Financial, Legal, etc.)
    "source_url",            # Link to the primary source
    "verification_status",   # Verified / Unverified / Debunked
]

# Recommended columns that add useful context.
RECOMMENDED_COLUMNS = [
    "year",                  # Extracted from date, useful for grouping
    "title",                 # Short label for the event
    "snippet",              # Brief excerpt from the source
    "category",              # Higher-level grouping
    "country",               # Country relevant to the event
    "date_confidence",       # High / Medium / Low
    "date_scraped",          # When this row was collected
    "notes",                 # Anything else
]

# Valid event types from the standard.
EVENT_TYPES = [
    "Policy",
    "Financial",
    "Legal",
    "Appointment",
    "Statement",
    "Temporal_Anchor",
    "Crisis",
    "Technology",
]


def prompt_user():
    """Ask the user a few questions to configure the new dataset."""
    print("=" * 60)
    print("  OSINT Dataset Scaffolder")
    print("  Generates a blank CSV with the Standard Schema headers.")
    print("=" * 60)
    print()

    # ── What are you tracking? ────────────────────────────────────────────
    entity = input("What entity are you tracking? (e.g., BlackRock, DHS, FDA): ").strip()
    if not entity:
        print("Error: Entity name is required.")
        sys.exit(1)

    # ── What kind of events? ──────────────────────────────────────────────
    print("\nAvailable event types:")
    for i, et in enumerate(EVENT_TYPES, 1):
        print(f"  {i}. {et}")
    print(f"  {len(EVENT_TYPES) + 1}. All of the above")
    print(f"  {len(EVENT_TYPES) + 2}. Custom (you'll type your own)")

    choice = input("\nWhich event types will you track? (comma-separated numbers): ").strip()
    selected_types = []
    for c in choice.split(","):
        c = c.strip()
        if not c.isdigit():
            continue
        idx = int(c)
        if idx == len(EVENT_TYPES) + 1:
            selected_types = EVENT_TYPES[:]
            break
        elif idx == len(EVENT_TYPES) + 2:
            custom = input("Enter your custom event types (comma-separated): ").strip()
            selected_types.extend([t.strip() for t in custom.split(",") if t.strip()])
        elif 1 <= idx <= len(EVENT_TYPES):
            selected_types.append(EVENT_TYPES[idx - 1])

    if not selected_types:
        selected_types = EVENT_TYPES[:]
        print("No valid selection - defaulting to all event types.")

    # ── Include recommended columns? ──────────────────────────────────────
    include_recommended = (
        input("\nInclude recommended columns (year, title, snippet, etc.)? [Y/n]: ")
        .strip()
        .lower()
    )
    use_recommended = include_recommended != "n"

    # ── Output file ───────────────────────────────────────────────────────
    safe_name = entity.lower().replace(" ", "_").replace("/", "_")
    default_filename = f"{safe_name}_dataset_{datetime.now().strftime('%Y%m%d')}.csv"
    filename = input(f"\nOutput filename [{default_filename}]: ").strip()
    if not filename:
        filename = default_filename

    # Ensure .csv extension.
    if not filename.endswith(".csv"):
        filename += ".csv"

    return entity, selected_types, use_recommended, filename


def create_csv(entity, selected_types, use_recommended, filename):
    """Create the blank CSV file with the correct headers."""
    columns = REQUIRED_COLUMNS[:]
    if use_recommended:
        columns.extend(RECOMMENDED_COLUMNS)

    # Create an empty DataFrame with the standard columns.
    df = pd.DataFrame(columns=columns)

    # Determine output path: put it in the current working directory.
    output_path = os.path.join(os.getcwd(), filename)

    df.to_csv(output_path, index=False)

    return output_path, columns, selected_types


def main():
    entity, selected_types, use_recommended, filename = prompt_user()
    output_path, columns, selected_types = create_csv(
        entity, selected_types, use_recommended, filename
    )

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"  Created: {output_path}")
    print(f"  Entity:  {entity}")
    print(f"  Columns: {len(columns)}")
    print(f"  Event types to use: {', '.join(selected_types)}")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"  1. Open {filename} in your editor or spreadsheet tool.")
    print(f"  2. Add rows - one event per row.")
    print(f"  3. Set verification_status to 'Unverified' for new entries.")
    print(f"  4. Run: python src/validate_dataset.py {filename}")
    print()


if __name__ == "__main__":
    main()
