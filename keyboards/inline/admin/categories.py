from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from keyboards.inline.admin.services import make_services_callback_data
from loader import db


categories_callback_data = CallbackData("admin_categories", "category_id", "action", "extra")


def make_categories_callback_data(category_id: int, action: str, extra: str = ""):
    return categories_callback_data.new(category_id=category_id, action=action, extra=extra)


def categories_keyboard(service_id: int):
    keyboard = InlineKeyboardMarkup(row_width=5)

    service = db.get_service(service_id)
    for category in service.get_categories(show_only=False):
        keyboard.add(
            InlineKeyboardButton(text=category.name,
                                 callback_data=make_categories_callback_data(category.id, "name")),
            InlineKeyboardButton(text="⬆️",
                                 callback_data=make_categories_callback_data(category.id, "up")),
            InlineKeyboardButton(text="⬇️",
                                 callback_data=make_categories_callback_data(category.id, "down")),
            InlineKeyboardButton(text="✏️",
                                 callback_data=make_categories_callback_data(category.id, "edit")),
            InlineKeyboardButton(text="🗑",
                                 callback_data=make_categories_callback_data(category.id, "delete")),
        )

    keyboard.add(InlineKeyboardButton(text="➕", callback_data=make_categories_callback_data(0, "add", str(service_id))))

    keyboard.add(InlineKeyboardButton(text="« Назад", callback_data=make_services_callback_data(service_id, "cancel")))

    return keyboard


def categories_delete_keyboard(category_id: int):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(text="Удалить", callback_data=make_categories_callback_data(category_id, "delete_confirm")),
        InlineKeyboardButton(text="Отмена", callback_data=make_categories_callback_data(category_id, "cancel"))
    )

    return keyboard


def categories_cancel_keyboard(category_id=0, back_text: bool = False):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(text="« Назад" if back_text else "Отмена", callback_data=make_categories_callback_data(category_id, "cancel")))

    return keyboard


def categories_edit_keyboard(category_id: int):
    keyboard = InlineKeyboardMarkup()

    category = db.get_category(category_id)

    keyboard.add(InlineKeyboardButton(text="Имя", callback_data=make_categories_callback_data(category_id, "edit_attribute", "name")),
                 InlineKeyboardButton(text=category.name, callback_data=make_categories_callback_data(category_id, "edit_attribute", "name")))

    keyboard.add(InlineKeyboardButton(text="Цена", callback_data=make_categories_callback_data(category_id, "edit_attribute", "price")),
                 InlineKeyboardButton(text=category.price, callback_data=make_categories_callback_data(category_id, "edit_attribute", "price")))

    keyboard.add(InlineKeyboardButton(text="Описание", callback_data=make_categories_callback_data(category_id, "edit_attribute", "description")),
                 InlineKeyboardButton(text=category.description if category.description else "-",
                                      callback_data=make_categories_callback_data(category_id, "edit_attribute", "description")))

    keyboard.add(InlineKeyboardButton(text="Отображать", callback_data=make_categories_callback_data(category_id, "edit_attribute", "show")),
                 InlineKeyboardButton(text="✅" if category.show else "❌", callback_data=make_categories_callback_data(category_id, "edit_attribute", "show")))

    keyboard.add(InlineKeyboardButton(text="« Назад", callback_data=make_categories_callback_data(category_id, "cancel")))

    return keyboard
