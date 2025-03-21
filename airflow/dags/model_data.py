"""
# Data Modeling Pipeline (Normalized Schema)

This DAG creates and populates a star schema optimized for book analytics. 
Trigger manually after data cleaning completes.

## Tasks:
1. **Schema & Table Creation**:
   - Creates `dim`, `fact`, `brg` schemas
   - Dimension Tables: publishers, authors, currencies, date
   - Fact Tables: books, book_prices
   - Bridge Table: book_author

2. **Data Loading**:
   - Dimensions: Publishers, Authors, Currencies, Dates
   - Facts: Book metadata, Historical prices
   - Relationships: Book-Author mappings

3. **Data Integrity**:
   - Referential integrity checks
   - Price history tracking (is_current flag)
   - Multi-author validation
   - Temporal data validation

4. **Validation Trigger**:
   - Initiates data quality checks post-load

## Dependencies:
- Requires cleaned data from `clean_data_pipeline`  
- Expects tables in `public` schema:
  - books_cleaned_data
  - books_scrapy_stats

## SQL Structure:
├── dim/
│   ├── create_publishers.sql
│   ├── insert_publishers.sql
│   ├── create_date.sql
│   └── ...
├── fact/
│   ├── create_books.sql
│   ├── insert_books.sql
│   ├── create_book_prices.sql
│   └── ...
└── brg/
    ├── create_book_author.sql
    └── insert_book_author.sql

## Data Flow:
Cleaned Data → Dimensions → Facts → Bridge Tables → Validation

## Key Improvements:
- Historical price tracking with date dimension
- Multi-author support via bridge table
- Currency normalization
- Schema isolation (dim/fact/brg)
"""

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1)
}

with DAG(
    "model_data_pipeline",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    template_searchpath=[
        '/opt/sql', 
        '/opt/modeling', 
        '/opt/modeling/dim',
        '/opt/modeling/fact',
        '/opt/modeling/brg'
    ],
    tags=['data_modeling', 'production'],
    description='Creates and populates structured book data models',
    doc_md=__doc__
) as dag:
    
    # ===== SCHEMA CREATION =====
    create_schemas = PostgresOperator(
        task_id="create_schemas",
        sql="create_schemas.sql"
    )

    # ===== DIMENSION CREATION (SEQUENTIAL) =====
    create_publishers_table = PostgresOperator(
        task_id="create_publishers_table",
        sql="dim/create_publishers.sql",
        postgres_conn_id="postgres_default"
    )

    create_authors_table = PostgresOperator(
        task_id="create_authors_table",
        sql="dim/create_authors.sql",
        postgres_conn_id="postgres_default"
    )

    create_currency_table = PostgresOperator(
        task_id="create_currency_table",
        sql="dim/create_currency.sql",
        postgres_conn_id="postgres_default"
    )

    # ===== DATE DIMENSION =====
    create_date_table = PostgresOperator(
        task_id="create_date_table",
        sql="dim/create_date.sql",
        postgres_conn_id="postgres_default"
    )

    # ===== FACT TABLES =====
    create_fact_book = PostgresOperator(
        task_id="create_fact_book",
        sql="fact/create_books.sql",
        postgres_conn_id="postgres_default"
    )

    # ===== BRIDGE TABLE =====
    create_brg = PostgresOperator(
        task_id="create_brg",
        sql="brg/create_book_author.sql",
        postgres_conn_id="postgres_default"
    )

    # ===== PRICE HISTORY TABLE =====
    create_book_prices_table = PostgresOperator(
        task_id="create_price_table",
        sql="fact/create_book_prices.sql",
        postgres_conn_id="postgres_default"
    )

    # ===== DATA LOADING =====
    load_publishers = PostgresOperator(
        task_id="load_publishers",
        sql="dim/insert_publishers.sql",
        postgres_conn_id="postgres_default"
    )

    load_authors = PostgresOperator(
        task_id="load_authors",
        sql="dim/insert_authors.sql",
        postgres_conn_id="postgres_default"
    )

    load_currency = PostgresOperator(
        task_id="load_currency",
        sql="dim/insert_currency.sql",
        postgres_conn_id="postgres_default"
    )

    insert_dates = PostgresOperator(
        task_id="load_dates",
        sql="dim/insert_date.sql",
        postgres_conn_id="postgres_default"
    )

    load_facts = PostgresOperator(
        task_id="load_facts",
        sql="fact/insert_books.sql",
        postgres_conn_id="postgres_default"
    )

    load_brg = PostgresOperator(
        task_id="load_brg",
        sql="brg/insert_book_author.sql",
        postgres_conn_id="postgres_default"
    )

    insert_book_prices = PostgresOperator(
        task_id="load_prices",
        sql="fact/insert_book_prices.sql",
        postgres_conn_id="postgres_default"
    )

    # ===== VALIDATION TRIGGER =====
    trigger_validation = TriggerDagRunOperator(
        task_id='trigger_validation_dag',
        trigger_dag_id='data_validation',
        wait_for_completion=False,
        params={
            'source_dag': 'model_data_pipeline',
            'dataset_version': '1.0'
        }
    )

    # ===== CORRECTED DEPENDENCIES =====
    (
        create_schemas 
        >> create_publishers_table
        >> create_authors_table
        >> create_currency_table
        >> [create_date_table, create_fact_book]
        >> create_brg
        >> create_book_prices_table
        >> load_publishers
        >> load_authors
        >> load_currency
        >> insert_dates
        >> load_facts
        >> load_brg
        >> insert_book_prices
        >> trigger_validation
    )
    
