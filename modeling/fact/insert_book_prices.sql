WITH latest_prices AS (
  SELECT 
    b.book_id,
    bc.old_price,
    bc.discount_price,
    c.currency_id,
    bc.scraped_at,
    d.date_id 
  FROM public.books_cleaned_data bc
  JOIN fact.books b ON b.title = bc.title
  JOIN dim.currency c ON c.currency_code = bc.currency
  JOIN dim.date d ON bc.scraped_at::DATE = d.date 
)

INSERT INTO fact.books_prices (
  book_id, old_price, discount_price, 
  currency_id, scraped_at, date_id, is_current
)
SELECT 
  book_id,
  old_price,
  discount_price,
  currency_id,
  scraped_at,
  date_id, 
  TRUE
FROM latest_prices;
