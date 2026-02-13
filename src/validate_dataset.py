#!/usr/bin/env python3
"""
validate_dataset.py - Scan a CSV file and flag dirty data.

Usage:
    python src/validate_dataset.py path/to/dataset.csv

Checks performed:
    1. Missing required columns (date, entity, event_type, source_url, verification_status)
    2. Dates in the future (potential hallucinations)
    3. Invalid date formats (not YYYY-MM-DD)
    4. Missing source_url entries
    5. Empty required fields
    6. Invalid verification_status values
    7. Duplicate rows

Exit codes:
    0 - All checks passed (warnings may still exist)
    1 - Critical issues found (missing columns or >20% of rows have errors)
    2 - File not found or unreadable
"""

import sys
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd


# ── Standard Schema ──────────────────────────────────────────────────────────
REQUIRED_COLUMNS = ["date", "entity", "event_type", "source_url", "verification_status"]
VALID_VERIFICATION = {"Verified", "Unverified", "Debunked"}


def load_csv(filepath):
    """Load a CSV file and return the DataFrame."""
    try:
        df = pd.read_csv(filepath, dtype=str)  # Read everything as strings for validation.
        return df
    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}")
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: Could not read {filepath}: {e}")
        sys.exit(2)


def check_required_columns(df):
    """Check that all required columns exist."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    issues = []
    if missing:
        issues.append({
            "severity": "CRITICAL",
            "check": "required_columns",
            "message": f"Missing required columns: {', '.join(missing)}",
            "rows": [],
        })
    return issues


def check_date_format(df):
    """Check that dates are in YYYY-MM-DD format."""
    if "date" not in df.columns:
        return []

    issues = []
    bad_rows = []
    for idx, val in df["date"].items():
        if pd.isna(val) or val.strip() == "":
            continue  # Handled by empty-field check.
        try:
            datetime.strptime(val.strip(), "%Y-%m-%d")
        except ValueError:
            bad_rows.append(idx)

    if bad_rows:
        issues.append({
            "severity": "ERROR",
            "check": "date_format",
            "message": f"{len(bad_rows)} row(s) have dates not in YYYY-MM-DD format.",
            "rows": bad_rows,
        })
    return issues


def check_future_dates(df):
    """Flag dates that are in the future (possible hallucinations)."""
    if "date" not in df.columns:
        return []

    issues = []
    today = datetime.now().date()
    future_rows = []
    for idx, val in df["date"].items():
        if pd.isna(val) or val.strip() == "":
            continue
        try:
            d = datetime.strptime(val.strip(), "%Y-%m-%d").date()
            if d > today:
                future_rows.append(idx)
        except ValueError:
            pass  # Already caught by date_format check.

    if future_rows:
        issues.append({
            "severity": "WARNING",
            "check": "future_dates",
            "message": f"{len(future_rows)} row(s) have dates in the future (after {today}).",
            "rows": future_rows,
        })
    return issues


def check_missing_source_urls(df):
    """Flag rows where source_url is missing or empty."""
    if "source_url" not in df.columns:
        return []

    issues = []
    missing_rows = []
    for idx, val in df["source_url"].items():
        if pd.isna(val) or val.strip() == "":
            missing_rows.append(idx)

    if missing_rows:
        issues.append({
            "severity": "ERROR",
            "check": "missing_source_url",
            "message": f"{len(missing_rows)} row(s) are missing a source_url.",
            "rows": missing_rows,
        })
    return issues


def check_invalid_urls(df):
    """Flag source_urls that don't look like valid URLs."""
    if "source_url" not in df.columns:
        return []

    issues = []
    bad_rows = []
    for idx, val in df["source_url"].items():
        if pd.isna(val) or val.strip() == "":
            continue  # Handled by missing check.
        parsed = urlparse(val.strip())
        if not parsed.scheme or not parsed.netloc:
            bad_rows.append(idx)

    if bad_rows:
        issues.append({
            "severity": "WARNING",
            "check": "invalid_urls",
            "message": f"{len(bad_rows)} row(s) have source_urls that don't look like valid URLs.",
            "rows": bad_rows,
        })
    return issues


def check_empty_required_fields(df):
    """Flag rows where any required column is empty."""
    issues = []
    present_required = [col for col in REQUIRED_COLUMNS if col in df.columns]

    for col in present_required:
        empty_rows = []
        for idx, val in df[col].items():
            if pd.isna(val) or val.strip() == "":
                empty_rows.append(idx)
        if empty_rows:
            issues.append({
                "severity": "ERROR",
                "check": f"empty_{col}",
                "message": f"{len(empty_rows)} row(s) have an empty '{col}' field.",
                "rows": empty_rows,
            })
    return issues


def check_verification_status(df):
    """Flag rows with non-standard verification_status values."""
    if "verification_status" not in df.columns:
        return []

    issues = []
    bad_rows = []
    bad_values = set()
    for idx, val in df["verification_status"].items():
        if pd.isna(val) or val.strip() == "":
            continue  # Handled by empty-field check.
        if val.strip() not in VALID_VERIFICATION:
            bad_rows.append(idx)
            bad_values.add(val.strip())

    if bad_rows:
        issues.append({
            "severity": "WARNING",
            "check": "verification_status",
            "message": (
                f"{len(bad_rows)} row(s) have non-standard verification_status values. "
                f"Expected one of {VALID_VERIFICATION}. "
                f"Found: {bad_values}"
            ),
            "rows": bad_rows,
        })
    return issues


def check_duplicates(df):
    """Flag fully duplicate rows."""
    issues = []
    dup_mask = df.duplicated(keep="first")
    dup_rows = list(df[dup_mask].index)
    if dup_rows:
        issues.append({
            "severity": "WARNING",
            "check": "duplicates",
            "message": f"{len(dup_rows)} duplicate row(s) found.",
            "rows": dup_rows,
        })
    return issues


def print_report(filepath, df, all_issues):
    """Print a formatted validation report."""
    print()
    print("=" * 70)
    print(f"  VALIDATION REPORT: {filepath}")
    print(f"  Rows: {len(df)}  |  Columns: {len(df.columns)}")
    print("=" * 70)

    if not all_issues:
        print("\n  All checks passed. No issues found.\n")
        return 0

    # Group by severity.
    critical = [i for i in all_issues if i["severity"] == "CRITICAL"]
    errors = [i for i in all_issues if i["severity"] == "ERROR"]
    warnings = [i for i in all_issues if i["severity"] == "WARNING"]

    for severity, group, symbol in [
        ("CRITICAL", critical, "!!!"),
        ("ERROR", errors, " X "),
        ("WARNING", warnings, " ! "),
    ]:
        if not group:
            continue
        print(f"\n  [{severity}]")
        for issue in group:
            print(f"    {symbol} {issue['message']}")
            # Show up to 5 example rows.
            if issue["rows"]:
                example_rows = issue["rows"][:5]
                row_nums = ", ".join(str(r + 2) for r in example_rows)  # +2 for header + 0-index.
                suffix = f" (and {len(issue['rows']) - 5} more)" if len(issue["rows"]) > 5 else ""
                print(f"        Rows: {row_nums}{suffix}")

    # Summary.
    total_error_rows = set()
    for issue in all_issues:
        total_error_rows.update(issue["rows"])

    error_rate = len(total_error_rows) / len(df) * 100 if len(df) > 0 else 0
    print(f"\n  Summary: {len(total_error_rows)}/{len(df)} rows ({error_rate:.1f}%) have issues.")
    print()

    # Determine exit code.
    if critical or error_rate > 20:
        return 1
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/validate_dataset.py <path_to_csv>")
        print()
        print("Example:")
        print("  python src/validate_dataset.py My_Datasets_as_Examples/BlackRock_Timeline_Full_Decade.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    df = load_csv(filepath)

    # Run all checks.
    all_issues = []
    all_issues.extend(check_required_columns(df))
    all_issues.extend(check_date_format(df))
    all_issues.extend(check_future_dates(df))
    all_issues.extend(check_missing_source_urls(df))
    all_issues.extend(check_invalid_urls(df))
    all_issues.extend(check_empty_required_fields(df))
    all_issues.extend(check_verification_status(df))
    all_issues.extend(check_duplicates(df))

    exit_code = print_report(filepath, df, all_issues)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
