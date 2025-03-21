CREATE TABLE IF NOT EXISTS dim.author (
    author_id SERIAL PRIMARY KEY,
    author_name TEXT UNIQUE  
   
);