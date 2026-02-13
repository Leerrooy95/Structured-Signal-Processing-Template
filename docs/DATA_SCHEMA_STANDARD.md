# Data Schema Standard

*The canonical column specification for all OSINT datasets in this project.*

---

## Overview

This standard was derived by analyzing the column structures of three reference datasets:

| Dataset | Rows | Original Columns |
|---------|------|-------------------|
| `BlackRock_Timeline_Full_Decade.csv` | 674 | date, year, event, category, snippet, source_url |
| `policy_cleaned.csv` | 60 | date_range, query, policy_scope, date, date_confidence, title, link, snippet, date_scraped, verification_status, event_type, country |
| `Holidays_2015_2025_Verified.csv` | 44 | ritual_type, year, date, verification_status, raw_verification |

The Standard Schema unifies these into a single consistent format so that every future dataset is immediately compatible with the validation and correlation tools in `/src`.

---

## Required Columns

Every dataset **must** include these columns. The validation script (`src/validate_dataset.py`) will flag any row where a required field is missing.

| Column | Type | Format | Description |
|--------|------|--------|-------------|
| `date` | string | `YYYY-MM-DD` (ISO 8601) | The date the event occurred. Must not be in the future. |
| `entity` | string | Free text | The primary subject being tracked (e.g., "BlackRock", "DHS", "U.S. Executive Branch"). One entity per row. |
| `event_type` | string | Controlled vocabulary | The classification of the event. See Event Type Vocabulary below. |
| `source_url` | string | Valid URL | A link to the primary source that documents this event. Required for verification. |
| `verification_status` | string | Controlled vocabulary | One of: `Verified`, `Unverified`, `Debunked`. See definitions below. |

## Recommended Columns

These columns are optional but strongly encouraged. They add context that makes datasets more useful for analysis and correlation.

| Column | Type | Format | Description |
|--------|------|--------|-------------|
| `year` | integer | `YYYY` | Extracted from `date`. Useful for grouping and filtering. |
| `title` | string | Free text | A short human-readable label for the event (e.g., article headline). |
| `snippet` | string | Free text | A brief excerpt from the source that supports the event claim. |
| `category` | string | Free text | A higher-level grouping (e.g., "Tech_Dominance", "Government_Ties"). Useful when `event_type` is too granular. |
| `country` | string | ISO 3166-1 name | The country most relevant to the event. |
| `date_confidence` | string | `High` / `Medium` / `Low` | How confident you are in the `date` value. Use `Low` when only a year or month is known. |
| `date_scraped` | string | `YYYY-MM-DD` | The date this row was collected. Important for provenance. |
| `notes` | string | Free text | Anything that doesn't fit elsewhere. |

---

## Controlled Vocabularies

### Event Type

Use these values for the `event_type` column. You may extend this list, but new values should be documented in your dataset's README.

| Value | Use When |
|-------|----------|
| `Policy` | Government policy, regulation, executive order |
| `Financial` | Market events, earnings, acquisitions, investments |
| `Legal` | Lawsuits, court rulings, regulatory enforcement |
| `Appointment` | Key personnel changes, nominations |
| `Statement` | Public speeches, press releases, open letters |
| `Temporal_Anchor` | Holidays, elections, recurring calendar events used as reference points |
| `Crisis` | Wars, natural disasters, market crashes, pandemics |
| `Technology` | Product launches, patents, infrastructure changes |

### Verification Status

| Value | Definition |
|-------|------------|
| `Verified` | The event is confirmed by at least one official or widely-trusted source. The `source_url` points to that source. |
| `Unverified` | The event is reported but not yet independently confirmed. Treat as a lead. |
| `Debunked` | The event has been shown to be false, inaccurate, or misattributed. Keep the row for transparency, but flag it. |

---

## How the Example Datasets Map to This Schema

### BlackRock_Timeline_Full_Decade.csv

| Standard Column | Original Column | Notes |
|----------------|-----------------|-------|
| `date` | `date` | Already ISO 8601. |
| `entity` | *(implicit)* | All rows are "BlackRock". Column missing - should be added. |
| `event_type` | `category` | Values like `Tech_Dominance` map to `Technology`, `Government_Ties` maps to `Policy`, etc. |
| `source_url` | `source_url` | Direct match. 0 missing values. |
| `verification_status` | *(missing)* | **Gap identified.** No verification column exists. |

### policy_cleaned.csv

| Standard Column | Original Column | Notes |
|----------------|-----------------|-------|
| `date` | `date` | **52 of 60 rows have missing dates.** Major data quality gap. |
| `entity` | *(implicit)* | Could be derived from `query` or `country`. |
| `event_type` | `event_type` | Direct match. Values: `policy`, `Executive Order`. |
| `source_url` | `link` | Different column name but same concept. 0 missing. |
| `verification_status` | `verification_status` | Direct match. Multiple granular values that could map to `Verified`. |

### Holidays_2015_2025_Verified.csv

| Standard Column | Original Column | Notes |
|----------------|-----------------|-------|
| `date` | `date` | Already ISO 8601. |
| `entity` | *(implicit)* | Could be the holiday name or "Calendar". |
| `event_type` | `ritual_type` | Maps to `Temporal_Anchor`. Values: Christmas, Easter, St. Patrick's Day, Halloween. |
| `source_url` | *(missing)* | **Gap identified.** No source URLs. Holidays are common knowledge, but the standard requires it. |
| `verification_status` | `verification_status` | Direct match. All rows are `Verified`. |

---

## Naming Conventions

- **File names**: `entity_topic_date_range.csv` (e.g., `blackrock_timeline_2015_2025.csv`)
- **Column names**: All lowercase, underscores for spaces. No spaces, no camelCase.
- **Dates**: Always `YYYY-MM-DD`. Never `MM/DD/YYYY` or `DD-MM-YYYY`.
- **URLs**: Full URLs including `https://`. No shortened links.

---

*This standard is a living document. Update it as your methodology evolves.*
