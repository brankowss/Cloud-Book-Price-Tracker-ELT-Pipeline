"""
# Data Cleaning Pipeline

This DAG handles the data cleaning and transformation process before loading into final tables.

## Tasks:
1. **Backup**: Creates backup of raw data
2. **Cleaning**: Removes duplicates, invalid entries
3. **Transformation**: Standardizes formats and values
4. **Normalization**: Structures data for optimal storage
5. **Load**: Moves cleaned data to production tables

## Dependencies:
- Each step must complete successfully before next begins
- Final validation triggered after clean data load

## SQL Files:
- All SQL operations located in /opt/sql, /opt/modeling, or /opt/tests
"""

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=10)
}

with DAG(
    "clean_data_pipeline",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    template_searchpath=['/opt/sql', '/opt/modeling', '/opt/tests'],
    description="Cleans and transforms raw scraped data",
    tags=['data_cleaning', 'transformation'],
    doc_md=__doc__
) as dag:

    backup_table = PostgresOperator(
        task_id="backup_raw_data",
        postgres_conn_id="postgres_default",
        sql="backup.sql",
    )

    clean_data = PostgresOperator(
        task_id="clean_raw_data",
        postgres_conn_id="postgres_default",
        sql="clean_data.sql",
    )

    transform_data = PostgresOperator(
        task_id="transform_data",
        postgres_conn_id="postgres_default",
        sql="transform_data.sql",
    )

    delete_rename = PostgresOperator(
        task_id="finalize_transformation",
        postgres_conn_id="postgres_default",
        sql="delete_rename.sql",
    )

    normalize_data = PostgresOperator(
        task_id="normalize_structures",
        postgres_conn_id="postgres_default",
        sql="normalize_data.sql",
    )

    load_cleaned_data = PostgresOperator(
        task_id="load_cleaned_data",
        postgres_conn_id="postgres_default",
        sql="load_cleaned_data.sql",
    )

    trigger_model_data = TriggerDagRunOperator(
        task_id="trigger_model_loading",
        trigger_dag_id="model_data_pipeline",
        wait_for_completion=True
    )

    backup_table >> clean_data >> transform_data >> delete_rename >> normalize_data >> load_cleaned_data >> trigger_model_data

