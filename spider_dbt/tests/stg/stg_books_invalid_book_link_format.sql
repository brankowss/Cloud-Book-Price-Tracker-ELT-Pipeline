-- tests/staging/stg_books_invalid_book_link_format.sql
-- Finds rows where book_link is NOT NULL, but does not start with http:// ili https://
-- The test passes if this query returns 0 rows.

SELECT 
    book_id,
    book_link
FROM {{ ref('stg_books') }}
WHERE 
    book_link IS NOT NULL
    -- Checks if the link starts with http:// or https:// (case-insensitive)
    -- Operator '~*' works case-insensitive regex match in PostgreSQL-u
    AND book_link !~* '^https?://.+' 
   