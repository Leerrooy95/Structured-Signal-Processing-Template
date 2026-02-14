"""
test_scrape_serp.py - Tests for the SerpApi scraping script.

These tests verify the data-transformation functions (results_to_rows,
write_csv) without calling the real SerpApi endpoint.

Run with:
    pytest tests/test_scrape_serp.py -v
"""

import csv
import os

import pytest

from src.scrape_serp import results_to_rows, write_csv


# ── Tests: results_to_rows ──────────────────────────────────────────────────

class TestResultsToRows:
    def test_maps_serpapi_fields(self):
        """SerpApi result fields should map to the standard schema columns."""
        raw = [
            {
                "title": "BlackRock buys startup",
                "link": "https://reuters.com/article/123",
                "snippet": "BlackRock announced the acquisition of...",
            },
        ]
        rows = results_to_rows(raw, entity="BlackRock", event_type="Financial")
        assert len(rows) == 1
        row = rows[0]
        assert row["entity"] == "BlackRock"
        assert row["event_type"] == "Financial"
        assert row["source_url"] == "https://reuters.com/article/123"
        assert row["title"] == "BlackRock buys startup"
        assert row["snippet"] == "BlackRock announced the acquisition of..."
        assert row["verification_status"] == "Unverified"

    def test_date_left_empty(self):
        """The date field should be empty (user fills it in manually)."""
        raw = [{"title": "Test", "link": "https://example.com", "snippet": "..."}]
        rows = results_to_rows(raw, entity="Test", event_type="Policy")
        assert rows[0]["date"] == ""

    def test_date_scraped_is_today(self):
        """date_scraped should be set to today's date."""
        from datetime import datetime

        raw = [{"title": "Test", "link": "https://example.com", "snippet": "..."}]
        rows = results_to_rows(raw, entity="Test", event_type="Policy")
        # Verify the format is YYYY-MM-DD (don't compare exact value to avoid
        # midnight race conditions).
        assert len(rows[0]["date_scraped"]) == 10
        datetime.strptime(rows[0]["date_scraped"], "%Y-%m-%d")  # Raises if bad format

    def test_empty_results(self):
        """An empty results list should produce an empty row list."""
        rows = results_to_rows([], entity="Test", event_type="Policy")
        assert rows == []

    def test_multiple_results(self):
        """Multiple results should produce multiple rows."""
        raw = [
            {"title": f"Article {i}", "link": f"https://example.com/{i}", "snippet": "..."}
            for i in range(5)
        ]
        rows = results_to_rows(raw, entity="FDA", event_type="Policy")
        assert len(rows) == 5
        assert all(r["entity"] == "FDA" for r in rows)

    def test_missing_fields_handled(self):
        """Results with missing fields should not crash."""
        raw = [{}]  # No title, link, or snippet
        rows = results_to_rows(raw, entity="Test", event_type="Policy")
        assert len(rows) == 1
        assert rows[0]["source_url"] == ""
        assert rows[0]["title"] == ""
        assert rows[0]["snippet"] == ""


# ── Tests: write_csv ────────────────────────────────────────────────────────

class TestWriteCsv:
    def test_creates_csv_file(self, tmp_path):
        """write_csv should create a CSV file at the given path."""
        rows = [
            {
                "date": "2024-01-15",
                "entity": "TestCorp",
                "event_type": "Financial",
                "source_url": "https://example.com",
                "verification_status": "Unverified",
                "title": "Test",
                "snippet": "...",
                "date_scraped": "2024-06-01",
                "notes": "",
            },
        ]
        path = os.path.join(str(tmp_path), "output.csv")
        write_csv(rows, path)
        assert os.path.exists(path)

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            loaded = list(reader)
        assert len(loaded) == 1
        assert loaded[0]["entity"] == "TestCorp"

    def test_empty_rows_no_file(self, tmp_path, capsys):
        """write_csv with empty rows should print a message, not crash."""
        path = os.path.join(str(tmp_path), "empty.csv")
        write_csv([], path)
        assert not os.path.exists(path)
        captured = capsys.readouterr()
        assert "No results" in captured.out
