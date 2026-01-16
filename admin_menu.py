from config import bot   
from telebot import types
from baza import get_subscription_statistics, get_all_active_subscriptions, get_expiring_subscriptions, get_all_user_ids
from datetime import datetime
from markup import admin_markup, back_markup


def admin_menu(message):
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
            
            markup = back_markup()
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
                    f"   ⏰ До: {user['subscription_end']}\n\n")
            
            if page == total_pages - 1:
                markup = back_markup()
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
            markup = back_markup()
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
                f"   📅 {days_text}")

        markup = back_markup()
        bot.send_message(chat_id, message, parse_mode='Markdown', reply_markup=markup)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
        print(f"Ошибка при получении истекающих подписок: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_') or call.data in ['message_to_user', 'message_to_all'])
def admin_callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    
    try:
        # bot.delete_message(chat_id, call.message.message_id)
        bot.edit_message_text(chat_id, call.message.message_id, text="⏳ Загрузка...", reply_markup=None)
    except:
        pass
    
    if data == 'admin_stats':
        show_statistics(chat_id)
        bot.answer_callback_query(call.id, "📊 Статистика загружена")
        
    elif data == 'admin_active_users':
        show_active_users(chat_id)
        bot.answer_callback_query(call.id, "🫂 Список активных пользователей")
        
    elif data == 'admin_expiring':
        show_expiring_subscriptions(chat_id)
        bot.answer_callback_query(call.id, "⚠️ Истекающие подписки")
        
    elif data == 'admin_notifications':
        from notifications import manual_check_notifications
        manual_check_notifications()
        bot.send_message(chat_id, "✅ Проверка уведомлений выполнена!")
        bot.answer_callback_query(call.id, "📢 Уведомления проверены")
        
    elif data == 'admin_cleanup':
        manual_cleanup_expired_keys(chat_id)
        bot.answer_callback_query(call.id, "🗑️ Проверка истекших ключей")
        
    elif data == 'admin_cleanup_confirm':
        confirm_cleanup_expired_keys(chat_id)
        bot.answer_callback_query(call.id, "🔄 Выполняю удаление...")
        
    elif data == 'admin_back':
        admin_menu_message = types.InlineKeyboardMarkup()
        admin_menu(types.SimpleNamespace(chat=types.SimpleNamespace(id=chat_id)))
        bot.answer_callback_query(call.id, "🔙 Возврат в админ-панель")
        
    elif data == 'message_to_user':
        bot.send_message(chat_id, "Введите ID пользователя и сообщение через запятую (например: 12345, Привет!)")
        bot.register_next_step_handler_by_chat_id(chat_id, process_message_to_user)
        bot.answer_callback_query(call.id)
        
    elif data == 'message_to_all':
        bot.send_message(chat_id, "Введите текст рассылки для всех пользователей:")
        bot.register_next_step_handler_by_chat_id(chat_id, process_message_to_all)
        bot.answer_callback_query(call.id)
        
    elif data == 'admin_back':
        markup = admin_markup()
        bot.send_message(chat_id, 'admin menu', reply_markup=markup, parse_mode='Markdown')


def process_message_to_user(message):
    try:
        user_id_str, text = message.text.split(',', 1)
        target_id = int(user_id_str.strip())
        bot.send_message(target_id, text.strip())
        bot.send_message(message.chat.id, f"✅ Сообщение отправлено пользователю {target_id}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Не удалось отправить. Проверьте формат: ID, сообщение")
        print(f"Ошибка при отправке личного сообщения: {e}")


def process_message_to_all(message):
    text = message.text.strip()
    user_ids = get_all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            bot.send_message(uid, text)
            sent += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ Рассылка выполнена: {sent} из {len(user_ids)}")


def manual_cleanup_expired_keys(chat_id):
    """Ручное удаление истекших ключей через админ-панель"""
    try:
        from notifications import get_expired_users, delete_expired_keys
        
        # Показываем информацию о истекших подписках
        expired_users = get_expired_users(3)
        
        if not expired_users:
            markup = types.InlineKeyboardMarkup()
            back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
            markup.add(back_btn)
            
            bot.send_message(chat_id, 
                "✅ Нет ключей для удаления\n\n"
                "Истекшие ключи удаляются автоматически через 3 дня после окончания подписки.", 
                reply_markup=markup)
            return
        
        # Показываем подтверждение удаления
        message = (
            f"🗑️ **Удаление истекших ключей**\n\n"
            f"Найдено **{len(expired_users)}** ключей для удаления:\n\n"
        )
        
        for user_id, username, subscription_end, server in expired_users:
            message += f"• {username or 'Без username'} (ID: {user_id})\n  Истекла: {subscription_end}, Сервер: {server}\n\n"
        
        message += "⚠️ **Внимание**: Это действие нельзя отменить!\n\nПродолжить удаление?"
        
        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton('✅ Да, удалить', callback_data='admin_cleanup_confirm')
        cancel_btn = types.InlineKeyboardButton('❌ Отмена', callback_data='admin_back')
        markup.add(confirm_btn)
        markup.add(cancel_btn)
        
        bot.send_message(chat_id, message, parse_mode='Markdown', reply_markup=markup)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
        print(f"Ошибка при подготовке очистки: {e}")


def confirm_cleanup_expired_keys(chat_id):
    """Подтверждение и выполнение удаления истекших ключей"""
    try:
        from notifications import delete_expired_keys, get_expired_users
        
        # Получаем количество ключей до удаления
        expired_users = get_expired_users(3)
        count_before = len(expired_users)
        
        bot.send_message(chat_id, "🔄 Выполняю удаление истекших ключей...")
        
        # Выполняем удаление
        delete_expired_keys()
        
        # Проверяем результат
        expired_users_after = get_expired_users(3)
        count_after = len(expired_users_after)
        deleted_count = count_before - count_after
        
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
        markup.add(back_btn)
        
        if deleted_count > 0:
            message = (
                f"✅ **Удаление завершено**\n\n"
                f"Удалено ключей: **{deleted_count}**\n"
                f"Пользователи получили уведомления об удалении.\n"
                f"Данные подписок очищены из базы данных."
            )
        else:
            message = (
                f"⚠️ **Удаление не выполнено**\n\n"
                f"Возможные причины:\n"
                f"• Ключи уже были удалены ранее\n"
                f"• Ошибки подключения к серверам\n"
                f"• Клиенты не найдены на серверах"
            )
        
        bot.send_message(chat_id, message, parse_mode='Markdown', reply_markup=markup)
        
    except Exception as e:
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton('🔙 Назад к меню', callback_data='admin_back')
        markup.add(back_btn)
        
        bot.send_message(chat_id, f"❌ Ошибка при удалении ключей: {str(e)}", reply_markup=markup)
        print(f"Ошибка при удалении ключей: {e}")




