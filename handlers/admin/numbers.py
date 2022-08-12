from sqlite3 import IntegrityError

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode

from filters import IsAdmin
from keyboards.inline.admin import numbers_keyboard, numbers_callback_data, numbers_delete_keyboard, numbers_cancel_keyboard, numbers_edit_keyboard
from loader import dp, db


async def show_numbers(message_id: int, user_id: int, category_id: int, offset: int = 0, limit: int = 10):
    user = db.get_user(user_id)

    text = f"""
Выберите номер
"""

    await user.edit_message_text(message_id, text, reply_markup=numbers_keyboard(category_id, offset, limit))


#region: Edit


@dp.callback_query_handler(numbers_callback_data.filter(action="edit"))
async def number_edit_handler(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    await number_edit(call.message.message_id, call.message.chat.id, callback_data.get("number_id"))


async def number_edit(message_id: int, user_id: int, number_id: int):
    user = db.get_user(user_id)

    number = db.get_number(number_id)

    text = f"""
<b>Настройка номера:</b> {number.phone_number}
{'❗️ Номер куплен пользователем ❗️' if number.busy else ''}

<b>Номер:</b> {number.phone_number}
<b>ID:</b> {number.id}

<b>Нажмите, чтобы изменить</b>
"""

    await user.edit_message_text(message_id, text, reply_markup=numbers_edit_keyboard(number.id))


@dp.callback_query_handler(numbers_callback_data.filter(action="edit_attribute"))
async def number_edit_attribute(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    user = db.get_user(call.message.chat.id)

    extra = callback_data.get("extra")
    number_id = callback_data.get("number_id")
    number = db.get_number(number_id)

    await state.set_state("number_edit_attribute")
    await state.update_data(extra=extra,
                            number_id=number_id,
                            message_id=call.message.message_id)

    text = "<b>Отправьте значение</b>"
    await user.edit_message_text(call.message.message_id, text, reply_markup=numbers_cancel_keyboard(number.id, back_text=True))


@dp.callback_query_handler(numbers_callback_data.filter(action="cancel"), state="number_edit_attribute")
async def number_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    await state.finish()
    number_id = callback_data.get("number_id")
    await number_edit(call.message.message_id, call.message.chat.id, number_id)


@dp.message_handler(IsAdmin(), state="number_edit_attribute")
async def number_edit_attribute_handler(message: types.Message, state: FSMContext):
    await message.delete()

    message_id: int = (await state.get_data()).get("message_id")
    extra = (await state.get_data()).get("extra")
    number_id = (await state.get_data()).get("number_id")
    number = db.get_number(number_id)

    # TODO: Проверка на валидность значения
    if extra == "number":
        number.set_number(int(message.text.replace("+", "")))
    elif extra == "id":
        number.set_id(message.text)

    await state.finish()
    await number_edit(message_id, message.chat.id, number.id)


#endregion

#region: Delete


@dp.callback_query_handler(numbers_callback_data.filter(action="delete"))
async def number_delete(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    number_id = callback_data.get("number_id")
    number = db.get_number(number_id)

    text = f"""
Вы действительно хотите удалить номер {hcode(number.phone_number)}?
"""

    user = db.get_user(call.message.chat.id)
    await user.edit_message_text(call.message.message_id, text, reply_markup=numbers_delete_keyboard(number.id))


@dp.callback_query_handler(numbers_callback_data.filter(action="delete_confirm"))
async def number_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    number_id = callback_data.get("number_id")
    number = db.get_number(number_id)
    number.delete()

    extra = callback_data.get("extra")
    if extra == "stop":
        await call.message.delete()
        return

    await show_numbers(call.message.message_id, call.message.chat.id, number.category_id)


#endregion

#region: Add


ADD_TEXT = f"""
<b>Введите следующие данные для добавления новых номеров (через | без пробелов)</b>

Номер|ID
Номер2|ID2

<b>Пример:</b>
<i>7999111133344|1657804225303080</i>
<i>7999111133345|1657804225303081</i>
"""


@dp.callback_query_handler(numbers_callback_data.filter(action="add"))
async def number_add(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    user = db.get_user(call.message.chat.id)

    await user.edit_message_text(call.message.message_id, ADD_TEXT, reply_markup=numbers_cancel_keyboard())

    category_id = callback_data.get("extra")
    await state.set_state("number_add")
    await state.update_data(message_id=call.message.message_id,
                            category_id=category_id)


@dp.message_handler(state="number_add")
async def number_add_handler(message: types.Message, state: FSMContext):
    async def send_error(error: str):
        text = f"""
<b><u>{error}</u></b>

<b>Вы ввели:</b>
{message.text}
{ADD_TEXT}
        """
        await user.edit_message_text(message_id, text, reply_markup=numbers_cancel_keyboard())

    user = db.get_user(message.chat.id)

    category_id = (await state.get_data()).get("category_id")
    message_id = (await state.get_data()).get("message_id")
    await message.delete()

    split_message = message.text.split("\n")
    split_lines = list(map(lambda x: x.split("|"), split_message))

    for split_line in split_lines:
        if len(split_line) != 2:
            await send_error("Неверный формат данных!")
            return

        number, number_id = split_line

        # TODO: Проверка на валидность значения

        try:
            db.add_number(number_id, category_id, number)
        except IntegrityError as e:
            await send_error(f"Ошибка добавления в Базу Данных: {e}")
            return

    await state.finish()
    await show_numbers(message_id, message.chat.id, category_id)


#endregion

#region: Cancel


@dp.callback_query_handler(numbers_callback_data.filter(action="cancel"), state="*")
async def service_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    number_id = callback_data.get("number_id")
    number = db.get_number(number_id)

    if number:
        category_id = number.category_id
    else:
        category_id = (await state.get_data()).get("category_id")

    await state.finish()

    await show_numbers(call.message.message_id, call.message.chat.id, category_id)


#endregion