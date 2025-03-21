WITH split_authors AS (
  SELECT 
    id AS book_id,
    TRIM(UNNEST(STRING_TO_ARRAY(author, ','))) AS author_name
  FROM books_cleaned_data
)
INSERT INTO dim.author (author_name)  
SELECT DISTINCT author_name FROM split_authors
ON CONFLICT (author_name) DO NOTHING;  