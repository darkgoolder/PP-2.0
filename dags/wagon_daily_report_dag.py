"""
DAG для ежедневного отчёта с использованием секретов из MinIO
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
import os
import psycopg2
import json
import tempfile

# ============================================
# ЗАГРУЗКА СЕКРЕТОВ ИЗ MINIO
# ============================================

def get_secret_from_minio(secret_key: str) -> str:
    """
    Получение секрета из MinIO через mc клиент
    """
    import subprocess
    
    # Временный файл для секретов
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp:
        # Копируем секреты из MinIO
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{tmp.name}:/tmp/secrets.json",
            "minio/mc:latest",
            "sh", "-c",
            f"mc alias set wagon-local http://host.docker.internal:9000 minioadmin minioadmin123 && "
            f"mc cp wagon-local/wagon-secrets/{secret_key} /tmp/secrets.json 2>/dev/null || echo 'null'"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            with open(tmp.name, 'r') as f:
                return f.read().strip()
    
    return None


def load_all_secrets():
    """
    Загрузка всех секретов из MinIO в Airflow Variables
    """
    import subprocess
    import json
    
    # Копируем весь файл секретов
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp:
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{tmp.name}:/tmp/secrets.json",
            "minio/mc:latest",
            "sh", "-c",
            "mc alias set wagon-local http://host.docker.internal:9000 minioadmin minioadmin123 && "
            "mc cp wagon-local/wagon-secrets/secrets/encrypted.json /tmp/secrets.json"
        ], capture_output=True)
        
        try:
            with open(tmp.name, 'r') as f:
                secrets_data = json.load(f)
                
            # Сохраняем в Airflow Variables
            for key, value in secrets_data.get('secrets', {}).items():
                Variable.set(key, value)
                print(f"✅ Secret {key} loaded from MinIO")
                
            return secrets_data.get('secrets', {})
        except:
            print("⚠️ Could not load secrets from MinIO")
            return {}


# ============================================
# ОСНОВНЫЕ ФУНКЦИИ DAG
# ============================================

def check_model_health(**context):
    """
    Проверка наличия модели с использованием секретов из MinIO
    """
    model_path = "/opt/airflow/models/best_model.pth"
    exists = os.path.exists(model_path)
    
    # Логируем статус
    print(f"🔍 Model path: {model_path}")
    print(f"✅ Model exists: {exists}")
    
    # Загружаем секреты из MinIO (опционально)
    secrets = load_all_secrets()
    if secrets:
        print(f"🔐 Loaded {len(secrets)} secrets from MinIO")
    
    return {"model_exists": exists, "secrets_loaded": len(secrets)}


def generate_daily_report(**context):
    """
    Генерация ежедневного отчёта с использованием секретов из MinIO
    """
    from datetime import datetime
    import psycopg2
    
    # Определяем дату отчёта
    execution_date = context.get('execution_date')
    if execution_date:
        report_date = execution_date.date()
    else:
        report_date = datetime.now().date() - timedelta(days=1)
    
    print(f"📅 Report date: {report_date}")
    
    # Получаем секреты из Airflow Variables (загружены из MinIO)
    db_user = Variable.get("DB_USER", default_var="wagon_user")
    db_password = Variable.get("DB_PASSWORD", default_var="wagon_pass")
    db_name = Variable.get("DB_NAME", default_var="wagon_db")
    db_host = "host.docker.internal"
    db_port = 5432
    
    print(f"🔐 Connecting to DB with user: {db_user}")
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        
        # Подсчёт новых пользователей
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s",
            (report_date,)
        )
        new_users = cursor.fetchone()[0]
        print(f"👥 New users on {report_date}: {new_users}")
        
        # Проверка существования отчёта
        cursor.execute(
            "SELECT id FROM daily_reports WHERE report_date = %s",
            (report_date,)
        )
        exists = cursor.fetchone()
        
        # Модель существует?
        model_path = "/opt/airflow/models/best_model.pth"
        model_exists = os.path.exists(model_path)
        
        if exists:
            print(f"⚠️ Report for {report_date} already exists, updating...")
            cursor.execute("""
                UPDATE daily_reports 
                SET new_users_count = %s, model_exists = %s, report_generated_at = NOW()
                WHERE report_date = %s
            """, (new_users, model_exists, report_date))
        else:
            print(f"📝 Creating new report for {report_date}")
            cursor.execute("""
                INSERT INTO daily_reports (report_date, new_users_count, model_exists)
                VALUES (%s, %s, %s)
            """, (report_date, new_users, model_exists))
        
        conn.commit()
        print(f"✅ Report saved for {report_date}")
        
        cursor.close()
        conn.close()
        
        return {
            "report_date": str(report_date),
            "new_users": new_users,
            "model_exists": model_exists,
            "db_user": db_user
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


# ============================================
# DAG ОПРЕДЕЛЕНИЕ
# ============================================

default_args = {
    'owner': 'wagon-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['alerts@wagon-classifier.com'],
}

dag = DAG(
    'wagon_daily_report',
    default_args=default_args,
    description='Daily report for Wagon Classifier API (with MinIO secrets)',
    schedule_interval='0 23 * * *',
    catchup=False,
    tags=['wagon', 'report', 'secrets'],
)

start = EmptyOperator(task_id='start', dag=dag)
check_model = PythonOperator(
    task_id='check_model_health',
    python_callable=check_model_health,
    dag=dag
)
generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_daily_report,
    dag=dag
)
end = EmptyOperator(task_id='end', dag=dag)

start >> check_model >> generate_report >> end