#!/usr/bin/env python3
"""
validate_dataset.py - Scan a CSV file and flag dirty data.

Usage:
    python -m src.validate_dataset path/to/dataset.csv
    python src/validate_dataset.py path/to/dataset.csv

Checks performed:
    1. Missing required columns (from config/settings.yaml)
    2. Dates in the future (potential hallucinations)
    3. Invalid date formats (not matching configured format)
    4. Missing source_url entries
    5. Empty required fields
    6. Invalid verification_status values
    7. Duplicate rows

Exit codes:
    0 - All checks passed (warnings may still exist)
    1 - Critical issues found (missing columns or error rate exceeds threshold)
    2 - File not found or unreadable
"""

import sys
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd

from src.config_loader import load_settings, get_logger

# ── Load config and logger ───────────────────────────────────────────────────
_settings = load_settings()
_schema = _settings["schema"]
_validation = _settings["validation"]

logger = get_logger("validate_dataset", _settings)

REQUIRED_COLUMNS = _schema["required_columns"]
VALID_VERIFICATION = set(_schema["valid_verification_statuses"])
DATE_FORMAT = _validation["date_format"]
ERROR_RATE_THRESHOLD = _validation["error_rate_threshold"]


def load_csv(filepath):
    """Load a CSV file and return the DataFrame."""
    try:
        df = pd.read_csv(filepath, dtype=str)  # Read everything as strings for validation.
        logger.info("Loaded %s (%d rows, %d columns)", filepath, len(df), len(df.columns))
        return df
    except FileNotFoundError:
        logger.error("File not found: %s", filepath)
        sys.exit(2)
    except Exception as e:
        logger.error("Could not read %s: %s", filepath, e)
        sys.exit(2)


def check_required_columns(df):
    """Check that all required columns exist."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    issues = []
    if missing:
        logger.warning("Missing required columns: %s", ", ".join(missing))
        issues.append({
            "severity": "CRITICAL",
            "check": "required_columns",
            "message": f"Missing required columns: {', '.join(missing)}",
            "rows": [],
        })
    return issues


def check_date_format(df):
    """Check that dates match the configured format."""
    if "date" not in df.columns:
        return []

    issues = []
    bad_rows = []
    for idx, val in df["date"].items():
        if pd.isna(val) or val.strip() == "":
            continue  # Handled by empty-field check.
        try:
            datetime.strptime(val.strip(), DATE_FORMAT)
        except ValueError:
            bad_rows.append(idx)

    if bad_rows:
        logger.warning("%d row(s) have dates not in %s format", len(bad_rows), DATE_FORMAT)
        issues.append({
            "severity": "ERROR",
            "check": "date_format",
            "message": f"{len(bad_rows)} row(s) have dates not in {DATE_FORMAT} format.",
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
            d = datetime.strptime(val.strip(), DATE_FORMAT).date()
            if d > today:
                future_rows.append(idx)
        except ValueError:
            pass  # Already caught by date_format check.

    if future_rows:
        logger.warning("%d row(s) have dates in the future (after %s)", len(future_rows), today)
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
        logger.warning("%d row(s) are missing a source_url", len(missing_rows))
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
        logger.warning("%d row(s) have invalid source_urls", len(bad_rows))
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
            logger.warning("%d row(s) have an empty '%s' field", len(empty_rows), col)
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
        logger.warning(
            "%d row(s) have non-standard verification_status: %s",
            len(bad_rows), bad_values
        )
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
        logger.warning("%d duplicate row(s) found", len(dup_rows))
        issues.append({
            "severity": "WARNING",
            "check": "duplicates",
            "message": f"{len(dup_rows)} duplicate row(s) found.",
            "rows": dup_rows,
        })
    return issues


def run_all_checks(df):
    """Run every validation check and return the combined issues list."""
    all_issues = []
    all_issues.extend(check_required_columns(df))
    all_issues.extend(check_date_format(df))
    all_issues.extend(check_future_dates(df))
    all_issues.extend(check_missing_source_urls(df))
    all_issues.extend(check_invalid_urls(df))
    all_issues.extend(check_empty_required_fields(df))
    all_issues.extend(check_verification_status(df))
    all_issues.extend(check_duplicates(df))
    return all_issues


def print_report(filepath, df, all_issues):
    """Print a formatted validation report."""
    print()
    print("=" * 70)
    print(f"  VALIDATION REPORT: {filepath}")
    print(f"  Rows: {len(df)}  |  Columns: {len(df.columns)}")
    print("=" * 70)

    if not all_issues:
        logger.info("All checks passed for %s", filepath)
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
    logger.info(
        "Validation complete: %d/%d rows (%.1f%%) have issues",
        len(total_error_rows), len(df), error_rate
    )
    print(f"\n  Summary: {len(total_error_rows)}/{len(df)} rows ({error_rate:.1f}%) have issues.")
    print()

    # Determine exit code.
    if critical or error_rate > ERROR_RATE_THRESHOLD:
        return 1
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.validate_dataset <path_to_csv>")
        print()
        print("Example:")
        print("  python -m src.validate_dataset My_Datasets_as_Examples/BlackRock_Timeline_Full_Decade.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    logger.info("Starting validation for %s", filepath)

    df = load_csv(filepath)
    all_issues = run_all_checks(df)
    exit_code = print_report(filepath, df, all_issues)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
