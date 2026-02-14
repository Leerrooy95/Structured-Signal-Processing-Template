#!/usr/bin/env python3
"""
scrape_serp.py - Collect OSINT data from search engines using SerpApi.

SerpApi is a paid service that lets you pull real Google search results
through a simple API.  You send a search query, and it sends back
structured JSON with titles, links, snippets, and dates.

This script turns those results into a CSV that matches the Data Schema
Standard (see docs/DATA_SCHEMA_STANDARD.md) so you can plug the output
straight into validate_dataset.py and correlate_anchors.py.

---------------------------------------------------------------------
HOW IT WORKS (plain English)
---------------------------------------------------------------------
1. You pick a search query  (e.g. "BlackRock acquisitions 2024")
2. This script sends that query to Google *through* SerpApi
3. SerpApi returns the results as clean JSON (no HTML scraping needed)
4. The script maps each result to the standard CSV columns:
       title       -> the headline Google shows
       snippet     -> the short description under the link
       source_url  -> the actual URL of the page
       date_scraped -> today's date (when you ran the script)
5. You get a ready-to-validate CSV file

---------------------------------------------------------------------
SETUP (one-time)
---------------------------------------------------------------------
1. Go to https://serpapi.com and create a free account (100 searches/month free).
2. Copy your API key from the SerpApi dashboard.
3. In the project root, copy .env.example to .env:
       cp .env.example .env
4. Paste your key into .env:
       SERPAPI_KEY=your_key_here

---------------------------------------------------------------------
USAGE
---------------------------------------------------------------------
    # Basic search (saves to CSV in current directory)
    python src/scrape_serp.py "BlackRock acquisitions 2024"

    # Specify entity name and event type for the output CSV
    python src/scrape_serp.py "FDA drug approvals 2023" --entity FDA --event-type Policy

    # Fetch more results (default is 10)
    python src/scrape_serp.py "SEC enforcement actions" --num 20

    # Custom output filename
    python src/scrape_serp.py "DHS border policy" --output dhs_results.csv
---------------------------------------------------------------------
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from urllib.parse import urlencode

import requests

from src.config_loader import load_settings, get_logger

# ── Config ────────────────────────────────────────────────────────────────────
_settings = load_settings()
logger = get_logger("scrape_serp", _settings)

# SerpApi base URL
SERPAPI_URL = "https://serpapi.com/search"


def _get_api_key():
    """
    Read the SerpApi key from the environment.

    The key is loaded from .env by config_loader.  If it is missing the
    script exits with a helpful message so the user knows what to do.
    """
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if not key:
        print(
            "ERROR: SERPAPI_KEY is not set.\n"
            "\n"
            "To fix this:\n"
            "  1. Sign up at https://serpapi.com (free tier: 100 searches/month)\n"
            "  2. Copy your API key from the dashboard\n"
            "  3. Create a .env file in the project root:\n"
            "         cp .env.example .env\n"
            "  4. Add your key:\n"
            "         SERPAPI_KEY=paste_your_key_here\n"
        )
        sys.exit(1)
    return key


def search_serpapi(query, api_key, num_results=10):
    """
    Send a search query to SerpApi and return a list of result dicts.

    Each dict has: title, link, snippet (matching SerpApi's JSON keys).

    Parameters
    ----------
    query : str
        The Google search query (same as what you'd type in Google).
    api_key : str
        Your SerpApi API key.
    num_results : int
        How many results to request (max ~100 per call).

    Returns
    -------
    list[dict]
        One dict per organic search result.
    """
    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": num_results,
    }

    logger.info("Searching SerpApi: %s", query)
    resp = requests.get(SERPAPI_URL, params=params, timeout=30)

    if resp.status_code == 401:
        print("ERROR: Invalid API key. Check your SERPAPI_KEY in .env.")
        sys.exit(1)
    if resp.status_code == 429:
        print("ERROR: Rate limit reached. SerpApi free tier allows 100 searches/month.")
        sys.exit(1)

    resp.raise_for_status()
    data = resp.json()

    results = data.get("organic_results", [])
    logger.info("Got %d results from SerpApi", len(results))
    return results


def results_to_rows(results, entity, event_type, query=""):
    """
    Convert raw SerpApi results into rows matching the Data Schema Standard.

    Parameters
    ----------
    results : list[dict]
        Raw results from search_serpapi().
    entity : str
        The entity you are tracking (e.g. "BlackRock").
    event_type : str
        The event classification (e.g. "Financial", "Policy").
    query : str
        The original search query (recorded in notes for provenance).

    Returns
    -------
    list[dict]
        Rows ready to write to CSV.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []

    for r in results:
        rows.append({
            "date": "",  # Must be filled in manually after reviewing each result
            "entity": entity,
            "event_type": event_type,
            "source_url": r.get("link", ""),
            "verification_status": "Unverified",
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "date_scraped": today,
            "notes": f"Auto-collected via SerpApi. Query: {query}",
        })

    return rows


def write_csv(rows, output_path):
    """Write rows to a CSV file with the standard headers."""
    if not rows:
        print("No results to write.")
        return

    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} rows to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Scrape Google search results via SerpApi and save them "
            "as a CSV in the standard OSINT schema."
        ),
    )
    parser.add_argument(
        "query",
        help='Search query, e.g. "BlackRock acquisitions 2024"',
    )
    parser.add_argument(
        "--entity",
        default="Unknown",
        help="Entity name for the CSV (default: Unknown)",
    )
    parser.add_argument(
        "--event-type",
        default="Policy",
        help="Event type for the CSV (default: Policy)",
    )
    parser.add_argument(
        "--num",
        type=int,
        default=10,
        help="Number of results to fetch (default: 10)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output CSV filename (default: auto-generated)",
    )
    args = parser.parse_args()

    api_key = _get_api_key()

    # Search
    results = search_serpapi(args.query, api_key, num_results=args.num)

    if not results:
        print("No results found for that query.")
        sys.exit(0)

    # Convert to standard rows
    rows = results_to_rows(results, args.entity, args.event_type, query=args.query)

    # Output path
    if args.output:
        output_path = args.output
    else:
        safe_query = args.query[:30].replace(" ", "_").replace("/", "_")
        output_path = f"scraped_{safe_query}_{datetime.now().strftime('%Y%m%d')}.csv"

    write_csv(rows, output_path)

    # Next steps
    print()
    print("Next steps:")
    print(f"  1. Open {output_path} and fill in the 'date' column for each row.")
    print(f"  2. Review each source_url and update verification_status.")
    print(f"  3. Validate: python src/validate_dataset.py {output_path}")
    print()


if __name__ == "__main__":
    main()
