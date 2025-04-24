-- tests/stg_books_price_outliers.sql
-- Finds rows where prices deviate significantly from the average.
-- The test passes if this query returns 0 rows.

WITH stats AS (
    SELECT
        AVG(old_price) AS avg_old_price,
        STDDEV_SAMP(old_price) AS stddev_old_price, -- Sample standard deviation
        AVG(discount_price) AS avg_discount_price,
        STDDEV_SAMP(discount_price) AS stddev_discount_price
    FROM {{ ref('stg_books') }}
    WHERE old_price IS NOT NULL OR discount_price IS NOT NULL -- Calculate based on current prices
)
SELECT
    t.book_id,
    t.old_price,
    t.discount_price
FROM {{ ref('stg_books') }} t
CROSS JOIN stats s -- Join statistics with each row
WHERE (
        t.old_price IS NOT NULL AND
        s.stddev_old_price IS NOT NULL AND -- Avoid division by zero or NULL if stddev 0
        s.stddev_old_price > 0 AND
        t.old_price > (s.avg_old_price + 5 * s.stddev_old_price)
      )
   OR (
        t.discount_price IS NOT NULL AND
        s.stddev_discount_price IS NOT NULL AND
        s.stddev_discount_price > 0 AND
        t.discount_price > (s.avg_discount_price + 5 * s.stddev_discount_price)
      )