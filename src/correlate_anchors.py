#!/usr/bin/env python3
"""
correlate_anchors.py - Measure temporal proximity between two datasets.

Loads a "Target" dataset (e.g., policy events) and an "Anchor" dataset
(e.g., holidays) and calculates how many target events happened within
a configurable window of an anchor event.

Usage:
    python -m src.correlate_anchors --target path/to/target.csv --anchor path/to/anchor.csv
    python -m src.correlate_anchors --target path/to/target.csv --anchor path/to/anchor.csv --window 7
    python -m src.correlate_anchors --target path/to/target.csv --anchor path/to/anchor.csv --window 3 --baseline

Arguments:
    --target    Path to the target CSV (must have a 'date' column in YYYY-MM-DD format)
    --anchor    Path to the anchor CSV (must have a 'date' column in YYYY-MM-DD format)
    --window    Number of days for the proximity window (default from config/settings.yaml)
    --baseline  Run a Monte Carlo baseline comparison with random dates
"""

import argparse
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.config_loader import load_settings, get_logger

# ── Load config and logger ───────────────────────────────────────────────────
_settings = load_settings()
_correlation = _settings["correlation"]
_validation = _settings["validation"]

logger = get_logger("correlate_anchors", _settings)

DEFAULT_WINDOW = _correlation["default_window_days"]
BASELINE_SIMULATIONS = _correlation["baseline_simulations"]
DATE_FORMAT = _validation["date_format"]


def load_dates(filepath, date_column="date"):
    """
    Load a CSV and extract valid dates from the specified column.

    Returns a sorted list of datetime.date objects (skipping rows with
    missing or unparseable dates).
    """
    try:
        df = pd.read_csv(filepath, dtype=str)
    except FileNotFoundError:
        logger.error("File not found: %s", filepath)
        sys.exit(2)
    except Exception as e:
        logger.error("Could not read %s: %s", filepath, e)
        sys.exit(2)

    if date_column not in df.columns:
        logger.error("'%s' column not found in %s. Available: %s", date_column, filepath, list(df.columns))
        sys.exit(1)

    dates = []
    skipped = 0
    for val in df[date_column]:
        if pd.isna(val) or str(val).strip() == "":
            skipped += 1
            continue
        try:
            d = datetime.strptime(str(val).strip(), DATE_FORMAT).date()
            dates.append(d)
        except ValueError:
            skipped += 1

    if skipped > 0:
        logger.info("Skipped %d rows in %s (missing or unparseable dates)", skipped, filepath)

    logger.info("Loaded %d valid dates from %s", len(dates), filepath)
    return sorted(dates)


def find_matches(target_dates, anchor_dates, window_days):
    """
    For each anchor date, find target events within +-window_days.

    Returns:
        matches: list of (target_date, anchor_date, delta_days) tuples
        matched_targets: set of target dates that matched at least one anchor
        matched_anchors: set of anchor dates that matched at least one target
    """
    matches = []
    matched_targets = set()
    matched_anchors = set()

    for anchor_date in anchor_dates:
        window_start = anchor_date - timedelta(days=window_days)
        window_end = anchor_date + timedelta(days=window_days)

        for target_date in target_dates:
            if window_start <= target_date <= window_end:
                delta = (target_date - anchor_date).days
                matches.append((target_date, anchor_date, delta))
                matched_targets.add(target_date)
                matched_anchors.add(anchor_date)

    logger.info("Found %d matches (window=+-%d days)", len(matches), window_days)
    return matches, matched_targets, matched_anchors


def run_baseline(target_dates, anchor_dates, window_days, n_simulations=None):
    """
    Monte Carlo baseline: generate random target dates within the same date
    range and count how many fall near anchor dates by chance.

    Returns the mean and standard deviation of the match count across simulations.
    """
    if n_simulations is None:
        n_simulations = BASELINE_SIMULATIONS

    if not target_dates or not anchor_dates:
        return 0.0, 0.0

    date_min = min(target_dates)
    date_max = max(target_dates)
    total_days = (date_max - date_min).days
    if total_days <= 0:
        return 0.0, 0.0

    n_target = len(target_dates)
    match_counts = []

    logger.info("Running %d baseline simulations...", n_simulations)

    for _ in range(n_simulations):
        # Generate random dates in the same range.
        random_offsets = np.random.randint(0, total_days + 1, size=n_target)
        random_dates = [date_min + timedelta(days=int(offset)) for offset in random_offsets]

        count = 0
        for anchor_date in anchor_dates:
            window_start = anchor_date - timedelta(days=window_days)
            window_end = anchor_date + timedelta(days=window_days)
            for rd in random_dates:
                if window_start <= rd <= window_end:
                    count += 1
        match_counts.append(count)

    mean_val = float(np.mean(match_counts))
    std_val = float(np.std(match_counts))
    logger.info("Baseline result: %.1f +- %.1f matches", mean_val, std_val)
    return mean_val, std_val


def print_report(target_path, anchor_path, target_dates, anchor_dates,
                 window_days, matches, matched_targets, matched_anchors,
                 baseline_mean=None, baseline_std=None):
    """Print a formatted correlation report."""
    print()
    print("=" * 70)
    print("  TEMPORAL CORRELATION REPORT")
    print("=" * 70)
    print(f"  Target:  {target_path} ({len(target_dates)} valid dates)")
    print(f"  Anchor:  {anchor_path} ({len(anchor_dates)} valid dates)")
    print(f"  Window:  +-{window_days} days")
    print()
    print(f"  Total matches:          {len(matches)}")
    print(f"  Unique target matches:  {len(matched_targets)} / {len(target_dates)}"
          f" ({len(matched_targets)/len(target_dates)*100:.1f}%)" if target_dates else "")
    print(f"  Unique anchor matches:  {len(matched_anchors)} / {len(anchor_dates)}"
          f" ({len(matched_anchors)/len(anchor_dates)*100:.1f}%)" if anchor_dates else "")

    # Baseline comparison.
    if baseline_mean is not None:
        print()
        print(f"  Baseline (random dates): {baseline_mean:.1f} +- {baseline_std:.1f} matches")
        if baseline_std > 0:
            z_score = (len(matches) - baseline_mean) / baseline_std
            print(f"  Z-score: {z_score:.2f}", end="")
            if abs(z_score) > 2.0:
                print("  (statistically significant at p < 0.05)")
            elif abs(z_score) > 1.5:
                print("  (marginally significant)")
            else:
                print("  (not statistically significant - likely chance)")
        else:
            print("  Z-score: N/A (zero variance in baseline)")

    # Show match details (up to 20).
    if matches:
        print()
        print("  Match Details (up to 20 shown):")
        print("  " + "-" * 55)
        print(f"  {'Target Date':<15} {'Anchor Date':<15} {'Delta (days)':<12}")
        print("  " + "-" * 55)
        for target_date, anchor_date, delta in matches[:20]:
            sign = "+" if delta >= 0 else ""
            print(f"  {target_date}       {anchor_date}       {sign}{delta}")
        if len(matches) > 20:
            print(f"  ... and {len(matches) - 20} more matches.")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Calculate temporal proximity between a target and anchor dataset."
    )
    parser.add_argument(
        "--target", required=True,
        help="Path to the target CSV (must have a 'date' column)."
    )
    parser.add_argument(
        "--anchor", required=True,
        help="Path to the anchor CSV (must have a 'date' column)."
    )
    parser.add_argument(
        "--window", type=int, default=DEFAULT_WINDOW,
        help=f"Proximity window in days (default: {DEFAULT_WINDOW}, meaning +-{DEFAULT_WINDOW} days)."
    )
    parser.add_argument(
        "--baseline", action="store_true",
        help=f"Run a Monte Carlo baseline comparison with {BASELINE_SIMULATIONS} random simulations."
    )
    args = parser.parse_args()

    logger.info("Correlation analysis: target=%s anchor=%s window=%d", args.target, args.anchor, args.window)

    print(f"\nLoading target: {args.target}")
    target_dates = load_dates(args.target)

    print(f"Loading anchor: {args.anchor}")
    anchor_dates = load_dates(args.anchor)

    if not target_dates:
        logger.error("No valid dates found in the target dataset")
        print("ERROR: No valid dates found in the target dataset.")
        sys.exit(1)
    if not anchor_dates:
        logger.error("No valid dates found in the anchor dataset")
        print("ERROR: No valid dates found in the anchor dataset.")
        sys.exit(1)

    # Find matches.
    matches, matched_targets, matched_anchors = find_matches(
        target_dates, anchor_dates, args.window
    )

    # Optional baseline.
    baseline_mean = None
    baseline_std = None
    if args.baseline:
        print(f"  Running baseline simulation ({BASELINE_SIMULATIONS} iterations)...")
        baseline_mean, baseline_std = run_baseline(
            target_dates, anchor_dates, args.window
        )

    print_report(
        args.target, args.anchor, target_dates, anchor_dates,
        args.window, matches, matched_targets, matched_anchors,
        baseline_mean, baseline_std,
    )


if __name__ == "__main__":
    main()
