-- analyses/newly_added_books.sql
-- Shows books that have been viewed for the first time in the last 7 days

WITH first_seen AS (
    -- For each book, we find the earliest date it had a price record
    SELECT
        f.book_id,
        MIN(d.full_date) as first_seen_date
    FROM {{ ref('fct_book_prices') }} f
    JOIN {{ ref('dim_date') }} d ON f.date_id = d.date_id
    GROUP BY 
        f.book_id -- Grupišemo po knjizi
)
-- We select books whose first seen date is within the last 7 days
SELECT
    b.title,
    p.publisher_name,
    b.book_id,
    fs.first_seen_date
FROM first_seen fs
JOIN {{ ref('dim_books') }} b ON fs.book_id = b.book_id
JOIN {{ ref('dim_publishers') }} p ON b.publisher_id = p.publisher_id
WHERE fs.first_seen_date >= CURRENT_DATE - INTERVAL '7 days' -- You can change the interval (eg '1 month')
ORDER BY 
    fs.first_seen_date DESC, -- Show newest first
    b.title;