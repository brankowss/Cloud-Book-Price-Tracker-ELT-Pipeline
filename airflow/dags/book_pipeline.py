"""
Secure Book Ingestion and Transformation Pipeline
Data Flow: Scrapy -> S3 -> Validate S3 -> Load Raw PG -> Test Raw (dbt) -> Transform (dbt) -> Test Models (dbt) -> Telegram Alerts
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from airflow.hooks.postgres_hook import PostgresHook
from airflow.exceptions import AirflowException
from airflow.models import Connection
from datetime import datetime, timedelta
import logging
import pandas as pd
from io import StringIO
import json
import os 
import requests
from pytz import timezone, UTC

# Configuration
S3_BUCKET = Variable.get("S3_BUCKET_NAME")
TELEGRAM_CHAT_ID = Variable.get("TELEGRAM_CHAT_ID")
DBT_PROJECT_DIR = '/opt/spider_dbt'
PUBLISHERS = json.loads(Variable.get("PUBLISHERS", default_var='["laguna", "mikrok", "prometej"]'))

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': lambda context: send_telegram_message(
        context,
        f"🚨 *Pipeline Failed: {context.get('dag').dag_id}*\n"
        f"- *Failed Task*: {context.get('task_instance').task_id}\n"
        f"- *Time (UTC+1)*: {datetime.now(timezone('Europe/Belgrade')).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- *Reason*: {context.get('exception')}"
    )
}

def send_telegram_message(context, message):
    """Sends message to Telegram using Airflow Connection"""
    try:
        conn_id = "telegram_conn"
        conn = Connection.get_connection_from_secrets(conn_id)
        bot_token = conn.password
        chat_id = conn.login
        
        if not bot_token or not chat_id:
            logging.error("Telegram bot token or chat ID is missing in Airflow connection.")
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to send Telegram notification: {e}")

def validate_s3_data(**context):
    """Validate that all publishers have data in S3"""
    s3_hook = S3Hook(
        aws_conn_id='aws_conn',
        region_name=Variable.get("AWS_REGION")
    )
    missing_publishers = []
    
    for publisher in PUBLISHERS:
        prefix = f"books_publishers/{publisher}/"
        keys = s3_hook.list_keys(S3_BUCKET, prefix=prefix)
        if not keys:
            missing_publishers.append(publisher)
    
    if missing_publishers:
        raise AirflowException(f"No data found for publishers: {', '.join(missing_publishers)}")

def load_to_postgres(**context):
    """Load all CSV files from S3 into PostgreSQL"""
    pg_hook = PostgresHook(
        postgres_conn_id='postgres_conn',
        sslmode='require'  # Critical for RDS connection
    )
    total_inserted = 0

    for publisher in PUBLISHERS:
        prefix = f"books_publishers/{publisher}/"
        keys = s3_hook.list_keys(S3_BUCKET, prefix=prefix)
        
        for key in keys:
            try:
                csv_content = s3_hook.read_key(key, S3_BUCKET)
                df = pd.read_csv(StringIO(csv_content), dtype=str)
                df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

                required_columns = [
                    'title', 'author', 'book_link', 'category', 'old_price',
                    'discount_price', 'currency', 'publisher', 'description', 'scraped_at'
                ]

                if not set(required_columns).issubset(df.columns):
                    missing = set(required_columns) - set(df.columns)
                    logging.warning(f"Skipping {key} - missing columns: {missing}")
                    continue

                buffer = StringIO()
                df[required_columns].to_csv(buffer, index=False, header=False)
                buffer.seek(0)

                with pg_hook.get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.copy_expert(f"""
                            COPY raw.books_data_raw ({', '.join(required_columns)}) 
                            FROM STDIN WITH CSV HEADER DELIMITER ','
                        """, buffer)
                        inserted = cur.rowcount
                        total_inserted += inserted
                        conn.commit()
                        
                logging.info(f"Loaded {inserted} rows from {key}")

            except Exception as e:
                logging.error(f"Failed to load {key}: {str(e)}")
                continue

    context['ti'].xcom_push(key='inserted_rows', value=total_inserted)

def success_notification(**context):
    """Sends success notification to Telegram"""
    current_time_utc_plus_1 = datetime.now(timezone('Europe/Berlin'))
    inserted = context['ti'].xcom_pull(key='inserted_rows', task_ids='load_to_postgres') or 0

    message = (
        "✅ *PIPELINE SUCCESS* ✅\n"
        f"📅 *Date:* {current_time_utc_plus_1.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📚 *Books Loaded:* {inserted}\n"
        f"✨ *dbt Models Run & Tested Successfully*"
    )
    send_telegram_message(context, message)

with DAG(
    dag_id='book_ingestion_and_transformation',
    default_args=default_args,
    schedule_interval='30 0 * * *',  # 00:30 UTC = 01:30 in Belgrade,
    catchup=False,
    max_active_runs=1,
    doc_md="""
    ## Book Pipeline Summary
    - Scrapes book data using Scrapy spiders 
    - Validates structure from S3
    - Loads into raw PostgreSQL table
    - dbt runs and tests transformations
    - Telegram used for monitoring and real-time notifications
    """
) as dag:

    create_schema_tables = PostgresOperator(
        task_id='create_schema_tables',
        postgres_conn_id='postgres_conn',
        sql="""
            CREATE SCHEMA IF NOT EXISTS raw;
            CREATE TABLE IF NOT EXISTS raw.books_data_raw (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT,
                book_link TEXT NOT NULL,
                category TEXT,
                old_price TEXT,
                discount_price TEXT,
                currency VARCHAR(3) DEFAULT 'RSD',
                publisher TEXT NOT NULL,
                description TEXT,
                scraped_at TIMESTAMPTZ NOT NULL
            );
            CREATE SCHEMA IF NOT EXISTS pipeline_monitoring;
            CREATE TABLE IF NOT EXISTS pipeline_monitoring.books_scrapy_stats (
                id SERIAL PRIMARY KEY,
                spider_name TEXT,
                item_scraped_count INTEGER,
                response_received_count INTEGER,
                request_count INTEGER,
                start_time TIMESTAMPTZ,
                finish_time TIMESTAMPTZ,
                duration FLOAT,
                run_timestamp TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') + INTERVAL '2 hours'
            );

            -- Dodaj i CREATE SCHEMA IF NOT EXISTS dbt_dbt; (ili koja ti je target šema za dbt)
            CREATE SCHEMA IF NOT EXISTS dbt_dbt; 

            -- Dodaj i CREATE SCHEMA IF NOT EXISTS snapshots; (ako koristiš snapshotove)
            -- CREATE SCHEMA IF NOT EXISTS snapshots; later in project  
        """
    )

    scrape_tasks = []
    for publisher in PUBLISHERS:
        scrape_task = BashOperator(
            task_id=f'scrape_{publisher.replace(" ", "_").lower()}',
            bash_command=f'cd /opt/booksscraper && scrapy crawl {publisher}'
        )
        scrape_tasks.append(scrape_task)

    validate_s3 = PythonOperator(
        task_id='validate_s3_data',
        python_callable=validate_s3_data
    )

    load_raw = PythonOperator(
        task_id='load_to_postgres',
        python_callable=load_to_postgres
    )

    dbt_source_test = BashOperator(
        task_id='dbt_source_test',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --select source:raw.books_data_raw --exclude tag:stg',
        trigger_rule='all_done'
    )

    dbt_run = BashOperator(
        task_id='dbt_run_models',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt run',
        trigger_rule='all_success'
    )

    dbt_model_test = BashOperator(
        task_id='dbt_model_test',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt test',
        trigger_rule='all_success'
    )

    notify_success = PythonOperator(
        task_id='notify_success',
        python_callable=success_notification,
        trigger_rule='all_success'
    )

    # Task dependencies
    create_schema_tables >> scrape_tasks
    scrape_tasks >> validate_s3 >> load_raw >> dbt_source_test
    dbt_source_test >> dbt_run >> dbt_model_test >> notify_success

