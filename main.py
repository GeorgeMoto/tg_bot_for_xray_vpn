import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import router, on_startup

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Регистрация обработчиков
dp.include_router(router)


# Основная функция для запуска бота
async def main():
    """Главная функция запуска бота"""
    logging.info("Запуск Telegram бота...")

    try:
        # Выполняем инициализацию при запуске
        await on_startup(bot)

        # Запускаем бота
        await dp.start_polling(bot, skip_updates=True)

    except Exception as e:
        logging.error(f"Критическая ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")