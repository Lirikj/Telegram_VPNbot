import sqlite3 
from datetime import datetime, timedelta


user_choice = {}


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
                premium INTEGER DEFAULT 0,
                email TEXT,
                server TEXT,                        
                subscription_type TEXT,
                subscription_start DATE,
                subscription_end DATE,
                registration_date TEXT,
                key TEXT
            )
        ''')
        
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'server' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN server TEXT')

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        if conn:
            conn.close()

def save_user_data(user, premium=0):
    try:
        conn = sqlite3.connect('usersVPN.db')
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO users (
                user_id, username, first_name, last_name, registration_date, premium
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            premium
        ))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении данных пользователя: {e}")
    finally:
        if conn:
            conn.close()


def check_premium_status(user_id):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT premium FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result and result[0] is not None:
                return bool(result[0])
            return False
            
    except sqlite3.Error as e:
        print(f"Ошибка при проверке премиум статуса: {e}")
        return False


def user_exists(user_id):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Ошибка при проверке существования пользователя: {e}")
        return False


def add_subscription(user_id, subscription_type, vpn_key=None, server_name=None):
    if subscription_type not in ['1 месяц', '3 месяца', '6 месяцев', '12 месяцев']:
        raise ValueError("Неверный тип подписки")

    days_mapping = {
        '1 месяц': 30,
        '3 месяца': 90, 
        '6 месяцев': 180,
        '12 месяцев': 365
    }
    duration_days = days_mapping[subscription_type]

    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=duration_days)

    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()

            if result:
                cursor.execute('''
                    UPDATE users
                    SET subscription_type = ?, 
                        subscription_start = ?, 
                        subscription_end = ?,
                        key = ?,
                        server = ?
                    WHERE user_id = ?
                ''', (subscription_type, start_date, end_date, vpn_key, server_name, user_id))
            else:
                cursor.execute('''
                    INSERT INTO users (
                        user_id, subscription_type, subscription_start, 
                        subscription_end, registration_date, key, server
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, subscription_type, start_date, end_date, 
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'), vpn_key, server_name))
                
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении подписки: {e}")
        return False


def get_user_subscription(user_id):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, 
                    subscription_type, subscription_start, subscription_end, 
                    registration_date, key, server
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'subscription_type': result[4],
                    'subscription_start': result[5],
                    'subscription_end': result[6],
                    'registration_date': result[7],
                    'key': result[8],
                    'server': result[9]
                }
            return None
            
    except sqlite3.Error as e:
        print(f"Ошибка при получении подписки: {e}")
        return None


def check_subscription_status(user_id):
    subscription = get_user_subscription(user_id)
    if not subscription:
        return None
        
    if not subscription['subscription_end']:
        return {'status': 'no_subscription', 'days_left': 0}
    
    try:
        end_date = datetime.strptime(subscription['subscription_end'], '%Y-%m-%d').date()
        current_date = datetime.now().date()
        
        if end_date >= current_date:
            days_left = (end_date - current_date).days
            return {
                'status': 'active',
                'days_left': days_left,
                'subscription_type': subscription['subscription_type'],
                'end_date': end_date,
                'key': subscription['key']
            }
        else:
            return {
                'status': 'expired',
                'days_left': 0,
                'subscription_type': subscription['subscription_type'],
                'end_date': end_date,
                'key': subscription['key']
            }
    except ValueError as e:
        print(f"Ошибка при парсинге даты: {e}")
        return None


def extend_subscription(user_id, additional_days):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT subscription_end FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                return False
                
            current_end_date = datetime.strptime(result[0], '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if current_end_date >= today:
                new_end_date = current_end_date + timedelta(days=additional_days)
            else:
                new_end_date = today + timedelta(days=additional_days)
            
            cursor.execute('''
                UPDATE users 
                SET subscription_end = ? 
                WHERE user_id = ?
            ''', (new_end_date, user_id))
            
            conn.commit()
            print(f"Подписка пользователя {user_id} продлена до {new_end_date}")
            return True
            
    except sqlite3.Error as e:
        print(f"Ошибка при продлении подписки: {e}")
        return False


def extend_subscription_with_server_update(user_id, subscription_type):
    days_map = {'1 месяц': 30, '3 месяца': 90, '6 месяцев': 180, '12 месяцев': 365}
    additional_days = days_map.get(subscription_type, 30)
    
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            
            # Получаем информацию о пользователе
            cursor.execute('SELECT subscription_end, username, server FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                return False, None
                
            current_end_date, username, server = result
            
            # Определяем сервер, если он не указан в БД
            if not server:
                server = '🇩🇪 Германия'  # По умолчанию
            
            # Продлеваем ключ на сервере
            from generation_key import extend_key
            server_success = extend_key(user_id, username, server, additional_days)
            
            if not server_success:
                return False, None
            
            # Обновляем дату в базе данных
            current_end_date_obj = datetime.strptime(current_end_date, '%Y-%m-%d').date()
            new_end_date = current_end_date_obj + timedelta(days=additional_days)
            
            cursor.execute(
                "UPDATE users SET subscription_end = ? WHERE user_id = ?",
                (new_end_date.strftime('%Y-%m-%d'), user_id)
            )
            conn.commit()
            
            return True, new_end_date
            
    except sqlite3.Error as e:
        return False, None
    except Exception as e:
        return False, None


def get_all_active_subscriptions():
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            today = datetime.now().date()
            
            cursor.execute('''
                SELECT user_id, username, subscription_type, subscription_end, key
                FROM users 
                WHERE subscription_end >= ? AND subscription_end IS NOT NULL
                ORDER BY subscription_end
            ''', (today,))
            
            results = cursor.fetchall()
            active_subscriptions = []
            
            for result in results:
                active_subscriptions.append({
                    'user_id': result[0],
                    'username': result[1],
                    'subscription_type': result[2],
                    'subscription_end': result[3],
                    'key': result[4]
                })
                
            return active_subscriptions
            
    except sqlite3.Error as e:
        print(f"Ошибка при получении активных подписок: {e}")
        return []


def get_expiring_subscriptions(days_threshold=3):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            today = datetime.now().date()
            threshold_date = today + timedelta(days=days_threshold)
            
            cursor.execute('''
                SELECT user_id, username, subscription_type, subscription_end, key
                FROM users 
                WHERE subscription_end BETWEEN ? AND ?
                ORDER BY subscription_end
            ''', (today, threshold_date))
            
            results = cursor.fetchall()
            expiring_subscriptions = []
            
            for result in results:
                days_left = (datetime.strptime(result[3], '%Y-%m-%d').date() - today).days
                expiring_subscriptions.append({
                    'user_id': result[0],
                    'username': result[1],
                    'subscription_type': result[2],
                    'subscription_end': result[3],
                    'days_left': days_left,
                    'key': result[4]
                })
                
            return expiring_subscriptions
            
    except sqlite3.Error as e:
        print(f"Ошибка при получении истекающих подписок: {e}")
        return []


def update_user_key(user_id, new_key):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET key = ? 
                WHERE user_id = ?
            ''', (new_key, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении ключа: {e}")
        return False


def delete_user_subscription(user_id):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
            
    except sqlite3.Error as e:
        print(f"Ошибка при удалении пользователя: {e}")
        return False


def get_subscription_statistics():
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            today = datetime.now().date()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE subscription_end >= ? AND subscription_end IS NOT NULL
            ''', (today,))
            active_subscriptions = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE subscription_end < ? AND subscription_end IS NOT NULL
            ''', (today,))
            expired_subscriptions = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT subscription_type, COUNT(*) FROM users 
                WHERE subscription_end >= ? AND subscription_end IS NOT NULL
                GROUP BY subscription_type
            ''', (today,))
            subscriptions_by_type = dict(cursor.fetchall())
            
            threshold_date = today + timedelta(days=7)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE subscription_end BETWEEN ? AND ?
            ''', (today, threshold_date))
            expiring_soon = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'active_subscriptions': active_subscriptions,
                'expired_subscriptions': expired_subscriptions,
                'subscriptions_by_type': subscriptions_by_type,
                'expiring_soon': expiring_soon
            }
            
    except sqlite3.Error as e:
        print(f"Ошибка при получении статистики: {e}")
        return None


def clean_expired_subscriptions(days_threshold=30):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            threshold_date = datetime.now().date() - timedelta(days=days_threshold)
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE subscription_end < ? AND subscription_end IS NOT NULL
            ''', (threshold_date,))
            count_to_delete = cursor.fetchone()[0]
            
            cursor.execute('''
                DELETE FROM users 
                WHERE subscription_end < ? AND subscription_end IS NOT NULL
            ''', (threshold_date,))
            
            conn.commit()
            
            print(f"Удалено {count_to_delete} истекших подписок (старше {days_threshold} дней)")
            return count_to_delete
            
    except sqlite3.Error as e:
        print(f"Ошибка при очистке истекших подписок: {e}")
        return 0


def search_users_by_username(username_pattern):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, subscription_type, subscription_end, key
                FROM users 
                WHERE username LIKE ?
                ORDER BY username
            ''', (f'%{username_pattern}%',))
            
            results = cursor.fetchall()
            users = []
            
            for result in results:
                users.append({
                    'user_id': result[0],
                    'username': result[1],
                    'subscription_type': result[2],
                    'subscription_end': result[3],
                    'key': result[4]
                })
                
            return users
            
    except sqlite3.Error as e:
        print(f"Ошибка при поиске пользователей: {e}")
        return []


def backup_database(backup_path="backup_usersVPN.db"):
    try:
        import shutil
        shutil.copy2('usersVPN.db', backup_path)
        print(f"Резервная копия создана: {backup_path}")
        return True
        
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")
        return False


def get_all_user_ids():
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users")
            return [row[0] for row in cur.fetchall()]
    except sqlite3.Error as e:
        print(f"Ошибка при получении всех пользователей: {e}")
        return []


def clear_user_subscription(user_id):
    """
    Очистка данных подписки пользователя после удаления ключа
    """
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET subscription_type = NULL,
                    subscription_start = NULL,
                    subscription_end = NULL,
                    server = NULL,
                    key = NULL
                WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"Ошибка при очистке подписки пользователя {user_id}: {e}")
        return False
    

def get_server_connections():
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            today = datetime.now().date()
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE server = ? AND subscription_end >= ? AND subscription_end IS NOT NULL
            ''', ('🇫🇮 Финляндия', today))
            
            finland_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE server = ? AND subscription_end >= ? AND subscription_end IS NOT NULL
            ''', ('🇩🇪 Германия', today))
            
            germany_count = cursor.fetchone()[0]
            
            return finland_count, germany_count
            
    except sqlite3.Error as e:
        print(f"Ошибка при получении статистики серверов: {e}")
        return 0, 0
