from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from loader import db


services_callback_data = CallbackData("admin_services", "service_id", "action", "extra")


def make_services_callback_data(service_id: int, action: str, extra: str = ""):
    return services_callback_data.new(service_id=service_id, action=action, extra=extra)


def services_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=5)

    services = db.get_all_services(show_only=False)
    for service in services:
        keyboard.add(
            InlineKeyboardButton(text=service.name,
                                 callback_data=make_services_callback_data(service.id, "name")),
            InlineKeyboardButton(text="⬆️",
                                 callback_data=make_services_callback_data(service.id, "up")),
            InlineKeyboardButton(text="⬇️",
                                 callback_data=make_services_callback_data(service.id, "down")),
            InlineKeyboardButton(text="✏️",
                                 callback_data=make_services_callback_data(service.id, "edit")),
            InlineKeyboardButton(text="🗑",
                                 callback_data=make_services_callback_data(service.id, "delete")),
        )

    keyboard.add(InlineKeyboardButton(text="➕", callback_data=make_services_callback_data(0, "add")))

    return keyboard


def services_delete_keyboard(service_id: int):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(text="Удалить", callback_data=make_services_callback_data(service_id, "delete_confirm")),
        InlineKeyboardButton(text="Отмена", callback_data=make_services_callback_data(0, "cancel"))
    )

    return keyboard


def services_cancel_keyboard(service_id=0, back_text: bool = False):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(text="« Назад" if back_text else "Отмена", callback_data=make_services_callback_data(service_id, "cancel")))

    return keyboard


def services_edit_keyboard(service_id: int):
    keyboard = InlineKeyboardMarkup()

    service = db.get_service(service_id)

    keyboard.add(InlineKeyboardButton(text="Имя", callback_data=make_services_callback_data(service_id, "edit_attribute", "name")),
                 InlineKeyboardButton(text=service.name, callback_data=make_services_callback_data(service_id, "edit_attribute", "name")))

    keyboard.add(InlineKeyboardButton(text="Код", callback_data=make_services_callback_data(service_id, "edit_attribute", "code")),
                 InlineKeyboardButton(text=service.code, callback_data=make_services_callback_data(service_id, "edit_attribute", "code")))

    keyboard.add(InlineKeyboardButton(text="Телеграф", callback_data=make_services_callback_data(service_id, "edit_attribute", "guide")),
                 InlineKeyboardButton(text=service.guide_url, callback_data=make_services_callback_data(service_id, "edit_attribute", "guide")))

    keyboard.add(InlineKeyboardButton(text="Отображать", callback_data=make_services_callback_data(service_id, "edit_attribute", "show")),
                 InlineKeyboardButton(text="✅" if service.show else "❌", callback_data=make_services_callback_data(service_id, "edit_attribute", "show")))

    keyboard.add(InlineKeyboardButton(text="« Назад", callback_data=make_services_callback_data(service_id, "cancel")))

    return keyboard
