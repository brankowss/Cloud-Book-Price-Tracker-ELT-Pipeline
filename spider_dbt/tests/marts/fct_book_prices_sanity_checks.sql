-- tests/marts/fct_book_prices_sanity_checks.sql
SELECT 
    book_price_daily_pk, -- Return the ID of the row that fails the test
    book_id,
    date_id,
    old_price,
    discount_price
FROM {{ ref('fct_book_prices') }}
WHERE (old_price IS NOT NULL AND old_price < 0)
   OR (discount_price IS NOT NULL AND discount_price < 0)
   OR (old_price IS NOT NULL AND discount_price IS NOT NULL AND discount_price > old_price)