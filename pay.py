import sqlite3
from config import bot
from AnonkaAPI import activate_premium
from markup import menu_markup
from datetime import datetime, timedelta
from generation_key import generation_key
from telebot.types import LabeledPrice, ShippingOption
from baza import add_subscription as db_add_subscription
from baza import user_choice

user_invoice_messages = {}


shipping_options = [
    ShippingOption(id='instant', title='WorldWide Teleporter').add_price(LabeledPrice('Teleporter', 50)),]

SUBSCRIPTION_OPTIONS = {
    '1 месяц 95🌟': 95,    
    '3 месяца 295🌟': 295,
    '6 месяцев 495🌟': 495,
    '12 месяцев 995🌟': 995
}

SUBSCRIPTION_OPTIONS_PREMIUM = {
    '1 месяц 70🌟': 1,
    '3 месяца 270🌟': 270,
    '6 месяцев 470🌟': 470,
    '12 месяцев 970🌟': 970
} 

SUBSCRIPTION_OPTIONS_ULTRA = {
    '1 месяц 100🌟': 1,
    '3 месяца 300🌟': 300,
    '12 месяцев 1000🌟': 1000
}

def add_subscription(user_id, subscription_type):
    if subscription_type not in SUBSCRIPTION_OPTIONS and subscription_type not in SUBSCRIPTION_OPTIONS_PREMIUM and subscription_type not in SUBSCRIPTION_OPTIONS_ULTRA:
        raise ValueError("Неверный тип подписки")

    if '1 месяц' in subscription_type:
        duration_days = 30
    elif '3 месяца' in subscription_type:
        duration_days = 90
    elif '6 месяцев' in subscription_type:
        duration_days = 180
    elif '12 месяцев' in subscription_type:
        duration_days = 365
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


@bot.callback_query_handler(func=lambda call: call.data in SUBSCRIPTION_OPTIONS or call.data in SUBSCRIPTION_OPTIONS_PREMIUM or call.data in SUBSCRIPTION_OPTIONS_ULTRA)
def callback_query(call):
    subscription_type = call.data
    user_id = call.from_user.id

    if user_id in user_invoice_messages:
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=user_invoice_messages[user_id])
        except Exception as e:
            pass
    
    if subscription_type in SUBSCRIPTION_OPTIONS_ULTRA:
        price = SUBSCRIPTION_OPTIONS_ULTRA[subscription_type]
    elif subscription_type in SUBSCRIPTION_OPTIONS_PREMIUM:
        price = SUBSCRIPTION_OPTIONS_PREMIUM[subscription_type]
    else:
        price = SUBSCRIPTION_OPTIONS[subscription_type]
    
    prices = [LabeledPrice(label=subscription_type, amount=price)]

    try:
        invoice_message = bot.send_invoice(
            chat_id=call.message.chat.id,
            title="Доступ к Vless VPN",
            description=f"Оплата подписки на {subscription_type}",
            invoice_payload=subscription_type,
            provider_token=None,
            currency="XTR",
            prices=prices,
            start_parameter="subscription-payment")
        
        user_invoice_messages[user_id] = invoice_message.message_id
        
    except Exception as e:
        bot.send_message(call.message.chat.id, "Произошла ошибка при отправке счёта. Пожалуйста, попробуйте позже.")
        print(f"Ошибка при отправке счёта: {e}") 


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    print(shipping_query)
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options, error_message='Попробуйте еще раз позже')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True, error_message="Попытайтесь заплатить еще раз через несколько минут, нам нужен небольшой отдых")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    if user_id in user_invoice_messages:
        del user_invoice_messages[user_id]

    if payload.startswith('renewal_'):
        from renewal import handle_renewal_payment
        handle_renewal_payment(message)
        return
    
    if '1 месяц' in payload:
        days = 30
        subscription_period = '1 месяц'
    elif '3 месяца' in payload:
        days = 90
        subscription_period = '3 месяца'
    elif '6 месяцев' in payload:
        days = 180
        subscription_period = '6 месяцев'
    elif '12 месяцев' in payload:
        days = 365
        subscription_period = '12 месяцев'
    else:
        days = 30
        subscription_period = '1 месяц'
    
    try:
        choice = user_choice.get(user_id, {})
        server = choice.get('server')
        if server == '💎 Anonka Ultra':
            if days == 30:
                type = 'month'
            elif days == 90:
                type = '3months'
            elif days == 365:
                type = 'year'
            activate_premium(user_id, type)
            server = '🇫🇮 Финляндия'

        key = generation_key(user_id, username, server, days)
        
        if key:
            markup = menu_markup()
            db_add_subscription(user_id, subscription_period, key, server)  
            bot.send_message(message.chat.id,
                            f"✅ Спасибо за оплату! Ваша подписка на {subscription_period} активирована.\n\n"
                            f"🔑 Ваш VPN ключ:\n<code>{key}</code>\n\n"
                            f"⏰ Срок действия: {days} дней\n"
                            f"💰 Сумма: {message.successful_payment.total_amount} 🌟\n\n"
                            "Также подпишитесь на наш канал с отслеживанием статуса работы VPN: @Eureverse\n\n"
                            f"📖 <a href=\"https://telegra.ph/Instrukciya-po-ustanovke-VPN-01-26\">Инструкция</a>",
                            parse_mode='HTML', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при генерации ключа. Обратитесь в поддержку.")
            
    except Exception as e:
        print(f"Ошибка при обработке платежа: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке платежа. Обратитесь в поддержку.")