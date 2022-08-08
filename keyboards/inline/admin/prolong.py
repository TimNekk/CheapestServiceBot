from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from loader import db

prolong_cancel_callback_data = CallbackData("cancel")
prolong_services_callback_data = CallbackData("prolong_services", "service_id")
prolong_categories_callback_data = CallbackData("prolong_category", "category_id")


def make_prolong_services_callback_data(service_id: int):
    return prolong_services_callback_data.new(service_id=service_id)


def make_prolong_categories_callback_data(category_id: int):
    return prolong_categories_callback_data.new(category_id=category_id)


def prolong_services_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    services = db.get_all_services(show_only=False)
    for service in services:
        keyboard.add(InlineKeyboardButton(text=f"{service.name} ({service.code})",
                                          callback_data=make_prolong_services_callback_data(service.id)))

    return keyboard


def prolong_categories_keyboard(service_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    service = db.get_service(service_id)
    categories = service.get_categories(show_only=False)
    for category in categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=make_prolong_categories_callback_data(category.id)))

    keyboard.add(InlineKeyboardButton(text="❌ Не добавлять", callback_data=prolong_cancel_callback_data.new()))

    return keyboard


def prolong_cancel_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton(text="❌ Отменить", callback_data=prolong_cancel_callback_data.new()))

    return keyboard
