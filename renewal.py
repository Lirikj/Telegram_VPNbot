import sqlite3
from config import bot
from telebot import types, telebot 
from datetime import datetime, timedelta
from telebot.types import LabeledPrice
from baza import extend_subscription_with_server_update, get_user_subscription
from pay import SUBSCRIPTION_OPTIONS
from markup import menu_markup

RENEWAL_OPTIONS = {
    '1 месяц': 90,    
    '3 месяца': 270,
    '6 месяцев': 450,
    '12 месяцев': 900
}

@bot.callback_query_handler(func=lambda call: call.data.startswith('renew_'))
def renewal_callback_query(call):
    subscription_type = call.data.replace('renew_', '')
    user_id = call.from_user.id

    from pay import check_subscription

    has_sub, current_sub_type, sub_end = check_subscription(user_id)
    
    if subscription_type not in RENEWAL_OPTIONS:
        bot.answer_callback_query(call.id, "Неверный тип продления!", show_alert=True)
        return

    price = RENEWAL_OPTIONS[subscription_type]
    prices = [LabeledPrice(label=f"Продление на {subscription_type}", amount=price)]

    try:
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title="Продление подписки Vless VPN",
            description=f"Продление подписки на {subscription_type}",
            invoice_payload=f"renewal_{subscription_type}",
            provider_token=None,
            currency="XTR",
            prices=prices,
            start_parameter="renewal-payment"
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, "Произошла ошибка при отправке счёта. Пожалуйста, попробуйте позже.")
        print(f"Ошибка при отправке счёта для продления: {e}") 


def handle_renewal_payment(message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    
    subscription_type = payload.replace('renewal_', '')
    
    if subscription_type not in RENEWAL_OPTIONS:
        bot.send_message(message.chat.id, "❌ Ошибка: неверный тип продления!")
        return
    
    success, new_end_date = extend_subscription_with_server_update(user_id, subscription_type)
    
    if success:
        user_data = get_user_subscription(user_id)
        
        if user_data and user_data.get('key'):
            markup = menu_markup()
            
            bot.send_message(message.chat.id,
                            f"✅ Подписка успешно продлена!\n\n"
                            f"📋 Тип продления: {subscription_type}\n"
                            f"⏰ Новая дата окончания: {new_end_date}\n"
                            f"🔑 Ваш VPN ключ остался тем же:\n"
                            f"<code>{user_data['key']}</code>\n\n"
                            f"💰 Сумма: {message.successful_payment.total_amount} {message.successful_payment.currency}\n\n"
                            f"Подписка автоматически обновлена на сервере!",
                            parse_mode='HTML',
                            reply_markup=markup)
        else:
            bot.send_message(message.chat.id,
                            f"✅ Подписка продлена до {new_end_date}, но возникла проблема с получением ключа. "
                            f"Обратитесь в поддержку.")
    else:
        bot.send_message(message.chat.id,"❌ Произошла ошибка при продлении подписки. Обратитесь в поддержку.")


def create_renewal_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    for option in RENEWAL_OPTIONS.keys():
        keyboard.add(types.InlineKeyboardButton(
            text=f"Продлить на {option} - {RENEWAL_OPTIONS[option]} ⭐", 
            callback_data=f"renew_{option}"
        ))
    return keyboard


def send_renewal_options(chat_id, user_name):
    keyboard = create_renewal_keyboard()
    
    bot.send_message(chat_id,
                    f"💎 {user_name}, выберите период продления вашей подписки:\n\n"
                    f"🔄 Ваш VPN ключ останется тем же\n"
                    f"⏰ Будет обновлена только дата истечения\n"
                    f"🚀 Обновление происходит автоматически на сервере",
                    reply_markup=keyboard)
