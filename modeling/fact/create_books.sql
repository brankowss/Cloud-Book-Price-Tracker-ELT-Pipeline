CREATE TABLE IF NOT EXISTS fact.books (
    book_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    book_link TEXT,
    year_of_publication INT,
    script_type TEXT,
    page_numbers INT,
    publisher_id INT REFERENCES dim.publisher(publisher_id),
    scraped_at TIMESTAMP
);
