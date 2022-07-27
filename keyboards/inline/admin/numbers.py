from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from keyboards.inline.admin.categories import make_categories_callback_data
from loader import db


numbers_callback_data = CallbackData("admin_numbers", "number_id", "action", "extra")


def make_numbers_callback_data(number_id: int, action: str, extra: str = ""):
    return numbers_callback_data.new(number_id=number_id, action=action, extra=extra)


def numbers_keyboard(category_id: int):
    keyboard = InlineKeyboardMarkup(row_width=5)

    category = db.get_category(category_id)
    for number in category.get_numbers(not_busy=False):
        keyboard.add(
            InlineKeyboardButton(text=("❗️" if number.busy else "") + str(number.phone_number),
                                 callback_data=make_numbers_callback_data(number.id, "edit")),
            InlineKeyboardButton(text="✏️",
                                 callback_data=make_numbers_callback_data(number.id, "edit")),
            InlineKeyboardButton(text="🗑",
                                 callback_data=make_numbers_callback_data(number.id, "delete")),
        )

    keyboard.add(InlineKeyboardButton(text="➕", callback_data=make_numbers_callback_data(0, "add", str(category_id))))

    keyboard.add(InlineKeyboardButton(text="« Назад", callback_data=make_categories_callback_data(category_id, "cancel")))

    return keyboard


def numbers_delete_keyboard(number_id: int):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(text="Удалить", callback_data=make_numbers_callback_data(number_id, "delete_confirm")),
        InlineKeyboardButton(text="Отмена", callback_data=make_numbers_callback_data(number_id, "cancel"))
    )

    return keyboard


def numbers_cancel_keyboard(number_id=0, back_text: bool = False):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(InlineKeyboardButton(text="« Назад" if back_text else "Отмена", callback_data=make_numbers_callback_data(number_id, "cancel")))

    return keyboard


def numbers_edit_keyboard(number_id: int):
    keyboard = InlineKeyboardMarkup()

    number = db.get_number(number_id)

    keyboard.add(InlineKeyboardButton(text="Номер", callback_data=make_numbers_callback_data(number_id, "edit_attribute", "number")),
                 InlineKeyboardButton(text=number.phone_number, callback_data=make_numbers_callback_data(number_id, "edit_attribute", "number")))

    keyboard.add(InlineKeyboardButton(text="ID", callback_data=make_numbers_callback_data(number_id, "edit_attribute", "id")),
                 InlineKeyboardButton(text=number.id, callback_data=make_numbers_callback_data(number_id, "edit_attribute", "id")))

    keyboard.add(InlineKeyboardButton(text="« Назад", callback_data=make_numbers_callback_data(number_id, "cancel")))

    return keyboard
