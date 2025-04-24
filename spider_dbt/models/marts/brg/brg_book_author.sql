{{ config(materialized='table') }}

WITH source_mapping AS (
    -- We use an intermediate table where we have the pair (book_id, author_name)
    SELECT DISTINCT -- We only take unique pairs
        book_id,
        author_name
    FROM {{ ref('int_books_metadata') }}
    WHERE author_name IS NOT NULL AND author_name != ''
)
SELECT DISTINCT -- We ensure that the final output is unique
    sm.book_id,
    da.author_id
FROM source_mapping sm
-- We join with the author dimension to get the author_id (INNER JOIN ensures that we only use authors that exist in the dimension)
INNER JOIN {{ ref('dim_authors') }} da ON sm.author_name = da.author_name

