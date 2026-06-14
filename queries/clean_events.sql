-- clean_events.sql
-- Bronze → Silver: deduplicate, normalize timezone, remove invalid records

CREATE OR REPLACE TABLE clean_events AS

WITH deduplicated AS (
    -- Remove duplicate event_ids, keep first occurrence
    SELECT DISTINCT ON (event_id)
        event_id,
        user_id,
        event_name,
        event_timestamp,
        session_id,
        app_version,
        country,
        device_platform,
        properties
    FROM raw_events
    ORDER BY event_id, event_timestamp
)

SELECT
    event_id,
    user_id,
    event_name,
    -- Normalize all timestamps to UTC
    CAST(event_timestamp AS TIMESTAMPTZ) AS event_timestamp_utc,
    CAST(CAST(event_timestamp AS TIMESTAMPTZ) AS DATE) AS event_date,
    session_id,
    app_version,
    country,
    device_platform,
    properties
FROM deduplicated
WHERE
    -- Remove rows with null user_id (cannot attribute to a user)
    user_id IS NOT NULL
    -- Remove internal test builds (release candidates)
    AND app_version NOT LIKE '%-rc%';
