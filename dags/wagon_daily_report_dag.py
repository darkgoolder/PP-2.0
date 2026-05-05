# dags/daily_report_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable

default_args = {
    'owner': 'wagon-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

DB_USER = Variable.get("DB_USER")
DB_PASSWORD = Variable.get("DB_PASSWORD")
DB_NAME = Variable.get("DB_NAME")

with DAG(
    'daily_report',
    default_args=default_args,
    description='Daily report for Wagon Classifier API',
    schedule_interval='0 23 * * *',
    catchup=False,
    tags=['wagon', 'report', 'docker'],
) as dag:
    
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    generate_report = DockerOperator(
        task_id='generate_report',
        image='wagon-report:latest',  # Используем собранный образ
        auto_remove=True,
        docker_url='unix://var/run/docker.sock',
        environment={
            'DB_USER': DB_USER,
            'DB_PASSWORD': DB_PASSWORD,
            'DB_NAME': DB_NAME,
        },
        mount_tmp_dir=False,
    )
    
    start >> generate_report >> end