"""
Обработчики callback запросов (нажатия на кнопки)
"""
from telegram import Update
from telegram.ext import ContextTypes


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback запросов от inline кнопок
    Не используется в текущей версии (нет кнопок настроек)
    """
    query = update.callback_query
    await query.answer()
    # Callback обработчик оставлен для возможного будущего расширения функционала
