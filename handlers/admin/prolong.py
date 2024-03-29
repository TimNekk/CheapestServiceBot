import re
from contextlib import suppress

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageToDeleteNotFound

from data.config import Commands
from filters import IsAdmin
from keyboards.inline.admin import prolong_cancel_keyboard, prolong_cancel_callback_data, \
    prolong_services_callback_data, prolong_services_keyboard, prolong_categories_callback_data, \
    prolong_categories_keyboard
from loader import dp, db, vak_sms
from utils.vak_sms import NoNumber


@dp.message_handler(IsAdmin(), commands=[Commands.Admin.prolong.command])
async def show_services_to_prolong(message: types.Message, state: FSMContext):
    user = db.get_user(message.chat.id)

    await user.send_message("Выберите сервис для продления", reply_markup=prolong_services_keyboard())


@dp.callback_query_handler(IsAdmin(), prolong_services_callback_data.filter())
async def save_prolong_service(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)

    ask_message = await call.message.edit_text(f"Введите номера для продления\n <b>{service.name}</b>",
                                               reply_markup=prolong_cancel_keyboard())

    await state.set_state("prolong_number")
    await state.update_data(service_id=service_id,
                            ask_message_id=ask_message.message_id)


@dp.callback_query_handler(IsAdmin(), prolong_cancel_callback_data.filter(), state='*')
async def cancel_prolong_service(call: types.CallbackQuery, state: FSMContext):
    ask_message_id: int = (await state.get_data()).get("ask_message_id")
    await state.finish()

    if ask_message_id:
        with suppress(MessageToDeleteNotFound):
            await dp.bot.delete_message(call.message.chat.id, ask_message_id)

    with suppress(MessageToDeleteNotFound):
        await call.message.delete()


@dp.message_handler(IsAdmin(), state='prolong_number')
async def prolong_number(message: types.Message, state: FSMContext):
    user = db.get_user(message.chat.id)
    service_id = (await state.get_data()).get("service_id")
    service = db.get_service(service_id)

    text = "<b>Номера продлены:</b>"

    prolonged_numbers = {}
    for number in message.text.split("\n"):
        number = re.findall(r'(?:\+|)(7[\d ]{9,}\d)', number)
        if not number:
            await message.answer("Неверный формат номера",
                                 reply_markup=prolong_cancel_keyboard())
            return

        number = number[0]
        try:
            id_num = vak_sms.prolong_number(number, service.code)
            text += f"\n<code>{number}|{id_num}</code>"
            prolonged_numbers[number] = id_num
        except NoNumber:
            await message.answer(f"Номер +{number} активен или не существует",
                                 reply_markup=prolong_cancel_keyboard())

    if not prolonged_numbers:
        return

    text += "\n\nКуда их добавить?"
    await user.send_message(text, reply_markup=prolong_categories_keyboard(service_id))
    await state.update_data(prolonged_numbers=prolonged_numbers)


@dp.callback_query_handler(IsAdmin(), prolong_categories_callback_data.filter(), state='prolong_number')
async def add_number_to_category(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    category_id = callback_data.get("category_id")
    prolonged_numbers: dict[str, str] = (await state.get_data()).get("prolonged_numbers")
    ask_message_id: int = (await state.get_data()).get("ask_message_id")

    for number, id_num in prolonged_numbers.items():
        db.add_number(id_num, category_id, number)

    await call.message.edit_text("Добавлено!")
    await dp.bot.delete_message(call.message.chat.id, ask_message_id)

    await state.finish()
