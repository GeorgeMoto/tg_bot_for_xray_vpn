# # import asyncio
# #
# # from aiogram import Bot, Dispatcher, executor
# # from aiogram.contrib.fsm_storage.memory import MemoryStorage
# # from aiogram.types import ParseMode
# #
# # from config import BOT_TOKEN
# #
# # loop = asyncio.get_event_loop()
# # storage = MemoryStorage()
# # bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
# # dp = Dispatcher(bot, loop=loop, storage=storage)
# #
# #
# # if __name__ == "__main__":
# #     from handlers import dp, send_greeting_to_admin
# #     executor.start_polling(dp, on_startup=send_greeting_to_admin, skip_updates=True)
#
#
# import asyncio
# from aiogram import Bot, Dispatcher
# from aiogram.enums import ParseMode  # Используй ParseMode из aiogram.enums
# from aiogram.fsm.storage.memory import MemoryStorage  # Новый путь для MemoryStorage
# from aiogram.client.default import DefaultBotProperties  # Для передачи parse_mode
#
# from config import BOT_TOKEN
#
# # Инициализация бота с использованием DefaultBotProperties
# bot = Bot(
#     token=BOT_TOKEN,
#     default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Указываем parse_mode здесь
# )
#
# # Инициализация диспетчера
# storage = MemoryStorage()
# dp = Dispatcher(storage=storage)
#
# # Импорт функции on_startup
# from handlers import send_greeting_to_admin
#
# if __name__ == "__main__":
#     from aiogram import Runner  # Используй Runner вместо executor
#
#     async def on_startup():
#         await send_greeting_to_admin(dp)
#
#     runner = Runner(
#         dp,
#         skip_updates=True,
#         on_startup=on_startup,
#     )
#     runner.run()

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import router, on_startup

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера с синтаксисом для aiogram 3.18
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Регистрация обработчиков
dp.include_router(router)

# Основная функция для запуска бота
async def main():
    await on_startup(bot)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())