# The OSINT Data Pipeline

**v1.1**

A methodology reference and toolkit for building, validating, and analyzing structured OSINT datasets.

**See Also:**
- [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project)
- [UVB-76 Analysis](https://github.com/Leerrooy95/UVB-76-Structured-Signal-Analysis/tree/main)
- [If you don't think you're capable, click here for more personalized instructions in the form of a PDF.](https://github.com/user-attachments/files/23444776/Research-Without-Trust-A-Reproducible-Playbook.pdf)

---

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/Leerrooy95/Structured-Signal-Processing-Template.git
cd Structured-Signal-Processing-Template
pip install -r requirements.txt

# 2. Set up your SerpApi key (free: 100 searches/month)
#    Sign up at https://serpapi.com, copy your key, then:
cp .env.example .env
#    Edit .env and paste your key next to SERPAPI_KEY=

# 3. Scrape search results into a CSV
python src/scrape_serp.py "BlackRock acquisitions 2024" --entity BlackRock --event-type Financial

# 4. Or scaffold a blank dataset manually
python src/scaffold_new_dataset.py

# 5. Validate your data
python src/validate_dataset.py path/to/your_dataset.csv

# 6. Correlate with temporal anchors
python src/correlate_anchors.py \
    --target path/to/your_dataset.csv \
    --anchor My_Datasets_as_Examples/Holidays_2015_2025_Verified.csv \
    --window 3 \
    --baseline
```

That's the whole loop: **Scrape** → **Review & fill in dates** → **Validate** → **Correlate**.

---

## What This Repo Does

This repository is a **reusable toolkit** for OSINT research. Clone it whenever you start a new investigation to get:

1. **A proven data schema** that keeps your datasets consistent and machine-readable.
2. **Python scripts** that scrape data from search APIs (SerpApi), scaffold new datasets, validate data quality, and detect temporal correlations.
3. **Reference datasets** that demonstrate the methodology in practice.

The pipeline follows five steps: **Define** → **Scrape / Collect** → **Validate** → **Correlate** → **Publish**.

---

## Repository Structure

```
├── src/                           # Python toolkit
│   ├── scrape_serp.py             # Scrape Google results via SerpApi into CSV
│   ├── scaffold_new_dataset.py    # Generate a blank CSV with correct headers
│   ├── validate_dataset.py        # Scan for dirty data and flag issues
│   └── correlate_anchors.py       # Measure temporal proximity between datasets
│
├── docs/                          # Methodology documentation
│   ├── DATA_SCHEMA_STANDARD.md    # Column specification for all datasets
│   └── RESEARCH_PROTOCOL.md       # Step-by-step: Raw Lead → Verified Dataset
│
├── My_Datasets_as_Examples/       # Reference datasets (ground truth)
│   ├── BlackRock_Timeline_Full_Decade.csv
│   ├── policy_cleaned.csv
│   └── Holidays_2015_2025_Verified.csv
│
├── templates/                     # CSV templates & checklists
│   ├── template_timeline.csv
│   └── publish_checklist.md
│
├── config/settings.yaml           # Central configuration
├── archive/                       # Older notes & analysis (kept for reference)
├── tests/                         # Automated tests
├── logs/                          # Runtime logs
└── requirements.txt
```

---

## Reference Datasets

The `My_Datasets_as_Examples/` folder contains three datasets that prove the methodology works. These are the "ground truth" — the toolkit was designed to produce datasets of this quality.

| Dataset | Rows | Purpose | Coverage |
|---------|------|---------|----------|
| **BlackRock_Timeline_Full_Decade.csv** | 674 | Entity tracking | BlackRock corporate events, 2015-2025 |
| **policy_cleaned.csv** | 60 | Regulatory compliance | U.S. Executive Orders on AI, 2015-2025 |
| **Holidays_2015_2025_Verified.csv** | 44 | Temporal anchors | Christmas, Easter, Halloween, St. Patrick's Day |

These datasets were produced as part of [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project).

---

## Methodology

The full research protocol is documented in [docs/RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md). The short version:

1. **Define** your scope: entity, time window, event types.
2. **Scrape** events using `scrape_serp.py` (SerpApi) or collect manually from official sources and journalism.
3. **Validate** with automated checks and manual review.
4. **Correlate** with anchor datasets to detect temporal patterns.
5. **Publish** after self-challenging with the skeptic prompts in [archive/ai_skeptic_prompts.txt](archive/ai_skeptic_prompts.txt).

The same method works for financial tracking, policy analysis, social media events, or anything with dates and observations.

---

*Last Updated: February 2026*
