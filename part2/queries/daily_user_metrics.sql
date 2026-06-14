-- daily_user_metrics.sql
-- Silver → Gold: aggregate clean events into daily metrics

SELECT
    event_date,
    COUNT(DISTINCT user_id) AS dau,
    COUNT(DISTINCT session_id) AS sessions,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT session_id), 2) AS events_per_session,
    -- Bonus: new users (first appearance in dataset)
    COUNT(DISTINCT CASE
        WHEN event_date = first_seen THEN user_id
    END) AS new_users
FROM clean_events
LEFT JOIN (
    SELECT user_id, MIN(event_date) AS first_seen
    FROM clean_events
    GROUP BY user_id
) user_first USING (user_id)
GROUP BY event_date
ORDER BY event_date;
