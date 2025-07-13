import sqlite3 
from datetime import datetime, timedelta



def users_db():
    try:
        conn = sqlite3.connect('usersVPN.db')
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                subscription_type TEXT,
                subscription_start DATE,
                subscription_end DATE,
                registration_date TEXT,
                key TEXT
            )
        ''')

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        if conn:
            conn.close()

def save_user_data(user):
    try:
        conn = sqlite3.connect('usersVPN.db')
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO users (
                user_id, username, first_name, last_name, registration_date
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении данных пользователя: {e}")
    finally:
        if conn:
            conn.close()

def user_exists(user_id):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Ошибка при проверке существования пользователя: {e}")
        return False