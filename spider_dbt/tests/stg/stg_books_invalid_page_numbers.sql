-- tests/stg_books_invalid_page_numbers.sql
-- Finds rows in stg_books where page_numbers is not a positive integer.
-- The test passes if this query returns 0 rows.

SELECT
    book_id,
    page_numbers
FROM {{ ref('stg_books') }}
WHERE page_numbers IS NOT NULL -- Just check the rows where the page number exists.
  AND page_numbers <= 0