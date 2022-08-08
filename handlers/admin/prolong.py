import re

from aiogram import types
from aiogram.dispatcher import FSMContext

from data.config import Commands
from filters import IsAdmin
from keyboards.inline import services_keyboard, services_callback_data, services_cancel_keyboard, services_cancel_callback_data
from loader import dp, db, vak_sms
from utils.vak_sms import NoNumber


@dp.message_handler(IsAdmin(), commands=[Commands.Admin.settings.command])
async def show_services_to_prolong(message: types.Message, state: FSMContext):
    user = db.get_user(message.chat.id)

    await message.answer("Выберите сервис для продления")

    await user.send_message("Выберите сервис для продления", reply_markup=services_keyboard())


@dp.callback_query_handler(IsAdmin(), services_callback_data.filter(), state='*')
async def save_prolong_service(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user = db.get_user(call.message.chat.id)

    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)

    await call.message.edit_text(f"Введите номер для продления <b>({service})</b>",
                                 reply_markup=services_cancel_keyboard())
    await user.set_state("prolong_number")
    await user.set_state_data({"service_id": service_id})


@dp.message_handler(IsAdmin(), services_cancel_callback_data.filter(), state='prolong_number')
async def cancel_prolong_service(message: types.Message, state: FSMContext):
    await message.answer("Отменено")
    await state.finish()


@dp.message_handler(IsAdmin(), state='prolong_number')
async def prolong_number(message: types.Message, state: FSMContext):
    user = db.get_user(message.chat.id)
    service_id = user.get_state_data().get("service_id")
    service = db.get_service(service_id)

    numbers = re.findall(r'(?:\+|)(7[\d ]{9,}\d)', message.text)
    if not numbers:
        await message.answer("Неверный формат номера",
                             reply_markup=services_cancel_keyboard())
        return

    number = numbers[0]
    try:
        new_id_num = vak_sms.prolong_number(number, service.code)
    except NoNumber:
        await message.answer("Нет такого номера",
                             reply_markup=services_cancel_keyboard())
        return

    text = f"""
<b>Номер продлен</b>
<code>{number}</code>
<code>{new_id_num}</code>
<code>{number}|{new_id_num}</code>
"""
    await user.send_message(text)
    await state.finish()