-- tests/marts/dim_publishers_without_books.sql
SELECT p.publisher_id
FROM {{ ref('dim_publishers') }} p
LEFT JOIN {{ ref('dim_books') }} b ON p.publisher_id = b.publisher_id
WHERE b.book_id IS NULL -- There are no related books in dim_books