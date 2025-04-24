{{ config(
    materialized='incremental',
    unique_key='book_price_daily_pk'
) }}


WITH source_data AS (
    -- We take data from the staging table
    SELECT * FROM {{ ref('stg_books') }}

    {% if is_incremental() %}
      -- For an incremental run, we process only rows that have been scanned
      -- after the last successfully processed scan in this table.
      -- We use max_scraped_at that we saved in the last step.
      WHERE scraped_at > (SELECT MAX(max_scraped_at) FROM {{ this }})
    {% endif %}
),

-- We rank scans within the same day for the same book, taking the most recent
latest_scrape_per_day AS (
    SELECT
        *,
        ROW_NUMBER() OVER(PARTITION BY book_id, scraped_at::DATE ORDER BY scraped_at DESC) as rn_per_day
    FROM source_data
),

-- We join with dimensions to get foreign keys
joined_with_dims AS (
    SELECT
        -- We generate Surrogate Primary Key for fact table (combination of book and date)
        {{ dbt_utils.generate_surrogate_key(['lsd.book_id', 'lsd.scraped_at::DATE']) }} AS book_price_daily_pk, 
        
        -- Foreign Keys
        lsd.book_id,
        dd.date_id,
        dp.publisher_id,
        -- Don't need currency_id if is not created a dimension right now 

        -- Measures
        lsd.old_price,
        lsd.discount_price,
        lsd.currency, -- We store the currency code directly here

        -- We save the exact scan time for potential more detailed analysis
        (lsd.scraped_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Belgrade') AS scraped_at,

        -- We keep the max scan time per PK for the next incremental run
        -- (If PK is book_id+date, the max scraped_at for that day is relevant)
        MAX(lsd.scraped_at) OVER (PARTITION BY lsd.book_id, lsd.scraped_at::DATE) as max_scraped_at_for_pk

    FROM latest_scrape_per_day lsd
    -- Join with date dimension based on date (without time)
    LEFT JOIN {{ ref('dim_date') }} dd ON lsd.scraped_at::DATE = dd.full_date 
    --  Join with the publisher dimension based on name
    LEFT JOIN {{ ref('dim_publishers') }} dp ON lsd.publisher = dp.publisher_name
    
    WHERE lsd.rn_per_day = 1 -- We only take the most recent scan for that day for that book
    --   AND dd.date_id IS NOT NULL -- Optional: ensures we have a date in the dimension
      -- AND dp.publisher_id IS NOT NULL -- Optional: ensures we have a publisher in the dimension
)
-- Final selection for the fact table
SELECT
  jwd.book_price_daily_pk,
  jwd.book_id,
  jwd.date_id,
  jwd.publisher_id,
  jwd.currency,
  jwd.old_price,
  jwd.discount_price,
  jwd.max_scraped_at_for_pk AS max_scraped_at -- Rename it for incremental logic
  -- We don't need scraped_at here because we have date_id and max_scraped_at is for incremental
FROM joined_with_dims jwd
-- No need to group if book_price_daily_pk is really unique after filter rn_per_day=1

