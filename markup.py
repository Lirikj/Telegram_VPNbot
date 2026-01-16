from telebot import types 
from AnonkaAPI import check_premium


def menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mysub = types.KeyboardButton('📃подписка')
    extend_sub = types.KeyboardButton('🔄Продлить')
    markup.add(mysub, extend_sub)
    return markup


def choosing_server_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    finland_btn = types.InlineKeyboardButton('🇫🇮 Финляндия', callback_data='finland')
    germany_btn = types.InlineKeyboardButton('🇩🇪 Германия', callback_data='germany')
    dont_understand_btn = types.InlineKeyboardButton('🤷‍♂️Без разницы', callback_data='dont_understand')
    ultra = types.InlineKeyboardButton('💎Anonka Ultra', callback_data='Ultra') 
    markup.add(finland_btn, germany_btn)
    markup.add(dont_understand_btn)
    if not check_premium(user_id):
        markup.add(ultra)
    return markup
    

def admin_markup():
    markup = types.InlineKeyboardMarkup()
    stats_btn = types.InlineKeyboardButton('📊 Статистика', callback_data='admin_stats')
    active_users_btn = types.InlineKeyboardButton('👥 Активные пользователи', callback_data='admin_active_users')
    expiring_btn = types.InlineKeyboardButton('⚠️ Истекающие подписки', callback_data='admin_expiring')
    notifications_btn = types.InlineKeyboardButton('📢 Проверить уведомления', callback_data='admin_notifications')
    cleanup_btn = types.InlineKeyboardButton('🗑️ Удалить истекшие ключи', callback_data='admin_cleanup')
    message_to_user = types.InlineKeyboardButton('✉️Сообщение пользователю', callback_data='message_to_user')
    message = types.InlineKeyboardButton('📬Сообщение всем', callback_data='message_to_all')
    markup.add(message_to_user)
    markup.add(message)
    markup.add(stats_btn, active_users_btn)
    markup.add(expiring_btn, notifications_btn)
    markup.add(cleanup_btn)
    return markup


def back_markup():
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_menu')
    markup.add(back_btn)
    return markup


def manual_markup():
    markup = types.InlineKeyboardMarkup()
    manual = types.InlineKeyboardButton('📖Инструкция по установке', url = 'https://telegra.ph/Instrukciya-po-ustanovke-VPN-01-26')
    markup.add(manual)
    return markup 