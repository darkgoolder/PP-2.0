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
    
    backup_secrets = BashOperator(
        task_id="backup_secrets",
        bash_command="""
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR="/tmp/backup_${TIMESTAMP}"
        
        # Создаём временную папку
        mkdir -p ${BACKUP_DIR}
        
        # Копируем секреты из MinIO через Docker
        docker run --rm \
            --network host \
            minio/mc:latest \
            sh -c "
                mc alias set wagon-local http://host.docker.internal:9000 minioadmin minioadmin123 && \
                mc cp --recursive wagon-local/wagon-secrets/ ${BACKUP_DIR}/
            "
        
        # Проверяем результат
        if [ -f "${BACKUP_DIR}/secrets/encrypted.json" ]; then
            echo "✅ Backup created: ${BACKUP_DIR}/secrets/encrypted.json"
            
            # Копируем в постоянное место (можно заменить на S3 или другую папку)
            cp -r ${BACKUP_DIR} /opt/airflow/backups/ 2>/dev/null || echo "⚠️ Could not copy to /opt/airflow/backups"
        else
            echo "❌ Backup failed"
            exit 1
        fi
        
        # Очистка старых бэкапов (оставляем последние 10)
        ls -1d /opt/airflow/backups/backup_* 2>/dev/null | head -n -10 | xargs rm -rf 2>/dev/null
        """,
    )
    
    start >> backup_secrets >> end