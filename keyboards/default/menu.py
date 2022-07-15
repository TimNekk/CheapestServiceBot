from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from data.config import Commands


def menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(KeyboardButton(text=Commands.buy.description),
                 KeyboardButton(text=Commands.guide.description))

    keyboard.add(KeyboardButton(text=Commands.support.description),
                 KeyboardButton(text=Commands.feedback.description))

    return keyboard
