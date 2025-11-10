"""
Главный файл Telegram бота для генерации изображений через n8n
Модульная архитектура с разделением на handlers, services и UI
"""
import os
import signal
import sys
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Импорты из модулей
from config import BOT_TOKEN, executor
from handlers.commands import start
from handlers.callbacks import button_handler
from handlers.messages import handle_text_message, handle_photo_message

# Глобальная переменная для приложения
application = None


def signal_handler(sig, frame):
    """Обработчик сигналов завершения (Ctrl+C, SIGTERM)"""
    global application, executor
    print('🛑 Received shutdown signal, stopping bot...')
    if executor:
        executor.shutdown(wait=False)
    if application:
        try:
            application.stop_running()
        except:
            pass
    sys.exit(0)


# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Главная функция запуска бота"""
    global application

    print("🔧 Initializing bot with modular architecture...")
    print(f"⚡ Thread pool size: {executor._max_workers} workers")

    # Очищаем webhook перед запуском
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🧹 Attempt {attempt + 1}/{max_retries}: Clearing webhook...")
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
                json={"drop_pending_updates": True},
                timeout=10
            )
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook cleared successfully")
                break
            else:
                print(f"⚠️ Webhook clear response: {result}")
        except Exception as e:
            print(f"❌ Error clearing webhook (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)

    time.sleep(2)

    # Создаем приложение и регистрируем обработчики
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

    print(f"🤖 Bot started with modular architecture!")
    print("📊 Bot can handle multiple concurrent requests from different users")
    print("🔒 Each user is limited to one active request at a time")

    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        print(f"❌ Bot error: {e}")
        raise
    finally:
        print("🛑 Shutting down thread pool...")
        executor.shutdown(wait=True)
        print("👋 Bot stopped")


if __name__ == '__main__':
    main()
