"""
# Data Validation Pipeline

This DAG performs comprehensive data quality checks across all stages of the pipeline.

## Validation Stages:
1. **Raw Data**: Completeness and basic sanity checks
2. **Clean Data**: Structural and format validation
3. **Model Data**: Business logic and relational integrity

## Alerting:
- Immediate Telegram notifications on failure
- Success notification after all validations pass

## Quality Checks:
- Uses SQL-based checks from /opt/tests directory
- Automated retries for transient failures
"""

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.models import Connection
from datetime import datetime, timedelta
import requests

def send_telegram_message(context, message):
    """Sends message to Telegram"""
    conn_id = "telegram_conn"  # Use your connection ID
    conn = Connection.get_connection_from_secrets(conn_id)
    bot_token = conn.password
    chat_id = conn.login #This is where the chat id should be stored.
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram notification: {str(e)}")

def _alert(context):
    """Sends formatted Telegram alert on task failure"""
    execution_date_utc = context.get('execution_date')
    execution_date_local = execution_date_utc + timedelta(hours=1)

    message = f"""
🚨 *Pipeline Failed: {context.get('dag').dag_id}*
- *Failed Task*: {context.get('task_instance').task_id}
- *Time (UTC+1)*: {execution_date_local.strftime("%Y-%m-%d %H:%M:%S")}
- *Action Required*: Review Airflow logs for more information.
"""
    send_telegram_message(context, message)

def _validate_result(sql_test_name, **context): 
    """Generic validation handler for SQL test results"""
    result = context['ti'].xcom_pull(task_ids=sql_test_name)

    # Ensure result is not None
    if result is None:
        raise ValueError(f"No data pulled from XCom for task {sql_test_name}")

    # Extract number from result (handling nested lists and strings)
    def extract_number(value):
        """Recursively extract the first valid number from a nested list or string."""
        if isinstance(value, (int, float)):  # If it's already a number, return it
            return value
        if isinstance(value, str):  # Convert string-based numbers
            try:
                return float(value) if '.' in value else int(value)
            except ValueError:
                print(f"WARNING: Ignoring unexpected string value: {value}")  # Log unexpected values
                return None  # Ignore non-numeric strings
        if isinstance(value, list) and value:  # If it's a non-empty list, extract the first valid number
            for item in value:  
                num = extract_number(item)
                if num is not None:
                    return num  # Return first valid number found
        return None  # Return None if no valid number is found

    result = extract_number(result)  # Flatten nested lists and extract number

    if result is None:
        raise ValueError(f"Data validation failed: No valid numeric result found for {sql_test_name}")

    if result > 0:
        raise ValueError(f"Data quality check failed! {result} issues found in {sql_test_name}")

def success_notification(**context):
    """Sends success notification to Telegram"""
    execution_date_utc = context.get('execution_date')
    execution_date_local = execution_date_utc + timedelta(hours=1)

    message = f"""
✅ *All data quality checks passed successfully!*
✅ *All DAGs completed successfully!*
✅ *Pipeline Success!*
*Execution Date (UTC+1)*: {execution_date_local.strftime("%Y-%m-%d %H:%M:%S")}
"""
    send_telegram_message(context, message)

with DAG(
    'data_validation',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    on_failure_callback=_alert,
    template_searchpath=['/opt/sql', '/opt/modeling', '/opt/tests'],
    description="Executes data quality checks and alerts on issues",
    tags=['data_quality', 'validation'],
    doc_md=__doc__,
    default_args={
        'owner': 'airflow',
        'retries': 0,
        # 'retry_delay': timedelta(minutes=5)
    }
) as dag:

    # Raw Data Validation
    validate_raw = PostgresOperator(
        task_id='validate_raw_quality',
        sql='raw_data_checks.sql',
        postgres_conn_id='postgres_default'
    )
    check_raw = PythonOperator(
        task_id='check_raw_results',
        python_callable=_validate_result,
        op_kwargs={'sql_test_name': 'validate_raw_quality'},
        provide_context=True
    )

    # Clean Data Validation
    validate_clean = PostgresOperator(
        task_id='validate_clean_quality',
        sql='clean_data_checks.sql',
        postgres_conn_id='postgres_default'
    )
    check_clean = PythonOperator(
        task_id='check_clean_results',
        python_callable=_validate_result,
        op_kwargs={'sql_test_name': 'validate_clean_quality'},
        provide_context=True
    )

    # Model Validation
    validate_model = PostgresOperator(
        task_id='validate_model_quality',
        sql='model_checks.sql',
        postgres_conn_id='postgres_default'
    )
    check_model = PythonOperator(
        task_id='check_model_results',
        python_callable=_validate_result,
        op_kwargs={'sql_test_name': 'validate_model_quality'},
        provide_context=True
    )
    
    # Modified success notification
    send_success = PythonOperator(
        task_id='notify_success',
        python_callable=success_notification,
        trigger_rule='all_success'
    )

    validate_raw >> check_raw >> validate_clean >> check_clean >> validate_model >> check_model >> send_success
