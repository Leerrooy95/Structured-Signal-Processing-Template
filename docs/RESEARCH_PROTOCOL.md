# Research Protocol

*How to go from a Raw Lead to a Verified Dataset.*

---

## Prerequisites

- Python 3.9+ with pandas installed (`pip install -r requirements.txt`)
- A clear research question (e.g., "What has BlackRock done in the last decade?")
- Familiarity with the [Data Schema Standard](DATA_SCHEMA_STANDARD.md)

---

## Phase 1: Define Scope

Before collecting any data, answer these questions in writing:

1. **Entity**: What person, organization, or topic are you tracking?
2. **Time window**: What date range are you investigating? (e.g., 2015-2025)
3. **Event types**: What kinds of events matter? (Policy, Financial, Legal, etc.)
4. **Anchor datasets**: What temporal reference points will you use for correlation? (Holidays, elections, fiscal quarters, etc.)

**Output**: A one-paragraph scope statement saved in your project folder.

**Tool**: Run `python src/scaffold_new_dataset.py` to generate a blank CSV with the correct headers.

---

## Phase 2: Collect Raw Data

### Sources (in order of priority)

1. **Official sources**: Government registries, SEC filings, court records, .gov/.mil sites
2. **Primary journalism**: Reuters, AP, original investigative reports
3. **Secondary sources**: Analysis pieces, opinion columns, blog posts (mark as lower confidence)
4. **API-based search (SerpApi)**: Use the included `scrape_serp.py` script to pull real Google results through the SerpApi service. This is the fastest way to collect leads at scale — see the step-by-step guide below.

### How to Scrape Data with SerpApi

SerpApi is a service that lets you pull structured Google search results through a simple API — no HTML scraping, no browser automation, no broken selectors. You send a search query, SerpApi sends back clean JSON with titles, URLs, and snippets.

**One-time setup (takes 2 minutes):**

1. Go to [serpapi.com](https://serpapi.com) and create a free account (100 searches/month free).
2. Copy your API key from the SerpApi dashboard.
3. In the project root, create your `.env` file:
   ```bash
   cp .env.example .env
   ```
4. Paste your key into `.env`:
   ```
   SERPAPI_KEY=paste_your_key_here
   ```

**Run a search:**

```bash
# Basic: search for BlackRock acquisitions and save to a CSV
python src/scrape_serp.py "BlackRock acquisitions 2024"

# Specify what entity you're tracking and what kind of events
python src/scrape_serp.py "FDA drug approvals 2023" --entity FDA --event-type Policy

# Get more results (default is 10)
python src/scrape_serp.py "SEC enforcement actions" --num 20

# Custom output filename
python src/scrape_serp.py "DHS border policy" --output dhs_results.csv
```

**What happens behind the scenes:**

1. `scrape_serp.py` reads your API key from `.env`
2. It sends your search query to SerpApi
3. SerpApi returns structured JSON (titles, URLs, snippets)
4. The script maps each result into the standard CSV columns
5. You get a CSV file ready for validation

**After scraping, you still need to:**

1. Open the CSV and fill in the `date` column (the script can't know when each event happened).
2. Review each `source_url` and update `verification_status` to `Verified` or `Debunked`.
3. Run `python src/validate_dataset.py your_file.csv` to catch any problems.

> **Note:** SerpApi is not the only option. [SerperApi](https://serper.dev) is a similar service
> with a different pricing model. The script uses SerpApi, but the concept is the same for any
> search API: send a query, get structured results, convert to your standard schema.

### Collection Rules

- One event per row.
- Record the `date_scraped` so you know when you found it.
- Set `verification_status` to `Unverified` for everything at this stage.
- Always paste the full `source_url`. If you can't link to it, note why in `notes`.
- If the exact date is unknown, use the best approximation and set `date_confidence` to `Low`.

**Output**: A CSV file with all leads. Expect some noise - that's fine.

---

## Phase 3: Clean and Validate

### Automated Checks

Run the validation script on your raw CSV:

```bash
python src/validate_dataset.py path/to/your_dataset.csv
```

This will flag:
- **Missing required columns** (date, entity, event_type, source_url, verification_status)
- **Future dates** (potential hallucinations or typos)
- **Invalid date formats** (anything not YYYY-MM-DD)
- **Missing source URLs** (rows that can't be verified)
- **Empty required fields**

### Manual Review

For each flagged row, decide:
- **Fix it**: Correct the date, add the missing URL, etc.
- **Downgrade it**: Change `verification_status` to `Unverified` and add a note.
- **Remove it**: If the event is fabricated or unfixable, delete the row.

### Verification Upgrade

For rows you want to mark as `Verified`:
1. Open the `source_url` in a browser.
2. Confirm the source still exists and says what the `snippet` claims.
3. Check at least one additional source (cross-reference).
4. Change `verification_status` to `Verified`.

**Output**: A clean CSV that passes validation with zero critical flags.

---

## Phase 4: Correlate with Anchors

### What is an Anchor Dataset?

An anchor dataset contains events with known, fixed dates (holidays, elections, fiscal deadlines). By measuring how many of your target events cluster near anchor dates, you can detect temporal patterns or rule out coincidence.

### Running Correlation

```bash
python src/correlate_anchors.py --target path/to/target.csv --anchor path/to/anchor.csv --window 3
```

The script will:
1. Load both datasets.
2. For each anchor date, check how many target events fall within +-N days.
3. Report the total matches, match rate, and list the specific pairs.

### Interpreting Results

- **High match rate** (>30%): Strong temporal clustering. Investigate whether there's a causal relationship or if the anchor dates are too common (e.g., weekdays).
- **Low match rate** (<10%): Weak or no clustering. Your target events are likely independent of the anchor dates.
- **Moderate match rate** (10-30%): Potentially interesting. Run with different window sizes (1, 3, 7 days) to see if the pattern holds.

**Always ask**: "Would random dates produce a similar match rate?" If your target dataset has 674 events over 10 years, some will land near holidays by chance. The `correlate_anchors.py` script includes a baseline comparison to help with this.

---

## Phase 5: Document and Publish

### Before Sharing

Use this checklist (adapted from `templates/templates/publish_checklist.md`):

- [ ] All dates are ISO 8601 (`YYYY-MM-DD`)
- [ ] Every row has a `source_url`
- [ ] Dataset passes `validate_dataset.py` with no critical flags
- [ ] README includes: scope statement, row count, date range, column descriptions
- [ ] Limitations are documented (what this data does NOT cover)
- [ ] At least one person has reviewed the dataset (peer review)

### Self-Challenge

Before publishing, run through the skeptic prompts in `templates/ai_skeptic_prompts.txt`:

1. Find 5 counter-examples (event happened but no signal).
2. Show me dates that contradict your pattern.
3. Pull original documents - no summaries.
4. Compare to a control group.
5. Find official denials or corrections.
6. Test with wider time windows.
7. Find alternative explanations.
8. Search for existing debunking.

If your dataset survives these challenges, it's ready to share.

---

## Quick Reference

| Phase | Action | Tool |
|-------|--------|------|
| 1. Define | Write scope, generate blank CSV | `scaffold_new_dataset.py` |
| 2. Collect | Scrape search results via API | `scrape_serp.py` (SerpApi) |
| 3. Validate | Clean data, fix flags | `validate_dataset.py` |
| 4. Correlate | Test for temporal patterns | `correlate_anchors.py` |
| 5. Publish | Document, self-challenge, share | Checklist + skeptic prompts |

---

*This protocol is based on the methodology proven by the datasets in `My_Datasets_as_Examples/`.*
