-- analyses/price_change_last_month.sql
-- Finds books with the biggest price change in the last ~month

WITH latest_date AS (
    -- Finds the latest date for which we have data
    SELECT MAX(date_id) as max_date_id, MAX(full_date) as max_date
    FROM {{ ref('dim_date') }}
    WHERE full_date <= CURRENT_DATE 
),Finds the latest date for which we have data
month_ago_date AS (
    -- Finds the date closest to the date of one month ago (relative to the latest date)
    SELECT MAX(date_id) as month_ago_date_id
    FROM {{ ref('dim_date') }}
    WHERE full_date <= (SELECT max_date FROM latest_date) - INTERVAL '1 month' -- You can set the interval (eg '30 days')
),
current_prices AS (
    -- Prices for the latest date
    SELECT book_id, discount_price 
    FROM {{ ref('fct_book_prices') }}
    WHERE date_id = (SELECT max_date_id FROM latest_date)
),
past_prices AS (
    -- Prices for a date from a month ago
    SELECT book_id, discount_price
    FROM {{ ref('fct_book_prices') }}
    WHERE date_id = (SELECT month_ago_date_id FROM month_ago_date)
)
-- We combine current and past prices, calculate the change and display the title
SELECT 
    b.title,
    p.publisher_name,
    pp.discount_price AS price_month_ago,
    cp.discount_price AS price_latest,
    (cp.discount_price - pp.discount_price) AS absolute_change -- Absolute change
    -- You can also add a percentage change if you want leter try:
    -- , CASE WHEN pp.discount_price != 0 THEN (cp.discount_price - pp.discount_price) * 100.0 / pp.discount_price ELSE NULL END AS percentage_change
FROM current_prices cp
-- We only combine books that have a price on BOTH dates
JOIN past_prices pp ON cp.book_id = pp.book_id
-- We combine with dimensions for context
JOIN {{ ref('dim_books') }} b ON cp.book_id = b.book_id
JOIN {{ ref('dim_publishers') }} p ON b.publisher_id = p.publisher_id
WHERE cp.discount_price IS NOT NULL AND pp.discount_price IS NOT NULL -- We only look at where both prices exist
ORDER BY 
    absolute_change DESC -- Sort by highest price increase (or ASC for decrease, or use percentage_change)
LIMIT 100; -- Show top 100