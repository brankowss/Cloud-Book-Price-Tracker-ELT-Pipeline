-- Delete rows with missing critical data
DELETE FROM books_data_raw
WHERE title IS NULL OR title = ''
   OR author IS NULL OR author = ''
   OR book_link IS NULL OR book_link = '';

-- Trim whitespace from all relevant text fields
UPDATE books_data_raw
SET title = TRIM(title),
    author = TRIM(author),
    book_link = TRIM(book_link),
    old_price = TRIM(old_price),
    discount_price = TRIM(discount_price),
    currency = TRIM(currency),
    publisher = TRIM(publisher),
    description = TRIM(description);

    


