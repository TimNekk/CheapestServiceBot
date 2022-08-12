import sys
from datetime import time, timedelta

from aiogram import executor
from loguru import logger

from loader import dp
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from utils import logging


async def on_startup(dispatcher):
    logging.setup(f"CSB", rotation=time(hour=0), retention=timedelta(days=3))

    # Устанавливаем дефолтные команды
    await set_default_commands(dispatcher)

    # Уведомляет про запуск
    await on_startup_notify(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
