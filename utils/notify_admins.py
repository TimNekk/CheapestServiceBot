from aiogram import Dispatcher
from aiogram_broadcaster import TextBroadcaster

from data.config import DEVELOPER, ADMINS


async def on_startup_notify(dp: Dispatcher):
    await dp.bot.send_message(DEVELOPER, "Бот Запущен")


async def notify_admins(message: str):
    await TextBroadcaster(ADMINS, message).run()

