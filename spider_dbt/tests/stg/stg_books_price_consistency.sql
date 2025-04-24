-- tests/stg_books_price_consistency.sql
-- Finds rows in stg_books where the discounted price is greater than the old price.
-- The test passes if this query returns 0 rows.

SELECT
    book_id,
    old_price,
    discount_price
FROM {{ ref('stg_books') }}
WHERE discount_price IS NOT NULL -- Only where there is a discounted price
  AND old_price IS NOT NULL -- And where there is an old price
  AND discount_price > old_price 

