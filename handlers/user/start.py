from sqlite3 import IntegrityError

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart

from filters import IsInDB
from keyboards.default import menu_keyboard
from loader import dp, db


@dp.message_handler(IsInDB(reverse=True), CommandStart(), state='*')
async def start_unknown(message: types.Message, state: FSMContext):
    try:
        db.add_user(message.chat.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    except IntegrityError:
        pass

    await start(message, state)


@dp.message_handler(IsInDB(), CommandStart())
async def start(message: types.Message, state: FSMContext):
    user = db.get_user(message.chat.id)

    text = f"""
Добро пожаловать, {user.first_name} {user.last_name if user.last_name else ''}
"""

    await user.send_message(text, reply_markup=menu_keyboard())
