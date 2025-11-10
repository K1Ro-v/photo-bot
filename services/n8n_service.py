"""
Сервис для работы с n8n API
Отправляет запросы на генерацию изображений и обрабатывает ответы
"""
import asyncio
import requests
from typing import Optional, Dict, Any
from config import N8N_WEBHOOK_URL, N8N_REQUEST_TIMEOUT, executor
from services.request_manager import unlock_user


def send_to_n8n(user_id: int, prompt: Optional[str], settings: dict,
                photo_url: Optional[str] = None, chat_id: Optional[int] = None) -> Optional[Dict[Any, Any]]:
    """
    Синхронная функция для отправки запроса в n8n
    Выполняется в отдельном потоке через ThreadPoolExecutor

    Args:
        user_id: ID пользователя Telegram
        prompt: Текстовый промпт (опционально, сейчас не используется)
        settings: Настройки генерации (model, orientation, resolution, duration)
        photo_url: URL фотографии (обязательно)
        chat_id: ID чата для отправки ответа

    Returns:
        Ответ от n8n в формате JSON или None в случае ошибки
    """
    try:
        payload = {
            'user_id': user_id,
            'chat_id': chat_id or user_id,
            'settings': settings,
            'photo_url': photo_url
        }
        print(f"📤 Sending request to n8n for user {user_id}")
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=N8N_REQUEST_TIMEOUT)
        result = response.json()
        print(f"✅ Response from n8n for user {user_id}: {result.get('success', False)}")
        return result
    except requests.exceptions.Timeout:
        print(f"⏱ N8N request timeout after {N8N_REQUEST_TIMEOUT} seconds for user {user_id}")
        return None
    except Exception as e:
        print(f"❌ Error sending to n8n for user {user_id}: {e}")
        return None


async def process_n8n_request(user_id: int, prompt: Optional[str], settings: dict,
                               photo_url: Optional[str], chat_id: int, context) -> None:
    """
    Асинхронная обработка запроса к n8n в фоновом режиме
    Отправляет запрос, ждет ответ и отправляет результат пользователю

    Args:
        user_id: ID пользователя Telegram
        prompt: Текстовый промпт (опционально, сейчас не используется)
        settings: Настройки генерации
        photo_url: URL фотографии (обязательно)
        chat_id: ID чата для отправки ответа
        context: Контекст бота для отправки сообщений
    """
    try:
        print(f"🚀 Starting background task for user {user_id}")

        # Запускаем send_to_n8n в отдельном потоке, не блокируя основной обработчик
        loop = asyncio.get_event_loop()
        n8n_response = await loop.run_in_executor(
            executor,
            send_to_n8n,
            user_id,
            prompt,
            settings,
            photo_url,
            chat_id
        )

        print(f"🏁 Completed background task for user {user_id}")

        # Отправляем результат пользователю после завершения
        if n8n_response and n8n_response.get('success'):
            await context.bot.send_message(chat_id=chat_id, text="✅ Твой портрет готов.\n\n📸 Отправь новое фото, если хочешь обновить образ.")
        else:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Не удалось создать портрет.\n\nПопробуй ещё раз через пару минут.")

    except Exception as e:
        print(f"❌ Error in background task for user {user_id}: {e}")
        try:
            await context.bot.send_message(chat_id=chat_id, text="❌ Произошёл сбой.\n\nСкоро всё будет исправлено — попробуй позже.")
        except:
            pass

    finally:
        # Всегда снимаем блокировку пользователя после завершения
        unlock_user(user_id)
