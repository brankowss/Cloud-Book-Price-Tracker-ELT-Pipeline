{{ config(materialized='table') }}

WITH latest_book_data AS (
    -- We use ROW_NUMBER to find the last record for each book based on the scan time
    SELECT
        *,
        ROW_NUMBER() OVER(PARTITION BY book_id ORDER BY scraped_at DESC) as rn
    FROM {{ ref('stg_books') }}
),
-- We join the publisher dimension to get the publisher_id
joined_publishers AS (
    SELECT
        lb.*,
        dp.publisher_id
    FROM latest_book_data lb
    LEFT JOIN {{ ref('dim_publishers') }} dp ON lb.publisher = dp.publisher_name
    WHERE lb.rn = 1 -- We only take the latest row for each book
)
-- We select the final columns for the book dimension
SELECT
    -- Keys
    jp.book_id, -- This is the natural key from the source, we use it as the PK dimension
    jp.publisher_id, -- FK to dim_publishers

    -- Descriptive Attributes (last known values)
    jp.title,
    jp.category, 
    jp.isbn,
    jp.script_type,
    jp.page_numbers,
    jp.year_of_publication,
    
    -- Audit columns (useful to know when it was last seen/updated)
    jp.scraped_at AS last_scraped_at, 
    jp.updated_at AS dbt_last_processed_at

FROM joined_publishers jp