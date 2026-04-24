from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator

default_args = {
    "owner": "wagon-team",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    "backup_secrets_bash",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=["backup", "minio"],
) as dag:
    start = DummyOperator(task_id="start")
    end = DummyOperator(task_id="end")
    
    test_docker = BashOperator(
        task_id="test_docker",
        bash_command="echo 'Docker check: ' && docker ps || echo 'Docker not available'",
    )
    
    start >> test_docker >> end
