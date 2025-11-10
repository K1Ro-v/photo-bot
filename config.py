"""
Конфигурация бота и глобальные переменные
"""
import os
from concurrent.futures import ThreadPoolExecutor

# Токены и URL
BOT_TOKEN = os.environ.get('BOT_TOKEN')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

# ThreadPoolExecutor для параллельной обработки запросов
executor = ThreadPoolExecutor(max_workers=20)

# Хранилище данных пользователей
user_data = {}

# Таймаут для запросов к n8n (в секундах)
N8N_REQUEST_TIMEOUT = 180
