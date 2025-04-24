-- analyses/avg_price_per_publisher.sql
-- Shows average, min, max price and number of books per publisher

SELECT 
    p.publisher_name,
    COUNT(DISTINCT f.book_id) as distinct_books_count, -- Number of different books from that publisher that have a price
    AVG(f.discount_price) as average_discount_price, -- Average price with discount
    MIN(f.discount_price) as min_discount_price,     -- Minimum price with discount
    MAX(f.discount_price) as max_discount_price      -- Maximum price with discount
FROM {{ ref('fct_book_prices') }} f
JOIN {{ ref('dim_publishers') }} p ON f.publisher_id = p.publisher_id
WHERE f.discount_price IS NOT NULL --  Only if the price exists
GROUP BY 
    p.publisher_name -- Group by publisher name
ORDER BY 
    average_discount_price DESC; -- Sort by average price descending (or by name: ORDER BY 1)