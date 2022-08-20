import asyncio
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Optional

from aiogram import types
from aiogram.utils.exceptions import MessageCantBeDeleted
from aiogram.utils.markdown import hcode
from loguru import logger

from data.config import ADMIN_NICKNAME
from keyboards.inline import resend_keyboard, resend_callback_data
from keyboards.inline.admin import delete_number_keyboard
from loader import db, vak_sms, dp
from utils.db_api.number import Number
from utils.notify_admins import notify_admins
from utils.vak_sms import IdNumNotFound, NoCode, Status, NoNumber


async def give_number(call: types.CallbackQuery, category_id: int):
    user = db.get_user(call.message.chat.id)
    category = db.get_category(category_id)
    numbers = category.get_numbers()

    working_number: Optional[Number] = None
    for number in numbers:
        try:
            vak_sms.get_code(number.id)
        except IdNumNotFound:
            continue
        except NoCode:
            working_number = number
            break

        working_number = number

    if not working_number:
        for number in numbers:
            try:
                working_number = number.prolong()
                break
            except NoNumber:
                await notify_admins(f"Номер {number.phone_number} не работает",
                                    reply_markup=delete_number_keyboard(number.id))

    if not working_number:
        text = f"""
В настоящий момент нет доступных номеров
Пожалуйста, обратитесь к администратору {ADMIN_NICKNAME}
"""
        await user.send_message(text)
        await notify_admins(f"<b>Нет номер из категории:</b> {category.service.name} - {category.name}")
        return

    working_number.set_busy(True)

    text = f"""
<b>Успешно!</b>
<b>Номер:</b> 7{hcode(str(working_number.phone_number)[1:])}
<b>Время на активацию:</b> 60 минут

Вы можете входить в аккаунт, я сразу же отправлю вам код из СМС.
Новые смс можно будет получать в течении 60 минут.
"""

    with suppress(MessageCantBeDeleted):
        await call.message.delete()
    await user.send_message(text)
    logger.info(f"{user.id} получил номер {working_number.phone_number} ({working_number.id})")

    await asyncio.sleep(5)
    text = f"""
<b>Аккаунт рабочий. На нашей стороне проблем нет.</b>

<i>Что ты можешь сделать?</i>

1. Удалить приложение Urent
2. Перейти на мобильные интернет
3. Перезагрузить телефон
4. Установить Urent
5. Войти в аккаунт
"""
    await user.send_message(text)

    activation_time = datetime.utcnow() + timedelta(minutes=60)
    await wait_for_code(working_number.id, user.id, activation_time)

    await asyncio.sleep((activation_time - datetime.utcnow()).total_seconds())

    await user.send_message(f"Время на активацию для номера 7{hcode(str(working_number.phone_number)[1:])} истекло")
    working_number.delete()


async def wait_for_code(number_id: str, user_id: int, activation_time: datetime) -> None:
    user = db.get_user(user_id)
    number = db.get_number(number_id)
    vak_sms.set_status(number.id, Status.RESEND)

    while activation_time > datetime.utcnow():
        try:
            code = vak_sms.get_code(number.id)
        except NoCode:
            await asyncio.sleep(5)
            continue
        except IdNumNotFound:
            number.prolong()
            continue

        text = f"""
<b>Номер:</b> 7{hcode(str(number.phone_number)[1:])}
<b>Код из СМС:</b> {hcode(code)}
"""
        await user.send_message(text, reply_markup=resend_keyboard(number_id, activation_time.timestamp()))
        logger.info(f"{user.id} получил код {code} от {number.phone_number} ({number.id})")
        return


@dp.callback_query_handler(resend_callback_data.filter())
async def resend_code(call: types.CallbackQuery, callback_data: dict):
    with suppress(Exception):
        await call.message.delete_reply_markup()

    number_id = callback_data.get("number_id")
    activation_time = datetime.fromtimestamp(float(callback_data.get("activation_time_timestamp")))

    if activation_time < datetime.utcnow():
        with suppress(Exception):
            await call.message.edit_text("Время на активацию истекло")
        return

    await wait_for_code(number_id, call.message.chat.id, activation_time)
