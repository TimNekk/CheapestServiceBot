import pickle
from sqlite3 import IntegrityError
from typing import Optional

import validators

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode, hlink

from data.config import API_DOCS_URL
from filters import IsAdmin
from handlers.admin.numbers import show_numbers
from keyboards.inline.admin import categories_keyboard, categories_callback_data, categories_delete_keyboard, categories_cancel_keyboard, categories_edit_keyboard
from loader import dp, db


async def show_categories(message: types.Message, service_id: int):
    user = db.get_user(message.chat.id)

    text = f"""
Выберите категорию
"""

    await user.edit_message_text(message.message_id, text, reply_markup=categories_keyboard(service_id))

#region: Name


@dp.callback_query_handler(categories_callback_data.filter(action="name"))
async def categories_name(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    category_id = callback_data.get("category_id")
    await show_numbers(call.message, category_id)


#endregion

#region: Move


@dp.callback_query_handler(categories_callback_data.filter(action="up"))
async def categories_up(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    category_id = callback_data.get("category_id")
    category = db.get_category(category_id)
    category.increase_order()
    await show_categories(call.message, category.service_id)


@dp.callback_query_handler(categories_callback_data.filter(action="down"))
async def categories_up(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    category_id = callback_data.get("category_id")
    category = db.get_category(category_id)
    category.decrease_order()
    await show_categories(call.message, category.service_id)


#endregion

#region: Edit


@dp.callback_query_handler(categories_callback_data.filter(action="edit"))
async def category_edit(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    user = db.get_user(call.message.chat.id)

    category_id = callback_data.get("category_id")
    category = db.get_category(category_id)

    text = f"""
<b>Настройка категории:</b> {category.name}

<b>Имя:</b> {category.name}
<b>Цена:</b> {category.price}₽
<b>Описание:</b> {category.description}

<b>Нажмите, чтобы изменить</b>
"""

    await user.edit_message_text(call.message.message_id, text, reply_markup=categories_edit_keyboard(category.id), disable_web_page_preview=True)


@dp.callback_query_handler(categories_callback_data.filter(action="edit_attribute"))
async def category_edit_attribute(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    user = db.get_user(call.message.chat.id)

    extra = callback_data.get("extra")
    category_id = callback_data.get("category_id")
    category = db.get_category(category_id)

    if extra == "show":
        category.set_show(not category.show)
        await category_edit(call, state, callback_data)
        return

    await state.set_state("category_edit_attribute")
    await state.update_data(extra=extra,
                            category_id=category_id,
                            call=pickle.dumps(call))

    text = "<b>Отправьте значение</b>"
    await user.edit_message_text(call.message.message_id, text, reply_markup=categories_cancel_keyboard(category.id, back_text=True))


@dp.callback_query_handler(categories_callback_data.filter(action="cancel"), state="category_edit_attribute")
async def category_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    await state.finish()
    await category_edit(call, state, callback_data)


@dp.message_handler(IsAdmin(), state="category_edit_attribute")
async def category_edit_attribute_handler(message: types.Message, state: FSMContext):
    await message.delete()

    call: types.CallbackQuery = pickle.loads((await state.get_data()).get("call"))
    extra = (await state.get_data()).get("extra")
    category_id = (await state.get_data()).get("category_id")
    category = db.get_category(category_id)

    if extra == "name":
        category.set_name(message.text)
    elif extra == "price":
        if not message.text.isdigit():
            return
        category.set_price(int(message.text))
    elif extra == "description":
        category.set_description(message.text)

    await state.finish()
    await category_edit(call, state, {"category_id": category_id})


#endregion

#region: Delete


@dp.callback_query_handler(categories_callback_data.filter(action="delete"))
async def category_delete(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    category_id = callback_data.get("category_id")
    category = db.get_category(category_id)

    text = f"""
<b><u>ВСЕ НОМЕРА, КОТОРЫЕ ПРЕНАДЛЕЖАТ ЭТОЙ КАТЕГОРИИ БУДУТ ТАКЖЕ УДАЛЕНЫ!</u></b>

Вы действительно хотите удалить категорию {hcode(category.name)}?
"""

    user = db.get_user(call.message.chat.id)
    await user.edit_message_text(call.message.message_id, text, reply_markup=categories_delete_keyboard(category.id))


@dp.callback_query_handler(categories_callback_data.filter(action="delete_confirm"))
async def category_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    category_id = callback_data.get("category_id")
    category = db.get_category(category_id)
    category.delete()
    await show_categories(call.message, category.service_id)


#endregion

#region: Add


ADD_TEXT = f"""
<b>Введите следующие данные для добавления новой категории (через | без пробелов)</b>

Имя|цена|описание (не обязательно)

<b>Пример:</b>
<i>150 баллов|299|Аккаунт Самоката с 150 баллами на аккаунте</i>
"""


@dp.callback_query_handler(categories_callback_data.filter(action="add"))
async def category_add(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    user = db.get_user(call.message.chat.id)

    await user.edit_message_text(call.message.message_id, ADD_TEXT, reply_markup=categories_cancel_keyboard(), disable_web_page_preview=True)

    service_id = callback_data.get("extra")
    await state.set_state("category_add")
    await state.update_data(message=pickle.dumps(call.message),
                            service_id=service_id)


@dp.message_handler(state="category_add")
async def category_add_handler(message: types.Message, state: FSMContext):
    async def send_error(error: str):
        text = f"""
<b><u>{error}</u></b>

<b>Вы ввели:</b>
{message.text}
{ADD_TEXT}
        """
        await user.edit_message_text(ask_message.message_id, text, reply_markup=categories_cancel_keyboard(), disable_web_page_preview=True)

    user = db.get_user(message.chat.id)

    ask_message = pickle.loads((await state.get_data()).get("message"))
    await message.delete()

    split_message = message.text.split("|")

    if len(split_message) not in (2, 3):
        await send_error("Неверный формат данных!")
        return

    if not split_message[1].isdigit():
        await send_error("Цена должна быть целым числом!")
        return

    name, price, description = None, None, None
    if len(split_message) == 2:
        name, price = split_message
    elif len(split_message) == 3:
        name, price, description = split_message

    service_id = (await state.get_data()).get("service_id")

    try:
        db.add_category(service_id, name, price, description)
    except IntegrityError as e:
        await send_error(f"Ошибка добавлния в Базу Данных: {e}")
        return

    await state.finish()
    await show_categories(ask_message, service_id)


#endregion

#region: Cancel


@dp.callback_query_handler(categories_callback_data.filter(action="cancel"), state="*")
async def category_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    category_id = callback_data.get("category_id")
    category = db.get_category(category_id)

    if category:
        service_id = category.service_id
    else:
        service_id = (await state.get_data()).get("service_id")

    await state.finish()

    await show_categories(call.message, service_id)


#endregion