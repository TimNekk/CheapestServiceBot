from aiogram import types
from aiogram.types import InputFile

from filters import IsAdmin
from loader import dp


@dp.message_handler(IsAdmin(), commands=['log', 'logs'])
async def send_logs(message: types.Message):
    await message.answer_document(InputFile('logs/CSB.log'))
