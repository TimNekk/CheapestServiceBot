import sys
from datetime import time

from aiogram import executor
from loguru import logger

from loader import dp
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands


async def on_startup(dispatcher):
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(f"logs/CSB.log", rotation="00:00", retention="3 days", level="DEBUG")

    # Устанавливаем дефолтные команды
    await set_default_commands(dispatcher)

    # Уведомляет про запуск
    await on_startup_notify(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
