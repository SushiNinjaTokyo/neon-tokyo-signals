# AI Arena JP Data Coverage Review

## Purpose

This adds a read-only GitHub Action that reviews the full data pipeline coverage:

- Universe CSV / DuckDB universe
- prices_daily
- features_daily
- agent_scores_daily
- company master
- fundamentals / valuation tables
- value_features_daily
- Arena runs / orders / trades / positions / equity curve
- public site JSON / HTML / CSS outputs
- repo artifact size pressure

It does not fetch data, call GPT, or change DuckDB.

## Added files

```text
scripts/review_data_coverage_jp.py
.github/workflows/ai-arena-jp-data-coverage-review.yml
```

## Output

```text
site/data/japan/ai-arena/diagnostics/data-coverage-latest.json
site/data/japan/ai-arena/diagnostics/data-coverage-latest.md
site/data/japan/ai-arena/diagnostics/latest-data-coverage.json
site/data/japan/ai-arena/diagnostics/latest-data-coverage.md
```

## First safe run

Run manually:

```text
Workflow: AI Arena JP data coverage review
fail_on_critical: false
commit_outputs: true
min_bars_required: 60
stale_price_days: 5
min_fundamental_coverage_pct: 50
```

`fail_on_critical=false` is recommended for the first run because the goal is to observe the current state, not block the workflow.

## What to inspect first

Open:

```text
site/data/japan/ai-arena/diagnostics/data-coverage-latest.md
```

Priority sections:

1. Executive Warnings
2. Fundamentals / valuation coverage
3. Agent Scores
4. Arena Simulation Tables
5. Repo Artifact Size

## When to enable schedule

After manual confirmation, uncomment the schedule in:

```text
.github/workflows/ai-arena-jp-data-coverage-review.yml
```

Recommended timing:

```text
20:15 JST on weekdays
```

That is after live update and prune.
