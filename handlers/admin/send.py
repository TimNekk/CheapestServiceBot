from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from aiogram_broadcaster import MessageBroadcaster

from data.config import Commands
from filters import IsAdmin
from keyboards.inline import broadcast_callback_data, broadcast_keyboard, broadcast_accept_keyboard
from loader import dp, db


@dp.message_handler(IsAdmin(), commands=Commands.Admin.send.command)
async def send_message(message: types.Message, state: FSMContext):
    user = db.get_user(message.chat.id)

    ask_message = await user.send_message(f'Введите текст для начала рассылки {dp.storage}', reply_markup=broadcast_keyboard())
    await state.set_state('broadcast_text')
    await state.update_data(ask_message_id=ask_message.message_id)


@dp.callback_query_handler(broadcast_callback_data.filter(action='cancel'), state='*')
async def cancel_broadcast(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()

    broadcast_message: id = (await state.get_data()).get('broadcast_message_id')
    try:
        await dp.bot.delete_message(broadcast_message)
    except Exception:
        pass

    await state.finish()


@dp.message_handler(content_types=ContentType.ANY, state='broadcast_text')
async def check_broadcast(message: types.Message, state: FSMContext):
    ask_message_id: int = (await state.get_data()).get('ask_message_id')
    try:
        await dp.bot.delete_message(message.chat.id, ask_message_id)
    except Exception:
        pass

    user = db.get_user(message.chat.id)

    broadcast_message = await message.send_copy(user.id)
    await message.delete()

    confirm_message = await user.send_message("Все пользователям будет отправлено сообщение 👆", reply_markup=broadcast_accept_keyboard())

    await state.update_data(broadcast_message_id=broadcast_message.message_id)
    await state.update_data(confirm_message_id=confirm_message.message_id)


@dp.callback_query_handler(broadcast_callback_data.filter(action='send'), state='broadcast_text')
async def start_broadcast(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    user = db.get_user(call.message.chat.id)

    broadcast_message_id: int = (await state.get_data()).get('broadcast_message_id')
    confirm_message_id: int = (await state.get_data()).get('confirm_message_id')

    await dp.bot.edit_message_reply_markup(call.message.chat.id, confirm_message_id, reply_markup=None)

    users_id = list(map(lambda u: u.id, db.get_all_users(without_ban=True)))
    await user.send_message(f'Рассылка на {len(users_id)} пользователей началась!')
    broadcast_message = await dp.bot.forward_message(call.message.chat.id, call.message.chat.id, broadcast_message_id)
    await broadcast_message.delete()
    await MessageBroadcaster(users_id, broadcast_message).run()

    await user.send_message('Рассылка закончилась!')

    await state.finish()
