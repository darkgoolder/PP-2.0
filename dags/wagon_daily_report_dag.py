from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import os
import psycopg2

DB_HOST = "host.docker.internal"

def check_model_health(**context):
    model_path = "/opt/airflow/models/best_model.pth"
    exists = os.path.exists(model_path)
    print(f"✅ Model exists: {exists}")
    return {"model_exists": exists}

def generate_daily_report(**context):
    # Исправлено: берём execution_date напрямую
    execution_date = context.get('execution_date')
    if execution_date:
        # Если указана конкретная дата, используем её
        report_date = execution_date.date()
    else:
        # Иначе за вчера
        report_date = datetime.now().date() - timedelta(days=1)
    
    print(f"📅 Report date: {report_date}")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=5432,
            user="wagon_user",
            password="wagon_pass",
            database="wagon_db"
        )
        cursor = conn.cursor()
        
        # Подсчёт новых пользователей за указанную дату
        cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s", (report_date,))
        new_users = cursor.fetchone()[0]
        print(f"👥 New users on {report_date}: {new_users}")
        
        # Проверка, существует ли уже запись
        cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s", (report_date,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"⚠️ Report for {report_date} already exists, updating...")
            cursor.execute("""
                UPDATE daily_reports 
                SET new_users_count = %s, model_exists = %s, report_generated_at = NOW()
                WHERE report_date = %s
            """, (new_users, True, report_date))
        else:
            print(f"📝 Creating new report for {report_date}")
            cursor.execute("""
                INSERT INTO daily_reports (report_date, new_users_count, model_exists)
                VALUES (%s, %s, %s)
            """, (report_date, new_users, True))
        
        conn.commit()
        print(f"✅ Report saved for {report_date}")
        
        cursor.close()
        conn.close()
        
        return {"report_date": str(report_date), "new_users": new_users}
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

default_args = {
    'owner': 'wagon-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'wagon_daily_report',
    default_args=default_args,
    description='Daily report for Wagon Classifier API',
    schedule_interval='0 23 * * *',
    catchup=False,
    tags=['wagon', 'report'],
)

start = EmptyOperator(task_id='start', dag=dag)
check_model = PythonOperator(task_id='check_model_health', python_callable=check_model_health, dag=dag)
generate_report = PythonOperator(task_id='generate_report', python_callable=generate_daily_report, dag=dag)
end = EmptyOperator(task_id='end', dag=dag)

start >> check_model >> generate_report >> end