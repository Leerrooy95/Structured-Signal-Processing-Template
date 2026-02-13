# The OSINT Data Pipeline

A methodology reference and toolkit for building, validating, and analyzing structured OSINT datasets.

**See Also:**
- [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project)
- [UVB-76 Analysis](https://github.com/Leerrooy95/UVB-76-Structured-Signal-Analysis/tree/main)
- [Research-Without-Trust-A-Reproducible-Playbook.pdf](https://github.com/user-attachments/files/23444776/Research-Without-Trust-A-Reproducible-Playbook.pdf)

---

## What This Repo Does

This repository is a **reusable toolkit** for OSINT research. Clone it whenever you start a new investigation to get:

1. **A proven data schema** that keeps your datasets consistent and machine-readable.
2. **Python scripts** that scaffold new datasets, validate data quality, and detect temporal correlations.
3. **Reference datasets** that demonstrate the methodology in practice.

The pipeline follows five steps: **Define** → **Collect** → **Validate** → **Correlate** → **Publish**.

---

## Repository Structure

```
├── My_Datasets_as_Examples/       # Reference datasets (ground truth)
│   ├── BlackRock_Timeline_Full_Decade.csv   (674 rows - Entity Tracking)
│   ├── policy_cleaned.csv                   (60 rows  - Regulatory Compliance)
│   └── Holidays_2015_2025_Verified.csv      (44 rows  - Temporal Anchors)
│
├── src/                           # Python toolkit
│   ├── scaffold_new_dataset.py    # Generate a blank CSV with correct headers
│   ├── validate_dataset.py        # Scan for dirty data and flag issues
│   └── correlate_anchors.py       # Measure temporal proximity between datasets
│
├── docs/                          # Methodology documentation
│   ├── DATA_SCHEMA_STANDARD.md    # Column specification for all datasets
│   └── RESEARCH_PROTOCOL.md       # Step-by-step: Raw Lead → Verified Dataset
│
├── templates/                     # CSV templates and self-challenge prompts
│   ├── ai_skeptic_prompts.txt     # 8 prompts to stress-test your findings
│   └── templates/
│       ├── template_timeline.csv
│       └── publish_checklist.md
│
├── Claude_Code_Opus_4.6_Analysis/ # Automated analysis of dataset gaps
│
├── QUICKSTART.md
├── LIMITATIONS.md
└── requirements.txt
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Scaffold a new dataset

```bash
python src/scaffold_new_dataset.py
```

The script asks what you're tracking and generates a blank CSV with the standard column headers defined in [docs/DATA_SCHEMA_STANDARD.md](docs/DATA_SCHEMA_STANDARD.md).

### 3. Validate your data

```bash
python src/validate_dataset.py path/to/your_dataset.csv
```

Flags future dates (hallucinations), missing source URLs, invalid date formats, empty required fields, and non-standard verification statuses.

### 4. Correlate with temporal anchors

```bash
python src/correlate_anchors.py \
    --target path/to/your_dataset.csv \
    --anchor My_Datasets_as_Examples/Holidays_2015_2025_Verified.csv \
    --window 3 \
    --baseline
```

Calculates how many of your events fall within ±N days of anchor dates (holidays, elections, etc.) and compares against a random baseline to test statistical significance.

---

## Reference Datasets

The `My_Datasets_as_Examples/` folder contains three datasets that prove the methodology works. These are the "ground truth" - the toolkit was designed to produce datasets of this quality.

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
2. **Collect** events from official sources, journalism, and AI-assisted search.
3. **Validate** with automated checks and manual review.
4. **Correlate** with anchor datasets to detect temporal patterns.
5. **Publish** after self-challenging with skeptic prompts.

The same method works for financial tracking, policy analysis, social media events, or anything with dates and observations.

---

## Self-Challenge

Before trusting any finding, run through the 8 skeptic prompts in `templates/ai_skeptic_prompts.txt`. If your dataset survives, it's ready to share.

---

*Last Updated: February 2026*
