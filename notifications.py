import sqlite3
import threading
import time
from datetime import datetime, timedelta
from config import bot
from telebot import types
from renewal import create_renewal_keyboard


def get_users_to_notify(days_before):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            target_date = datetime.now().date() + timedelta(days=days_before)
            
            cursor.execute('''
                SELECT user_id, first_name, subscription_type, subscription_end
                FROM users 
                WHERE DATE(subscription_end) = ? AND subscription_end IS NOT NULL
            ''', (target_date,))
            
            return cursor.fetchall()
            
    except sqlite3.Error as e:
        print(f"Ошибка при получении пользователей для уведомления: {e}")
        return []


def send_expiry_notification(user_id, first_name, subscription_type, subscription_end, days_left):
    try:
        if days_left == 2:
            message = (
                f"⚠️ Внимание, {first_name}!\n\n"
                f"Ваша подписка '{subscription_type}' истекает через 2 дня "
                f"({subscription_end}).\n\n"
                f"Не забудьте продлить подписку, чтобы не потерять доступ к VPN!"
            )
        elif days_left == 1:
            message = (
                f"🚨 Срочно, {first_name}!\n\n"
                f"Ваша подписка '{subscription_type}' истекает завтра "
                f"({subscription_end})!\n\n"
                f"Продлите подписку сегодня, чтобы не потерять доступ к VPN."
            )
        elif days_left == 0:
            message = (
                f"❌ {first_name}, ваша подписка истекла!\n\n"
                f"Подписка '{subscription_type}' истекла сегодня "
                f"({subscription_end}).\n\n"
                f"Оформите новую подписку для восстановления доступа к VPN."
            )
        else:
            return
        
        keyboard = create_renewal_keyboard()
        bot.send_message(user_id, message, reply_markup=keyboard)
        
    except Exception as e:
        print(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")


def check_and_notify_users():
    users_2_days = get_users_to_notify(2)
    for user_id, first_name, subscription_type, subscription_end in users_2_days:
        send_expiry_notification(user_id, first_name, subscription_type, subscription_end, 2)
    
    users_1_day = get_users_to_notify(1)
    for user_id, first_name, subscription_type, subscription_end in users_1_day:
        send_expiry_notification(user_id, first_name, subscription_type, subscription_end, 1)
    
    users_today = get_users_to_notify(0)
    for user_id, first_name, subscription_type, subscription_end in users_today:
        send_expiry_notification(user_id, first_name, subscription_type, subscription_end, 0)
    
    total_notifications = len(users_2_days) + len(users_1_day) + len(users_today)


def notification_scheduler():
    while True:
        try:
            current_time = datetime.now()
            if current_time.hour == 10 and current_time.minute == 0:
                check_and_notify_users()
                time.sleep(60)
            else:
                time.sleep(60)
        except Exception as e:
            print(f"Ошибка в планировщике уведомлений: {e}")
            time.sleep(300)  

def start_notification_service():
    notification_thread = threading.Thread(target=notification_scheduler, daemon=True)
    notification_thread.start()


def manual_check_notifications():
    check_and_notify_users()
