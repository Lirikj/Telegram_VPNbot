import os
import telebot

# Конфигурация берётся из переменных окружения.
# Заполните .env или экспортируйте переменные перед запуском.

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'REPLACE_WITH_TELEGRAM_BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# API endpoints (можно оставить пустыми и заполнить из окружения)
api_base_url = os.environ.get('API_BASE_URL', 'REPLACE_WITH_API_BASE_URL')
ger_api_base_url = os.environ.get('GER_API_BASE_URL', 'REPLACE_WITH_GER_API_BASE_URL')

# Данные для доступа к серверу
username_server = os.environ.get('SERVER_USERNAME', 'REPLACE_WITH_SERVER_USERNAME')
password = os.environ.get('SERVER_PASSWORD', 'REPLACE_WITH_SERVER_PASSWORD')