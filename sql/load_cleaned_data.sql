-- Create a new table with the same structure as books_data_raw (PostgreSQL-compatible)
CREATE TABLE IF NOT EXISTS books_cleaned_data AS 
TABLE books_data_raw 
LIMIT 0;

-- Insert all data from the source table into the new table
INSERT INTO books_cleaned_data 
SELECT * FROM books_data_raw;

ALTER TABLE books_cleaned_data
ADD PRIMARY KEY (id); 


