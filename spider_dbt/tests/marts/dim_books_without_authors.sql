    -- tests/marts/dim_books_without_authors.sql
    SELECT b.book_id
    FROM {{ ref('dim_books') }} b
    LEFT JOIN {{ ref('brg_book_author') }} ba ON b.book_id = ba.book_id
    WHERE ba.author_id IS NULL