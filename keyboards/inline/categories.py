from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from keyboards.inline.services import make_services_select_callback_data, make_services_callback_data
from loader import db


categories_callback_data = CallbackData("categories", "category_id")
category_callback_data = CallbackData("category", "category_id")


def make_categories_callback_data(category_id: str):
    return categories_callback_data.new(category_id=category_id)


def make_category_callback_data(category_id: str):
    return category_callback_data.new(category_id=category_id)


def categories_keyboard(service_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    service = db.get_service(service_id)
    categories = service.get_categories(show_only=True)

    for category in categories:
        text = f"{category.name} | {category.price} ₽ | {category.get_number_count()} шт."
        if category.id == 17:
            text = f"{category.name} | {category.price} ₽ | В наличии"
        keyboard.add(InlineKeyboardButton(text=text, callback_data=make_categories_callback_data(category.id)))

    keyboard.add(InlineKeyboardButton(text="« Назад", callback_data=make_services_select_callback_data()))

    return keyboard


def category_keyboard(category_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    category = db.get_category(category_id)

    keyboard.add(InlineKeyboardButton(text="Купить", callback_data=make_category_callback_data(category.id)))
    keyboard.add(InlineKeyboardButton(text="« Назад", callback_data=make_services_callback_data(category.service_id)))

    return keyboard
