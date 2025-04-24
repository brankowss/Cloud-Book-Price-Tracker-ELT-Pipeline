-- tests/dim_date_future_limit.sql

SELECT *
FROM {{ ref('dim_date') }}
WHERE full_date > DATE '2030-12-31'
