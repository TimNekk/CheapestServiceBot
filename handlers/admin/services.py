import validators

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode, hlink

from data.config import API_DOCS_URL, Commands
from filters import IsAdmin
from handlers.admin.categories import show_categories
from keyboards.inline.admin import services_keyboard, services_callback_data, services_delete_keyboard, services_cancel_keyboard, services_edit_keyboard
from loader import dp, db


@dp.message_handler(IsAdmin(), commands=[Commands.Admin.settings.command])
async def show_services(message: types.Message):
    user = db.get_user(message.chat.id)

    text = f"""
Выберите сервис
"""

    await user.edit_message_text(message.message_id, text, reply_markup=services_keyboard())

#region: Name


@dp.callback_query_handler(services_callback_data.filter(action="name"))
async def service_name(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    service_id = callback_data.get("service_id")
    await show_categories(call.message, service_id)


#endregion

#region: Move


@dp.callback_query_handler(services_callback_data.filter(action="up"))
async def services_up(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)
    service.increase_order()
    await show_services(call.message)


@dp.callback_query_handler(services_callback_data.filter(action="down"))
async def services_up(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)
    service.decrease_order()
    await show_services(call.message)


#endregion

#region: Edit


@dp.callback_query_handler(services_callback_data.filter(action="edit"))
async def service_edit(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    user = db.get_user(call.message.chat.id)

    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)

    text = f"""
<b>Настройка сервиса:</b> {service.name}

<b>Имя:</b> {service.name}
<b>Код:</b> {service.code}
<b>Телеграф:</b> {service.guide_url}

<b>Нажмите, чтобы изменить</b>
"""

    await user.edit_message_text(call.message.message_id, text, reply_markup=services_edit_keyboard(service.id), disable_web_page_preview=True)


@dp.callback_query_handler(services_callback_data.filter(action="edit_attribute"))
async def service_edit_attribute(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    user = db.get_user(call.message.chat.id)

    extra = callback_data.get("extra")
    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)

    if extra == "show":
        service.set_show(not service.show)
        await service_edit(call, state, callback_data)
        return

    await state.set_state("service_edit_attribute")
    await state.update_data(extra=extra,
                            service_id=service_id,
                            call=call)

    text = "<b>Отправьте значение</b>"
    await user.edit_message_text(call.message.message_id, text, reply_markup=services_cancel_keyboard(service.id, back_text=True))


@dp.callback_query_handler(services_callback_data.filter(action="cancel"), state="service_edit_attribute")
async def service_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    await state.finish()
    await service_edit(call, state, callback_data)


@dp.message_handler(IsAdmin(), state="service_edit_attribute")
async def service_edit_attribute_handler(message: types.Message, state: FSMContext):
    await message.delete()

    call: types.CallbackQuery = (await state.get_data()).get("call")
    extra = (await state.get_data()).get("extra")
    service_id = (await state.get_data()).get("service_id")
    service = db.get_service(service_id)

    if extra == "name":
        service.set_name(message.text)
    elif extra == "code":
        service.set_code(message.text)
    elif extra == "guide":
        service.set_guide_url(message.text)

    await state.finish()
    await service_edit(call, state, {"service_id": service_id})


#endregion

#region: Delete


@dp.callback_query_handler(services_callback_data.filter(action="delete"))
async def service_delete(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)

    text = f"""
<b><u>ВСЕ КАТЕГОРИИ И НОМЕРА, КОТОРЫЕ ПРЕНАДЛЕЖАТ ЭТОМУ СЕРВИСУ БУДУТ ТАКЖЕ УДАЛЕНЫ!</u></b>

Вы действительно хотите удалить сервис {hcode(service.name)}?
"""

    user = db.get_user(call.message.chat.id)
    await user.edit_message_text(call.message.message_id, text, reply_markup=services_delete_keyboard(service.id))


@dp.callback_query_handler(services_callback_data.filter(action="delete_confirm"))
async def service_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    service_id = callback_data.get("service_id")
    service = db.get_service(service_id)
    service.delete()
    await show_services(call.message)


#endregion

#region: Add


ADD_TEXT = f"""
<b>Введите следующие данные для добавления нового сервиса (через | без пробелов)</b>

Имя|{hlink('код', API_DOCS_URL)}|ссылка на телеграф

<b>Пример:</b>
<i>Самокат 🛴|sk|https://telegra.ph/Samokat-07-14-2</i>
"""


@dp.callback_query_handler(services_callback_data.filter(action="add"))
async def service_add(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()

    user = db.get_user(call.message.chat.id)

    await user.edit_message_text(call.message.message_id, ADD_TEXT, reply_markup=services_cancel_keyboard(), disable_web_page_preview=True)

    await state.set_state("service_add")
    await state.update_data(message=call.message)


@dp.message_handler(state="service_add")
async def service_add_handler(message: types.Message, state: FSMContext):
    async def send_error(error: str):
        text = f"""
<b><u>{error}</u></b>

<b>Вы ввели:</b>
{message.text}
{ADD_TEXT}
        """
        await user.edit_message_text(ask_message.message_id, text, reply_markup=services_cancel_keyboard(), disable_web_page_preview=True)

    user = db.get_user(message.chat.id)

    ask_message = (await state.get_data()).get("message")
    await message.delete()

    split_message = message.text.split("|")

    if len(split_message) != 3:
        await send_error("Неверный формат данных!")
        return

    name, code, guide_url = split_message

    if not validators.url(guide_url):
        await send_error("Неверная ссылка на телеграф!")
        return

    db.add_service(name, code, guide_url)

    await state.finish()
    await show_services(ask_message)


#endregion

#region: Cancel


@dp.callback_query_handler(services_callback_data.filter(action="cancel"), state="*")
async def service_delete_confirm(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    await state.finish()
    await show_services(call.message)


#endregion