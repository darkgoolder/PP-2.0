"""
DAG для ежедневного отчёта с использованием секретов из MinIO
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.models import Variable
from cryptography.fernet import Fernet
import os
import psycopg2
import json
import tempfile
import subprocess

# ============================================
# ФУНКЦИЯ ДЛЯ РАСШИФРОВКИ СЕКРЕТОВ
# ============================================

def get_encryption_key():
    """Получение ключа шифрования из файла"""
    key_paths = [
        "/home/airflow/.wagon_encryption_key",
        "/opt/airflow/.wagon_encryption_key",
        "/home/airflow/airflow/.wagon_encryption_key"
    ]
    
    for key_path in key_paths:
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
    
    # Если ключ не найден, пробуем получить из Variable
    try:
        key = Variable.get("ENCRYPTION_KEY")
        return key.encode()
    except:
        pass
    
    raise FileNotFoundError("Encryption key not found")


def decrypt_secret(encrypted_value: str) -> str:
    """Расшифровка секрета"""
    try:
        key = get_encryption_key()
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        print(f"❌ Decryption error: {e}")
        raise


def load_secrets_from_minio():
    """Загрузка секретов из MinIO в Airflow Variables"""
    try:
        # Получаем credentials из переменных окружения
        minio_endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
        minio_access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        minio_secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp:
            # Копируем файл секретов из MinIO
            result = subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{tmp.name}:/tmp/secrets.json",
                "--network", "wagon_network",
                "minio/mc:latest",
                "sh", "-c",
                f"mc alias set wagon-local http://{minio_endpoint} {minio_access_key} {minio_secret_key} && "
                "mc cp wagon-local/wagon-secrets/secrets/encrypted.json /tmp/secrets.json"
            ], capture_output=True)
            
            if result.returncode != 0:
                print("⚠️ Could not load secrets from MinIO")
                return {}
            
            with open(tmp.name, 'r') as f:
                secrets_data = json.load(f)
            
            # Сохраняем расшифрованные секреты в Variables
            for key, encrypted_value in secrets_data.get('secrets', {}).items():
                try:
                    decrypted_value = decrypt_secret(encrypted_value)
                    Variable.set(key, decrypted_value)
                    print(f"✅ Secret {key} loaded and decrypted")
                except Exception as e:
                    print(f"⚠️ Could not decrypt {key}: {e}")
            
            return secrets_data.get('secrets', {})
            
    except Exception as e:
        print(f"⚠️ Error loading secrets: {e}")
        return {}


# ============================================
# ОСНОВНЫЕ ФУНКЦИИ DAG
# ============================================

def check_model_health(**context):
    """Проверка наличия модели"""
    model_path = "/opt/airflow/models/best_model.pth"
    exists = os.path.exists(model_path)
    
    print(f"🔍 Model path: {model_path}")
    print(f"✅ Model exists: {exists}")
    
    # Попытка загрузить секреты (опционально)
    try:
        secrets = load_secrets_from_minio()
        if secrets:
            print(f"🔐 Loaded {len(secrets)} secrets from MinIO")
    except Exception as e:
        print(f"⚠️ Could not load secrets: {e}")
    
    return {"model_exists": exists, "secrets_loaded": len(secrets) if 'secrets' in locals() else 0}


def generate_daily_report(**context):
    """Генерация ежедневного отчёта"""
    import psycopg2
    from datetime import datetime
    
    logical_date = context.get('logical_date')
    if logical_date:
        report_date = logical_date.date()
    else:
        report_date = datetime.now().date() - timedelta(days=1)
    
    print(f"📅 Report date: {report_date}")
    
    # Получаем секреты (сначала из Variables, потом fallback из .env)
    try:
        db_user = Variable.get("DB_USER")
        db_password = Variable.get("DB_PASSWORD")
        db_name = Variable.get("DB_NAME")
        print("✅ Using secrets from Airflow Variables")
    except:
        # Fallback: используем переменные окружения из Docker
        db_user = os.environ.get("DB_USER", "wagon_user")
        db_password = os.environ.get("DB_PASSWORD", "wagon_pass")
        db_name = os.environ.get("DB_NAME", "wagon_db")
        print("⚠️ Using fallback environment variables")
    
    db_host = "host.docker.internal"  # Для доступа к БД на хосте
    db_port = 5432
    
    print(f"🔐 Connecting to DB (user: {db_user})")
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        
        # Проверка существования таблицы users
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        users_exists = cursor.fetchone()[0]
        
        if not users_exists:
            print("⚠️ Table 'users' does not exist, creating...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        
        # Подсчёт новых пользователей
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s",
            (report_date,)
        )
        new_users = cursor.fetchone()[0]
        print(f"👥 New users on {report_date}: {new_users}")
        
        # Проверка существования таблицы daily_reports
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'daily_reports'
            );
        """)
        reports_exists = cursor.fetchone()[0]
        
        if not reports_exists:
            print("⚠️ Table 'daily_reports' does not exist, creating...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id SERIAL PRIMARY KEY,
                    report_date DATE UNIQUE,
                    new_users_count INTEGER DEFAULT 0,
                    model_exists BOOLEAN DEFAULT FALSE,
                    report_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        
        # Проверка существования отчёта
        cursor.execute(
            "SELECT id FROM daily_reports WHERE report_date = %s",
            (report_date,)
        )
        exists_row = cursor.fetchone()
        
        model_path = "/opt/airflow/models/best_model.pth"
        model_exists = os.path.exists(model_path)
        
        if exists_row:
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
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
    'email_on_failure': False,
    'email_on_retry': False,
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