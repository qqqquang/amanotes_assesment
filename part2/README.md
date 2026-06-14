# Amanotes Case Study — Part 2: Daily User Metrics

## How to run

**Python 3.12** (tested on 3.12.2)

```bash
cd part2
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
# or: .venv/bin/pip install -r requirements.txt  # Mac/Linux
.venv/Scripts/python main.py                    # Windows
# or: .venv/bin/python main.py                   # Mac/Linux
```

Output: `daily_user_metrics.csv` (generated in the `part2/` folder)

## What I built

- **DuckDB + Python** pipeline that loads `events.jsonl`, cleans the data via SQL, and produces a `daily_user_metrics` table.
- SQL queries are in `queries/` folder (separation of logic from orchestration).
- Data quality checks run automatically and fail loudly if something is wrong.

## Data issues found and how I handled them

| Issue | Count | Action |
|---|---|---|
| Duplicate `event_id` | 112 | Deduplicated (keep first occurrence) |
| Null `user_id` | 38 | Removed — cannot attribute to a user |
| Mixed timezones (UTC vs +07:00) | ~50/50 | Normalized all to UTC via `TIMESTAMPTZ` cast |
| RC app versions (`5.3.0-rc1`) | 1019 events | Removed — internal test builds, not production users |

## Data quality checks

1. `clean_events` is not empty
2. No duplicate `event_id` after cleaning
3. Date range spans ≤ 10 days (expected ~7)
4. No null `user_id` in cleaned data
5. DAU > 0 for every day

## What I deliberately skipped

- **Anomaly detection on metrics** — out of scope for Part 2.
- **Partitioning/clustering** — irrelevant for a 4K-row sample file.
- **Separate staging models per event_name** — not needed for the required output (DAU, sessions, events_per_session don't need properties parsed).

## What I would do with one more hour

- **BigQuery cost note:** With 1 year of production data (~5M DAU × multiple events/day), this query scans the entire table daily. I would:
  - Partition by `event_date` → scan only relevant days
  - Use incremental materialization (dbt) with 3-day lookback for late-arriving events
  - Cluster by `user_id` to speed up `COUNT(DISTINCT)`
- Add retention cohort analysis (Day-1, Day-7 retention).
- Validate `revenue_usd` is non-negative in `ad_impression` events.
