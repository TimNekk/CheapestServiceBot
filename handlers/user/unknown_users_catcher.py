from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType

from filters import IsInDB
from handlers.user.start import start_unknown
from loader import dp


@dp.message_handler(IsInDB(reverse=True), content_types=ContentType.ANY)
async def bot_echo(message: types.Message, state: FSMContext):
    await start_unknown(message, state)