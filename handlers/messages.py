"""
Обработчики текстовых и фото сообщений
"""
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from config import user_data
from services.request_manager import is_user_busy, lock_user
from services.n8n_service import process_n8n_request


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстовых сообщений
    Теперь бот принимает только изображения, поэтому отвечает что нужно отправить фото
    """
    await update.message.reply_text(
        "🤖 Я работаю только с фото.\n\n"
        "📷 Отправь изображение — и получи свой портрет в стиле Olymptrade Club."
    )


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик фото сообщений (обработка изображения)
    Проверяет блокировку пользователя и отправляет запрос в n8n
    Игнорирует текст (caption) если он был отправлен
    """
    user_id = update.effective_user.id

    # Проверяем, есть ли у пользователя активный запрос
    if is_user_busy(user_id):
        await update.message.reply_text(
            "⏳ Идёт создание твоего портрета.\n\n"
            "Подожди немного, прежде чем отправить новое фото."
        )
        print(f"🔒 User {user_id} tried to send request while having active one")
        return

    # Блокируем пользователя
    lock_user(user_id)

    photo = update.message.photo[-1]
    photo_file = await context.bot.get_file(photo.file_id)
    photo_url = photo_file.file_path

    # Отправляем подтверждение
    confirmation = (
        f"🧠 Фото получено.\n\n"
        f"🚀 Создаю твой портрет — тёмный фон, изумрудный свет, уверенный взгляд.\n\n"
        f"Обычно это занимает около минуты."
    )
    await update.message.reply_text(confirmation)

    print(f"🚀 Creating background task for user {user_id} (photo)")

    # Запускаем обработку в фоновой задаче БЕЗ await - обработчик сразу освобождается
    # Передаем None вместо prompt, так как теперь обрабатываем только изображение
    asyncio.create_task(process_n8n_request(
        user_id,
        None,  # prompt больше не используется
        {},  # settings - больше не используются
        photo_url,
        update.message.chat_id,
        context
    ))

    # Обработчик завершается сразу, бот готов принимать новые запросы
    print(f"✅ Handler for user {user_id} completed immediately, bot ready for next request")
