# Clay Partner Tier Progression Analysis

A data analysis of Clay's public solutions-partner ecosystem, exploring **what
distinguishes partners who climb tiers** (Artisan → Advanced Artisan → Studio →
Elite Studio) and producing a recommendation the partnerships team could act on.

> Built as a portfolio project using **only publicly available data** from
> [clay.com/experts](https://www.clay.com/experts). No private or proprietary
> data was used. Raw scraped data is intentionally excluded from this repo;
> the scraper is included for reproducibility.

## Why this project

Clay's Data Analyst role emphasizes going *beyond the "what" to understand the
"why."* Clay tiers its 160+ partner agencies, so a natural analytical question
is: **which characteristics predict a partner reaching the top (Elite) tier?**
That's a question Clay's own partnerships and data teams would care about, and
it mirrors the analytical motion described in the job.

## Architecture

```
scraper/        Polite, cached scraper for the public directory (Python + bs4)
data/raw/       Cached HTML (gitignored)
data/processed/ Clean CSVs: partners_list.csv, partners_detail.csv
dbt_clay/       dbt project: staging -> intermediate -> marts
  models/staging/        stg_partners, stg_partner_detail   (clean + type)
  models/intermediate/   int_partner_features               (derive features)
  models/marts/          mart_partner_tier_analysis         (window functions)
analysis/       Standalone DuckDB analysis (run without a warehouse)
dashboard/      Charts + exports for the BI layer (Sigma / Hex / Tableau)
```

The dbt layer is written for **Snowflake** (Clay's warehouse) but the
`analysis/tier_analysis.py` script reproduces the same logic locally in DuckDB
so you can explore with zero setup.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install requests beautifulsoup4 pandas duckdb

# 1. collect the data (polite: cached, 2.5s delay, honest user-agent)
python scraper/scrape_partners.py --pages 6 --detail

# 2. quick local analysis (no warehouse needed)
python analysis/tier_analysis.py

# 3. (optional) run the dbt models against Snowflake
cd dbt_clay && dbt run
```

> Before running the scraper, review clay.com/terms-of-service. Set your real
> contact email in `scraper/scrape_partners.py` (HEADERS).

## Key questions explored

1. What's the tier distribution, and how exclusive is each tier?
2. Does an **ex-Clay founder** correlate with reaching a higher tier?
3. Which **regions** are over- or under-served (expansion opportunity)?
4. Do higher-tier partners list **broader expertise** or richer profiles?
5. What **profile** best predicts Elite status — and how could the
   partnerships team spot those partners earlier?

## Findings

See [`analysis/findings.md`](analysis/findings.md) for the 1-page memo. (Write
this after you run the analysis — let the data tell you the story.)

## Tech

SQL (CTEs, window functions) · dbt · Snowflake · DuckDB · Python (pandas,
BeautifulSoup) · BI dashboard (Sigma / Hex / Tableau Public)

## Caveats

This is an outside-in analysis built from a public directory snapshot. Some
inferences (region from location strings, ex-Clay flags from page text) are
heuristic and would be refined with internal data. The point is to demonstrate
analytical approach and clear communication, not to claim definitive answers.
