from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from loader import db


buy_callback_data = CallbackData("buy", "category_id", "action")


def make_buy_callback_data(category_id: int, action: str):
    return buy_callback_data.new(category_id=category_id, action=action)


def buy_keyboard(category_id: int, pay_url: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    category = db.get_category(category_id)

    keyboard.add(InlineKeyboardButton(text="Оплатить", url=pay_url))
    keyboard.add(InlineKeyboardButton(text="Проверить оплату", callback_data=make_buy_callback_data(category.id, "paid")))
    keyboard.add(InlineKeyboardButton(text="❌ Отменить", callback_data=make_buy_callback_data(category.id, "cancel")))

    return keyboard


def buy_cancel_keyboard(category_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    category = db.get_category(category_id)

    keyboard.add(InlineKeyboardButton(text="❌ Отменить платеж", callback_data=make_buy_callback_data(category.id, "cancel")))

    return keyboard
