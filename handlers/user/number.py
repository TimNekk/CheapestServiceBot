import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode
from loguru import logger

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

        if status == "success" or (status == "error" and response.get('message') == "STATUS_WAIT_CODE"):
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
<b>Номер:</b> 7{hcode(str(working_number.phone_number)[1:])}
<b>Время на активацию:</b> 20 минут

Вы можете входить в аккаунт, я сразу же отправлю вам код из СМС.
Новые смс будут приходить в течении 20 минут.
"""

    await call.message.delete()
    await user.send_message(text)

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

    await wait_for_code(working_number, sms_count, call)


async def wait_for_code(working_number: Number, sms_count: int, call: types.CallbackQuery) -> None:
    user = db.get_user(call.message.chat.id)

    give_time = datetime.utcnow()
    code: Optional[str] = None
    while give_time + timedelta(minutes=20) > datetime.utcnow():
        sms_s = sms_api.getRentStatus(working_number.id).get('values')
        logger.info(sms_s)
        logger.info(f"{len(sms_s)} {sms_count}")
        if len(sms_s) > sms_count and len(sms_s) > 0:
            try:
                logger.info("Getting code")
                code = re.findall(r"\d+", list(sms_s.values())[0].get("text"))[0]
            except IndexError:
                logger.error(f"Index Error for {sms_s}")
                await asyncio.sleep(3)
                continue

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
