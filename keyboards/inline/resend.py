from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

resend_callback_data = CallbackData("resend", "number_id", "activation_time_timestamp")


def make_resend_callback_data(number_id: str, activation_time_timestamp: float):
    return resend_callback_data.new(number_id=number_id, activation_time_timestamp=activation_time_timestamp)


def resend_keyboard(number_id: str, activation_time_timestamp: float):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton(text="Еще SMS",
                                      callback_data=make_resend_callback_data(number_id, activation_time_timestamp)))

    return keyboard
