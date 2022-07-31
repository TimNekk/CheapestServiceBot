from typing import Optional

from aiogram import Dispatcher, types
from aiogram_broadcaster import TextBroadcaster

from data.config import DEVELOPER, ADMINS


async def on_startup_notify(dp: Dispatcher):
    await dp.bot.send_message(DEVELOPER, "Бот Запущен")


async def notify_admins(message: str, reply_markup: Optional[types.InlineKeyboardMarkup] = None):
    await TextBroadcaster(ADMINS, message, reply_markup=reply_markup).run()

