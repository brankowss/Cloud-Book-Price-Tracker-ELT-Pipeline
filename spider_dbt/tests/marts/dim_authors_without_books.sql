-- tests/marts/dim_authors_without_books.sql
SELECT a.author_id
FROM {{ ref('dim_authors') }} a
LEFT JOIN {{ ref('brg_book_author') }} ba ON a.author_id = ba.author_id
WHERE ba.book_id IS NULL