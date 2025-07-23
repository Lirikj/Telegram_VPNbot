import renewal  
from pay import SUBSCRIPTION_OPTIONS, check_subscription
from config import bot, admin
from telebot import types, telebot
from baza import users_db, save_user_data, user_exists, add_subscription, get_user_subscription
from notifications import start_notification_service, manual_check_notifications
from renewal import send_renewal_options
from admin_menu import admin_menu, admin_text_handler
from markup import menu_markup


@bot.message_handler(commands=['start', 'menu', 'st', 'mn'])
def start_message(message):
    user = message.from_user
    user_id = message.from_user.id
    save_user_data(user)

    if user_exists(user_id):
        has_sub, sub_type, sub_end = check_subscription(user_id)
        if has_sub:
            markup = menu_markup()
            bot.send_message(message.chat.id, f'Привет, {user.first_name}! \nВаша подписка: {sub_type}\nИстекает: {sub_end}', reply_markup=markup)
        else:
            keyboard = telebot.types.InlineKeyboardMarkup()
            for option in SUBSCRIPTION_OPTIONS.keys():
                keyboard.add(telebot.types.InlineKeyboardButton(text=option, callback_data=option))
            bot.send_message(message.chat.id, 'Привет! это Vless VPN'
                            "\nЧтоб оформить выберите тип подписки:", reply_markup=keyboard)


@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == admin:
        admin_menu(message)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора.")
    

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, 'VPN бот \n\n'
                    '🧑‍💻Developer - @JonsonP \n'
                    '🤖версия бота 1.0 \n'
                    '<a href="https://telegra.ph/Instrukciya-po-ustanovke-VPN-01-26">Инструкция</a> \n\n'
                    'для ответов используем нейросеть ChatGPT 4.1', parse_mode='HTML')


@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    
    if admin_text_handler(message):
        return  
    
    if message.text == '🔑Получить ключ':
        has_sub, sub_type, sub_end = check_subscription(user_id)
        if has_sub:
            user_data = get_user_subscription(user_id)
            if user_data and user_data.get('key'):
                bot.send_message(message.chat.id, 
                                f"🔑 Ваш VPN ключ:\n\n"
                                f"`{user_data['key']}`\n\n"
                                f"📱 Скопируйте ключ и добавьте его в ваше VPN приложение",
                                parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, 
                                "❌ Ключ не найден. Обратитесь в поддержку.")
        else:
            bot.send_message(message.chat.id, 
                            "❌ У вас нет активной подписки. Оформите подписку для получения ключа.")
    
    elif message.text == '📃Моя подписка':
        has_sub, sub_type, sub_end = check_subscription(user_id)
        if has_sub:
            user_data = get_user_subscription(user_id)
            if user_data:
                bot.send_message(message.chat.id,
                                f"📃 Информация о вашей подписке:\n\n"
                                f"👤 Пользователь: {user_data['first_name']}\n"
                                f"📋 Тип подписки: {user_data['subscription_type']}\n"
                                f"📅 Начало: {user_data['subscription_start']}\n"
                                f"⏰ Окончание: {user_data['subscription_end']}\n"
                                f"📊 Статус: Активна ✅")
        else:
            bot.send_message(message.chat.id, "❌ У вас нет активной подписки. Оформите подписку в главном меню.")
            start_message(message)

    
    elif message.text == '🔄Продлить подписку':
        has_sub, sub_type, sub_end = check_subscription(user_id)
        if has_sub:
            user = message.from_user
            send_renewal_options(message.chat.id, user.first_name)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет активной подписки для продления. Оформите новую подписку в главном меню.")
            start_message(message)


@bot.message_handler(commands=['check_notifications'])
def check_notifications_command(message):
    manual_check_notifications()
    bot.send_message(message.chat.id, "Проверка уведомлений выполнена!")


users_db()
start_notification_service() 
bot.polling()


