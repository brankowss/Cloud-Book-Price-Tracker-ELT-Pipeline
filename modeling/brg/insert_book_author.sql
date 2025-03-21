WITH split_authors AS (
  SELECT 
    bc.id AS book_id,
    TRIM(UNNEST(STRING_TO_ARRAY(bc.author, ','))) AS author_name
  FROM public.books_cleaned_data bc
)
INSERT INTO brg.book_author (book_id, author_id)
SELECT 
    b.book_id, 
    a.author_id
FROM split_authors sa
JOIN fact.books b ON sa.book_id = b.book_id
JOIN dim.author a ON sa.author_name = a.author_name;