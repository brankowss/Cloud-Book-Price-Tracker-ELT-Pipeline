INSERT INTO fact.books (
    title, book_link, year_of_publication, 
    script_type, page_numbers, publisher_id, scraped_at
)
SELECT 
    bc.title, bc.book_link, bc.year_of_publication,
    bc.script_type, bc.page_numbers, 
    p.publisher_id, bc.scraped_at
FROM public.books_cleaned_data bc
JOIN dim.publisher p ON bc.publisher = p.publisher_name;