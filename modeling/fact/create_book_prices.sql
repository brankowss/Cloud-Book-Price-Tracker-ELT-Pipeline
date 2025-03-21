CREATE TABLE IF NOT EXISTS fact.books_prices (
    price_id SERIAL PRIMARY KEY,
    book_id INT REFERENCES fact.books(book_id),
    old_price NUMERIC(10,2),
    discount_price NUMERIC(10,2),
    currency_id INT REFERENCES dim.currency(currency_id),
    scraped_at TIMESTAMP,
    date_id INT REFERENCES dim.date(date_id), 
    is_current BOOLEAN DEFAULT TRUE
);
