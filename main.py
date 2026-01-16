import time
import traceback
import telebot
import random
from AnonkaAPI import check_premium
from pay import SUBSCRIPTION_OPTIONS, SUBSCRIPTION_OPTIONS_PREMIUM, SUBSCRIPTION_OPTIONS_ULTRA, check_subscription
from config import bot, admin
from baza import users_db, save_user_data, user_exists, get_user_subscription, user_choice, get_server_connections
from notifications import start_notification_service
from renewal import send_renewal_options
from admin_menu import admin_menu
from markup import menu_markup, manual_markup, choosing_server_markup


@bot.message_handler(commands=['start', 'menu', 'st', 'mn'])
def start_message(message):
    user = message.from_user
    user_id = message.from_user.id
    first_name = message.from_user.first_name 
    last_name = message.from_user.last_name
    if check_premium(user_id):
        premium = 1
    else:
        premium = 0
    save_user_data(user, premium)
    
    if last_name:
        name = f'{first_name} {last_name}!'
    else:
        name = f'{first_name}!'

    finland_connections, germany_connections = get_server_connections()

    if user_exists(user_id):
        has_sub, sub_type, sub_end = check_subscription(user_id)
        if has_sub:
            user_data = get_user_subscription(user_id)
            if user_data:
                markup = menu_markup()
                bot.send_message(message.chat.id, f'Привет, {name} \n'
                                '📖menu', reply_markup=markup)
        else:
            if finland_connections < 3 and germany_connections < 3:
                connect = '🇫🇮 Финляндия — 🟢 *Свободен* \n🏎️Быстрее меня нету\n\n' \
                        '🇩🇪 Германия — 🟢 *Свободен* \n🛩️Я быстрее света \n'
            elif finland_connections > germany_connections:
                connect = '🇫🇮 Финляндия — 🔴 *Загружен* \n📊Всё стабильно, просто есть более быстрые варианты. \n\n' \
                        '🇩🇪 Германия — 🟢 *Свободен* \n🚀Самый быстрый на данный момент \n' 
            elif germany_connections > finland_connections:
                connect = '🇫🇮 Финляндия — 🟢 *Свободен* \n🧊Свободный и холодный \n\n' \
                        '🇩🇪 Германия — 🔴 *Загружен* \n🛜Всё работает, но нагрузка выше обычного \n'
            else:
                connect = '🇫🇮 Финляндия — 🟡 *Средняя загрузка* \n⚙️Работает уверенно \n\n' \
                        '🇩🇪 Германия — 🟡 *Средняя загрузка* \n⚖️Баланс скорости и стабильности \n'


            keyboard = choosing_server_markup(user_id)
            bot.send_message(message.chat.id, f'👋Привет {name} Это VenomVPN \n\n\n'
                            "🌎Загруженость серверов: \n\n"
                            f"{connect}\n"
                            "⚡️Уровень загруженности сервера определяется относительно других доступных серверов.\n\n"
                            "Чтоб оформить выберите сервер:", reply_markup=keyboard)
    

@bot.message_handler(commands=['info'])
def info(message):
    markup = manual_markup()
    bot.send_message(message.chat.id, '🧑‍💻Developer - @JonsonP \n'
                    '📕VPN status - @Eureverse \n\n'
                    '🤖версия бота 1.3 \n\n', reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == admin:
        admin_menu(message)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора.")
    

@bot.message_handler(commands=['promo'])
def promokod(message):
    bot.send_message(message.chat.id, '🛠Этот раздел пока в разработке')


@bot.callback_query_handler(func=lambda callback: callback.data in ['finland', 'germany', 'dont_understand', 'Ultra'])
def choise_server_handler(callback):
    user_id = callback.from_user.id

    keyboard = telebot.types.InlineKeyboardMarkup() 
    if check_premium(user_id):
        for option in SUBSCRIPTION_OPTIONS_PREMIUM.keys():
            keyboard.add(telebot.types.InlineKeyboardButton(text=option, callback_data=option))
    else:
        for option in SUBSCRIPTION_OPTIONS.keys():
            keyboard.add(telebot.types.InlineKeyboardButton(text=option, callback_data=option))

        
    if callback.data == 'finland':
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='🇫🇮 Вы выбрали сервер Финляндия \n\n'
                                                                                                        'Теперь выберите тип подписки:', reply_markup=keyboard)
        user_choice[user_id] = {'server': '🇫🇮 Финляндия', 'subscription_type': None}
    elif callback.data == 'germany':
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='🇩🇪 Вы выбрали сервер Германия \n\n'
                                                                                                        'Теперь выберите тип подписки:', reply_markup=keyboard)
        user_choice[user_id] = {'server': '🇩🇪 Германия', 'subscription_type': None}
    elif callback.data == 'dont_understand':
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='🤷‍♂️ Вы выбрали "Без разницы" \n\n'
                                                                                                        'Теперь выберите тип подписки:', reply_markup=keyboard)
        user_choice[user_id] = {'server': '🇩🇪 Германия', 'subscription_type': None}
    elif callback.data == 'Ultra':
        keyboardultra = telebot.types.InlineKeyboardMarkup() 
        for option in SUBSCRIPTION_OPTIONS_ULTRA.keys():
            keyboardultra.add(telebot.types.InlineKeyboardButton(text=option, callback_data=option))
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text='💎 Anonka Ultra \nВсё, что есть в Premium, и ещё больше: \n\n'
                                                                                                            '1. 🌟Включает всё, что есть в Anonka Premium \nВсе функции премиума — уже внутри Ultra. Максимум удобства, свободы и интеллекта. \n\n'
                                                                                                            '2. 🛡 Бесплатный доступ к VenomVPN \nПолноценный доступ к VPN без дополнительных оплат — подключайтесь в один клик через @VenomVless_bot и оставайтесь анонимными в любой точке мира.', reply_markup=keyboardultra)
        user_choice[user_id] = {'server': '💎 Anonka Ultra', 'subscription_type': None}

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    
    if message.text == '📃подписка':
        has_sub, sub_type, sub_end = check_subscription(user_id)
        markup = manual_markup()
        if has_sub:
            user_data = get_user_subscription(user_id)
            if user_data:
                bot.send_message(message.chat.id,
                                f"📃 Информация о вашей подписке:\n\n"
                                f"👤 Пользователь: {user_data['first_name']}\n"
                                f"📋 Тип подписки: {user_data['subscription_type']}\n"
                                f"📅 Начало: {user_data['subscription_start']}\n"
                                f"⏰ Окончание: {user_data['subscription_end']}\n"
                                f"📊 Статус: Активна ✅ \n\n"
                                f"🔑 Ваш VPN ключ:\n"
                                f"<code>{user_data['key']}</code>", reply_markup=markup, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "❌ У вас нет активной подписки. Оформите подписку в главном меню.")
            start_message(message)

    elif message.text == '🔄Продлить':
        has_sub, sub_type, sub_end = check_subscription(user_id)
        if has_sub:
            user = message.from_user
            send_renewal_options(message.chat.id, user.first_name)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет активной подписки для продления. Оформите новую подписку в главном меню.")
            start_message(message)
    
    elif message.text in ['📃Моя подписка', '🔄Продлить подписку', '🔑Получить ключ']: 
        bot.send_message(message.chat.id, 'Ты пользуешься устаревой версией бота \n'
                        'Введи комманду /start чтоб обновиться')
    
    else: 
        text = [
            "Пока что молчу, но не просто так — я учусь. Совсем скоро стану куда разговорчивее. 🚀💬", 
            "Я в режиме апгрейда. Скоро буду говорить яснее, быстрее и умнее. ⚙️🚀", 
            "Если честно, то я скучаю по прайму анонки. 😔",
            "Тишина — это не пауза, это подготовка. Скоро будет громко и интересно. 🔧💬", 
            "Я не молчу — я настраиваюсь. Скоро заговорю так, что не захочешь меня отключать. 🎛️🗣️", 
            "Купи анонку премиум, пожжержи разработчика", 
            "Сейчас я в тени, но скоро выйду на свет — с голосом, идеями и новыми фишками. 🌒✨", 
            "Дааа, мемодел отжигает, жалко только что сейчас ничего не постит",
            "Интересно Артем Белов найдет админа или нет? 🤔",
            "Молчу не просто так — внутри кипит работа. Скоро будет вау. 🔥🔜", 
            "Честно говоря, мне нурлатская анонимка больше по душе, чем ИТН и найдись нурлат"
        ]
        
        i = random.randint(0, 10)
        bot.send_message(message.chat.id, text[i])




users_db()
start_notification_service() 
while True:
    try:
        print("🚀 Запуск VPN бота...")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ Ошибка в работе бота: {e}")
        traceback.print_exc()
        print("⏳ Перезапуск через 5 секунд...")
        time.sleep(5)



