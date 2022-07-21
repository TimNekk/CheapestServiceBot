import validators
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import InlineKeyboardExpected

from loader import db


services_callback_data = CallbackData("services", "service_id")
services_select_callback_data = CallbackData("services_select")


def make_services_callback_data(service_id: int):
    return services_callback_data.new(service_id=service_id)


def make_services_select_callback_data():
    return services_select_callback_data.new()


def services_keyboard(guides: bool = False) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    services = db.get_all_services(show_only=True)
    for service in services:
        if guides:
            if validators.url(service.guide_url):
                keyboard.add(InlineKeyboardButton(text=service.name, url=service.guide_url))
        else:
            keyboard.add(InlineKeyboardButton(text=service.name, callback_data=make_services_callback_data(service.id)))

    return keyboard
