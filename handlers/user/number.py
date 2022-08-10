import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode

from data.config import ADMIN_NICKNAME
from keyboards.inline.admin import delete_number_keyboard
from loader import db, sms_api
from utils.db_api.number import Number
from utils.notify_admins import notify_admins


async def give_number(call: types.CallbackQuery, category_id: int):
    user = db.get_user(call.message.chat.id)
    category = db.get_category(category_id)
    numbers = category.get_numbers()

    working_number: Optional[Number] = None
    for number in numbers:
        response = sms_api.getRentStatus(number.id)
        status = response.get('status')

        if status == "success" or (status == "error" and status.get('message') == "STATUS_WAIT_CODE"):
            working_number = number
            break

    if not working_number:
        text = f"""
В настоящий момент нет доступных номеров
Пожалуйста, обратитесь к администратору {ADMIN_NICKNAME}
"""
        await user.send_message(text)
        await notify_admins(f"<b>Нет номер из категории:</b> {category.service.name} - {category.name}")
        return

    working_number.set_busy(True)
    sms_count = len(response.get('values'))

    text = f"""
<b>Успешно!</b>
<b>Номер:</b> {hcode(working_number.phone_number)}
<b>Время на активацию:</b> 20 минут

Вы можете входить в аккаунт, я сразу же отправлю вам код из СМС.
Новые смс будут приходить в течении 20 минут.
"""

    await call.message.delete()
    await user.send_message(text)

    await asyncio.sleep(5)
    text = f"""
Если в течение 1 минуты вам не придёт код, <b>переустановите приложение и отключитесь от вай фай, и введите заново этот номер.</b>

<i>Если проблема не решится, пишите нам в поддержку.</i>
"""
    await user.send_message(text)

    await wait_for_code(working_number, sms_count, call)


async def wait_for_code(working_number: Number, sms_count: int, call: types.CallbackQuery) -> None:
    user = db.get_user(call.message.chat.id)

    give_time = datetime.utcnow()
    code: Optional[str] = None
    while give_time + timedelta(minutes=20) > datetime.utcnow():
        sms_s = sms_api.getRentStatus(working_number.id).get('values')
        if len(sms_s) > sms_count and len(sms_s) > 0:
            code = re.findall(r"Urent: (\d*)", list(sms_s.values())[0].get("text"))[0]

            text = f"""
            <b>Номер:</b> {hcode(working_number.phone_number)}
            <b>Код из СМС:</b> {hcode(code)}
            """

            await user.send_message(text)

            sms_count = len(sms_s)
        else:
            await asyncio.sleep(3)

    if not code and working_number:
        working_number.set_busy(False)
        await user.send_message("Время на активацию истекло")
        return

    working_number.delete()

    # TODO: (FUTURE) Сделать кнопку повторного запроса кода
