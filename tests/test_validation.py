"""
test_validation.py - Prove the validation pipeline catches bad data.

Run with:
    pytest tests/test_validation.py -v

Each test intentionally feeds "dirty" data to the validator and asserts
that the correct issue is detected. If all tests pass, the pipeline works.
"""

import os
import tempfile
from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.validate_dataset import (
    check_date_format,
    check_duplicates,
    check_empty_required_fields,
    check_future_dates,
    check_invalid_urls,
    check_missing_source_urls,
    check_required_columns,
    check_verification_status,
    load_csv,
    run_all_checks,
)
from src.config_loader import load_settings


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_df(overrides=None, n_rows=3):
    """Create a minimal valid DataFrame, optionally overriding columns."""
    data = {
        "date": [f"2024-01-{15 + i:02d}" for i in range(n_rows)],
        "entity": [f"TestCorp_{i}" for i in range(n_rows)],
        "event_type": ["Policy"] * n_rows,
        "source_url": ["https://example.com/article"] * n_rows,
        "verification_status": ["Verified"] * n_rows,
    }
    if overrides:
        data.update(overrides)
    return pd.DataFrame(data)


def _write_csv(df, tmp_path):
    """Write a DataFrame to a temp CSV and return the path."""
    path = os.path.join(str(tmp_path), "test_data.csv")
    df.to_csv(path, index=False)
    return path


# ── Tests: Config loads correctly ────────────────────────────────────────────

class TestConfigLoads:
    def test_settings_yaml_loads(self):
        """config/settings.yaml should load without errors."""
        settings = load_settings()
        assert "schema" in settings
        assert "validation" in settings
        assert "correlation" in settings
        assert "logging" in settings

    def test_required_columns_from_config(self):
        """Required columns should come from settings.yaml, not hardcoded."""
        settings = load_settings()
        required = settings["schema"]["required_columns"]
        assert "date" in required
        assert "entity" in required
        assert "source_url" in required


# ── Tests: Clean data passes ─────────────────────────────────────────────────

class TestCleanDataPasses:
    def test_clean_data_has_no_issues(self):
        """A properly formatted dataset should produce zero issues."""
        df = _make_df()
        issues = run_all_checks(df)
        assert len(issues) == 0, f"Expected no issues, got: {issues}"


# ── Tests: Missing columns ──────────────────────────────────────────────────

class TestMissingColumns:
    def test_missing_all_required_columns(self):
        """A CSV with none of the required columns should trigger CRITICAL."""
        df = pd.DataFrame({"random_col": ["a", "b"]})
        issues = check_required_columns(df)
        assert len(issues) == 1
        assert issues[0]["severity"] == "CRITICAL"
        assert "date" in issues[0]["message"]

    def test_missing_one_column(self):
        """Dropping a single required column should be caught."""
        df = _make_df()
        df = df.drop(columns=["source_url"])
        issues = check_required_columns(df)
        assert len(issues) == 1
        assert "source_url" in issues[0]["message"]


# ── Tests: Date format ──────────────────────────────────────────────────────

class TestDateFormat:
    def test_bad_date_format_mm_dd_yyyy(self):
        """MM/DD/YYYY dates should be flagged as invalid."""
        df = _make_df({"date": ["01/15/2024", "02/20/2024", "03/25/2024"]})
        issues = check_date_format(df)
        assert len(issues) == 1
        assert issues[0]["check"] == "date_format"
        assert len(issues[0]["rows"]) == 3

    def test_garbage_date(self):
        """Non-date strings in the date column should be flagged."""
        df = _make_df({"date": ["not-a-date", "2024-01-15", "yesterday"]})
        issues = check_date_format(df)
        assert len(issues) == 1
        assert len(issues[0]["rows"]) == 2  # "not-a-date" and "yesterday"

    def test_valid_dates_pass(self):
        """Properly formatted ISO dates should produce no issues."""
        df = _make_df({"date": ["2024-01-15", "2023-06-30", "2020-12-31"]})
        issues = check_date_format(df)
        assert len(issues) == 0


# ── Tests: Future dates ─────────────────────────────────────────────────────

class TestFutureDates:
    def test_future_date_flagged(self):
        """A date in the future should be flagged as a potential hallucination."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        far_future = "2099-12-31"
        df = _make_df({"date": ["2024-01-15", tomorrow, far_future]})
        issues = check_future_dates(df)
        assert len(issues) == 1
        assert issues[0]["check"] == "future_dates"
        assert len(issues[0]["rows"]) == 2

    def test_past_dates_pass(self):
        """Dates in the past should not be flagged."""
        df = _make_df({"date": ["2020-01-01", "2023-06-15", "2024-01-01"]})
        issues = check_future_dates(df)
        assert len(issues) == 0


# ── Tests: Missing source URLs ──────────────────────────────────────────────

class TestMissingSourceUrls:
    def test_empty_source_url(self):
        """Empty source_url fields should be flagged."""
        df = _make_df({"source_url": ["https://example.com", "", "   "]})
        issues = check_missing_source_urls(df)
        assert len(issues) == 1
        assert len(issues[0]["rows"]) == 2

    def test_nan_source_url(self):
        """NaN source_url values should be flagged."""
        df = _make_df({"source_url": ["https://example.com", None, "https://example.com"]})
        issues = check_missing_source_urls(df)
        assert len(issues) == 1
        assert len(issues[0]["rows"]) == 1


# ── Tests: Invalid URLs ─────────────────────────────────────────────────────

class TestInvalidUrls:
    def test_no_scheme(self):
        """URLs without http/https should be flagged."""
        df = _make_df({"source_url": ["example.com/article", "https://good.com", "ftp://ok.com"]})
        issues = check_invalid_urls(df)
        assert len(issues) == 1
        assert len(issues[0]["rows"]) == 1  # "example.com/article"

    def test_valid_urls_pass(self):
        """Well-formed URLs should not be flagged."""
        df = _make_df({"source_url": [
            "https://reuters.com/article/123",
            "http://sec.gov/filings/abc",
            "https://example.com/page?q=test",
        ]})
        issues = check_invalid_urls(df)
        assert len(issues) == 0


# ── Tests: Empty required fields ────────────────────────────────────────────

class TestEmptyFields:
    def test_empty_entity(self):
        """Empty entity values should be flagged."""
        df = _make_df({"entity": ["BlackRock", "", "DHS"]})
        issues = check_empty_required_fields(df)
        assert any(i["check"] == "empty_entity" for i in issues)

    def test_all_fields_filled_passes(self):
        """A fully populated dataset should produce no empty-field issues."""
        df = _make_df()
        issues = check_empty_required_fields(df)
        assert len(issues) == 0


# ── Tests: Verification status ──────────────────────────────────────────────

class TestVerificationStatus:
    def test_nonstandard_status(self):
        """Non-standard verification values should be flagged as warnings."""
        df = _make_df({"verification_status": ["Verified", "Trusted Media", "Widely Reported"]})
        issues = check_verification_status(df)
        assert len(issues) == 1
        assert len(issues[0]["rows"]) == 2  # "Trusted Media" and "Widely Reported"

    def test_standard_statuses_pass(self):
        """Verified, Unverified, Debunked should all pass."""
        df = _make_df({"verification_status": ["Verified", "Unverified", "Debunked"]})
        issues = check_verification_status(df)
        assert len(issues) == 0


# ── Tests: Duplicates ───────────────────────────────────────────────────────

class TestDuplicates:
    def test_duplicate_rows_flagged(self):
        """Fully identical rows should be flagged."""
        df = _make_df(n_rows=1)
        df = pd.concat([df, df, df], ignore_index=True)  # 3 identical rows
        issues = check_duplicates(df)
        assert len(issues) == 1
        assert len(issues[0]["rows"]) == 2  # 2 duplicates (first kept)

    def test_unique_rows_pass(self):
        """Distinct rows should not be flagged."""
        df = _make_df({"entity": ["A", "B", "C"]})
        issues = check_duplicates(df)
        assert len(issues) == 0


# ── Tests: Full pipeline integration ────────────────────────────────────────

class TestFullPipeline:
    def test_maximally_bad_data(self):
        """A CSV with every possible problem should produce issues from multiple checks."""
        df = pd.DataFrame({
            "date": ["not-a-date", "2099-12-31", ""],
            "entity": ["", "Test", ""],
            "event_type": ["Policy", "", "Legal"],
            "source_url": ["not_a_url", "", "https://good.com"],
            "verification_status": ["WRONG", "Verified", ""],
        })
        issues = run_all_checks(df)
        check_names = {i["check"] for i in issues}
        assert "date_format" in check_names
        assert "future_dates" in check_names
        assert "missing_source_url" in check_names
        assert "invalid_urls" in check_names
        assert "empty_entity" in check_names
        assert len(issues) >= 5  # Multiple distinct problems

    def test_load_csv_from_file(self, tmp_path):
        """load_csv should correctly read a CSV file from disk."""
        df = _make_df()
        path = _write_csv(df, tmp_path)
        loaded = load_csv(path)
        assert len(loaded) == 3
        assert "date" in loaded.columns

    def test_real_example_dataset(self):
        """The reference Holidays dataset should trigger known issues (missing columns)."""
        holidays_path = os.path.join("My_Datasets_as_Examples", "Holidays_2015_2025_Verified.csv")
        if not os.path.exists(holidays_path):
            pytest.skip("Example dataset not found (running outside repo root)")
        df = load_csv(holidays_path)
        issues = run_all_checks(df)
        # Holidays is missing entity, event_type, source_url columns.
        critical = [i for i in issues if i["severity"] == "CRITICAL"]
        assert len(critical) >= 1
        assert "Missing required columns" in critical[0]["message"]
