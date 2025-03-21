INSERT INTO dim.currency (currency_code)
SELECT DISTINCT currency 
FROM public.books_cleaned_data 
ON CONFLICT (currency_code) DO NOTHING;  