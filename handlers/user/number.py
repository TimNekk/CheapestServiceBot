import asyncio
from datetime import datetime, timedelta
from typing import Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode

from data.config import ADMIN_NICKNAME
from loader import db, vak_sms
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

        vak_sms.set_status(number.id, Status.RESEND)
        working_number = number

    if not working_number:
        for number in numbers:
            try:
                working_number = number.prolong()
                break
            except NoNumber:
                await notify_admins(f"Номер {number.phone_number} не работает")

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
<b>Номер:</b> {hcode(working_number.phone_number)}
<b>Время на активацию:</b> 20 минут

Вы можете входить в аккаунт, я сразу же отправлю вам код из СМС.
"""

    await call.message.delete()
    await user.send_message(text)

    await wait_for_code(working_number, call)


async def wait_for_code(working_number: Number, call: types.CallbackQuery) -> None:
    user = db.get_user(call.message.chat.id)

    give_time = datetime.utcnow()
    code: Optional[str] = None
    while give_time + timedelta(minutes=20) > datetime.utcnow():
        try:
            code = vak_sms.get_code(working_number.id)
            break
        except NoCode:
            await asyncio.sleep(3)
            continue
        except IdNumNotFound:
            working_number.prolong()
            continue

    if not code:
        working_number.set_busy(False)
        await user.send_message("Время на активацию истекло")
        return

    text = f"""
<b>Номер:</b> {hcode(working_number.phone_number)}
<b>Код из СМС:</b> {hcode(code)}
"""

    await user.send_message(text)

    working_number.delete()

    # TODO: (FUTURE) Сделать кнопку повторного запроса кода
