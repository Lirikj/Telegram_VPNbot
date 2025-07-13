from telebot import types, telebot 
from datetime import datetime, timedelta
from telebot.types import LabeledPrice, ShippingOption
from config import bot
from baza import users_db, save_user_data, user_exists, add_subscription, check_subscription
import sqlite3



shipping_options = [
    ShippingOption(id='instant', title='WorldWide Teleporter').add_price(LabeledPrice('Teleporter', 50)),]
SUBSCRIPTION_OPTIONS = {
    '1 месяц': 1,    
    '3 месяца': 10,  
    '6 месяцев': 100    
}

    

def add_subscription(user_id, subscription_type):
    if subscription_type not in SUBSCRIPTION_OPTIONS:
        raise ValueError("Неверный тип подписки")

    if subscription_type == '1 месяц':
        duration_days = 30
    elif subscription_type == '3 месяца':
        duration_days = 90
    elif subscription_type == '6 месяцев':
        duration_days = 180
    else:
        duration_days = 30  

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
                    SET subscription_type = ?, subscription_start = ?, subscription_end = ?
                    WHERE user_id = ?
                ''', (subscription_type, start_date, end_date, user_id))
            else:
                cursor.execute('''
                    INSERT INTO users (
                        user_id, subscription_type, subscription_start, subscription_end, registration_date
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (user_id, subscription_type, start_date, end_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении подписки: {e}")

def check_subscription(user_id):
    try:
        with sqlite3.connect('usersVPN.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT subscription_type, subscription_end FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()

            if result:
                subscription_type, subscription_end = result
                
                if subscription_end is None:
                    return False, None, None  

                subscription_end_date = datetime.strptime(subscription_end, '%Y-%m-%d').date()
                if subscription_end_date >= datetime.now().date():
                    return True, subscription_type, subscription_end_date
                else:
                    return False, None, None
            else:
                return False, None, None
    except sqlite3.Error as e:
        print(f"Ошибка при проверке подписки: {e}")
        return False, None, None


@bot.message_handler(commands=['start', 'menu', 'st', 'mn'])
def start_message(message):
    user = message.from_user
    user_id = message.from_user.id
    save_user_data(user)

    if user_exists(user_id):
        has_sub, sub_type, sub_end = check_subscription(user_id)
        if has_sub:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            getkeyvpn = types.KeyboardButton('🔑Получить ключ')

            bot.send_message(message.chat.id, f'Привет, {user.first_name}! \nВаша подписка: {sub_type}\nИстекает: {sub_end}')
        else:
            keyboard = telebot.types.InlineKeyboardMarkup()
            for option in SUBSCRIPTION_OPTIONS.keys():
                keyboard.add(telebot.types.InlineKeyboardButton(text=option, callback_data=option))
            bot.send_message(message.chat.id, 'Привет! это Vless VPN'
                            "\nЧтоб оформить выберите тип подписки:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in SUBSCRIPTION_OPTIONS)
def callback_query(call):
    subscription_type = call.data
    user_id = call.from_user.id

    price = SUBSCRIPTION_OPTIONS[subscription_type]
    prices = [LabeledPrice(label=subscription_type, amount=price)]

    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title="Доступ к Vless VPN",
            description=f"Оплата подписки на {subscription_type}",
            invoice_payload=subscription_type,
            provider_token=None,
            currency="XTR",
            prices=prices,
            start_parameter="subscription-payment"
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, "Произошла ошибка при отправке счёта. Пожалуйста, попробуйте позже.")
        print(f"Ошибка при отправке счёта: {e}") 


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    print(shipping_query)
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options,
                              error_message='Попробуйте еще раз позже')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Попытайтесь заплатить еще раз через несколько минут, нам нужен небольшой отдых")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    subscription_type = payload.invoice_payload

    add_subscription(user_id, subscription_type) #добавить ключ 

    bot.send_message(message.chat.id,
                        f"Спасибо за оплату! Ваша подписка на {subscription_type} активирована.".format(
                        message.successful_payment.total_amount / 100, message.successful_payment.currency),
                        parse_mode='Markdown') 


users_db()
bot.polling()


