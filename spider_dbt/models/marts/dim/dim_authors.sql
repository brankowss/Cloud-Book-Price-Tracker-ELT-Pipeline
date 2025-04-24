{{ config(materialized='table') }}

WITH source AS (
    -- We take unique author names from the intermediate table
    SELECT DISTINCT author_name 
    FROM {{ ref('int_books_metadata') }}
    WHERE author_name IS NOT NULL AND author_name != '' -- We ignore empty or NULL values
)
SELECT
    -- We generate a surrogate key using dbt_utils
    {{ dbt_utils.generate_surrogate_key(['author_name']) }} AS author_id, 
    author_name
FROM source



