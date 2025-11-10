"""
Обработчики команд бота
"""
from telegram import Update
from telegram.ext import ContextTypes
from config import user_data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start
    Инициализирует пользователя и показывает инструкции
    """
    user_id = update.effective_user.id

    # Инициализируем данные пользователя
    user_data[user_id] = {}

    await update.message.reply_text(
        '🎃 Добро пожаловать в Pumpkin Head Bot!\n\n'
        '👻 Готов превратить твою голову в жуткую тыкву на Хэллоуин!\n\n'
        '📸 Отправь мне свое фото, и я сделаю из тебя настоящую тыквоголовку! 🎃\n\n'
        'Trick or treat? 🍬'
    )
