from telebot import types 


def menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    getkeyvpn = types.KeyboardButton('🔑Получить ключ')
    mysub = types.KeyboardButton('📃Моя подписка')
    extend_sub = types.KeyboardButton('🔄Продлить подписку')
    markup.add(getkeyvpn, mysub)
    markup.add(extend_sub)
    return markup
    

def admin_markup():
    markup = types.InlineKeyboardMarkup()
    stats_btn = types.InlineKeyboardButton('� Статистика', callback_data='admin_stats')
    active_users_btn = types.InlineKeyboardButton('👥 Активные пользователи', callback_data='admin_active_users')
    expiring_btn = types.InlineKeyboardButton('⚠️ Истекающие подписки', callback_data='admin_expiring')
    notifications_btn = types.InlineKeyboardButton('📢 Проверить уведомления', callback_data='admin_notifications')
    markup.add(stats_btn, active_users_btn)
    markup.add(expiring_btn, notifications_btn)
    return markup

