-- Create a dynamic backup table with a timestamp column
CREATE TABLE books_data_raw_backup AS 
SELECT *, CURRENT_TIMESTAMP AS backup_time 
FROM books_data_raw;


