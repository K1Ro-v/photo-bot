import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        '👋 Привет! Я бот для обработки изображений.\n\n'
        'Отправь мне фото, и я обработаю его через Seaart API.\n\n'
        'Команды:\n'
        '/start - Начать работу\n'
        '/help - Помощь'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        '📖 Как пользоваться ботом:\n\n'
        '1. Отправьте мне любое фото\n'
        '2. Я отправлю его на обработку в Seaart\n'
        '3. Получите результат обратно\n\n'
        'Это может занять некоторое время, пожалуйста, подождите ⏳'
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий"""
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text('⏳ Получил ваше фото, начинаю обработку...')
        
        # Получаем файл с максимальным разрешением
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Получаем информацию о пользователе
        user_id = update.effective_user.id
        username = update.effective_user.username or "No username"
        
        # Скачиваем фото
        photo_bytes = await file.download_as_bytearray()
        
        logger.info(f"Получено фото от пользователя {user_id} ({username}), размер: {len(photo_bytes)} байт")
        
        # Отправляем запрос в n8n
        files = {
            'photo': ('image.jpg', bytes(photo_bytes), 'image/jpeg')
        }
        
        data = {
            'user_id': user_id,
            'username': username,
            'chat_id': update.effective_chat.id
        }
        
        await processing_msg.edit_text('🔄 Отправляю на обработку в Seaart...')
        
        # Отправляем POST запрос в n8n
        response = requests.post(
            N8N_WEBHOOK_URL,
            files=files,
            data=data,
            timeout=300  # 5 минут таймаут
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Проверяем формат ответа от n8n
            if 'image_url' in result:
                # Если вернулся URL изображения
                await processing_msg.edit_text('✅ Обработка завершена! Отправляю результат...')
                await update.message.reply_photo(
                    photo=result['image_url'],
                    caption='✨ Вот ваше обработанное изображение!'
                )
                await processing_msg.delete()
                
            elif 'image_data' in result:
                # Если вернулись байты изображения (base64 или бинарные)
                await processing_msg.edit_text('✅ Обработка завершена! Отправляю результат...')
                await update.message.reply_photo(
                    photo=result['image_data'],
                    caption='✨ Вот ваше обработанное изображение!'
                )
                await processing_msg.delete()
                
            else:
                # Если формат ответа неожиданный
                await processing_msg.edit_text(
                    f'✅ Обработка завершена!\n\nОтвет: {result.get("message", "Успешно")}'
                )
        else:
            logger.error(f"Ошибка от n8n: {response.status_code} - {response.text}")
            await processing_msg.edit_text(
                f'❌ Ошибка при обработке изображения.\n'
                f'Код: {response.status_code}\n'
                f'Попробуйте ещё раз позже.'
            )
            
    except requests.Timeout:
        logger.error("Таймаут запроса к n8n")
        await update.message.reply_text(
            '⏱ Превышено время ожидания обработки.\n'
            'Попробуйте ещё раз или используйте изображение меньшего размера.'
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {str(e)}", exc_info=True)
        await update.message.reply_text(
            '❌ Произошла ошибка при обработке вашего фото.\n'
            'Пожалуйста, попробуйте ещё раз.'
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик документов (если пользователь отправит изображение как файл)"""
    await update.message.reply_text(
        '⚠️ Пожалуйста, отправьте изображение как фото, а не как файл.\n'
        'Используйте функцию "Отправить как фото" в Telegram.'
    )

def main():
    """Запуск бота"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    if not N8N_WEBHOOK_URL:
        logger.error("N8N_WEBHOOK_URL не установлен!")
        return
    
    logger.info("Запуск бота...")
    
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    
    # Запускаем бота
    logger.info("Бот успешно запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
