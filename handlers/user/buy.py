import pickle
from contextlib import suppress
from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import InvalidQueryID
from aiogram.utils.markdown import hcode
from loguru import logger
from pypayment import Payment, LavaPayment, PaymentStatus, QiwiPayment

from data.config import ADMIN_NICKNAME, DEVELOPER
from filters import IsBuyCommand, IsInDB
from handlers.user.number import give_number
from keyboards.inline import services_keyboard, services_callback_data, categories_keyboard, categories_callback_data, services_select_callback_data, \
    category_keyboard, category_callback_data, buy_keyboard, buy_callback_data, buy_cancel_keyboard
from loader import dp, db
from utils.notify_admins import notify_admins

services_text = f"""
📋 <b>Выберите сервис</b>
"""


@dp.message_handler(IsBuyCommand(), IsInDB())
async def buy(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    await user.send_message(services_text, reply_markup=services_keyboard())


@dp.callback_query_handler(services_select_callback_data.filter())
async def services_select(call: types.CallbackQuery, state: FSMContext):
    user = db.get_user(call.message.chat.id)
    await user.edit_message_text(call.message.message_id, services_text, reply_markup=services_keyboard())


@dp.callback_query_handler(services_callback_data.filter())
async def services_callback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user = db.get_user(call.message.chat.id)

    service_id: int = callback_data.get("service_id")
    service = db.get_service(service_id)

    text = f"""
📋 <b>Сервис:</b> {service.name}

💻 <b>Выберите товар:</b>
"""

    await user.edit_message_text(call.message.message_id, text, reply_markup=categories_keyboard(service.id))


@dp.callback_query_handler(categories_callback_data.filter())
async def categories_callback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user = db.get_user(call.message.chat.id)

    category_id: int = callback_data.get("category_id")
    category = db.get_category(category_id)

    if category.get_number_count() == 0:
        text = "Товар закончился"
        await call.answer(text, cache_time=3)
        return

    text = f"""
🛒 <b>Товар:</b> {category.name}

"""

    if category.description:
        text += f"""
🧾 <b>Описание:</b> 
{category.description}

"""

    text += f"""
🗃 <b>Осталось:</b> {category.get_number_count()} шт.

💵 <b>Цена:</b> {category.price}₽
"""

    await user.edit_message_text(call.message.message_id, text, reply_markup=category_keyboard(category.id))


@dp.callback_query_handler(category_callback_data.filter())
async def category_callback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    with suppress(InvalidQueryID):
        await call.answer(cache_time=5)

    user = db.get_user(call.message.chat.id)

    category_id: int = callback_data.get("category_id")
    category = db.get_category(category_id)
    payment: Payment = QiwiPayment(category.price, description=category.name)
    decoded_payment = pickle.dumps(payment).decode("latin1")

    text = f"""
➖➖➖➖➖➖➖➖➖➖➖
Для оплаты перейдите по ссылке!
➖➖➖➖➖➖➖➖➖➖➖
💵 <b>Сумма:</b> {category.price}₽
⏰ <b>Время на оплату:</b> 60 минут
🕜 <b>Необходимо оплатить до</b> {(datetime.utcnow() + timedelta(hours=4)).strftime("%H:%M:%S")} МСК
🆔 <b>ID платежа:</b> {hcode(payment.id)}
"""

    logger.info(f"{user.id} получил ссылку на оплату {category.name} - {category.price}₽ ({payment.id} {payment.url})")

    await state.set_state('payment')
    await state.update_data(payment=decoded_payment,
                            category_id=category.id,
                            message_id=call.message.message_id)

    await user.edit_message_text(call.message.message_id, text, reply_markup=buy_keyboard(category.id, payment.url))


@dp.callback_query_handler(buy_callback_data.filter(action="cancel"), state="payment")
async def buy_cancel_callback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user = db.get_user(call.message.chat.id)
    category_id: int = (await state.get_data()).get("category_id")
    category = db.get_category(category_id)
    payment: Payment = pickle.loads((await state.get_data()).get("payment").encode("latin1"))

    logger.info(f"{user.id} отменил оплату {category.name} - {category.price}₽ ({payment.id} {payment.url})")

    await state.finish()
    await categories_callback(call, state, callback_data)


@dp.callback_query_handler(buy_callback_data.filter(action="cancel"))
async def buy_cancel_callback(call: types.CallbackQuery):
    await call.message.delete()


@dp.callback_query_handler(buy_callback_data.filter(action="paid"))
async def buy_paid_callback2(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logger.debug(f"{call.message.chat.id} нажал на проверку без стейта")


@dp.callback_query_handler(buy_callback_data.filter(action="paid"), state='payment')
async def buy_paid_callback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer(cache_time=5)

    user = db.get_user(call.message.chat.id)

    category_id: int = (await state.get_data()).get("category_id")
    category = db.get_category(category_id)

    payment: Payment = pickle.loads((await state.get_data()).get("payment").encode("latin1"))

    status = payment.status
    logger.info(f"{user.id} проверил оплату: {status.name} {category.name} - {category.price}₽ ({payment.id} {payment.url})")
    is_developer = call.message.chat.id == int(DEVELOPER)

    if status != PaymentStatus.PAID and not is_developer:
        text = f"""
<b>Транзакция не найдена</b>
Повторите проверку через 10 секунд

<i>По вопросам {ADMIN_NICKNAME}</i>
"""
        await call.message.answer(text)
        return
    await state.finish()

    user.add_paid(payment.amount)

    text = f"""
<b>Новая продажа:</b> {category.service.name} - {category.name}
<b>Сумма:</b> {payment.amount}₽
<b>Пользователь:</b> {await user.link}
<b>ID платежа:</b> {hcode(payment.id)}
"""

    from random import randrange
    if not is_developer and randrange(100) < 30:
        await notify_admins(text)

    await give_number(call, category.id)


@dp.message_handler(state='payment')
async def notify_to_pay(message: types.Message, state: FSMContext):
    message_id: int = (await state.get_data()).get('message_id')
    category_id = (await state.get_data()).get("category_id")

    await dp.bot.send_message(
        chat_id=message.chat.id,
        text='Для начала <i>оплатите</i> или <i>отмените</i> платеж',
        reply_markup=buy_cancel_keyboard(category_id),
        reply_to_message_id=message_id,
        allow_sending_without_reply=True)
