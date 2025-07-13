import uuid
from pyxui import XUI
from pyxui.config_gen import config_generator
from pyxui.errors import BadLogin

# Настройки подключения
FULL_ADDRESS = "http://150.241.96.86:2053/kyIwW5mBjaLIKYb/"  # Замените на адрес вашего сервера
PANEL_NAME = "sanaei"  # Для 3x-ui используйте "sanaei"
USERNAME = "Abramovich"  # Ваше имя пользователя
PASSWORD = "Abramov!ch129@"  # Ваш пароль

# Инициализация XUI
xui = XUI(
    full_address=FULL_ADDRESS,
    panel=PANEL_NAME,
    https=False  # Установите False, если не используете HTTPS
)

try:
    xui.login(USERNAME, PASSWORD)
    print("Успешный вход в систему.")
except BadLogin:
    print("Неверное имя пользователя или пароль.")
    exit(1)
except Exception as e:
    print(f"Произошла непредвиденная ошибка: {e}")
    exit(1)

