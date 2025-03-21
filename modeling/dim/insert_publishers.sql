INSERT INTO dim.publisher (publisher_name, scraped_at)
SELECT DISTINCT publisher, scraped_at 
FROM public.books_cleaned_data
ON CONFLICT (publisher_name) DO NOTHING;