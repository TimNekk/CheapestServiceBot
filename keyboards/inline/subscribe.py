from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from data.config import Subscription


subscribe_callback_data = CallbackData("subscribe")


def make_subscribe_callback_data():
    return subscribe_callback_data.new()


def subscribe_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(text="Подписаться", url=Subscription.url))
    keyboard.add(InlineKeyboardButton(text="Проверить", callback_data=make_subscribe_callback_data()))

    return keyboard
