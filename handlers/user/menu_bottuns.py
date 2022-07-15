from aiogram import types
from aiogram.dispatcher import FSMContext

from data.config import ADMIN_NICKNAME, FEEDBACK_NICKNAME
from filters import IsGuideCommand, IsInDB, IsSupportCommand, IsFeedbackCommand
from keyboards.inline import services_keyboard
from loader import dp, db


@dp.message_handler(IsGuideCommand(), IsInDB())
async def guide(message: types.Message):
    user = db.get_user(message.from_user.id)

    text = f"""
📋 <b>Выберите сервис</b>
"""

    await user.send_message(text, reply_markup=services_keyboard(guides=True))


@dp.message_handler(IsSupportCommand(), IsInDB())
async def support(message: types.Message):
    user = db.get_user(message.from_user.id)

    text = f"""
По все вопросам - {ADMIN_NICKNAME}
"""

    await user.send_message(text)


@dp.message_handler(IsFeedbackCommand(), IsInDB())
async def feedback(message: types.Message):
    user = db.get_user(message.from_user.id)

    text = f"""
Наши отзывы - {FEEDBACK_NICKNAME}
"""

    await user.send_message(text)
