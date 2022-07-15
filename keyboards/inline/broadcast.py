from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData


broadcast_callback_data = CallbackData("broadcast", "action")


def make_broadcast_callback_data(action: str):
    return broadcast_callback_data.new(action=action)


def broadcast_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data=make_broadcast_callback_data("cancel")))

    return keyboard


def broadcast_accept_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton(text="Отправить", callback_data=make_broadcast_callback_data("send")))
    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data=make_broadcast_callback_data("cancel")))

    return keyboard
