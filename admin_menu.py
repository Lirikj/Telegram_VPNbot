from config import bot, admin   
from telebot import types
from baza import get_subscription_statistics, get_all_active_subscriptions, get_expiring_subscriptions
from datetime import datetime
from markup import admin_markup


def is_admin(user_id):
    return user_id == admin


def admin_menu(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора.")
        return

    markup = admin_markup()
    bot.send_message(message.chat.id, "admin menu", reply_markup=markup, parse_mode='Markdown')


def show_statistics(chat_id):
    try:
        stats = get_subscription_statistics()
        
        if stats:
            message = (
                "📊 **Статистика VPN бота**\n\n"
                f"👥 Всего пользователей: **{stats['total_users']}**\n"
                f"✅ Активных подписок: **{stats['active_subscriptions']}**\n"
                f"❌ Истекших подписок: **{stats['expired_subscriptions']}**\n"
                f"⚠️ Истекают в ближайшие 7 дней: **{stats['expiring_soon']}**\n\n"
                "📋 **Подписки по типам:**\n")
            
            if stats['subscriptions_by_type']:
                for sub_type, count in stats['subscriptions_by_type'].items():
                    message += f"   • {sub_type}: **{count}** чел.\n"
            else:
                message += "Нет активных подписок\n"
            
            message += f"\n📅 Данные на: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            # Добавляем кнопку "Назад"
            markup = types.InlineKeyboardMarkup()
            back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
            markup.add(back_btn)
            
            bot.send_message(chat_id, message, parse_mode='Markdown', reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ Ошибка получения статистики")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
        print(f"Ошибка при получении статистики: {e}")


def show_active_users(chat_id):
    try:
        active_subs = get_all_active_subscriptions()
        
        if not active_subs:
            markup = types.InlineKeyboardMarkup()
            back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
            markup.add(back_btn)
            
            bot.send_message(chat_id, "📭 Нет активных подписок", reply_markup=markup)
            return
        
        page_size = 10
        total_pages = (len(active_subs) + page_size - 1) // page_size
        
        for page in range(total_pages):
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(active_subs))
            page_users = active_subs[start_idx:end_idx]
            
            message = f"👥 **Активные пользователи** (страница {page + 1}/{total_pages}):\n\n"
            
            for i, user in enumerate(page_users, start=start_idx + 1):
                username = user.get('username', 'Не указан')
                if username and not username.startswith('@'):
                    username = f"@{username}"
                elif not username:
                    username = "Не указан"
                
                message += (
                    f"**{i}.** ID: `{user['user_id']}`\n"
                    f"   👤 Username: {username}\n"
                    f"   📋 Подписка: {user['subscription_type']}\n"
                    f"   ⏰ До: {user['subscription_end']}\n\n"
                )
            
            if page == total_pages - 1:
                markup = types.InlineKeyboardMarkup()
                back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
                markup.add(back_btn)
                bot.send_message(chat_id, message, parse_mode='Markdown', reply_markup=markup)
            else:
                bot.send_message(chat_id, message, parse_mode='Markdown')
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
        print(f"Ошибка при получении активных пользователей: {e}")


def show_expiring_subscriptions(chat_id):
    try:
        expiring_subs = get_expiring_subscriptions(7)
        
        if not expiring_subs:
            markup = types.InlineKeyboardMarkup()
            back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
            markup.add(back_btn)
            
            bot.send_message(chat_id, "✅ Нет подписок, истекающих в ближайшие 7 дней", reply_markup=markup)
            return
        
        message = f"⚠️ **Подписки, истекающие в ближайшие 7 дней** ({len(expiring_subs)}):\n\n"
        
        for i, user in enumerate(expiring_subs, 1):
            username = user.get('username', 'Не указан')
            if username and not username.startswith('@'):
                username = f"@{username}"
            elif not username:
                username = "Не указан"
            
            end_date = datetime.strptime(user['subscription_end'], '%Y-%m-%d').date()
            today = datetime.now().date()
            days_left = (end_date - today).days
            
            if days_left == 0:
                days_text = "🔴 Истекает сегодня"
            elif days_left == 1:
                days_text = "🟡 Истекает завтра"
            else:
                days_text = f"🟠 Осталось {days_left} дн."
            
            message += (
                f"**{i}.** ID: `{user['user_id']}`\n"
                f"   👤 Username: {username}\n"
                f"   📋 Тип: {user['subscription_type']}\n"
                f"   📅 {days_text}\n\n"
            )
        
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
        markup.add(back_btn)
        
        bot.send_message(chat_id, message, parse_mode='Markdown', reply_markup=markup)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
        print(f"Ошибка при получении истекающих подписок: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback_handler(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ У вас нет прав администратора!", show_alert=True)
        return
    
    chat_id = call.message.chat.id
    data = call.data
    
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    if data == 'admin_stats':
        show_statistics(chat_id)
        bot.answer_callback_query(call.id, "� Статистика загружена")
        
    elif data == 'admin_active_users':
        show_active_users(chat_id)
        bot.answer_callback_query(call.id, "� Список активных пользователей")
        
    elif data == 'admin_expiring':
        show_expiring_subscriptions(chat_id)
        bot.answer_callback_query(call.id, "⚠️ Истекающие подписки")
        
    elif data == 'admin_notifications':
        from notifications import manual_check_notifications
        manual_check_notifications()
        bot.send_message(chat_id, "✅ Проверка уведомлений выполнена!")
        bot.answer_callback_query(call.id, "📢 Уведомления проверены")
        
    elif data == 'admin_back':
        markup = admin_markup()
        bot.send_message(chat_id, 'admin menu', reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "Главное меню")




