# scripts/daily_report.py
import psycopg2
import requests
import os
from datetime import datetime, timedelta

def check_model_health():
    """Проверка наличия модели"""
    try:
        response = requests.get("http://host.docker.internal:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ Модель полностью работает")
            return True
    except Exception as e:
        print(f"⚠️ Проверка модели неудачна: {e}")
    
    model_paths = ["/models/best_model.pth", "/opt/airflow/models/best_model.pth"]
    for path in model_paths:
        if os.path.exists(path):
            print(f"✅ Модель найдена: {path}")
            return True
    
    print("⚠️ Модель не найдена")
    return False

def generate_daily_report():
    """Генерация ежедневного отчёта - ПОЛНАЯ ВЕРСИЯ"""
    
    report_date = (datetime.now() - timedelta(days=1)).date()
    print(f"📅 Report date: {report_date}")
    
    # Получаем секреты из переменных окружения
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")
    
    try:
        conn = psycopg2.connect(
            host="host.docker.internal",
            port=5432,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        
        # 1. ПРОВЕРКА И СОЗДАНИЕ ТАБЛИЦЫ users
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
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("✅ Табличца 'users' создана")
        
        # 2. ПОДСЧЁТ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s",
            (report_date,)
        )
        new_users = cursor.fetchone()[0]
        print(f"👥 New users on {report_date}: {new_users}")
        
        # 3. ПРОВЕРКА И СОЗДАНИЕ ТАБЛИЦЫ daily_reports
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
            print("✅ Таблица 'daily_reports' создана")
        
        # 4. ПРОВЕРКА МОДЕЛИ
        model_exists = check_model_health()
        
        # 5. ПРОВЕРКА СУЩЕСТВОВАНИЯ ОТЧЁТА
        cursor.execute(
            "SELECT id FROM daily_reports WHERE report_date = %s",
            (report_date,)
        )
        exists_row = cursor.fetchone()
        
        # 6. UPSERT
        if exists_row:
            print(f"⚠️ Репорт за {report_date} создаётся...")
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
        print(f"✅ Репорт за {report_date} сохранён")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    generate_daily_report()