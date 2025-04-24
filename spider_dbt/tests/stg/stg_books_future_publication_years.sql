-- tests/stg_books_future_publication_years.sql
-- Finds rows in stg_books where the publication year is in the future.
-- The test passes if this query returns 0 rows.

SELECT
    book_id,
    year_of_publication
FROM {{ ref('stg_books') }}
WHERE year_of_publication IS NOT NULL
  AND year_of_publication > EXTRACT(YEAR FROM CURRENT_DATE) -- Use the current server date
  