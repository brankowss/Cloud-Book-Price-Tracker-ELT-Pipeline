CREATE TABLE IF NOT EXISTS brg.book_author (
    book_id INT REFERENCES fact.books(book_id),
    author_id INT REFERENCES dim.author(author_id),
    PRIMARY KEY (book_id, author_id)
);