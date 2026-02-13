# Analysis: Gaps and Recommendations

*Automated analysis by Claude Code (Opus 4.6) based on the three reference datasets.*

---

## What I Found

After analyzing the column structures, data quality, and consistency across your three reference datasets, I identified several gaps that are worth addressing as you build future datasets. None of these diminish the quality of your existing work - they're opportunities to tighten the methodology going forward.

---

## Gap 1: Schema Inconsistency Across Datasets

**The Problem:** Each of your three datasets uses different column names for similar concepts.

| Concept | BlackRock | Policy | Holidays |
|---------|-----------|--------|----------|
| Event classification | `category` | `event_type` | `ritual_type` |
| Source link | `source_url` | `link` | *(missing)* |
| Entity being tracked | *(implicit)* | *(implicit)* | *(implicit)* |

**Why It Matters:** When you try to merge, compare, or run the same script against multiple datasets, these naming differences force manual column renaming every time. The `correlate_anchors.py` script works because it only needs a `date` column, but any more sophisticated cross-dataset analysis will break.

**Recommendation:** The Data Schema Standard (`docs/DATA_SCHEMA_STANDARD.md`) I created addresses this. Future datasets should follow it. For existing datasets, consider creating a `src/normalize_to_standard.py` script that maps legacy column names to the standard schema.

---

## Gap 2: BlackRock Dataset Has No Verification Status

**The Problem:** The BlackRock dataset (674 rows) has zero verification metadata. Every row has a `source_url` (good), but there's no column indicating whether anyone has confirmed the source still exists and says what the row claims.

**Why It Matters:** Verification status is the difference between "I found this" and "I confirmed this." Without it, the dataset is a collection of leads, not a verified timeline. This matters especially when other people use your data.

**Recommendation:** Add a `verification_status` column. For a dataset this size, you could:
1. Set all 674 rows to `Unverified` initially.
2. Spot-check a sample (e.g., every 10th row) and mark those as `Verified`.
3. Document the sampling strategy in the dataset README.

---

## Gap 3: Policy Dataset Has 87% Missing Dates

**The Problem:** 52 out of 60 rows in `policy_cleaned.csv` have no value in the `date` column. Only 8 rows have parseable dates.

**Why It Matters:** A dataset without dates can't be used for temporal correlation - which is the core capability of this toolkit. The `correlate_anchors.py` script will silently skip these 52 rows, giving you results based on only 13% of the data.

**Recommendation:** The dates may be recoverable. The `title` and `snippet` columns often contain dates in natural language (e.g., "signed on December 11, 2025"). A dedicated extraction script could parse these. Alternatively, the `date_range` column might contain usable information. This is worth a targeted cleanup pass.

---

## Gap 4: Holidays Dataset Has No Source URLs

**The Problem:** The Holidays dataset has no `source_url` column. The `raw_verification` column contains text excerpts but no links.

**Why It Matters:** While holiday dates are common knowledge, the Standard Schema requires `source_url` for every row. More importantly, if you ever expand this to include less obvious temporal anchors (fiscal year deadlines, regulatory comment periods, election dates), you'll need sources.

**Recommendation:** For well-known holidays, a single canonical source like `https://www.timeanddate.com/holidays/us/christmas-day` is sufficient. The point isn't that someone will doubt Christmas is on December 25 - it's that the discipline of always having a source URL prevents you from skipping it when the event *isn't* obvious.

---

## Gap 5: No `.gitignore` File

**The Problem:** The repository has no `.gitignore`. This means generated CSV files, Python cache files, virtual environments, and potentially sensitive files could be accidentally committed.

**Why It Matters:** When you run `scaffold_new_dataset.py`, the generated CSV will sit in the repo root. Without `.gitignore`, a `git add .` could commit work-in-progress data or large files.

**Recommendation:** I've added a `.gitignore` in this refactor that covers common Python artifacts and generated data files.

---

## Gap 6: No `__init__.py` or Package Structure for `/src`

**The Problem:** The Python scripts in `/src` are standalone scripts, not an importable package. This is fine for now, but limits reusability.

**Why It Matters:** If you want to use `validate_dataset` as a library function inside a Jupyter notebook or another script (e.g., `from src.validate_dataset import check_future_dates`), you currently can't without modifying `sys.path`.

**Recommendation:** This is low priority. The scripts work fine as standalone CLI tools. If you later want to build a Jupyter-based workflow, adding `src/__init__.py` and restructuring will enable imports. Don't do it now unless you need it.

---

## Gap 7: The Nested `templates/` Directory

**The Problem:** There's a `templates/templates/templates/` nesting pattern in the repo structure:
```
templates/
├── ai_skeptic_prompts.txt
├── .gitkeep
└── templates/
    ├── template_timeline.csv
    └── templates/
        └── publish_checklist.md
```

**Why It Matters:** This looks like an accidental artifact. Finding `publish_checklist.md` requires navigating three levels deep into identically-named directories.

**Recommendation:** Flatten the structure so all template files live directly under `templates/`. This is a minor cleanup but prevents confusion.

---

## Summary

| Gap | Severity | Effort to Fix |
|-----|----------|---------------|
| Schema inconsistency | High | Already addressed by DATA_SCHEMA_STANDARD.md |
| BlackRock missing verification_status | Medium | Add column, bulk-set to Unverified |
| Policy 87% missing dates | High | Extract dates from title/snippet text |
| Holidays missing source_url | Low | Add canonical URL column |
| No .gitignore | Low | Added in this refactor |
| No package structure for /src | Low | Skip for now |
| Nested templates directory | Low | Flatten when convenient |

The two highest-impact improvements you could make to your existing datasets are:
1. **Recover the missing dates in policy_cleaned.csv** - this unlocks temporal correlation for that dataset.
2. **Add verification_status to BlackRock** - this completes the dataset's provenance chain.

---

*This analysis was generated by examining the actual data, not by guessing. All row counts and column names were verified programmatically.*
