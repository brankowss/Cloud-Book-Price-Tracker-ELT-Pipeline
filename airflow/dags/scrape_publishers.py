"""
# Scrapy to PostgreSQL Pipeline

This DAG coordinates the web scraping process using Scrapy spiders and triggers the data cleaning pipeline.

## Tasks:
1. **Run Spiders**: Executes 3 different Scrapy spiders (laguna, mikrok, prometej)
2. **Trigger Cleaning**: Starts the data cleaning pipeline after successful scraping

## Dependencies:
- Spiders run sequentially to avoid overloading websites
- Cleaning process starts only after all spiders complete

## Connections:
- Uses default PostgreSQL connection for any potential metadata tracking
- Scrapy project located at `/opt/booksscraper` (Docker volume)
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5)
}

with DAG(
    "scrapy_to_postgres",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    description="Orchestrates book data scraping from multiple sources",
    tags=['scraping', 'data_collection'],
    doc_md=__doc__
) as dag:
    
    run_spider1 = BashOperator(
        task_id="run_laguna_spider",
        bash_command="cd /opt/booksscraper && scrapy crawl laguna",
    )

    run_spider2 = BashOperator(
        task_id="run_mikrok_spider",
        bash_command="cd /opt/booksscraper && scrapy crawl mikrok",
    )

    run_spider3 = BashOperator(
        task_id="run_prometej_spider",
        bash_command="cd /opt/booksscraper && scrapy crawl prometej",
    )

    trigger_clean_data = TriggerDagRunOperator(
        task_id="trigger_clean_data_dag",
        trigger_dag_id="clean_data_pipeline",
        wait_for_completion=True,
        params={
            "message": "Scraping completed, starting data cleaning"
        }
    )

    run_spider1 >> run_spider2 >> run_spider3 >> trigger_clean_data
