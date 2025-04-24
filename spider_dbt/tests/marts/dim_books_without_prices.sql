-- tests/marts/dim_books_without_prices.sql
SELECT b.book_id
FROM {{ ref('dim_books') }} b
LEFT JOIN {{ ref('fct_book_prices') }} bp ON b.book_id = bp.book_id
WHERE bp.book_price_daily_pk IS NULL -- No related prices (use PK fact table)