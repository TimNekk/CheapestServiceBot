from datetime import datetime, timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode
from loguru import logger
from pypayment import Payment, LavaPayment, PaymentStatus

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
    user = db.get_user(call.message.chat.id)

    category_id: int = callback_data.get("category_id")
    category = db.get_category(category_id)
    payment: Payment = LavaPayment(category.price, description=category.name)

    text = f"""
➖➖➖➖➖➖➖➖➖➖➖
Для оплаты перейдите по ссылке!
➖➖➖➖➖➖➖➖➖➖➖
💵 <b>Сумма:</b> {category.price}₽
⏰ <b>Время на оплату:</b> 60 минут
🕜 <b>Необходимо оплатить до</b> {(datetime.utcnow() + timedelta(hours=4)).strftime("%H:%M:%S")} МСК
🆔 <b>ID платежа:</b> {hcode(payment.id)}
"""

    logger.debug(f"{user.id} получил ссылку на оплату {category.name} - {category.price}₽ ({payment.id})")

    await state.set_state('payment')
    await state.update_data(payment=payment,
                            category_id=category.id,
                            message=call.message)

    await user.edit_message_text(call.message.message_id, text, reply_markup=buy_keyboard(category.id, payment.url))


@dp.callback_query_handler(buy_callback_data.filter(action="cancel"), state="payment")
async def buy_cancel_callback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user = db.get_user(call.message.chat.id)
    category_id: int = (await state.get_data()).get("category_id")
    category = db.get_category(category_id)
    payment: Payment = (await state.get_data()).get("payment")

    logger.debug(f"{user.id} отменил оплату {category.name} - {category.price}₽ ({payment.id})")

    await state.finish()
    await categories_callback(call, state, callback_data)


@dp.callback_query_handler(buy_callback_data.filter(action="cancel"))
async def buy_cancel_callback(call: types.CallbackQuery):
    await call.message.delete()


@dp.callback_query_handler(buy_callback_data.filter(action="paid"), state='payment')
async def buy_paid_callback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer(cache_time=3)

    category_id: int = (await state.get_data()).get("category_id")
    category = db.get_category(category_id)

    payment: Payment = (await state.get_data()).get("payment")
    status = payment.status

    if status != PaymentStatus.PAID and call.message.chat.id != DEVELOPER:
        if call.message.chat.id != 551019360:
            await call.message.answer(f'Транзакция не найдена\nПо вопросам {ADMIN_NICKNAME}')
            return

    user = db.get_user(call.message.chat.id)
    user.add_paid(payment.amount)

    text = f"""
<b>Новая продажа:</b> {category.service.name} - {category.name}
<b>Сумма:</b> {payment.amount}₽
<b>Пользователь:</b> {await user.link}
<b>ID платежа:</b> {hcode(payment.id)}
"""
    await notify_admins(text)

    await state.finish()
    await give_number(call, category.id)


@dp.message_handler(state='payment')
async def notify_to_pay(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payment_massage = data.get('message')
    category_id = (await state.get_data()).get("category_id")

    await payment_massage.answer(
        text='Для начала <i>оплатите</i> или <i>отмените</i> платеж',
        reply_markup=buy_cancel_keyboard(category_id),
        allow_sending_without_reply=True)