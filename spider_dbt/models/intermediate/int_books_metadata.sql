-- models/intermediate/int_books_metadata.sql

WITH staging_data AS (
    -- We select everything from the staging model
    SELECT * FROM {{ ref('stg_books') }}
),

split_authors AS (
    -- We use PostgreSQL functions to separate authors
    SELECT
        book_id,
        -- TRIM removes spaces before/after commas and before/after author names
        TRIM(UNNEST(STRING_TO_ARRAY(author, ','))) AS author_name 
    FROM staging_data
    WHERE author IS NOT NULL AND author != '' -- We make sure not to split NULL or empty strings
),

joined_data AS (
    SELECT
        sd.book_id,
        -- This JOIN will MULTIPLY the rows if there are multiple authors.
        sa.author_name, 
        sd.title,
        sd.category,
        sd.year_of_publication,
        sd.script_type,
        sd.page_numbers,
        sd.publisher AS publisher_name, -- Renamed for clarity
        sd.currency,
        sd.old_price,
        sd.discount_price,
        sd.scraped_at,
        sd.updated_at 

    FROM staging_data sd
    -- LEFT JOIN to save books even if they have no authors (although split_authors filters NULL/empty)
    LEFT JOIN split_authors sa ON sd.book_id = sa.book_id 
)

SELECT * FROM joined_data

