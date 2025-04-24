-- tests/stg_books_completeness.sql
-- Finds IDs from raw data that are not in stg_books.
-- The test passes if this query returns 0 rows.
{{ config(
    tags=["stg"]
) }}

SELECT r.id
FROM {{ source('raw', 'books_data_raw') }} r -- Raw data reference
LEFT JOIN {{ ref('stg_books') }} c ON md5(trim(r.book_link)) = c.book_id
-- LEFT JOIN {{ ref('stg_books') }} c ON r.id = c.book_id -- Reference to cleaned data 
WHERE c.book_id IS NULL -- If it is NULL, it means that the ID from the raw table does not exist in the cleaned table