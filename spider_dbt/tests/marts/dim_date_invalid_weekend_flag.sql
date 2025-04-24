-- tests/marts/dim_date_invalid_weekend_flag.sql
SELECT date_id, full_date, day_of_week_iso, is_weekend
FROM {{ ref('dim_date') }}
WHERE is_weekend != (EXTRACT(ISODOW FROM full_date) IN (6,7))