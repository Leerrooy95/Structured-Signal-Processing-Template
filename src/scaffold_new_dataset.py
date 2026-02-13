#!/usr/bin/env python3
"""
scaffold_new_dataset.py - Generate a blank CSV with the Standard Schema headers.

Usage:
    python -m src.scaffold_new_dataset
    python src/scaffold_new_dataset.py

The script will ask you what you're tracking and create a correctly-formatted
blank CSV file so you don't have to remember or type the column headers manually.

The generated CSV follows the Data Schema Standard defined in docs/DATA_SCHEMA_STANDARD.md.
Column definitions and event types are loaded from config/settings.yaml.
"""

import os
import sys
from datetime import datetime

import pandas as pd

from src.config_loader import load_settings, get_logger

# ── Load config and logger ───────────────────────────────────────────────────
_settings = load_settings()
_schema = _settings["schema"]
_paths = _settings["paths"]

logger = get_logger("scaffold_new_dataset", _settings)

REQUIRED_COLUMNS = _schema["required_columns"]
RECOMMENDED_COLUMNS = _schema["recommended_columns"]
EVENT_TYPES = _schema["event_types"]


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
        logger.error("No entity name provided")
        print("Error: Entity name is required.")
        sys.exit(1)

    logger.info("Entity: %s", entity)

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

    logger.info("Selected event types: %s", selected_types)

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


def create_csv(entity, selected_types, use_recommended, filename, output_dir=None):
    """Create the blank CSV file with the correct headers."""
    columns = REQUIRED_COLUMNS[:]
    if use_recommended:
        columns.extend(RECOMMENDED_COLUMNS)

    # Create an empty DataFrame with the standard columns.
    df = pd.DataFrame(columns=columns)

    # Determine output path.
    base_dir = output_dir or _paths.get("output_dir", ".")
    output_path = os.path.join(base_dir, filename)

    df.to_csv(output_path, index=False)
    logger.info("Created dataset: %s (%d columns)", output_path, len(columns))

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
    print(f"  4. Run: python -m src.validate_dataset {filename}")
    print()


if __name__ == "__main__":
    main()
