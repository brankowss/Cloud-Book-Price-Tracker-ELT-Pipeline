{{ config(materialized='table') }}

WITH source AS (
    -- We take unique publisher names from the staging table
    SELECT DISTINCT publisher -- We use the final publisher column from stg_books
    FROM {{ ref('stg_books') }}
    WHERE publisher IS NOT NULL 
      AND publisher != '' 
)
SELECT
    -- We generate SK
    {{ dbt_utils.generate_surrogate_key(['publisher']) }} AS publisher_id, 
    publisher AS publisher_name
FROM source


