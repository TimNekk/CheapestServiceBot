import asyncio
from datetime import datetime, timedelta
from typing import Optional

from aiogram import types
from aiogram.utils.markdown import hcode
from loguru import logger

from data.config import ADMIN_NICKNAME
from keyboards.inline.admin import delete_number_keyboard
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

    logger.info(f"{user.id} получил номер {working_number.phone_number} ({working_number.id})")
    working_number.set_busy(True)

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

    await wait_for_code(working_number, call)


async def wait_for_code(working_number: Number, call: types.CallbackQuery) -> None:
    user = db.get_user(call.message.chat.id)

    give_time = datetime.utcnow()
    code: Optional[str] = None
    while give_time + timedelta(minutes=20) > datetime.utcnow():
        try:
            code = vak_sms.get_code(working_number.id)
        except NoCode:
            await asyncio.sleep(5)
            continue
        except IdNumNotFound:
            working_number.prolong()
            continue

        text = f"""
<b>Номер:</b> 7{hcode(str(working_number.phone_number)[1:])}
<b>Код из СМС:</b> {hcode(code)}
"""

        logger.info(f"{user.id} получил код {code} от {working_number.phone_number} ({working_number.id})")
        await user.send_message(text)
        vak_sms.set_status(working_number.id, Status.RESEND)

    if not code and working_number:
        working_number.set_busy(False)
        await user.send_message("Время на активацию истекло")
        return

    working_number.delete()
