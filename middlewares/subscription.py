from contextlib import suppress
from typing import Callable, Awaitable, Dict, Any, Optional

from aiogram import Dispatcher
from aiogram.dispatcher.handler import current_handler, CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import RetryAfter, ChatNotFound, InvalidQueryID
from loguru import logger

from data.config import Subscription
from keyboards.inline import subscribe_keyboard


class SubscriptionMiddleware(BaseMiddleware):
    async def on_process_message(self, message: Message, data: dict):
        await self.check_subscription(message)

    async def on_process_callback_query(self, call: CallbackQuery, data: dict):
        await self.check_subscription(call.message, call)

    @staticmethod
    async def check_subscription(message: Message, call: Optional[CallbackQuery] = None):
        dispatcher = Dispatcher.get_current()

        try:
            check_user = await dispatcher.bot.get_chat_member(chat_id=Subscription.id, user_id=message.chat.id)
        except ChatNotFound:
            logger.warning(f"Chat {Subscription.id} not found")
            return
        if check_user.status not in ['creator', 'administrator', 'member']:
            text = "Для продолжения подпишитесь на канал"

            try:
                if message.reply_markup == subscribe_keyboard():
                    with suppress(InvalidQueryID):
                        await call.answer(text)
                    raise CancelHandler()

                await message.answer(text, reply_markup=subscribe_keyboard())
                raise CancelHandler()
            except RetryAfter:
                print(message.chat.id)
                CancelHandler()

