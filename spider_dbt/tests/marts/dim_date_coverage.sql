-- tests/marts/dim_date_coverage.sql
WITH dates_in_staging AS (
  SELECT DISTINCT scraped_at::DATE AS scraped_date 
  FROM {{ ref('stg_books') }}
  WHERE scraped_at IS NOT NULL
)
SELECT src.scraped_date
FROM dates_in_staging src
LEFT JOIN {{ ref('dim_date') }} d ON src.scraped_date = d.full_date
WHERE d.date_id IS NULL -- The staging date does not exist in the date dimension.

