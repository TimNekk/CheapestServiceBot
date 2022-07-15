from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.user.start import start_unknown
from keyboards.inline import subscribe_callback_data
from loader import dp


SUBSCRIPTION_FOUND_TEXT = "Подписка найдена. Можете пользоваться ботом."


@dp.callback_query_handler(subscribe_callback_data.filter())
async def subscribe_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer(SUBSCRIPTION_FOUND_TEXT)
    await call.message.delete()
    await start_unknown(call.message, state)
