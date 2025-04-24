{{ config(materialized='table') }}

WITH manual_date_range AS (
    -- Start date to "last month" and the end to "2 years ago"
    SELECT
        DATE_TRUNC('MONTH', CURRENT_DATE - INTERVAL '1 month')::DATE AS start_date,  -- Beginning of last month
        CURRENT_DATE + INTERVAL '2 years' AS end_date  -- Today + 2 years
),
date_series AS (
    -- Generate all days from last month up to 2 years in advance
    SELECT generated_date::DATE
    FROM generate_series(
        (SELECT start_date FROM manual_date_range),
        (SELECT end_date FROM manual_date_range),
        '1 day'::interval
    ) AS gs(generated_date)
)
SELECT
    TO_CHAR(generated_date, 'YYYYMMDD')::INT AS date_id,
    generated_date AS full_date,
    EXTRACT(DAY FROM generated_date) AS day_of_month,
    EXTRACT(MONTH FROM generated_date) AS month_of_year,
    EXTRACT(YEAR FROM generated_date) AS year,
    EXTRACT(QUARTER FROM generated_date) AS quarter_of_year,
    TRIM(TO_CHAR(generated_date, 'Day')) AS day_name,
    EXTRACT(ISODOW FROM generated_date) AS day_of_week_iso,
    CASE
        WHEN EXTRACT(ISODOW FROM generated_date) IN (6, 7) THEN TRUE
        ELSE FALSE
    END AS is_weekend
FROM date_series





