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
4. **AI-assisted search**: Use LLMs to surface leads, but **never** trust AI output as a source. Every AI-generated claim must be traced back to a real URL.

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
| 2. Collect | Gather events from sources | Manual + AI-assisted search |
| 3. Validate | Clean data, fix flags | `validate_dataset.py` |
| 4. Correlate | Test for temporal patterns | `correlate_anchors.py` |
| 5. Publish | Document, self-challenge, share | Checklist + skeptic prompts |

---

*This protocol is based on the methodology proven by the datasets in `My_Datasets_as_Examples/`.*
