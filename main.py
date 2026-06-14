"""
Amanotes Case Study - Part 2: Daily User Metrics Pipeline
Uses DuckDB to process events.jsonl and produce daily_user_metrics.csv
"""

import duckdb
import pandas as pd
from pathlib import Path


def main():
    conn = duckdb.connect()

    # --- 1. Load raw data ---
    print("Loading raw events from events.jsonl...")
    conn.execute("""
        CREATE TABLE raw_events AS
        SELECT * FROM read_json_auto('events.jsonl')
    """)

    raw_count = conn.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]
    print(f"  Raw events loaded: {raw_count}")

    # --- 2. Data profiling (before cleaning) ---
    print("\n--- Data Profiling ---")

    dupes = conn.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT event_id) AS duplicate_count
        FROM raw_events
    """).fetchone()[0]
    print(f"  Duplicate event_ids: {dupes}")

    null_users = conn.execute("""
        SELECT COUNT(*) FROM raw_events WHERE user_id IS NULL
    """).fetchone()[0]
    print(f"  Null user_ids: {null_users}")

    rc_versions = conn.execute("""
        SELECT COUNT(*) FROM raw_events WHERE app_version LIKE '%-rc%'
    """).fetchone()[0]
    print(f"  RC (test) version events: {rc_versions}")

    # --- 3. Clean events (run SQL) ---
    print("\nCleaning events (dedup, normalize TZ, remove nulls & RC versions)...")
    clean_sql = Path("queries/clean_events.sql").read_text(encoding="utf-8")
    conn.execute(clean_sql)

    clean_count = conn.execute("SELECT COUNT(*) FROM clean_events").fetchone()[0]
    print(f"  Clean events: {clean_count} (removed {raw_count - clean_count} rows)")

    # --- 4. Data quality checks ---
    print("\n--- Data Quality Checks ---")

    # Check 1: clean_events should not be empty
    assert clean_count > 0, "FAIL: clean_events table is empty!"
    print("  ✓ Check 1: clean_events is not empty")

    # Check 2: no duplicate event_ids after cleaning
    clean_dupes = conn.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT event_id) FROM clean_events
    """).fetchone()[0]
    assert clean_dupes == 0, f"FAIL: {clean_dupes} duplicates remain after cleaning!"
    print("  ✓ Check 2: no duplicate event_ids after cleaning")

    # Check 3: event_date range is within expected 7-day window
    date_range = conn.execute("""
        SELECT MIN(event_date), MAX(event_date),
               DATEDIFF('day', MIN(event_date), MAX(event_date)) AS span_days
        FROM clean_events
    """).fetchone()
    assert date_range[2] <= 10, f"FAIL: date range spans {date_range[2]} days, expected ~7"
    print(f"  ✓ Check 3: date range is {date_range[0]} to {date_range[1]} ({date_range[2]} days)")

    # Check 4: no null user_ids in clean table
    null_after = conn.execute("""
        SELECT COUNT(*) FROM clean_events WHERE user_id IS NULL
    """).fetchone()[0]
    assert null_after == 0, "FAIL: null user_ids found in clean_events!"
    print("  ✓ Check 4: no null user_ids in clean_events")

    # --- 5. Produce daily_user_metrics ---
    print("\nProducing daily_user_metrics...")
    metrics_sql = Path("queries/daily_user_metrics.sql").read_text(encoding="utf-8")
    result = conn.execute(metrics_sql).df()

    # Check 5: every day should have DAU > 0
    assert result["dau"].min() > 0, "FAIL: DAU is zero for at least one day!"
    print("  ✓ Check 5: DAU > 0 for all days")

    # --- 6. Export ---
    output_path = "daily_user_metrics.csv"
    result.to_csv(output_path, index=False)
    print(f"\n--- Output saved to {output_path} ---")
    print(result.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()
