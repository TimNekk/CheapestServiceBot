from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

resend_callback_data = CallbackData("resend", "number_id", "activation_time_timestamp", "sms_count")


def make_resend_callback_data(number_id: str, activation_time_timestamp: float, sms_count: int):
    return resend_callback_data.new(number_id=number_id, activation_time_timestamp=activation_time_timestamp, sms_count=sms_count)


def resend_keyboard(number_id: str, activation_time_timestamp: float, sms_count: int):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton(text="Еще SMS",
                                      callback_data=make_resend_callback_data(number_id, activation_time_timestamp, sms_count)))

    return keyboard
